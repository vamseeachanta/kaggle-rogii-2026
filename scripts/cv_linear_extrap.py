"""CV sweep: linear extrapolation vs carry-forward on the 10-well sample (issue #3).

Mirrors the evaluation harness in ``notebooks/10_dtw_alignment.ipynb``: the SAME
10 train wells (``np.random.default_rng(0).choice(wells, 10, replace=False)``),
the SAME eval mask (rows where ``TVT_input`` is NaN), the SAME RMSE helper. For
each well we score carry-forward and linear extrapolation across a sweep of
``n_recent`` window lengths and report per-well RMSE, the aggregate, and how many
wells each window beats the carry-forward floor on.

Run:  uv run python scripts/cv_linear_extrap.py
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

from rogii.features.correlation import rmse  # noqa: E402
from rogii.models.linear_extrap import (  # noqa: E402
    predict_carry_forward,
    predict_linear_extrap,
)

TRAIN = repo / "data" / "raw" / "train"
N_RECENT_SWEEP: list[int | None] = [50, 100, 200, 500, None]  # None = ALL heel
CARRY_FORWARD_FLOOR = 11.53  # from docs/decisions.md 2026-05-05


def load(well: str) -> pd.DataFrame:
    return pd.read_csv(TRAIN / f"{well}__horizontal_well.csv")


def label(n: int | None) -> str:
    return "ALL" if n is None else str(n)


def main() -> None:
    wells = sorted({p.name.split("__")[0] for p in TRAIN.glob("*__horizontal_well.csv")})
    rng = np.random.default_rng(0)
    sample_wells = list(rng.choice(wells, size=10, replace=False))
    print(f"{len(wells)} train wells; sample (seed=0):")
    print(sample_wells)
    print()

    rows = []
    for well in sample_wells:
        h = load(well)
        eval_mask = h["TVT_input"].isna().to_numpy()
        y_true = h["TVT"].to_numpy(float)
        n_heel = int((~eval_mask).sum())

        cf = predict_carry_forward(h)
        rec: dict[str, object] = {
            "well": well,
            "eval_rows": int(eval_mask.sum()),
            "heel_rows": n_heel,
            "rmse_cf": rmse(y_true[eval_mask], cf[eval_mask]),
        }
        for n in N_RECENT_SWEEP:
            lin = predict_linear_extrap(h, n_recent=n)
            rec[f"rmse_lin_{label(n)}"] = rmse(y_true[eval_mask], lin[eval_mask])
        rows.append(rec)

    df = pd.DataFrame(rows)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", None)
    print("Per-well eval-zone RMSE (ft):")
    print(df.round(2).to_string(index=False))
    print()

    print(f"{'n_recent':>10} | {'agg RMSE':>9} | {'vs floor':>9} | wins/10")
    print("-" * 48)
    print(f"{'carry-fwd':>10} | {df['rmse_cf'].mean():9.2f} | {'(floor)':>9} | {'-':>5}")
    for n in N_RECENT_SWEEP:
        col = f"rmse_lin_{label(n)}"
        agg = df[col].mean()
        wins = int((df[col] < df["rmse_cf"]).sum())
        delta = agg - CARRY_FORWARD_FLOOR
        print(f"{label(n):>10} | {agg:9.2f} | {delta:+9.2f} | {wins:>5}/10")
    print()
    print(f"Reference carry-forward floor (decisions.md): {CARRY_FORWARD_FLOOR} ft")
    print(f"This run's carry-forward aggregate:           {df['rmse_cf'].mean():.2f} ft")

    # Canonical decision window from the plan (locked in advance): n_recent=200.
    col200 = "rmse_lin_200"
    wins200 = int((df[col200] < df["rmse_cf"]).sum())
    print()
    print(
        f"Decision window n_recent=200: agg={df[col200].mean():.2f} ft, "
        f"wins on {wins200}/10 wells (plan rule: adopt if >= 6/10)."
    )


if __name__ == "__main__":
    main()
