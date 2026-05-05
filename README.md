# Kaggle ROGII — Wellbore Geology Prediction (2026)

Competition repo for [ROGII - Wellbore Geology Prediction](https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction).

| | |
|---|---|
| Task | Predict TVT (True Vertical Thickness, ft) along the evaluation zone of horizontal wellbores |
| Metric | RMSE |
| Prize pool | $50,000 (1st $25k / 2nd $13k / 3rd $7k / 4th $5k) |
| Start | 2026-05-05 |
| Entry & team-merge deadline | 2026-07-29 |
| Final submission | 2026-08-05 |
| Submission format | Kaggle Notebook, ≤9 h CPU/GPU runtime, no internet at submit time |

See `docs/competition-overview.md` for the full problem and dataset spec captured from the Kaggle pages.

---

## Disk layout

```
kaggle-rogii-2026/
├── data/                # gitignored (1.33 GB raw dataset)
│   ├── raw/             # downloaded archive + extracted CSVs/PNGs/PPTX
│   ├── interim/         # per-well intermediate artifacts
│   └── processed/       # model-ready features
├── docs/                # competition spec, decisions log, experiment notes
├── notebooks/           # exploration + Kaggle submission notebooks
├── scripts/             # data download, verification, submission helpers
├── src/rogii/           # importable code (features, models, eval)
└── tests/               # pytest
```

---

## Bootstrap

### One-time manual steps (you, not Claude)

1. **Sign in to Kaggle and accept the competition rules** on the [competition page](https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction/rules). Without this, the API will refuse to download.
2. **Create a Kaggle API token**: visit <https://www.kaggle.com/settings>, click *Create New Token*. A `kaggle.json` will download.
3. **Install the token locally** — never paste it into chat:
   ```bash
   mkdir -p ~/.kaggle
   mv ~/Downloads/kaggle.json ~/.kaggle/kaggle.json
   chmod 600 ~/.kaggle/kaggle.json
   ```
4. **Identity verification** on Kaggle (passport/ID): required for *submitting* (not for downloading data). Defer to week 2.

### Automated bootstrap

Once `~/.kaggle/kaggle.json` is in place:

```bash
./scripts/download_data.sh        # ~1.33 GB, ~2,327 files, expands under data/raw/
uv run scripts/verify_data.py     # sanity check counts and sizes
```

`uv` provides the Kaggle CLI on demand (`uv run --with kaggle ...`) — no global install needed.

---

## Working agreements

- Python via `uv run` (matches workspace-hub convention).
- Branches: feature branches off `main`, no force pushes.
- Commits: small and descriptive; no secrets, no data.
- Notebooks committed without large outputs (use `nbstripout` or `--clear-output` before committing).
- Decisions log: append to `docs/decisions.md` whenever a non-obvious choice is locked in.
