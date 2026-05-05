# Decisions log

Append-only. One entry per non-obvious choice, dated.

## 2026-05-05 — Repo location and data layout

- Sibling repo at `/mnt/local-analysis/kaggle-rogii-2026/`, separate git project (not a workspace-hub subdir, not a digitalmodel subdir).
- Dataset (`data/raw/`, ~1.33 GB) is gitignored; reproduced on demand via `scripts/download_data.sh`.
- `/mnt/local-analysis` has 749 GB free → no need to push data to `/mnt/ace` (which is at 93%).
- Python toolchain: `uv` + Python 3.11–3.13. Kaggle CLI invoked through `uv run --with kaggle`, no global install.

## 2026-05-05 — Team policy

- Open to merging with other Kagglers, per user direction. Team-merger deadline 2026-07-29.

## (template)

## YYYY-MM-DD — Title
- Decision:
- Why:
- Alternatives considered:
- Reverse cost:
