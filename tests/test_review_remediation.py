"""Tests for the deterministic review-2026-05-23 remediations.

Covers the three behavioural fixes from the review:

- ``resample_to_step`` uses an exact (linspace) sample count, so a long depth
  range with a float step does not drift by ±1 sample (MEDIUM, correlation.py:36).
- ``best_match_depth`` honours the ``expected_idx`` prior when the query window
  is flat (constant GR), instead of returning the series mid-point
  (LOW, correlation.py:70-71).
- ``predict_tvt_via_correlation`` rejects a non-uniform reference grid loudly
  instead of computing a garbage step from the first two samples
  (LOW, correlation.py:130).
"""

from __future__ import annotations

import numpy as np
import pytest

from rogii.features.correlation import (
    best_match_depth,
    predict_tvt_via_correlation,
    resample_to_step,
)


def test_resample_step_no_drift_over_long_range():
    """linspace grid keeps the exact step over a long range; arange would drift."""
    step = 0.1
    depth = np.array([0.0, 100000.0])
    value = np.array([0.0, 100000.0])
    new_depth, _ = resample_to_step(depth, value, step)
    # Exact sample count: (100000 / 0.1) + 1.
    assert len(new_depth) == 1000001
    # First/last pinned, and the realised step matches within float epsilon.
    assert new_depth[0] == pytest.approx(0.0)
    assert new_depth[-1] == pytest.approx(100000.0, abs=1e-6)
    diffs = np.diff(new_depth)
    assert np.allclose(diffs, step, atol=1e-9)


def test_resample_step_endpoint_exact_unit_step():
    new_depth, new_value = resample_to_step(
        np.array([10.0, 20.0]), np.array([1.0, 2.0]), step=1.0
    )
    assert len(new_depth) == 11
    assert new_depth[-1] == pytest.approx(20.0)
    assert new_value[-1] == pytest.approx(2.0)


def test_flat_query_returns_prior_depth_not_midpoint():
    """A constant (flat-GR) query honours the expected_idx prior."""
    ref_gr = np.sin(np.arange(100) / 5.0)
    ref_depth = np.arange(100, dtype=float) * 1.0
    flat_query = np.full(11, 42.0)  # zero variance → q_norm == 0
    expected_idx = 30
    depth, corr = best_match_depth(
        flat_query, ref_gr, ref_depth,
        expected_idx=expected_idx, search_radius=5,
    )
    assert corr == 0.0
    assert depth == pytest.approx(ref_depth[expected_idx])  # prior, not ref_depth[50]


def test_flat_query_clamps_out_of_range_prior():
    ref_depth = np.arange(10, dtype=float)
    depth, corr = best_match_depth(
        np.full(5, 7.0), np.sin(np.arange(10) / 2.0), ref_depth,
        expected_idx=999, search_radius=2,
    )
    assert depth == pytest.approx(ref_depth[-1])
    assert corr == 0.0


def test_flat_query_no_prior_falls_back_to_midpoint():
    ref_depth = np.arange(10, dtype=float)
    depth, corr = best_match_depth(np.full(5, 7.0), np.sin(np.arange(10)), ref_depth)
    assert depth == pytest.approx(ref_depth[5])
    assert corr == 0.0


def test_nonuniform_reference_grid_rejected():
    """predict_tvt_via_correlation refuses a non-uniform ref grid."""
    lateral_md = np.arange(20, dtype=float)
    lateral_gr = np.sin(lateral_md / 3.0)
    eval_mask = np.zeros(20, dtype=bool)
    eval_mask[10:] = True
    # Geometrically-spaced (non-uniform) reference depth.
    ref_depth = np.array([0.0, 1.0, 3.0, 7.0, 15.0, 31.0])
    ref_gr = np.sin(ref_depth)
    with pytest.raises(ValueError, match="uniform grid"):
        predict_tvt_via_correlation(
            lateral_md, lateral_gr, eval_mask, ref_depth, ref_gr,
            window_size=5, last_known_tvt=0.0,
        )


def test_uniform_reference_grid_accepted():
    """The uniformity guard does not reject a proper resample_to_step grid."""
    ref_depth, ref_gr = resample_to_step(
        np.arange(0.0, 200.0, 2.0), np.sin(np.arange(0.0, 200.0, 2.0) / 4.0), step=1.0
    )
    lateral_md = np.arange(60, dtype=float)
    lateral_gr = np.sin(lateral_md / 4.0)
    eval_mask = np.zeros(60, dtype=bool)
    eval_mask[40:] = True
    out = predict_tvt_via_correlation(
        lateral_md, lateral_gr, eval_mask, ref_depth, ref_gr,
        window_size=11, last_known_tvt=40.0,
    )
    assert out.shape == lateral_md.shape
    assert np.isfinite(out[eval_mask]).all()
