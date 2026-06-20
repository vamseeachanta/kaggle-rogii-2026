"""Tests for rogii.models.linear_extrap (issue #3, Phase 0.5).

The extrapolation math is asserted exactly:
- an exact line in → the same line extrapolated out,
- a flat heel in → flat out (must match carry-forward),
- degenerate windows (n_recent=1, single point, all-NaN) handled gracefully,
- the clip guard bounds a runaway slope.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from rogii.models.linear_extrap import (
    fit_line,
    predict_carry_forward,
    predict_linear_extrap,
)


def _make_well(tvt_full: np.ndarray, n_heel: int, md0: float = 1000.0) -> pd.DataFrame:
    """Build a well frame: TVT (truth) full, TVT_input observed only on the heel.

    MD is a 1-ft step starting at md0; TVT_input is NaN past row n_heel (the toe
    eval zone), mirroring the real data shape.
    """
    n = len(tvt_full)
    md = md0 + np.arange(n, dtype=float)
    tvt_input = tvt_full.astype(float).copy()
    tvt_input[n_heel:] = np.nan
    return pd.DataFrame({"MD": md, "TVT": tvt_full.astype(float), "TVT_input": tvt_input})


def test_fit_line_recovers_exact_slope_intercept() -> None:
    md = np.array([100.0, 101.0, 102.0, 103.0])
    tvt = 2.5 * md - 7.0
    slope, intercept = fit_line(md, tvt)
    assert slope == pytest.approx(2.5)
    assert intercept == pytest.approx(-7.0)


def test_exact_line_input_extrapolates_exactly() -> None:
    """A heel that is a perfect line must extrapolate to that same line on the toe."""
    n, n_heel = 50, 30
    md = 1000.0 + np.arange(n, dtype=float)
    slope, intercept = 0.3, 5.0
    tvt_full = slope * md + intercept
    h = _make_well(tvt_full, n_heel)

    # Wide clip so the (legitimate, in-trend) extrapolation is not bounded away.
    pred = predict_linear_extrap(h, n_recent=n_heel, clip_margin_factor=1000.0)

    # Toe predictions must equal the true line (the data IS that line).
    np.testing.assert_allclose(pred[n_heel:], tvt_full[n_heel:], rtol=0, atol=1e-6)
    # Heel rows echo the observed input unchanged.
    np.testing.assert_allclose(pred[:n_heel], tvt_full[:n_heel], atol=1e-9)


def test_flat_input_matches_carry_forward() -> None:
    """A flat heel → flat toe at the last value; identical to carry-forward."""
    n, n_heel = 40, 25
    tvt_full = np.full(n, 11250.0)
    h = _make_well(tvt_full, n_heel)

    lin = predict_linear_extrap(h, n_recent=10)
    cf = predict_carry_forward(h)

    np.testing.assert_allclose(lin, cf, atol=1e-9)
    # And every toe prediction is exactly the last observed heel value.
    np.testing.assert_allclose(lin[n_heel:], 11250.0, atol=1e-9)


def test_n_recent_one_degenerates_to_carry_forward() -> None:
    """n_recent<=1 cannot define a slope → must fall back to carry-forward."""
    n, n_heel = 30, 20
    md = 1000.0 + np.arange(n, dtype=float)
    tvt_full = 0.5 * md  # sloping truth
    h = _make_well(tvt_full, n_heel)

    lin = predict_linear_extrap(h, n_recent=1)
    cf = predict_carry_forward(h)
    np.testing.assert_allclose(lin, cf, atol=1e-9)


def test_all_nan_input_returns_zeros() -> None:
    """No observed heel at all → carry-forward floor of 0.0 everywhere."""
    n = 10
    h = pd.DataFrame(
        {
            "MD": 1000.0 + np.arange(n, dtype=float),
            "TVT": np.zeros(n),
            "TVT_input": np.full(n, np.nan),
        }
    )
    pred = predict_linear_extrap(h, n_recent=5)
    np.testing.assert_allclose(pred, 0.0, atol=1e-9)


def test_no_eval_rows_returns_observed() -> None:
    """A fully-observed well (no toe) returns its TVT_input untouched."""
    n = 8
    tvt = 11000.0 + np.arange(n, dtype=float)
    h = pd.DataFrame({"MD": 1000.0 + np.arange(n, dtype=float), "TVT": tvt, "TVT_input": tvt})
    pred = predict_linear_extrap(h, n_recent=5)
    np.testing.assert_allclose(pred, tvt, atol=1e-9)


def test_clip_guard_bounds_runaway_slope() -> None:
    """A steep slope over a long toe is clipped to the heel range + margin."""
    n, n_heel = 5000, 200
    md = 1000.0 + np.arange(n, dtype=float)
    # Steep heel slope (1.0 ft/ft) → unclipped would reach ~+4800 ft over the toe.
    tvt_full = 1.0 * md
    h = _make_well(tvt_full, n_heel)

    heel = tvt_full[:n_heel]
    heel_min, heel_max = heel.min(), heel.max()
    drift = heel_max - heel_min
    margin = 1.5 * drift

    pred = predict_linear_extrap(h, n_recent=n_heel, clip_margin_factor=1.5)
    assert pred[n_heel:].max() <= heel_max + margin + 1e-6
    assert pred[n_heel:].min() >= heel_min - margin - 1e-6
    # The far-toe prediction must actually be clipped (hit the upper bound).
    assert pred[-1] == pytest.approx(heel_max + margin)


def test_n_recent_uses_only_recent_window() -> None:
    """Slope is fit on the LAST n_recent heel rows, not the whole heel.

    A heel that is flat early then turns sloping at the end should extrapolate
    with the recent (sloping) trend when n_recent is small.
    """
    n, n_heel = 60, 40
    md = 1000.0 + np.arange(n, dtype=float)
    tvt_full = np.empty(n)
    tvt_full[:20] = 5000.0  # flat early heel
    tvt_full[20:] = 5000.0 + 2.0 * (md[20:] - md[20])  # then slope 2.0
    h = _make_well(tvt_full, n_heel)

    # Last 10 heel rows are purely on the slope-2 segment.
    pred = predict_linear_extrap(h, n_recent=10, clip_margin_factor=1000.0)
    # First toe row continues the slope-2 trend from the last heel point.
    expected_first_toe = tvt_full[n_heel - 1] + 2.0
    assert pred[n_heel] == pytest.approx(expected_first_toe, abs=1e-6)
