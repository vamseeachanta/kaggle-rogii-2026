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

## (template)

## YYYY-MM-DD — Title
- Decision:
- Why:
- Alternatives considered:
- Reverse cost:
