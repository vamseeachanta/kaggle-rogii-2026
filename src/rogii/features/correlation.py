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


# ---------------------------------------------------------------------------
# v2: heel-anchored DTW with an advancing anchor (issue #1)
# ---------------------------------------------------------------------------
#
# Why v1 failed (docs/decisions.md 2026-05-05): the prior was *pinned* at the
# heel-exit TVT and the search radius grew with MD offset, so by mid-toe it
# spanned the whole reference and correlation locked onto spurious repeats of
# the GR signature hundreds of feet away (297 ft RMSE vs an 11.53 ft floor).
#
# v2 fixes three things, all in ``predict_tvt_advancing_anchor`` below:
#
#   1. Advancing anchor. After predicting each toe row's TVT, the anchor moves
#      to that prediction. The next row searches a fixed, tight band around the
#      *last* prediction, not around the far-away heel exit. The prior tracks
#      the well instead of decaying.
#   2. Heel as primary reference. The lateral heel carries a known
#      (TVT_input, GR) mapping at the well's own resolution (Slide 9: lateral GR
#      out-resolves typewell GR). We build the reference from the heel first and
#      only fall back to a secondary reference (typewell) where the heel does
#      not cover the toe's GR range.
#   3. Tight search radius. ``max_search_ft`` (default 30 ft of TVT) caps how
#      far a single row may step. Geology does not jump faster than that absent
#      a fault, and faults are rare enough to leave to a separate fallback.


def build_reference_from_heel(
    heel_tvt: np.ndarray,
    heel_gr: np.ndarray,
    *,
    step: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Build a (TVT-grid, GR) reference series from the observed heel rows.

    The heel of the same well provides a ground-truth depth-to-GR mapping
    (``TVT_input`` is observed there). We resample it onto a uniform TVT grid so
    the advancing-anchor search can index it by depth.

    Args:
        heel_tvt: Observed heel TVT values (``TVT_input`` over the heel), 1-D.
        heel_gr: Heel GR values, same length as ``heel_tvt``.
        step: TVT grid step in feet.

    Returns:
        ``(ref_depth, ref_gr)`` on a uniform ``step``-ft grid, sorted by depth.
        Duplicate/non-monotone TVT samples (the heel can fold back on itself)
        are collapsed by averaging GR within each TVT bin before resampling.
    """
    tvt = np.asarray(heel_tvt, dtype=float)
    gr = np.asarray(heel_gr, dtype=float)
    finite = np.isfinite(tvt) & np.isfinite(gr)
    tvt, gr = tvt[finite], gr[finite]
    if len(tvt) < 2:
        raise ValueError("need at least two finite heel (tvt, gr) samples")

    # Collapse to a strictly increasing TVT axis: bin by rounded TVT, average GR.
    order = np.argsort(tvt)
    tvt, gr = tvt[order], gr[order]
    uniq_tvt, inv = np.unique(np.round(tvt / step) * step, return_inverse=True)
    if len(uniq_tvt) < 2:
        raise ValueError("heel TVT range collapses to a single grid cell")
    sums = np.zeros(len(uniq_tvt))
    counts = np.zeros(len(uniq_tvt))
    np.add.at(sums, inv, gr)
    np.add.at(counts, inv, 1.0)
    binned_gr = sums / counts
    return resample_to_step(uniq_tvt, binned_gr, step)


def predict_tvt_advancing_anchor(
    lateral_md: np.ndarray,
    lateral_gr: np.ndarray,
    eval_mask: np.ndarray,
    references: list[tuple[np.ndarray, np.ndarray]],
    *,
    window_size: int = 51,
    last_known_tvt: float | None = None,
    max_search_ft: float = 30.0,
    min_corr: float = 0.0,
) -> np.ndarray:
    """Predict toe TVT by advancing-anchor correlation against prioritised references.

    For each eval (toe) row, in MD order:

    1. Take a GR window centred on the row.
    2. For each reference in priority order, search a band of width
       ``±max_search_ft`` (in TVT) around the **current anchor** for the best
       Pearson-correlation match. Use the first reference whose best correlation
       clears ``min_corr`` and whose band overlaps the reference; otherwise hold
       the anchor (carry-forward this row).
    3. Set the row's prediction to the matched TVT and **advance the anchor** to
       it, so the next row searches around this prediction rather than the heel.

    The advancing anchor is what keeps the search local: the prior tracks the
    well instead of fanning out with MD offset (the v1 failure mode).

    Args:
        lateral_md: Full-lateral MD, 1-D, monotonically increasing.
        lateral_gr: Full-lateral GR, same length as ``lateral_md``.
        eval_mask: bool 1-D, True where TVT must be predicted (the toe).
        references: list of ``(ref_depth, ref_gr)`` on a uniform grid, **highest
            priority first** (e.g. heel-built reference, then typewell).
        window_size: GR window length around each row (odd recommended).
        last_known_tvt: TVT at the last observed heel row; seeds the anchor. If
            None, the first reference's mid-depth is used.
        max_search_ft: Half-width of the TVT search band around the anchor (ft).
        min_corr: Minimum correlation for a match to be accepted; below it the
            row holds the anchor (carry-forward) rather than jumping to noise.

    Returns:
        Predicted TVT, same length as ``lateral_md``. Non-eval rows echo NaN.
    """
    md = np.asarray(lateral_md, dtype=float)
    gr = np.asarray(lateral_gr, dtype=float)
    n = len(md)
    out = np.full(n, np.nan, dtype=float)
    half = window_size // 2

    if not references:
        raise ValueError("at least one reference is required")

    eval_indices = np.flatnonzero(eval_mask)
    if len(eval_indices) == 0:
        return out

    # Per-reference grid metadata (step, span) for index<->depth conversion.
    ref_meta = []
    for ref_depth, ref_gr in references:
        rd = np.asarray(ref_depth, dtype=float)
        rg = np.asarray(ref_gr, dtype=float)
        if len(rd) < 2 or rd.shape != rg.shape:
            raise ValueError("each reference must be matching 1-D arrays of length >= 2")
        ref_meta.append((rd, rg, float(rd[1] - rd[0])))

    # Seed the anchor.
    if last_known_tvt is not None and np.isfinite(last_known_tvt):
        anchor = float(last_known_tvt)
    else:
        rd0 = ref_meta[0][0]
        anchor = float(rd0[len(rd0) // 2])

    for i in eval_indices:
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        q = gr[lo:hi]
        # Too short a window (lateral edge) → hold the anchor.
        if len(q) < max(2, window_size // 2):
            out[i] = anchor
            continue

        matched = anchor
        for rd, rg, step in ref_meta:
            if len(q) > len(rg):
                continue
            anchor_idx = int(round((anchor - rd[0]) / step))
            radius_idx = int(round(max_search_ft / step))
            # Skip a reference whose band does not overlap its depth span.
            if anchor_idx + radius_idx < 0 or anchor_idx - radius_idx > len(rg) - 1:
                continue
            best_depth, best_corr = best_match_depth(
                q, rg, rd,
                expected_idx=anchor_idx, search_radius=radius_idx,
            )
            if best_corr >= min_corr:
                matched = best_depth
                break
        # else: no reference cleared min_corr → matched stays at anchor.

        # Hard-clamp the step to the search band (a reference whose band only
        # partially overlapped could otherwise return a far center).
        matched = float(np.clip(matched, anchor - max_search_ft, anchor + max_search_ft))
        out[i] = matched
        anchor = matched  # advance the anchor to this prediction

    return out
