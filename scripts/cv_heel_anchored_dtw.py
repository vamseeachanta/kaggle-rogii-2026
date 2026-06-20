"""CV sweep: heel-anchored advancing-anchor DTW vs carry-forward (issue #1, v2).

Mirrors the harness in ``notebooks/10_dtw_alignment.ipynb`` and
``scripts/cv_linear_extrap.py``: the SAME 10 train wells
(``np.random.default_rng(0).choice(wells, 10, replace=False)``), the SAME eval
mask (rows where ``TVT_input`` is NaN), the SAME ``rmse`` helper.

For each well we build the v2 reference list — primary = the lateral heel's own
(TVT_input, GR) mapping (Slide 9: heel GR out-resolves typewell GR), secondary =
the typewell GR(TVT) — and run the advancing-anchor search seeded at the last
observed heel TVT with a tight ±30 ft search band. We report per-well RMSE,
per-well win/loss vs carry-forward, the aggregate, and the count vs the 11.53 ft
carry-forward floor (docs/decisions.md 2026-05-05).

Run:  uv run python scripts/cv_heel_anchored_dtw.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Bounded upward walk to the repo root (issue #9 pattern), then put src on path.
repo = Path(__file__).resolve().parent
for _ in range(40):
    if (repo / "pyproject.toml").exists():
        break
    if repo.parent == repo:
        raise RuntimeError("pyproject.toml not found walking up")
    repo = repo.parent
sys.path.insert(0, str(repo / "src"))

from rogii.features.correlation import (  # noqa: E402
    build_reference_from_heel,
    predict_tvt_advancing_anchor,
    resample_to_step,
    rmse,
)
from rogii.models.linear_extrap import predict_carry_forward  # noqa: E402

TRAIN = repo / "data" / "raw" / "train"
CARRY_FORWARD_FLOOR = 11.53  # from docs/decisions.md 2026-05-05
WINDOW_SIZE = 51
MAX_SEARCH_FT = 30.0
MIN_CORR = 0.3


def load(well: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    h = pd.read_csv(TRAIN / f"{well}__horizontal_well.csv")
    t = pd.read_csv(TRAIN / f"{well}__typewell.csv")
    return h, t


def heel_anchored_pred(h: pd.DataFrame, t: pd.DataFrame) -> np.ndarray:
    """v2 prediction over the full lateral; heel rows echo TVT_input."""
    md = h["MD"].to_numpy(float)
    gr = h["GR"].to_numpy(float)
    tvt_in = h["TVT_input"].to_numpy(float)
    eval_mask = ~np.isfinite(tvt_in)

    # Impute GR gaps (nearest valid neighbour), matching the v1 notebook.
    if np.isnan(gr).any():
        gr = pd.Series(gr).ffill().bfill().to_numpy()

    observed_idx = np.flatnonzero(np.isfinite(tvt_in))
    out = tvt_in.copy()
    if len(observed_idx) < 2 or not eval_mask.any():
        # Degenerate: nothing to anchor on → carry-forward.
        return predict_carry_forward(h)

    last_known_tvt = float(tvt_in[observed_idx[-1]])

    references: list[tuple[np.ndarray, np.ndarray]] = []
    # Primary reference: the lateral heel's own (TVT, GR) mapping.
    try:
        heel_ref = build_reference_from_heel(
            tvt_in[observed_idx], gr[observed_idx], step=1.0
        )
        references.append(heel_ref)
    except ValueError:
        pass
    # Secondary reference: the typewell GR(TVT).
    try:
        tw_ref = resample_to_step(
            t["TVT"].to_numpy(float), t["GR"].to_numpy(float), step=1.0
        )
        references.append(tw_ref)
    except ValueError:
        pass

    if not references:
        return predict_carry_forward(h)

    pred = predict_tvt_advancing_anchor(
        md, gr, eval_mask, references,
        window_size=WINDOW_SIZE,
        last_known_tvt=last_known_tvt,
        max_search_ft=MAX_SEARCH_FT,
        min_corr=MIN_CORR,
    )
    out[eval_mask] = pred[eval_mask]
    # Any row the search held as NaN (shouldn't happen) → carry-forward.
    still_nan = eval_mask & ~np.isfinite(out)
    out[still_nan] = last_known_tvt
    return out


def main() -> None:
    wells = sorted({p.name.split("__")[0] for p in TRAIN.glob("*__horizontal_well.csv")})
    rng = np.random.default_rng(0)
    sample_wells = list(rng.choice(wells, size=10, replace=False))
    print(f"{len(wells)} train wells; sample (seed=0): {sample_wells}\n")

    rows = []
    for well in sample_wells:
        h, t = load(well)
        eval_mask = h["TVT_input"].isna().to_numpy()
        y_true = h["TVT"].to_numpy(float)

        cf = predict_carry_forward(h)
        v2 = heel_anchored_pred(h, t)

        r_cf = rmse(y_true[eval_mask], cf[eval_mask])
        r_v2 = rmse(y_true[eval_mask], v2[eval_mask])
        rows.append({
            "well": well,
            "eval_rows": int(eval_mask.sum()),
            "rmse_cf": r_cf,
            "rmse_v2": r_v2,
            "delta": r_cf - r_v2,            # positive => v2 wins
            "result": "WIN" if r_v2 < r_cf else "loss",
        })

    df = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", None)
    print("Per-well eval-zone RMSE (ft):")
    print(df.round(2).to_string(index=False))
    print()

    wins = int((df["rmse_v2"] < df["rmse_cf"]).sum())
    agg_cf = df["rmse_cf"].mean()
    agg_v2 = df["rmse_v2"].mean()
    print(f"{'method':>14} | {'agg RMSE':>9} | {'vs floor':>9} | wins/10")
    print("-" * 52)
    print(f"{'carry-fwd':>14} | {agg_cf:9.2f} | {'(floor)':>9} | {'-':>5}")
    print(f"{'heel-anchored':>14} | {agg_v2:9.2f} | {agg_v2 - CARRY_FORWARD_FLOOR:+9.2f} | {wins:>5}/10")
    print()
    print(f"Reference floor (decisions.md): {CARRY_FORWARD_FLOOR} ft")
    print(f"This run's carry-forward agg:   {agg_cf:.2f} ft")
    print(f"Plan acceptance: v2 adopted only if it beats the floor and wins >= 6/10.")


if __name__ == "__main__":
    main()
