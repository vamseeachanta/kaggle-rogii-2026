"""Tests for the heel-anchored advancing-anchor DTW (issue #1, Phase 1 v2).

The v1 ``predict_tvt_via_correlation`` path must remain working (backward
compat) — covered by ``test_v1_path_still_works``. The new
``predict_tvt_advancing_anchor`` is asserted on synthetic shifted-but-similar
signals where the true alignment is known:

- on a clean shifted copy of a heel-built reference, the advancing anchor
  recovers the known offset within the grid step,
- the advancing anchor is monotone and terminates over a long toe,
- degenerate inputs (empty eval mask, flat window, no references) are handled,
- ``build_reference_from_heel`` collapses a fold-back heel without raising.
"""

from __future__ import annotations

import numpy as np
import pytest

from rogii.features.correlation import (
    build_reference_from_heel,
    predict_tvt_advancing_anchor,
    predict_tvt_via_correlation,
    resample_to_step,
)

RNG = np.random.default_rng(0)


def _wiggly_gr(n: int, *, seed: int = 0) -> np.ndarray:
    """A non-repeating-ish GR-like signal: sum of incommensurate sinusoids + noise."""
    rng = np.random.default_rng(seed)
    x = np.arange(n, dtype=float)
    sig = (
        30.0 * np.sin(x / 7.0)
        + 18.0 * np.sin(x / 23.0 + 0.6)
        + 12.0 * np.sin(x / 3.1 + 1.2)
        + 90.0
    )
    return sig + rng.normal(0.0, 1.0, size=n)


# --------------------------------------------------------------------------- #
# build_reference_from_heel
# --------------------------------------------------------------------------- #
def test_build_reference_from_heel_uniform_grid() -> None:
    tvt = np.arange(1000.0, 1100.0, 1.0)
    gr = _wiggly_gr(len(tvt))
    rd, rg = build_reference_from_heel(tvt, gr, step=1.0)
    assert rd.shape == rg.shape
    assert np.all(np.diff(rd) > 0)
    assert rd[0] == pytest.approx(1000.0)


def test_build_reference_collapses_foldback_heel() -> None:
    # A heel that folds back on itself in TVT (drill up then down) must not raise.
    up = np.arange(1000.0, 1050.0, 1.0)
    down = np.arange(1050.0, 1000.0, -1.0)
    tvt = np.concatenate([up, down])
    gr = _wiggly_gr(len(tvt))
    rd, rg = build_reference_from_heel(tvt, gr, step=1.0)
    assert np.all(np.diff(rd) > 0)


def test_build_reference_rejects_degenerate() -> None:
    with pytest.raises(ValueError):
        build_reference_from_heel(np.array([1000.0]), np.array([5.0]))


# --------------------------------------------------------------------------- #
# predict_tvt_advancing_anchor — known-offset recovery
# --------------------------------------------------------------------------- #
def test_recovers_known_constant_offset() -> None:
    """Toe GR is the reference GR shifted by a known constant TVT offset.

    Construct a long reference GR(TVT). The lateral toe walks through the same
    geology but its TVT is the reference depth minus a constant ``offset``. With
    the anchor seeded at the true start, each toe row should match back to
    ref_depth = toe_truth + offset's mirror — i.e. the prediction tracks the
    monotone true TVT to within the grid step.
    """
    step = 1.0
    ref_depth = np.arange(1000.0, 1600.0, step)
    ref_gr = _wiggly_gr(len(ref_depth), seed=1)

    # The toe's true TVT marches linearly; its GR is read off the reference at
    # that exact TVT (so the matching reference center IS the true TVT).
    n_toe = 200
    true_tvt = 1200.0 + np.arange(n_toe, dtype=float)  # 1 ft/row, inside ref span
    toe_gr = np.interp(true_tvt, ref_depth, ref_gr)

    md = np.arange(0.0, n_toe, 1.0)
    eval_mask = np.ones(n_toe, dtype=bool)

    pred = predict_tvt_advancing_anchor(
        md, toe_gr, eval_mask,
        references=[(ref_depth, ref_gr)],
        window_size=31,
        last_known_tvt=float(true_tvt[0]),
        max_search_ft=30.0,
    )
    err = np.abs(pred - true_tvt)
    # Median tracking error within a couple of grid steps; never runs away.
    assert np.median(err) <= 3.0
    assert np.max(err) <= 30.0  # hard search-band clamp holds


def test_heel_reference_preferred_over_secondary() -> None:
    """When the heel reference matches, the (misleading) secondary is not used."""
    step = 1.0
    depth = np.arange(1000.0, 1400.0, step)
    heel_gr = _wiggly_gr(len(depth), seed=2)
    # A secondary reference with totally different geology that would mislead.
    bad_gr = _wiggly_gr(len(depth), seed=99)

    n_toe = 100
    true_tvt = 1100.0 + np.arange(n_toe, dtype=float)
    toe_gr = np.interp(true_tvt, depth, heel_gr)

    md = np.arange(0.0, n_toe, 1.0)
    eval_mask = np.ones(n_toe, dtype=bool)

    pred = predict_tvt_advancing_anchor(
        md, toe_gr, eval_mask,
        references=[(depth, heel_gr), (depth, bad_gr)],
        window_size=31,
        last_known_tvt=float(true_tvt[0]),
        max_search_ft=30.0,
        min_corr=0.5,
    )
    assert np.median(np.abs(pred - true_tvt)) <= 3.0


# --------------------------------------------------------------------------- #
# advancing-anchor invariants: monotone & terminates
# --------------------------------------------------------------------------- #
def test_anchor_step_is_bounded_and_terminates() -> None:
    """Each prediction is within max_search_ft of the previous one (and finite)."""
    step = 1.0
    ref_depth = np.arange(0.0, 5000.0, step)
    ref_gr = _wiggly_gr(len(ref_depth), seed=3)

    n_toe = 4000
    toe_gr = _wiggly_gr(n_toe, seed=7)  # unrelated noise: worst case for jumps
    md = np.arange(0.0, n_toe, 1.0)
    eval_mask = np.ones(n_toe, dtype=bool)

    pred = predict_tvt_advancing_anchor(
        md, toe_gr, eval_mask,
        references=[(ref_depth, ref_gr)],
        window_size=51,
        last_known_tvt=2500.0,
        max_search_ft=30.0,
    )
    assert np.all(np.isfinite(pred))  # it terminated with a value for every row
    steps = np.abs(np.diff(pred))
    assert np.max(steps) <= 30.0 + 1e-6  # no row jumps more than the band


def test_anchor_monotone_when_truth_monotone() -> None:
    """On a cleanly increasing-TVT toe, predictions are (weakly) increasing."""
    step = 1.0
    ref_depth = np.arange(1000.0, 1800.0, step)
    ref_gr = _wiggly_gr(len(ref_depth), seed=4)
    n_toe = 300
    true_tvt = 1200.0 + np.arange(n_toe, dtype=float)
    toe_gr = np.interp(true_tvt, ref_depth, ref_gr)

    md = np.arange(0.0, n_toe, 1.0)
    eval_mask = np.ones(n_toe, dtype=bool)
    pred = predict_tvt_advancing_anchor(
        md, toe_gr, eval_mask,
        references=[(ref_depth, ref_gr)],
        window_size=31, last_known_tvt=float(true_tvt[0]), max_search_ft=30.0,
    )
    # Allow tiny local dips from noise but the trend must be increasing.
    assert pred[-1] > pred[0] + 0.5 * n_toe


# --------------------------------------------------------------------------- #
# degenerate handling
# --------------------------------------------------------------------------- #
def test_empty_eval_mask_returns_all_nan() -> None:
    ref_depth = np.arange(0.0, 100.0, 1.0)
    ref_gr = _wiggly_gr(len(ref_depth))
    md = np.arange(0.0, 50.0, 1.0)
    gr = _wiggly_gr(50)
    pred = predict_tvt_advancing_anchor(
        md, gr, np.zeros(50, dtype=bool),
        references=[(ref_depth, ref_gr)],
    )
    assert np.all(np.isnan(pred))


def test_no_references_raises() -> None:
    md = np.arange(0.0, 10.0, 1.0)
    gr = _wiggly_gr(10)
    with pytest.raises(ValueError):
        predict_tvt_advancing_anchor(md, gr, np.ones(10, dtype=bool), references=[])


def test_flat_window_holds_anchor() -> None:
    """A zero-variance query window cannot correlate → it holds the anchor."""
    ref_depth = np.arange(0.0, 200.0, 1.0)
    ref_gr = _wiggly_gr(len(ref_depth))
    n_toe = 20
    gr = np.full(n_toe, 100.0)  # perfectly flat → undefined correlation
    md = np.arange(0.0, n_toe, 1.0)
    pred = predict_tvt_advancing_anchor(
        md, gr, np.ones(n_toe, dtype=bool),
        references=[(ref_depth, ref_gr)],
        window_size=11, last_known_tvt=100.0, max_search_ft=30.0, min_corr=0.3,
    )
    # Flat query never clears min_corr → every prediction stays at the seed.
    assert np.allclose(pred, 100.0)


def test_deterministic_under_fixed_inputs() -> None:
    ref_depth = np.arange(0.0, 500.0, 1.0)
    ref_gr = _wiggly_gr(len(ref_depth), seed=5)
    toe_gr = _wiggly_gr(120, seed=6)
    md = np.arange(0.0, 120.0, 1.0)
    mask = np.ones(120, dtype=bool)
    a = predict_tvt_advancing_anchor(md, toe_gr, mask, references=[(ref_depth, ref_gr)], last_known_tvt=250.0)
    b = predict_tvt_advancing_anchor(md, toe_gr, mask, references=[(ref_depth, ref_gr)], last_known_tvt=250.0)
    assert np.array_equal(a, b, equal_nan=True)


# --------------------------------------------------------------------------- #
# backward compatibility: v1 path unchanged
# --------------------------------------------------------------------------- #
def test_v1_path_still_works() -> None:
    ref_depth = np.arange(0.0, 300.0, 1.0)
    ref_gr = _wiggly_gr(len(ref_depth))
    md = np.arange(0.0, 100.0, 1.0)
    gr = _wiggly_gr(100)
    eval_mask = np.zeros(100, dtype=bool)
    eval_mask[60:] = True
    out = predict_tvt_via_correlation(
        md, gr, eval_mask, ref_depth, ref_gr,
        window_size=21, last_known_tvt=150.0, drift_per_ft=0.5,
    )
    assert out.shape == (100,)
    assert np.all(np.isnan(out[:60]))
    assert np.all(np.isfinite(out[60:]))


def test_resample_to_step_unchanged() -> None:
    d = np.array([0.0, 1.0, 2.0, 3.0])
    v = np.array([0.0, 2.0, 4.0, 6.0])
    nd, nv = resample_to_step(d, v, step=0.5)
    assert nv[0] == pytest.approx(0.0)
    assert nv[-1] == pytest.approx(6.0)
