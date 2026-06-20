"""Linear-extrapolation baseline for TVT continuation (Phase 0.5, issue #3).

The carry-forward floor (`notebooks/00`) predicts the toe TVT as the *last*
observed heel ``TVT_input`` — a flat line. This module instead fits a straight
line to the last ``n_recent`` observed heel rows and projects that slope forward
through the toe eval zone.

Hypothesis (issue #3): wells generally continue their heel-exit dip into the
toe, so a non-zero slope should beat the flat carry-forward on the drift-y wells
without losing much on the flat ones (where the fitted slope is ~0, which
degenerates back to carry-forward).

Geometry of the data
--------------------
Each horizontal-well CSV has columns ``MD`` (measured depth, 1-ft step) and
``TVT_input`` (true vertical thickness, observed continuously over the heel and
NaN over the toe eval zone). ``TVT`` (ground truth over the full lateral) is
present only in *train* wells. The eval zone is exactly the rows where
``TVT_input`` is NaN.

Design notes
------------
- **Least-squares line.** Slope/intercept from ``numpy.polyfit(md, tvt, 1)`` on
  the last ``n_recent`` *observed* heel rows. With ``n_recent`` large enough the
  fit is stable; a single noisy point cannot swing it.
- **Degenerate fallbacks.** Fewer than two usable heel points → no slope is
  defined, so we fall back to carry-forward (flat at the last observed value),
  or 0.0 if nothing is observed at all. ``n_recent <= 1`` is treated the same
  way (a single point cannot define a slope).
- **Clip guard.** Extrapolating a slope over a multi-thousand-foot toe can blow
  up. Predictions are clipped to ``[heel_min - margin, heel_max + margin]`` with
  ``margin = clip_margin_factor * heel_drift`` (``heel_drift`` = observed heel
  TVT range). This is the same guard the plan (issue #3) requires.
- **Known rows preserved.** Over the heel (non-eval) rows we echo the observed
  ``TVT_input`` unchanged, so the returned array can be scored directly against
  ``TVT`` on the eval mask and matches the carry-forward harness shape.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def fit_line(md: np.ndarray, tvt: np.ndarray) -> tuple[float, float]:
    """Least-squares fit of ``tvt ~ slope * md + intercept``.

    Args:
        md: 1-D measured-depth values.
        tvt: 1-D TVT values, same length as ``md``.

    Returns:
        ``(slope, intercept)``. If fewer than two finite (md, tvt) pairs are
        available the slope is undefined; we return ``(0.0, mean_tvt)`` — i.e. a
        flat line at the mean observed value (carry-forward-like). With exactly
        one point that mean is that point's value.

    Raises:
        ValueError: If ``md`` and ``tvt`` have different lengths.
    """
    md = np.asarray(md, dtype=float)
    tvt = np.asarray(tvt, dtype=float)
    if md.shape != tvt.shape:
        raise ValueError("md and tvt must be the same length")
    finite = np.isfinite(md) & np.isfinite(tvt)
    md, tvt = md[finite], tvt[finite]
    if len(md) == 0:
        return 0.0, 0.0
    if len(md) == 1:
        return 0.0, float(tvt[0])
    # A vertical (constant-MD) window has no defined slope → flat at the mean.
    if np.ptp(md) == 0:
        return 0.0, float(tvt.mean())
    slope, intercept = np.polyfit(md, tvt, 1)
    return float(slope), float(intercept)


def predict_linear_extrap(
    h: pd.DataFrame,
    n_recent: int | None = 200,
    *,
    clip_margin_factor: float = 1.5,
) -> np.ndarray:
    """Predict full-lateral TVT by linear extrapolation of the heel slope.

    Fits a line to the last ``n_recent`` observed heel rows of ``(MD, TVT_input)``
    and projects it across the toe eval zone (the rows where ``TVT_input`` is
    NaN). Observed heel rows echo their ``TVT_input`` unchanged.

    Args:
        h: Horizontal-well frame with ``MD`` and ``TVT_input`` columns.
        n_recent: Number of most-recent observed heel rows to fit the line on.
            ``None`` (or a value >= the heel length) uses **all** observed heel
            rows. ``<= 1`` degenerates to carry-forward (no slope from one point).
        clip_margin_factor: Predictions are clipped to
            ``[heel_min - m, heel_max + m]`` with ``m = clip_margin_factor *
            heel_drift`` to prevent slope blow-up over long toes. Set to a large
            number to effectively disable clipping.

    Returns:
        Predicted TVT for every row of ``h`` (heel rows = observed value, toe
        rows = extrapolated + clipped), as a float ``np.ndarray`` of length
        ``len(h)``.
    """
    md = h["MD"].to_numpy(dtype=float)
    tvt_in = h["TVT_input"].to_numpy(dtype=float)
    eval_mask = ~np.isfinite(tvt_in)

    out = tvt_in.copy()

    observed_idx = np.flatnonzero(np.isfinite(tvt_in))
    if len(observed_idx) == 0:
        # Nothing observed at all → predict 0.0 everywhere (carry-forward floor).
        out[:] = 0.0
        return out

    last_known = float(tvt_in[observed_idx[-1]])
    if not eval_mask.any():
        # No eval rows to predict; return the observed series as-is.
        return out

    # Select the last n_recent observed heel rows for the fit.
    if n_recent is None or n_recent >= len(observed_idx):
        fit_idx = observed_idx
    elif n_recent <= 1:
        # A single point cannot define a slope → carry-forward this well.
        out[eval_mask] = last_known
        return out
    else:
        fit_idx = observed_idx[-n_recent:]

    slope, intercept = fit_line(md[fit_idx], tvt_in[fit_idx])

    # Extrapolate over the eval (toe) rows.
    preds = slope * md[eval_mask] + intercept

    # Clip guard: bound predictions to the observed heel range plus a margin.
    heel_tvt = tvt_in[observed_idx]
    heel_min, heel_max = float(heel_tvt.min()), float(heel_tvt.max())
    heel_drift = heel_max - heel_min
    margin = clip_margin_factor * heel_drift
    lo, hi = heel_min - margin, heel_max + margin
    # If the heel is perfectly flat (drift==0) margin is 0; widen so a tiny slope
    # is not entirely clipped to the flat carry-forward value.
    if heel_drift == 0:
        lo, hi = heel_min - 1.0, heel_max + 1.0
    preds = np.clip(preds, lo, hi)

    out[eval_mask] = preds
    return out


def predict_carry_forward(h: pd.DataFrame) -> np.ndarray:
    """Carry-forward baseline matching ``notebooks/00`` (the floor to beat).

    Predicts every toe (eval) row as the last observed heel ``TVT_input`` value;
    observed heel rows echo their value unchanged. Returns a float array of
    length ``len(h)``.
    """
    tvt_in = h["TVT_input"].to_numpy(dtype=float)
    eval_mask = ~np.isfinite(tvt_in)
    observed_idx = np.flatnonzero(np.isfinite(tvt_in))
    last_known = float(tvt_in[observed_idx[-1]]) if len(observed_idx) else 0.0
    out = tvt_in.copy()
    out[eval_mask] = last_known
    return out
