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

## (template)

## YYYY-MM-DD — Title
- Decision:
- Why:
- Alternatives considered:
- Reverse cost:
