# Decisions log

Append-only. One entry per non-obvious choice, dated.

## 2026-05-05 — Repo location and data layout

- Sibling repo at `/mnt/local-analysis/kaggle-rogii-2026/`, separate git project (not a workspace-hub subdir, not a digitalmodel subdir).
- Dataset (`data/raw/`, ~1.33 GB) is gitignored; reproduced on demand via `scripts/download_data.sh`.
- `/mnt/local-analysis` has 749 GB free → no need to push data to `/mnt/ace` (which is at 93%).
- Python toolchain: `uv` + Python 3.11–3.13. Kaggle CLI invoked through `uv run --with kaggle`, no global install.

## 2026-05-05 — Team policy

- Open to merging with other Kagglers, per user direction. Team-merger deadline 2026-07-29.

## 2026-05-05 — Data on /mnt/ace, repo on /mnt/local-analysis

- Dataset lives at `/mnt/ace/kaggle-rogii-2026/data/`.
- `data/{raw,interim,processed}` inside the repo are symlinks pointing there.
- Why: user direction; `/mnt/ace` is the household large-disk staging area (7.3 TB volume) and the canonical home for ingest data across this workspace's projects.
- Symlinks themselves are gitignored (matched without trailing slash so the symlink-as-file is caught).
- Per-machine portability: `scripts/bootstrap_data_dir.sh` recreates the symlinks; `DATA_ROOT` env var overrides the default path on machines that don't have `/mnt/ace`.

## 2026-05-05 — Phase 1 v1 finding: typewell-only correlation fails badly

- **Empirical result.** On 10 random train wells, carry-forward RMSE = 11.53 ft; naive windowed-cross-correlation against the typewell GR series RMSE = 297.86 ft. Correlation loses on 0/10 wells.
- **Why carry-forward is hard to beat.** Wells generally stay near their heel-exit TVT through the toe; ground-truth TVT typically drifts only tens of feet over the 4–5 k row eval zone. "Predict last observed TVT_input" exploits this directly.
- **Why naive correlation explodes.** GR signatures repeat within a typewell — multiple positions look similar. Without a *tight, advancing* depth prior, correlation finds spurious matches hundreds of feet away. The v1 implementation (`src/rogii/features/correlation.py`) used a fixed anchor at the heel-exit TVT and a per-row drift bound, so the search radius grew unboundedly with MD offset and effectively spanned the entire typewell by mid-toe.
- **Fixes required for v2.**
  1. Advance the anchor row-by-row (each prediction becomes the next row's prior).
  2. Use the lateral heel as primary reference (per Slide 9 — heel GR has higher resolution than typewell GR), with typewell as a secondary tiebreaker.
  3. Replace the carry-forward floor with linear extrapolation from the last ~200 heel rows; that's the real bar Phase 1 must clear.
- **Reverse cost.** Low. v1 module and notebook are kept in the repo as the negative-result baseline; v2 will iterate on the same `predict_tvt_via_correlation` API.

## 2026-06-20 — Phase 0.5 finding: linear extrapolation does NOT beat carry-forward

- **Implementation.** `src/rogii/models/linear_extrap.py` — `predict_linear_extrap(h, n_recent=200)` fits `polyfit(MD, TVT_input, 1)` on the last `n_recent` observed heel rows and projects the slope across the toe eval zone, clipped to `[heel_min - 1.5·drift, heel_max + 1.5·drift]`. Plus `predict_carry_forward(h)` for a shared harness. Notebook: `notebooks/05_linear_extrapolation.ipynb` (mirrors `10_dtw_alignment.ipynb`: same RNG seed 0, same 10 wells, same `rmse`).
- **Empirical result (10-well sample, eval-zone RMSE).** Carry-forward reproduces the **11.53 ft** floor exactly. Linear extrapolation loses at every window:

  | n_recent | agg RMSE | vs 11.53 floor | wins/10 |
  |---|---|---|---|
  | carry-forward | 11.53 | (floor) | – |
  | 50  | 77.48  | +65.95  | 2/10 |
  | 100 | 72.46  | +60.93  | 0/10 |
  | 200 | 66.06  | +54.53  | 1/10 |
  | 500 | 81.06  | +69.53  | 1/10 |
  | ALL | 807.18 | +795.65 | 0/10 |

- **Decision (plan rule: adopt only if linear @ n_recent=200 wins ≥ 6/10).** Wins = **1/10** → **keep carry-forward as the Phase-0 floor (11.53 ft).** Phase 1 v2 still targets 11.53 ft, not a new linear floor.
- **Why linear loses.** The hypothesis (wells continue their heel dip into the toe) is falsified on this sample: most wells stay near their heel-exit TVT through the toe, so any non-zero slope projected over a ~5,000-ft toe diverges from the near-flat truth. The clip guard works (it caps the blow-up — see ALL window, which without clipping would be far worse) but cannot rescue a wrong slope direction. The ALL-heel fit is worst because it folds in the steep heel-build section. The two wells where any window wins (`0dc5e64d`, `052d64df`, `4f4afcc6` marginally) are the genuinely drift-y ones — too few to flip the floor.
- **Caveats.** n=10 sample only. If a regime-classifier (Slide 7: increasing/decreasing/constant) later gates linear-vs-flat per well, re-evaluate at n=50 wells before adopting. A rolling-median-smoothed slope variant was deferred.
- **Reverse cost.** Low. Module + notebook + tests are kept as the negative-result baseline; nothing downstream depends on a changed floor.
- **Repro.** `uv run python scripts/cv_linear_extrap.py` (table above) and `uv run pytest tests/test_linear_extrap.py` (8 passed).

## (template)

## YYYY-MM-DD — Title
- Decision:
- Why:
- Alternatives considered:
- Reverse cost:
