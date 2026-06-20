"""Leave-pad-out CV of the offset-well prediction (issue #2, Phase 2).

Mirrors the harness in ``scripts/cv_linear_extrap.py`` / ``notebooks/10`` but
swaps the modelling and the split:

* Model: the offset-well prior. For each eval row of a target well, predict TVT
  as the inverse-distance-weighted mean of the K nearest *train* wells' TVT(MD)
  projected into the target's MD frame (``rogii.features.spatial``). No DTW, no
  correlation -- this isolates whether the offset signal is real on its own
  (issue #2 acceptance: "offset-mean beats the floor on its own").
* Split: leave-PAD-out. Pads come from DBSCAN on lateral midpoints; when scoring
  a target well, its *entire pad* is excluded from the neighbour pool, so a
  pad-mate's correlated geology can never leak into the prior.

We score on the SAME 10-well sample (seed=0) used by the carry-forward / linear
baselines so the carry-forward floor is directly comparable.

Run:  uv run python scripts/cv_offset_well.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

repo = Path(__file__).resolve().parent
for _ in range(40):
    if (repo / "pyproject.toml").exists():
        break
    if repo.parent == repo:
        raise RuntimeError("pyproject.toml not found walking up")
    repo = repo.parent
sys.path.insert(0, str(repo / "src"))

from rogii.features.correlation import rmse  # noqa: E402
from rogii.features.spatial import (  # noqa: E402
    SpatialIndex,
    assign_pads,
    leave_pad_out_folds,
    offset_tvt_features,
    well_midpoints,
)
from rogii.models.linear_extrap import predict_carry_forward  # noqa: E402

TRAIN = repo / "data" / "raw" / "train"
CARRY_FORWARD_FLOOR = 11.53  # docs/decisions.md 2026-05-05
K_NEIGHBOURS = 8
PAD_EPS_FT = 2000.0


def load(well: str) -> pd.DataFrame:
    return pd.read_csv(TRAIN / f"{well}__horizontal_well.csv")


def main() -> None:
    wells = sorted({p.name.split("__")[0] for p in TRAIN.glob("*__horizontal_well.csv")})
    print(f"{len(wells)} train wells")

    # Load every well once (needed both as targets and as neighbour priors).
    t0 = time.perf_counter()
    frames = {w: load(w) for w in wells}
    mids = well_midpoints(frames)
    index = SpatialIndex(mids)
    pads = assign_pads(mids, eps=PAD_EPS_FT)
    folds = leave_pad_out_folds(pads)
    print(
        f"loaded {len(frames)} wells, {pads.nunique()} pads "
        f"(eps={PAD_EPS_FT:.0f} ft) in {time.perf_counter() - t0:.1f}s"
    )

    # Time a single KDTree query for the acceptance criterion.
    tq = time.perf_counter()
    index.query(wells[0], k=K_NEIGHBOURS)
    print(f"single KDTree K-NN query: {(time.perf_counter() - tq) * 1e3:.2f} ms")

    # Map each well -> its pad-mates (to exclude from the neighbour pool).
    pad_of = {w: pads[w] for w in wells}
    padmates = {w: {o for o in wells if pad_of[o] == pad_of[w]} for w in wells}

    # Same 10-well sample (seed=0) as the carry-forward / linear baselines.
    rng = np.random.default_rng(0)
    sample = list(rng.choice(wells, size=10, replace=False))
    print(f"sample (seed=0): {sample}\n")

    rows = []
    for w in sample:
        h = frames[w]
        eval_mask = h["TVT_input"].isna().to_numpy()
        y_true = h["TVT"].to_numpy(float)

        # Leave-pad-out neighbour pool: drop the target's whole pad.
        res = index.query(w, k=K_NEIGHBOURS, exclude=padmates[w])
        neigh = {nid: frames[nid] for nid in res.wells}
        feats = offset_tvt_features(h, neigh, res.distances)
        pred = feats["offset_wmean"].to_numpy(float)

        # Fallback where no neighbour covers a row: carry-forward (so the model
        # is always defined and comparable to the floor on identical rows).
        cf = predict_carry_forward(h)
        filled = np.where(np.isfinite(pred), pred, cf)

        rmse_off = rmse(y_true[eval_mask], filled[eval_mask])
        rmse_off_only = rmse(y_true[eval_mask], pred[eval_mask])  # rows w/ coverage
        rmse_cf = rmse(y_true[eval_mask], cf[eval_mask])
        cover = float(np.isfinite(pred[eval_mask]).mean())

        # Datum-anchored variant: each lateral has its own absolute-TVT datum, so
        # the raw offset *level* is meaningless. The transferable offset signal is
        # the SHAPE: anchor the neighbour mean to the target's last observed TVT at
        # the heel, then add the neighbour-derived delta from that anchor point.
        obs = h["TVT_input"].to_numpy(float)
        heel_idx = np.where(np.isfinite(obs))[0]
        anchored = filled.copy()
        if heel_idx.size and np.isfinite(pred[heel_idx[-1]]):
            anchor_row = heel_idx[-1]
            offset_shift = obs[anchor_row] - pred[anchor_row]
            anchored = np.where(np.isfinite(pred), pred + offset_shift, cf)
        rmse_anchored = rmse(y_true[eval_mask], anchored[eval_mask])
        rows.append(
            {
                "well": w,
                "pad": int(pad_of[w]),
                "padmates": len(padmates[w]) - 1,
                "n_neigh": len(res.wells),
                "nearest_ft": float(res.distances[0]) if res.distances.size else np.nan,
                "eval_rows": int(eval_mask.sum()),
                "cover": cover,
                "rmse_cf": rmse_cf,
                "rmse_offset_cov": rmse_off_only,
                "rmse_offset_filled": rmse_off,
                "rmse_anchored": rmse_anchored,
            }
        )

    df = pd.DataFrame(rows)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", None)
    print("Per-well eval-zone RMSE (ft):")
    print(df.round(2).to_string(index=False))
    print()

    agg_cf = df["rmse_cf"].mean()
    agg_off = df["rmse_offset_filled"].mean()
    agg_anch = df["rmse_anchored"].mean()
    wins_off = int((df["rmse_offset_filled"] < df["rmse_cf"]).sum())
    wins_anch = int((df["rmse_anchored"] < df["rmse_cf"]).sum())
    print(f"{'model':>28} | {'agg RMSE':>9} | {'vs floor':>9} | wins/10")
    print("-" * 66)
    print(f"{'carry-forward (this run)':>28} | {agg_cf:9.2f} | {'(floor)':>9} | {'-':>5}")
    print(
        f"{'offset-wmean (raw level)':>28} | {agg_off:9.2f} | "
        f"{agg_off - CARRY_FORWARD_FLOOR:+9.2f} | {wins_off:>5}/10"
    )
    print(
        f"{'offset shape, heel-anchored':>28} | {agg_anch:9.2f} | "
        f"{agg_anch - CARRY_FORWARD_FLOOR:+9.2f} | {wins_anch:>5}/10"
    )
    print()
    print(f"Reference carry-forward floor (decisions.md): {CARRY_FORWARD_FLOOR} ft")
    print(f"Mean neighbour coverage of eval rows:         {df['cover'].mean():.1%}")
    best = min(agg_off, agg_anch)
    verdict = "BEATS" if best < CARRY_FORWARD_FLOOR else "does NOT beat"
    print(f"\nVerdict: offset prior {verdict} the carry-forward floor on the 10-well sample.")


if __name__ == "__main__":
    main()
