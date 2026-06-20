"""Offset-well spatial features and leave-pad-out CV (issue #2, Phase 2).

Task-brief slides 12-13 promote neighbouring ("offset") wells from a stretch
goal to a *primary* signal: geological dip is correlated across pad-mates, so an
offset well's ``TVT(MD)`` trajectory is a usable prior for the current well.

This module is pure feature engineering over **train coordinates only** -- it has
no upstream dependency on the correlation/DTW work (issue #1/#3). It provides:

1. ``well_midpoints`` -- collapse each well's per-row (X, Y) into a single
   lateral-midpoint coordinate.
2. ``SpatialIndex`` -- a KDTree over those midpoints with a K-NN query that
   *excludes the query well itself* (and, for leave-pad-out, its whole pad).
3. ``offset_tvt_features`` -- for each target row, project every neighbour's
   ``TVT(MD)`` into the target's MD frame (linear interpolation in MD), then emit
   distance-weighted mean, median, quantiles, cross-neighbour variance, and the
   median local tilt ``dTVT/dMD`` across neighbours.
4. ``assign_pads`` -- DBSCAN clustering of midpoints into pads.
5. ``leave_pad_out_folds`` -- CV fold generator that holds out an *entire* pad
   per fold, so a well's own pad never appears in its training fold (no leakage
   of correlated geology through the neighbour prior).

Everything is deterministic: KDTree ties broken by index order, DBSCAN is
deterministic for fixed inputs/params, and the fold order is sorted by pad id.

References: ``scripts/cv_linear_extrap.py`` (CV harness pattern, issue #3),
``src/rogii/features/correlation.py`` (``rmse`` helper), ``src/rogii/paths.py``
(issue #9).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.cluster import DBSCAN

# ---------------------------------------------------------------------------
# Well coordinates
# ---------------------------------------------------------------------------


def lateral_midpoint(well: pd.DataFrame) -> tuple[float, float]:
    """Return the lateral midpoint ``(X, Y)`` of a horizontal-well frame.

    The horizontal-well CSVs carry a per-row ``(X, Y, Z)`` trajectory; a single
    representative coordinate is the mean of the lateral's surveyed points. This
    is robust to uneven sampling along MD and cheap to compute.
    """
    if "X" not in well or "Y" not in well:
        raise ValueError("well frame must have X and Y columns")
    return float(well["X"].mean()), float(well["Y"].mean())


def well_midpoints(wells: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build a midpoint table from a mapping ``{well_id: horizontal_well_df}``.

    Returns a DataFrame indexed by well id with columns ``X``, ``Y`` (the lateral
    midpoints), sorted by well id for deterministic ordering.
    """
    rows = []
    for wid, df in wells.items():
        x, y = lateral_midpoint(df)
        rows.append((wid, x, y))
    out = pd.DataFrame(rows, columns=["well", "X", "Y"]).sort_values("well")
    return out.set_index("well")


# ---------------------------------------------------------------------------
# Spatial index (KDTree K-NN)
# ---------------------------------------------------------------------------


@dataclass
class Neighbours:
    """K-NN query result for one target well.

    Attributes:
        wells: neighbour well ids, nearest first.
        distances: 2D Euclidean distances (ft) to each neighbour, same order.
    """

    wells: list[str]
    distances: np.ndarray


class SpatialIndex:
    """KDTree over per-well lateral midpoints with self/pad-excluding K-NN.

    Construction is O(n log n); a K-NN query is well under a second for the full
    ~773-well train set (acceptance criterion in issue #2). Ties in distance are
    resolved by KDTree's internal ordering, which is deterministic for fixed
    inputs, and we then stably drop excluded wells -- so results are reproducible.
    """

    def __init__(self, midpoints: pd.DataFrame) -> None:
        if not {"X", "Y"}.issubset(midpoints.columns):
            raise ValueError("midpoints must have X and Y columns")
        self.well_ids: list[str] = list(midpoints.index)
        self._pos: dict[str, int] = {w: i for i, w in enumerate(self.well_ids)}
        self.coords: np.ndarray = midpoints[["X", "Y"]].to_numpy(float)
        self.tree = cKDTree(self.coords)

    def query(
        self,
        target: str,
        k: int = 5,
        *,
        exclude: set[str] | None = None,
    ) -> Neighbours:
        """Return the ``k`` nearest train wells to ``target`` by 2D distance.

        The target well is always excluded from its own neighbour set. Any well
        in ``exclude`` (e.g. every pad-mate of the target, for leave-pad-out) is
        also dropped. We over-query the tree and then filter, so the result still
        contains ``k`` neighbours whenever that many remain.
        """
        if target not in self._pos:
            raise KeyError(f"unknown well {target!r}")
        drop = {target}
        if exclude:
            drop |= exclude
        # Over-query: ask for k + |drop| so that after filtering we still have k.
        want = min(len(self.well_ids), k + len(drop))
        dists, idxs = self.tree.query(self.coords[self._pos[target]], k=want)
        dists = np.atleast_1d(dists)
        idxs = np.atleast_1d(idxs)
        out_w: list[str] = []
        out_d: list[float] = []
        for d, i in zip(dists, idxs):
            w = self.well_ids[int(i)]
            if w in drop:
                continue
            out_w.append(w)
            out_d.append(float(d))
            if len(out_w) == k:
                break
        return Neighbours(wells=out_w, distances=np.asarray(out_d, dtype=float))


def inverse_distance_weights(distances: np.ndarray, *, eps: float = 1.0) -> np.ndarray:
    """Normalised inverse-distance weights ``w_i = (1/(d_i+eps)) / sum_j ...``.

    ``eps`` (ft) guards against a zero/near-zero distance blowing up. Weights sum
    to 1. A single neighbour gets weight 1.
    """
    distances = np.asarray(distances, dtype=float)
    if distances.size == 0:
        return distances
    raw = 1.0 / (distances + eps)
    s = raw.sum()
    if s == 0:
        return np.full_like(raw, 1.0 / raw.size)
    return raw / s


# ---------------------------------------------------------------------------
# Offset-well feature emission
# ---------------------------------------------------------------------------


def project_neighbour_tvt(
    target_md: np.ndarray,
    neighbour: pd.DataFrame,
) -> np.ndarray:
    """Project a neighbour's ``TVT(MD)`` onto the target's MD grid.

    Linear interpolation of the neighbour's ``TVT`` as a function of its ``MD``,
    evaluated at ``target_md``. Outside the neighbour's MD coverage we return NaN
    (no extrapolation) so the neighbour simply doesn't contribute there.

    The neighbour frame must have ``MD`` and ``TVT`` columns. Rows with a NaN MD
    or TVT are dropped before interpolation; MD is sorted ascending.
    """
    md = neighbour["MD"].to_numpy(float)
    tvt = neighbour["TVT"].to_numpy(float)
    ok = np.isfinite(md) & np.isfinite(tvt)
    md, tvt = md[ok], tvt[ok]
    if md.size < 2:
        return np.full(np.shape(target_md), np.nan)
    order = np.argsort(md, kind="stable")
    md, tvt = md[order], tvt[order]
    # Collapse duplicate MDs (keep first) so np.interp sees a strictly-increasing x.
    keep = np.concatenate(([True], np.diff(md) > 0))
    md, tvt = md[keep], tvt[keep]
    out = np.interp(target_md, md, tvt, left=np.nan, right=np.nan)
    return out


def offset_tvt_features(
    target: pd.DataFrame,
    neighbours: dict[str, pd.DataFrame],
    distances: np.ndarray,
    *,
    quantiles: tuple[float, ...] = (0.25, 0.5, 0.75),
    eps: float = 1.0,
) -> pd.DataFrame:
    """Emit per-row offset-well features for one target well.

    For each target row (indexed by the target's ``MD``) we gather the projected
    ``TVT`` of every neighbour at that MD (NaN where a neighbour doesn't cover the
    depth), then summarise across neighbours:

    * ``offset_wmean``   -- inverse-distance-weighted mean of neighbour TVT.
    * ``offset_mean``    -- plain mean (unweighted).
    * ``offset_q{p}``    -- the requested quantiles (default 25/50/75).
    * ``offset_var``     -- cross-neighbour variance (a confidence proxy; high
      variance => neighbours disagree => weak prior).
    * ``offset_tilt``    -- median local ``dTVT/dMD`` across neighbours (the
      shared geological tilt), computed from each projected series.
    * ``offset_n``       -- how many neighbours actually cover each row.

    ``distances`` are the 2D distances to ``neighbours`` (same order as the dict's
    insertion / the KDTree query result). Returns a DataFrame aligned row-for-row
    with ``target``.
    """
    target_md = target["MD"].to_numpy(float)
    n_rows = target_md.size
    nb_ids = list(neighbours.keys())
    k = len(nb_ids)

    if k == 0:
        empty = pd.DataFrame(index=target.index)
        empty["offset_wmean"] = np.nan
        empty["offset_mean"] = np.nan
        for q in quantiles:
            empty[f"offset_q{int(round(q * 100))}"] = np.nan
        empty["offset_var"] = np.nan
        empty["offset_tilt"] = np.nan
        empty["offset_n"] = 0
        return empty

    distances = np.asarray(distances, dtype=float)
    weights = inverse_distance_weights(distances, eps=eps)  # (k,)

    # Projected TVT: shape (n_rows, k).
    proj = np.full((n_rows, k), np.nan)
    tilt = np.full((n_rows, k), np.nan)
    for j, wid in enumerate(nb_ids):
        col = project_neighbour_tvt(target_md, neighbours[wid])
        proj[:, j] = col
        # Local tilt dTVT/dMD on the target grid (gradient of the projection).
        with np.errstate(invalid="ignore"):
            tilt[:, j] = np.gradient(col, target_md)

    valid = np.isfinite(proj)  # (n_rows, k)
    n_valid = valid.sum(axis=1)

    # Weighted mean across only the valid neighbours (renormalise weights per row).
    w_row = np.where(valid, weights[None, :], 0.0)
    w_sum = w_row.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        wmean = np.nansum(np.where(valid, proj * w_row, 0.0), axis=1) / w_sum
    wmean = np.where(w_sum > 0, wmean, np.nan)

    mean = _nan_reduce(proj, np.nanmean)
    var = _nan_reduce(proj, np.nanvar)
    tilt_med = _nan_reduce(tilt, np.nanmedian)

    out = pd.DataFrame(index=target.index)
    out["offset_wmean"] = wmean
    out["offset_mean"] = mean
    for q in quantiles:
        out[f"offset_q{int(round(q * 100))}"] = _nan_quantile(proj, q)
    out["offset_var"] = var
    out["offset_tilt"] = tilt_med
    out["offset_n"] = n_valid
    return out


def _nan_reduce(arr: np.ndarray, fn) -> np.ndarray:
    """Apply a nan-aware row reduction, returning NaN for all-NaN rows."""
    with np.errstate(invalid="ignore"):
        allnan = np.all(~np.isfinite(arr), axis=1)
        out = np.empty(arr.shape[0])
        out[~allnan] = fn(arr[~allnan], axis=1)
        out[allnan] = np.nan
    return out


def _nan_quantile(arr: np.ndarray, q: float) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        allnan = np.all(~np.isfinite(arr), axis=1)
        out = np.empty(arr.shape[0])
        out[~allnan] = np.nanquantile(arr[~allnan], q, axis=1)
        out[allnan] = np.nan
    return out


# ---------------------------------------------------------------------------
# Pad clustering + leave-pad-out CV
# ---------------------------------------------------------------------------


def assign_pads(
    midpoints: pd.DataFrame,
    *,
    eps: float = 2000.0,
    min_samples: int = 1,
) -> pd.Series:
    """Cluster well midpoints into pads via DBSCAN on 2D (X, Y).

    ``eps`` is the neighbourhood radius in feet (issue #2 suggests ~500-2000 ft).
    With ``min_samples=1`` every well lands in a pad (no DBSCAN "noise" label of
    -1); a geographically isolated well becomes its own singleton pad. The
    returned labels are non-negative integers, deterministic for fixed inputs.

    Returns a Series indexed like ``midpoints`` mapping well -> pad id.
    """
    coords = midpoints[["X", "Y"]].to_numpy(float)
    labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(coords)
    # min_samples=1 guarantees no -1; but be defensive and remap any -1 to fresh ids.
    labels = _resolve_noise_to_singletons(labels)
    return pd.Series(labels, index=midpoints.index, name="pad")


def _resolve_noise_to_singletons(labels: np.ndarray) -> np.ndarray:
    labels = labels.copy()
    next_id = (labels.max() + 1) if labels.size and labels.max() >= 0 else 0
    for i in range(labels.size):
        if labels[i] == -1:
            labels[i] = next_id
            next_id += 1
    return labels


@dataclass
class PadFold:
    """One leave-pad-out CV fold.

    Attributes:
        pad: the held-out pad id.
        test_wells: wells belonging to the held-out pad (the validation set).
        train_wells: every other well (the fold's training set).
    """

    pad: int
    test_wells: list[str]
    train_wells: list[str]


def leave_pad_out_folds(pads: pd.Series) -> list[PadFold]:
    """Generate leave-pad-out CV folds from a well -> pad mapping.

    One fold per distinct pad: that pad's wells are the test set, all others are
    the train set. Folds are ordered by pad id for determinism.

    Leakage safety: by construction ``test_wells`` and ``train_wells`` are a
    disjoint partition of all wells, and a test well's *entire* pad is held out,
    so no pad-mate of any test well can appear in that fold's training set. The
    accompanying tests assert this explicitly.
    """
    folds: list[PadFold] = []
    well_index = list(pads.index)
    for pad in sorted(pads.unique()):
        test = [w for w in well_index if pads[w] == pad]
        train = [w for w in well_index if pads[w] != pad]
        folds.append(PadFold(pad=int(pad), test_wells=test, train_wells=train))
    return folds
