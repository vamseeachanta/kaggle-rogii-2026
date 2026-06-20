"""Tests for rogii.models.gbdt (issue #4, Phase 3 GBDT fusion).

Asserted on tiny, hand-checkable synthetic wells:
- the feature matrix has the right shape, only eval rows, the declared columns,
  and no NaN leakage (every prior is imputed to a finite value),
- residual reconstruction is exact: ``predict_tvt == carry_forward + residual_hat``,
- the model trains and predicts on a small synthetic set,
- leave-pad-out folds are a leakage-safe partition (reusing the #2 assertion).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from rogii.features.spatial import assign_pads, leave_pad_out_folds, well_midpoints
from rogii.models.gbdt import (
    FEATURE_COLUMNS,
    GBDTResult,
    build_feature_matrix,
    feature_importance,
    train_gbdt,
)


# ---------------------------------------------------------------------------
# Synthetic well factory
# ---------------------------------------------------------------------------


def _well(
    *,
    x: float,
    y: float,
    n_heel: int = 60,
    n_toe: int = 40,
    slope: float = 0.01,
    base: float = 100.0,
    seed: int = 0,
) -> pd.DataFrame:
    """A horizontal-well frame: a drifting TVT line, observed over the heel only.

    The toe rows have ``TVT_input = NaN`` (the eval zone) but keep ground-truth
    ``TVT`` so the residual target is defined. GR is a smooth wave so the DTW
    reference build does not degenerate.
    """
    rng = np.random.default_rng(seed)
    n = n_heel + n_toe
    md = np.arange(n, dtype=float) * 1.0 + 1000.0
    tvt = base + slope * (md - md[0])
    gr = 50.0 + 20.0 * np.sin(md / 7.0) + rng.normal(0, 0.5, n)
    z = -tvt  # trajectory proxy
    tvt_input = tvt.copy()
    tvt_input[n_heel:] = np.nan  # toe = eval zone
    return pd.DataFrame(
        {"MD": md, "X": x, "Y": y, "Z": z, "GR": gr, "TVT": tvt, "TVT_input": tvt_input}
    )


def _typewell(n: int = 120, base: float = 100.0) -> pd.DataFrame:
    tvt = np.linspace(base - 5, base + 5, n)
    gr = 50.0 + 20.0 * np.sin(tvt / 7.0)
    return pd.DataFrame({"TVT": tvt, "GR": gr, "Geology": "x"})


# ---------------------------------------------------------------------------
# Feature-matrix assembly
# ---------------------------------------------------------------------------


def test_feature_matrix_shape_and_columns():
    h = _well(x=0.0, y=0.0)
    nb = {"n1": _well(x=10.0, y=0.0, slope=0.012)}
    X = build_feature_matrix("w0", h, _typewell(), nb, np.array([10.0]))

    n_eval = int(h["TVT_input"].isna().sum())
    assert len(X) == n_eval, "one feature row per eval (toe) row"
    for c in FEATURE_COLUMNS:
        assert c in X.columns
    # eval rows only: the positional index must all be in the toe.
    assert (X.index >= 60).all()


def test_feature_matrix_no_nan_leakage():
    h = _well(x=0.0, y=0.0)
    # A neighbour that does NOT cover the toe MD range → offset prior is all-NaN
    # there; the matrix must still come out finite (imputed to 0 delta).
    nb = {"far": _well(x=1.0, y=1.0).assign(MD=lambda d: d["MD"] + 100000.0)}
    X = build_feature_matrix("w0", h, _typewell(), nb, np.array([5.0]))
    assert np.isfinite(X[list(FEATURE_COLUMNS)].to_numpy()).all(), "no NaN in features"


def test_carry_forward_feature_equals_last_heel_tvt():
    h = _well(x=0.0, y=0.0, n_heel=50, base=200.0, slope=0.0)
    nb = {"n1": _well(x=10.0, y=0.0)}
    X = build_feature_matrix("w0", h, None, nb, np.array([10.0]))
    last_heel = float(h["TVT_input"].dropna().iloc[-1])
    assert np.allclose(X["carry_forward_level"], last_heel)
    # residual target = truth - carry_forward
    assert np.allclose(X["residual"], X["tvt_truth"] - X["carry_forward_level"])


# ---------------------------------------------------------------------------
# Train / predict / residual reconstruction
# ---------------------------------------------------------------------------


def _training_matrix() -> pd.DataFrame:
    parts = []
    for i in range(6):
        h = _well(x=float(i), y=0.0, slope=0.005 * (i + 1), base=100.0 + i, seed=i)
        nb = {"a": _well(x=float(i) + 1, y=0.0, slope=0.006 * (i + 1), seed=i + 10)}
        parts.append(build_feature_matrix(f"w{i}", h, _typewell(base=100.0 + i), nb, np.array([1.0])))
    return pd.concat(parts, ignore_index=True)


def test_model_trains_and_predicts():
    X = _training_matrix()
    res = train_gbdt(X, seed=0, n_estimators=50)
    assert isinstance(res, GBDTResult)
    assert res.backend in {"lightgbm", "histgbr"}
    r_hat = res.predict_residual(X)
    assert r_hat.shape == (len(X),)
    assert np.isfinite(r_hat).all()


def test_residual_reconstruction_is_exact():
    X = _training_matrix()
    res = train_gbdt(X, seed=0, n_estimators=50)
    r_hat = res.predict_residual(X)
    tvt_hat = res.predict_tvt(X)
    # The model's TVT prediction is *exactly* carry-forward + predicted residual.
    expected = X["carry_forward_level"].to_numpy(dtype=float) + r_hat
    assert np.allclose(tvt_hat, expected, atol=1e-9)


def test_determinism_same_seed():
    X = _training_matrix()
    a = train_gbdt(X, seed=7, n_estimators=40).predict_residual(X)
    b = train_gbdt(X, seed=7, n_estimators=40).predict_residual(X)
    assert np.allclose(a, b)


def test_feature_importance_reported():
    X = _training_matrix()
    res = train_gbdt(X, seed=0, n_estimators=50)
    imp = feature_importance(res, X)
    assert set(imp.index) == set(FEATURE_COLUMNS)
    assert imp.is_monotonic_decreasing


# ---------------------------------------------------------------------------
# Leave-pad-out leakage safety (reuse of the issue #2 invariant)
# ---------------------------------------------------------------------------


def test_leave_pad_out_is_leakage_safe():
    # Two tight clusters (pads) far apart.
    wells = {
        "a1": _well(x=0.0, y=0.0),
        "a2": _well(x=10.0, y=0.0),
        "b1": _well(x=50000.0, y=0.0),
        "b2": _well(x=50010.0, y=0.0),
    }
    mids = well_midpoints(wells)
    pads = assign_pads(mids, eps=2000.0)
    folds = leave_pad_out_folds(pads)
    all_wells = set(wells)
    for fold in folds:
        # disjoint partition
        assert set(fold.test_wells).isdisjoint(fold.train_wells)
        assert set(fold.test_wells) | set(fold.train_wells) == all_wells
        # a test well's entire pad is held out: no pad-mate leaks into train.
        test_pads = {pads[w] for w in fold.test_wells}
        assert all(pads[w] not in test_pads for w in fold.train_wells)
