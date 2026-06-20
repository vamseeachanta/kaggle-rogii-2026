"""GBDT fusion of Phase-1/2/3 priors as a residual on carry-forward (issue #4).

Three priors were each tried standalone in earlier phases and *each lost* to the
carry-forward floor (11.53 ft eval-zone RMSE, ``docs/decisions.md`` 2026-05-05):

* heel-anchored advancing-anchor DTW (issue #1, ``rogii.features.correlation``),
* offset-well neighbour TVT prior (issue #2, ``rogii.features.spatial``),
* linear-extrapolation of the heel slope (issue #3, ``rogii.models.linear_extrap``).

Issue #4's framing -- echoed by #2's finding -- is that these are *priors to
fuse*, not competitors. The value a GBDT adds is **learning how to weight** them
against each other plus depth/trajectory/history context. The recommended
framing (and the one implemented here) is a **correction on top of
carry-forward**: the model predicts the *residual* ``r = TVT_truth -
carry_forward`` and the final prediction is ``carry_forward + r_hat``. At
worst the model learns ``r_hat ~= 0`` and degenerates back to the floor; any
signal it can extract is pure upside.

Leakage discipline
------------------
All offset/DTW priors are built from *other* wells (or the target's own observed
heel) only -- never from the toe truth being predicted. CV uses leave-pad-out
folds (issue #2): a target well's *entire pad* is excluded from both the GBDT
training rows and its neighbour pool, so correlated pad geology cannot leak in.

Backend
-------
LightGBM (``LGBMRegressor``) is the primary backend. If LightGBM is unavailable
the code falls back to sklearn's ``HistGradientBoostingRegressor`` (a histogram
GBDT with the same train/predict/feature-importance surface). The substitution
is recorded on the fitted model (``backend`` attribute) so the CV report can
note it.

Determinism: a fixed ``random_state`` seed, single-threaded
(``n_jobs=1`` / deterministic histogram), sorted feature columns.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from rogii.features.correlation import (
    build_reference_from_heel,
    predict_tvt_advancing_anchor,
    resample_to_step,
)
from rogii.features.spatial import SpatialIndex, offset_tvt_features
from rogii.models.linear_extrap import predict_carry_forward, predict_linear_extrap

# Ordered, stable feature-column list. Kept explicit so the matrix is identical
# across folds and the importance report is interpretable.
FEATURE_COLUMNS: tuple[str, ...] = (
    # --- priors (the things we are fusing) ---
    "carry_forward",      # #0 baseline level (the residual is measured off this)
    "dtw_delta",          # DTW v2 prediction minus carry-forward (issue #1)
    "linex_delta",        # linear-extrap prediction minus carry-forward (issue #3)
    "offset_delta",       # offset neighbour wmean (heel-anchored) minus carry-forward (#2)
    "offset_tilt",        # median neighbour dTVT/dMD (shared geological tilt, #2)
    "offset_var",         # cross-neighbour variance (prior-confidence proxy, #2)
    "offset_n",           # how many neighbours cover this row (#2)
    "offset_spread",      # neighbour q75 - q25 spread (#2)
    # --- depth / trajectory context ---
    "md_into_toe",        # MD distance from heel exit into the toe (ft)
    "frac_into_toe",      # md_into_toe normalised by total toe length [0, 1]
    "z",                  # absolute Z (TVD-ish) at the row
    "dz_dmd",             # local trajectory slope dZ/dMD
    # --- GR / history context (from the observed heel) ---
    "gr",                 # GR at the row (imputed)
    "heel_last_tvt",      # last observed heel TVT (== carry_forward level, kept for trees)
    "heel_slope",         # slope of the last-N observed heel TVT samples
    "heel_drift",         # observed heel TVT range (max - min)
)


def _impute_gr(gr: np.ndarray) -> np.ndarray:
    """Forward/back-fill GR gaps (matches the DTW CV harness imputation)."""
    if np.isnan(gr).any():
        return pd.Series(gr).ffill().bfill().to_numpy(dtype=float)
    return np.asarray(gr, dtype=float)


def _heel_slope(md: np.ndarray, tvt: np.ndarray, n_recent: int = 200) -> float:
    """Least-squares slope of the last ``n_recent`` observed heel TVT samples."""
    finite = np.isfinite(md) & np.isfinite(tvt)
    md, tvt = md[finite], tvt[finite]
    if len(md) < 2:
        return 0.0
    md, tvt = md[-n_recent:], tvt[-n_recent:]
    if np.ptp(md) == 0:
        return 0.0
    slope, _ = np.polyfit(md, tvt, 1)
    return float(slope)


def build_feature_matrix(
    well_id: str,
    h: pd.DataFrame,
    t: pd.DataFrame | None,
    neighbours: dict[str, pd.DataFrame],
    distances: np.ndarray,
    *,
    n_recent: int = 200,
) -> pd.DataFrame:
    """Assemble the per-eval-row GBDT feature matrix for one well.

    Only the *eval* rows (toe; ``TVT_input`` is NaN) get a feature row -- those
    are exactly the rows the competition scores. Every prior is expressed as a
    **delta from carry-forward** so the trees fuse corrections rather than
    re-deriving the absolute datum (each lateral has its own TVT datum, #2).

    Args:
        well_id: target well id (for traceability; not used as a feature).
        h: target horizontal-well frame (``MD, X, Y, Z, GR, TVT_input`` [, ``TVT``]).
        t: target typewell frame (``TVT, GR``) or ``None`` (DTW uses heel only).
        neighbours: ``{neighbour_id: horizontal_well_df}`` for the offset prior,
            already pad-filtered by the caller (no pad-mates).
        distances: 2D distances to ``neighbours`` (same order as the dict).
        n_recent: heel window for the linear-extrap slope / heel_slope feature.

    Returns:
        A DataFrame indexed by the eval-row positional index of ``h`` with the
        columns in :data:`FEATURE_COLUMNS`, plus ``well`` and (if ``TVT`` is
        present) ``residual`` (= ``TVT - carry_forward``) and ``carry_forward``
        target-helper columns. No NaNs in the feature columns (all are imputed /
        defaulted), so the matrix never leaks NaN structure into the model.
    """
    md = h["MD"].to_numpy(dtype=float)
    tvt_in = h["TVT_input"].to_numpy(dtype=float)
    eval_mask = ~np.isfinite(tvt_in)
    n = len(md)
    eval_idx = np.flatnonzero(eval_mask)

    cf = predict_carry_forward(h)            # length n, eval rows = last heel TVT
    linex = predict_linear_extrap(h, n_recent=n_recent)

    # DTW v2 prediction over the lateral (heel-anchored advancing anchor, #1).
    dtw = _dtw_prediction(h, t)

    # Offset neighbour prior, heel-anchored to the target's last observed TVT so
    # only the transferable *shape* contributes (mirrors cv_offset_well.py).
    off = offset_tvt_features(h, neighbours, distances)
    off_wmean = off["offset_wmean"].to_numpy(dtype=float)
    obs_idx = np.flatnonzero(np.isfinite(tvt_in))
    off_anchored = np.full(n, np.nan)
    if obs_idx.size and np.isfinite(off_wmean[obs_idx[-1]]):
        shift = float(tvt_in[obs_idx[-1]] - off_wmean[obs_idx[-1]])
        off_anchored = off_wmean + shift
    # q-spread feature
    q75 = off["offset_q75"].to_numpy(dtype=float) if "offset_q75" in off else np.full(n, np.nan)
    q25 = off["offset_q25"].to_numpy(dtype=float) if "offset_q25" in off else np.full(n, np.nan)
    off_spread = q75 - q25

    # Depth / trajectory context.
    z = h["Z"].to_numpy(dtype=float) if "Z" in h else np.zeros(n)
    dz_dmd = np.gradient(z, md) if n >= 2 else np.zeros(n)
    gr = _impute_gr(h["GR"].to_numpy(dtype=float)) if "GR" in h else np.zeros(n)

    heel_exit_md = float(md[obs_idx[-1]]) if obs_idx.size else float(md[0])
    md_into_toe = md - heel_exit_md
    toe_len = float(md[eval_idx].max() - heel_exit_md) if eval_idx.size else 1.0
    toe_len = toe_len if toe_len > 0 else 1.0
    frac_into_toe = md_into_toe / toe_len

    heel_last = float(tvt_in[obs_idx[-1]]) if obs_idx.size else 0.0
    h_slope = _heel_slope(md[obs_idx], tvt_in[obs_idx], n_recent) if obs_idx.size else 0.0
    heel_tvt = tvt_in[obs_idx]
    h_drift = float(heel_tvt.max() - heel_tvt.min()) if heel_tvt.size else 0.0

    rows: dict[str, np.ndarray] = {
        "carry_forward": cf,
        "dtw_delta": dtw - cf,
        "linex_delta": linex - cf,
        "offset_delta": off_anchored - cf,
        "offset_tilt": off["offset_tilt"].to_numpy(dtype=float),
        "offset_var": off["offset_var"].to_numpy(dtype=float),
        "offset_n": off["offset_n"].to_numpy(dtype=float),
        "offset_spread": off_spread,
        "md_into_toe": md_into_toe,
        "frac_into_toe": frac_into_toe,
        "z": z,
        "dz_dmd": dz_dmd,
        "gr": gr,
        "heel_last_tvt": np.full(n, heel_last),
        "heel_slope": np.full(n, h_slope),
        "heel_drift": np.full(n, h_drift),
    }

    out = pd.DataFrame({c: rows[c][eval_idx] for c in FEATURE_COLUMNS}, index=eval_idx)
    # Defensive imputation: any prior that returned NaN for an eval row (no
    # neighbour coverage / degenerate heel) becomes a 0 *delta* (i.e. fall back
    # to carry-forward for that prior), and other context NaNs become 0. This is
    # what keeps the residual framing a strict superset of the floor.
    out = out.fillna(0.0)
    out["well"] = well_id
    out["carry_forward_level"] = cf[eval_idx]
    if "TVT" in h.columns:
        y = h["TVT"].to_numpy(dtype=float)[eval_idx]
        out["residual"] = y - cf[eval_idx]
        out["tvt_truth"] = y
    return out


def _dtw_prediction(h: pd.DataFrame, t: pd.DataFrame | None) -> np.ndarray:
    """Heel-anchored advancing-anchor DTW prediction over the lateral (issue #1).

    Returns a length-``len(h)`` array: eval rows carry the DTW prediction, heel
    rows echo ``TVT_input``. Falls back to carry-forward on degenerate wells.
    """
    md = h["MD"].to_numpy(dtype=float)
    tvt_in = h["TVT_input"].to_numpy(dtype=float)
    eval_mask = ~np.isfinite(tvt_in)
    cf = predict_carry_forward(h)
    obs_idx = np.flatnonzero(np.isfinite(tvt_in))
    if obs_idx.size < 2 or not eval_mask.any():
        return cf
    gr = _impute_gr(h["GR"].to_numpy(dtype=float)) if "GR" in h else np.zeros(len(md))
    last_known = float(tvt_in[obs_idx[-1]])

    references: list[tuple[np.ndarray, np.ndarray]] = []
    try:
        references.append(build_reference_from_heel(tvt_in[obs_idx], gr[obs_idx], step=1.0))
    except ValueError:
        pass
    if t is not None and {"TVT", "GR"}.issubset(t.columns):
        try:
            references.append(
                resample_to_step(t["TVT"].to_numpy(float), t["GR"].to_numpy(float), step=1.0)
            )
        except ValueError:
            pass
    if not references:
        return cf

    pred = predict_tvt_advancing_anchor(
        md, gr, eval_mask, references,
        window_size=51, last_known_tvt=last_known, max_search_ft=30.0, min_corr=0.3,
    )
    out = cf.copy()
    ok = eval_mask & np.isfinite(pred)
    out[ok] = pred[ok]
    return out


@dataclass
class GBDTResult:
    """A fitted residual-on-carry-forward GBDT and its provenance."""

    model: object
    backend: str  # "lightgbm" or "histgbr"
    feature_columns: tuple[str, ...] = field(default=FEATURE_COLUMNS)

    def predict_residual(self, X: pd.DataFrame) -> np.ndarray:
        """Predict the residual ``r_hat`` for a feature matrix."""
        return np.asarray(self.model.predict(X[list(self.feature_columns)]), dtype=float)

    def predict_tvt(self, X: pd.DataFrame) -> np.ndarray:
        """Reconstruct ``TVT = carry_forward + r_hat`` (the model's actual prediction).

        Requires the ``carry_forward_level`` helper column on ``X`` (emitted by
        :func:`build_feature_matrix`). The reconstruction is exact: the returned
        prediction equals the carry-forward level plus the predicted residual.
        """
        return X["carry_forward_level"].to_numpy(dtype=float) + self.predict_residual(X)


def train_gbdt(
    X: pd.DataFrame,
    *,
    seed: int = 0,
    n_estimators: int = 400,
    learning_rate: float = 0.03,
    num_leaves: int = 31,
    max_depth: int = -1,
    min_child_samples: int = 40,
) -> GBDTResult:
    """Train a residual-predicting GBDT on an assembled feature matrix.

    ``X`` must carry the :data:`FEATURE_COLUMNS` plus a ``residual`` target
    column (= ``TVT - carry_forward``). LightGBM is used when importable; else
    sklearn ``HistGradientBoostingRegressor``. Deterministic for a fixed seed.
    """
    if "residual" not in X.columns:
        raise ValueError("training matrix needs a 'residual' target column")
    feats = list(FEATURE_COLUMNS)
    X_train = X[feats]
    y_train = X["residual"].to_numpy(dtype=float)

    try:
        import lightgbm as lgb

        model = lgb.LGBMRegressor(
            objective="regression",
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            num_leaves=num_leaves,
            max_depth=max_depth,
            min_child_samples=min_child_samples,
            subsample=1.0,
            random_state=seed,
            n_jobs=1,
            deterministic=True,
            force_row_wise=True,
            verbose=-1,
        )
        model.fit(X_train, y_train)
        return GBDTResult(model=model, backend="lightgbm")
    except ImportError:
        from sklearn.ensemble import HistGradientBoostingRegressor

        model = HistGradientBoostingRegressor(
            loss="squared_error",
            max_iter=n_estimators,
            learning_rate=learning_rate,
            max_leaf_nodes=num_leaves,
            max_depth=None if max_depth < 0 else max_depth,
            min_samples_leaf=min_child_samples,
            random_state=seed,
        )
        model.fit(X_train, y_train)
        return GBDTResult(model=model, backend="histgbr")


def feature_importance(result: GBDTResult, X: pd.DataFrame | None = None) -> pd.Series:
    """Return a feature-importance Series (descending), indexed by feature name.

    LightGBM exposes a native ``feature_importances_`` (split-count gain). The
    sklearn HistGBR fallback has no native importance, so we compute permutation
    importance on ``X`` (which must then carry ``residual``); without ``X`` a
    uniform series is returned with a note in the index name.
    """
    feats = list(result.feature_columns)
    if result.backend == "lightgbm":
        imp = np.asarray(result.model.feature_importances_, dtype=float)
        s = pd.Series(imp, index=feats, name="lightgbm_gain")
        return s.sort_values(ascending=False)
    # HistGBR: permutation importance if we have a labelled matrix.
    if X is not None and "residual" in X.columns:
        from sklearn.inspection import permutation_importance

        r = permutation_importance(
            result.model, X[feats], X["residual"].to_numpy(dtype=float),
            n_repeats=5, random_state=0, n_jobs=1,
        )
        s = pd.Series(r.importances_mean, index=feats, name="histgbr_perm")
        return s.sort_values(ascending=False)
    return pd.Series(np.zeros(len(feats)), index=feats, name="unavailable")
