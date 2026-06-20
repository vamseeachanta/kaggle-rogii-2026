"""Leave-pad-out CV of the GBDT residual-on-carry-forward fusion (issue #4, Phase 3).

Fuses the three earlier-phase priors -- heel-anchored DTW (#1), offset-well prior
(#2), linear-extrap slope (#3) -- plus depth/trajectory/GR/history context into a
LightGBM regressor that predicts the *residual* off carry-forward
(``r = TVT - carry_forward``); the final prediction is ``carry_forward + r_hat``.

Split: leave-PAD-out (issue #2). For each held-out pad we train the GBDT on every
*other* pad's eval rows and predict the held-out pad's eval rows. The target
well's whole pad is also excluded from its offset-neighbour pool, so no pad-mate
geology leaks through either the training rows or the priors.

We score on the SAME 10-well sample (seed=0) used by every prior baseline, so the
11.53 ft carry-forward floor (docs/decisions.md 2026-05-05) is directly comparable.

Run:  uv run python scripts/cv_gbdt.py
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
    well_midpoints,
)
from rogii.models.gbdt import (  # noqa: E402
    FEATURE_COLUMNS,
    build_feature_matrix,
    feature_importance,
    train_gbdt,
)
from rogii.models.linear_extrap import predict_carry_forward  # noqa: E402

TRAIN = repo / "data" / "raw" / "train"
CARRY_FORWARD_FLOOR = 11.53  # docs/decisions.md 2026-05-05
K_NEIGHBOURS = 8
PAD_EPS_FT = 2000.0
SEED = 0
# Train the GBDT on this many train wells per fold (capped for runtime on the
# sample; the priors are the expensive part). None => use every eligible well.
MAX_TRAIN_WELLS = 120


def load_h(well: str) -> pd.DataFrame:
    return pd.read_csv(TRAIN / f"{well}__horizontal_well.csv")


def load_t(well: str) -> pd.DataFrame | None:
    p = TRAIN / f"{well}__typewell.csv"
    return pd.read_csv(p) if p.exists() else None


def main() -> None:
    wells = sorted({p.name.split("__")[0] for p in TRAIN.glob("*__horizontal_well.csv")})
    print(f"{len(wells)} train wells")

    t0 = time.perf_counter()
    h_frames = {w: load_h(w) for w in wells}
    mids = well_midpoints(h_frames)
    index = SpatialIndex(mids)
    pads = assign_pads(mids, eps=PAD_EPS_FT)
    pad_of = {w: int(pads[w]) for w in wells}
    padmates = {w: {o for o in wells if pad_of[o] == pad_of[w]} for w in wells}
    print(
        f"loaded {len(h_frames)} wells, {pads.nunique()} pads (eps={PAD_EPS_FT:.0f} ft) "
        f"in {time.perf_counter() - t0:.1f}s"
    )

    rng = np.random.default_rng(SEED)
    sample = list(rng.choice(wells, size=10, replace=False))
    print(f"sample (seed={SEED}): {sample}\n")

    # Pre-cache the offset neighbours for a target well (pad-excluded).
    def neighbours_for(w: str, exclude: set[str]) -> tuple[dict[str, pd.DataFrame], np.ndarray]:
        res = index.query(w, k=K_NEIGHBOURS, exclude=exclude)
        return {nid: h_frames[nid] for nid in res.wells}, res.distances

    sample_set = set(sample)
    rng_train = np.random.default_rng(SEED + 1)
    all_importances = []
    rows = []

    # Build a fixed shared training pool ONCE (the priors are the expensive part,
    # and a well's feature matrix is identical across folds because its priors
    # exclude its own pad regardless of which pad is currently held out). Each
    # per-fold model then simply drops the held-out pad's rows from this cache --
    # still leave-pad-out, but the DTW/offset priors are computed a single time.
    eligible = [u for u in wells if u not in sample_set]
    if MAX_TRAIN_WELLS and len(eligible) > MAX_TRAIN_WELLS:
        eligible = sorted(rng_train.choice(eligible, size=MAX_TRAIN_WELLS, replace=False))
    print(f"building shared training-feature cache over {len(eligible)} wells (priors)...")
    tcache = time.perf_counter()
    feat_cache: dict[str, pd.DataFrame] = {}
    for u in eligible:
        nb, dist = neighbours_for(u, padmates[u])
        Xu = build_feature_matrix(u, h_frames[u], load_t(u), nb, dist)
        if "residual" in Xu.columns and len(Xu):
            Xu = Xu.copy()
            Xu["_pad"] = pad_of[u]
            feat_cache[u] = Xu
    print(f"  cached {len(feat_cache)} wells in {time.perf_counter() - tcache:.1f}s\n")

    for w in sample:
        test_pad = pad_of[w]
        # Leave-pad-out: drop every cached well belonging to the held-out pad.
        train_parts = [Xu for u, Xu in feat_cache.items() if pad_of[u] != test_pad]
        X_train = pd.concat(train_parts, ignore_index=True)

        res_model = train_gbdt(X_train, seed=SEED)

        # Predict the held-out target well (its whole pad excluded from priors).
        h = h_frames[w]
        nb, dist = neighbours_for(w, padmates[w])
        X_test = build_feature_matrix(w, h, load_t(w), nb, dist)

        eval_mask = h["TVT_input"].isna().to_numpy()
        y_true = h["TVT"].to_numpy(float)
        cf = predict_carry_forward(h)

        tvt_hat = res_model.predict_tvt(X_test)  # carry_forward + r_hat, eval rows
        pred = cf.copy()
        pred[X_test.index.to_numpy()] = tvt_hat

        r_cf = rmse(y_true[eval_mask], cf[eval_mask])
        r_gbdt = rmse(y_true[eval_mask], pred[eval_mask])
        all_importances.append(feature_importance(res_model, X_train))
        rows.append(
            {
                "well": w,
                "pad": test_pad,
                "eval_rows": int(eval_mask.sum()),
                "n_train_wells": len(train_parts),
                "n_train_rows": len(X_train),
                "rmse_cf": r_cf,
                "rmse_gbdt": r_gbdt,
                "delta": r_cf - r_gbdt,  # positive => GBDT wins
                "result": "WIN" if r_gbdt < r_cf else "loss",
            }
        )
        print(
            f"  {w} pad={test_pad:>4} eval={int(eval_mask.sum()):>4} ntrain={len(train_parts):>3} "
            f"cf={r_cf:7.2f} gbdt={r_gbdt:7.2f} "
            f"{'WIN' if r_gbdt < r_cf else 'loss'} ({res_model.backend})"
        )

    df = pd.DataFrame(rows)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", None)
    print("\nPer-well eval-zone RMSE (ft):")
    print(df.round(2).to_string(index=False))

    agg_cf = df["rmse_cf"].mean()
    agg_gbdt = df["rmse_gbdt"].mean()
    wins = int((df["rmse_gbdt"] < df["rmse_cf"]).sum())
    print(f"\n{'model':>32} | {'agg RMSE':>9} | {'vs floor':>9} | wins/10")
    print("-" * 72)
    print(f"{'carry-forward (this run)':>32} | {agg_cf:9.2f} | {'(floor)':>9} | {'-':>5}")
    print(
        f"{'GBDT residual-on-carry-forward':>32} | {agg_gbdt:9.2f} | "
        f"{agg_gbdt - CARRY_FORWARD_FLOOR:+9.2f} | {wins:>5}/10"
    )
    print(f"\nReference carry-forward floor (decisions.md): {CARRY_FORWARD_FLOOR} ft")
    verdict = "BEATS" if agg_gbdt < CARRY_FORWARD_FLOOR else "does NOT beat"
    print(f"Verdict: GBDT fusion {verdict} the 11.53 ft floor on the 10-well sample.")
    print(f"         (also {'BEATS' if agg_gbdt < agg_cf else 'does NOT beat'} this run's own carry-forward = {agg_cf:.2f}.)")

    # Aggregate feature importance across folds (mean of per-fold importances).
    imp = pd.concat(all_importances, axis=1).mean(axis=1).sort_values(ascending=False)
    print("\nTop feature importances (mean across folds):")
    for name, val in imp.head(10).items():
        print(f"  {name:>18}  {val:12.2f}")


if __name__ == "__main__":
    main()
