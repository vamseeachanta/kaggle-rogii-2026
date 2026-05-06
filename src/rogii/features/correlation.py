"""Windowed cross-correlation alignment of horizontal-well GR to a reference GR series.

The geosteering operation maps each lateral-well MD position to a depth in some
reference frame (typewell TVT or, equivalently, the heel of the same well) such
that the local GR signature around that MD matches the reference. This module
provides a simple correlation-based aligner that beats raw carry-forward and
serves as the v1 of Phase 1 in the modeling roadmap.

For each lateral row we:
1. Take a window of GR centered on that MD position.
2. Slide the window across the reference GR(depth) series within a search band.
3. Pick the depth where Pearson correlation is highest.
4. Return the reference depth value at that position.

This is the simplest sensible implementation. Future iterations should add:
- Sakoe-Chiba band-constrained DTW for noise robustness.
- Monotonicity constraints within a regime (climbing / descending / flat).
- Multi-reference fusion (heel of same well + typewell, weighted by correlation strength).
"""

from __future__ import annotations

import numpy as np


def resample_to_step(depth: np.ndarray, value: np.ndarray, step: float) -> tuple[np.ndarray, np.ndarray]:
    """Resample (depth, value) onto a uniform grid with the given step size.

    Both inputs must be 1-D arrays of equal length, with depth strictly increasing.
    Returns (new_depth, new_value).
    """
    if depth.ndim != 1 or value.ndim != 1 or depth.shape != value.shape:
        raise ValueError("depth and value must be matching 1-D arrays")
    if not np.all(np.diff(depth) > 0):
        raise ValueError("depth must be strictly increasing")
    new_depth = np.arange(depth[0], depth[-1] + step / 2, step)
    new_value = np.interp(new_depth, depth, value)
    return new_depth, new_value


def best_match_depth(
    query_gr: np.ndarray,
    ref_gr: np.ndarray,
    ref_depth: np.ndarray,
    *,
    expected_idx: int | None = None,
    search_radius: int | None = None,
) -> tuple[float, float]:
    """Find the depth in (ref_depth, ref_gr) where ref_gr best matches query_gr.

    Both arrays must be on the same step size. The query is treated as a fixed
    window; we slide it over the reference and compute Pearson correlation at
    each offset. The best-matching reference center is returned.

    If `expected_idx` and `search_radius` are given, the search is restricted to
    `[expected_idx - search_radius, expected_idx + search_radius]` (in reference
    indices) — useful when we have a prior on where the match should be.

    Returns:
        (best_depth, best_correlation): the depth in ref_depth at the center of
        the best match, and its correlation strength in [-1, 1].
    """
    n_query = len(query_gr)
    n_ref = len(ref_gr)
    if n_query > n_ref:
        raise ValueError("query window longer than reference series")

    q = query_gr - query_gr.mean()
    q_norm = np.linalg.norm(q)
    if q_norm == 0:
        return float(ref_depth[len(ref_depth) // 2]), 0.0

    half = n_query // 2
    starts = range(0, n_ref - n_query + 1)
    if expected_idx is not None and search_radius is not None:
        lo = max(0, expected_idx - search_radius - half)
        hi = min(n_ref - n_query, expected_idx + search_radius - half)
        starts = range(lo, hi + 1) if lo <= hi else starts

    best_corr = -np.inf
    best_start = 0
    for s in starts:
        window = ref_gr[s : s + n_query]
        w = window - window.mean()
        w_norm = np.linalg.norm(w)
        if w_norm == 0:
            continue
        corr = float(np.dot(q, w) / (q_norm * w_norm))
        if corr > best_corr:
            best_corr = corr
            best_start = s
    best_center_idx = best_start + half
    return float(ref_depth[best_center_idx]), float(best_corr)


def predict_tvt_via_correlation(
    lateral_md: np.ndarray,
    lateral_gr: np.ndarray,
    eval_mask: np.ndarray,
    ref_depth: np.ndarray,
    ref_gr: np.ndarray,
    *,
    window_size: int = 51,
    last_known_tvt: float | None = None,
    drift_per_ft: float = 0.5,
) -> np.ndarray:
    """Predict TVT at each eval-zone MD by sliding-window correlation against a reference series.

    Args:
        lateral_md: MD values for the full lateral, 1-D, monotonically increasing.
        lateral_gr: GR values for the full lateral, same length as lateral_md.
        eval_mask: bool 1-D array, same length; True where TVT must be predicted.
        ref_depth: reference depth series (e.g. typewell TVT, 1 ft step).
        ref_gr: reference GR series, same length as ref_depth.
        window_size: GR window around each lateral position (ft, odd recommended).
        last_known_tvt: TVT value at the last observed lateral row (start of eval zone).
            Used to seed the search prior. If None, no prior is used.
        drift_per_ft: Allowed |dTVT/dMD| in feet (per-foot drift bound). Used to
            translate "I've moved this many MD steps from the last anchor" into
            "the TVT search radius around the prior".

    Returns:
        Predicted TVT, same length as lateral_md. Non-eval positions echo NaN.
    """
    n = len(lateral_md)
    out = np.full(n, np.nan, dtype=float)
    half = window_size // 2

    # Build a fast lookup from depth value to reference index
    ref_step = float(ref_depth[1] - ref_depth[0])
    if last_known_tvt is not None:
        anchor_idx = int(round((last_known_tvt - ref_depth[0]) / ref_step))
    else:
        anchor_idx = None

    eval_indices = np.flatnonzero(eval_mask)
    if len(eval_indices) == 0:
        return out

    last_eval_md = lateral_md[eval_indices[0] - 1] if eval_indices[0] > 0 else lateral_md[0]
    for i in eval_indices:
        # Window around this lateral MD position
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        q = lateral_gr[lo:hi]
        # If trailing/leading window is too short, skip with carry-forward fallback
        if len(q) < window_size // 2:
            out[i] = last_known_tvt if last_known_tvt is not None else 0.0
            continue
        if anchor_idx is not None:
            md_offset = lateral_md[i] - last_eval_md
            search_rad = int(round(drift_per_ft * md_offset / ref_step)) + window_size
            best_depth, _corr = best_match_depth(
                q, ref_gr, ref_depth,
                expected_idx=anchor_idx, search_radius=search_rad,
            )
        else:
            best_depth, _corr = best_match_depth(q, ref_gr, ref_depth)
        out[i] = best_depth
    return out


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root mean squared error, NaN-safe."""
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if not mask.any():
        return float("nan")
    diff = y_true[mask] - y_pred[mask]
    return float(np.sqrt(np.mean(diff * diff)))
