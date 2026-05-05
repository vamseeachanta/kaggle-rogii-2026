# ROGII — Wellbore Geology Prediction (captured 2026-05-05)

Source: <https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction>

## Problem

Predict the geology along a horizontal wellbore — specifically the **TVT (True Vertical Thickness, ft)** at each ~1 ft step of the lateral, over an *evaluation zone* whose target values are hidden. Drilling crews use TVT as the proxy for "where the bit sits within the formation"; better TVT prediction reduces drift into low-yield zones, redundant drilling, and corrective sidetracks.

## Data layout

`train/` and `test/` directories. Each well is identified by an 8-character hash (e.g., `015fe0d2`). Per well:

### `{WELLNAME}__horizontal_well.csv`
| Column | Units | Description |
|---|---|---|
| `WELLNAME` | — | Well id |
| `MD` | ft | Measured depth (along-hole length from surface) |
| `X` | ft | Easting |
| `Y` | ft | Northing |
| `Z` | ft | True vertical depth below sea level |
| `ANCC`, `ASTNU`, `ASTNL`, `EGFDU`, `EGFDL`, `BUDA` | ft | Predicted depth of geological formations (**train only**) |
| `GR` | API | Gamma-ray log (natural radioactivity) |
| `TVT` | ft | **Target.** Manually interpreted geological position (train only) |
| `TVT_input` | ft | TVT with NaN over the evaluation zone — provided as a feature |

### `{WELLNAME}__typewell.csv` — vertical reference log for correlation
| Column | Units | Description |
|---|---|---|
| `TVT` | ft | Vertical depth index — corresponds to TVT in the horizontal well |
| `GR` | API | Vertical gamma-ray signature |
| `Geology` | label | Formation label (e.g., `EGFDL`, `BUDA`) |

### `{WELLNAME}.png`
Visualization of the well path and geological cross-section (useful for QA and intuition).

### Top-level
- `sample_submission.csv` — `id,tvt` where `id = {WELLNAME}_{row_index}`.
- `AI_wellbore_geology_prediction_task_en.pptx` (28.79 MB) — task brief with diagrams.
- `test/` shown to contestants is a tiny sample drawn from train; on submission rerun, it's replaced with the real ~200-well hidden set.

### Totals
- 2,327 files, 1.33 GB.

## Evaluation

Root mean squared error on `tvt`:
$$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2}$$

Submission file:
```
id,tvt
000d7d20_1442,0.0
000d7d20_1443,0.0
...
```

## Code competition rules

- Submissions via Kaggle Notebook only.
- ≤9 h CPU runtime, ≤9 h GPU runtime.
- **Internet disabled at submission time** — pretrained models must be uploaded as Kaggle Datasets/Models first.
- Public external data and pre-trained models permitted.
- Output filename: `submission.csv`.
- Identity verification required to submit.

## Timeline (UTC, 23:59)

| Date | Event |
|---|---|
| 2026-05-05 | Start |
| 2026-07-29 | Entry deadline + team merger deadline |
| 2026-08-05 | Final submission |

## Prizes

| Place | USD |
|---|---|
| 1st | $25,000 |
| 2nd | $13,000 |
| 3rd | $7,000 |
| 4th | $5,000 |

## Citation
Igor Kuvaev, Rafael Aguilar, John Granmayeh, Ryan Holbrook, María Cruz, and Ashley Oldacre. ROGII - Wellbore Geology Prediction. <https://kaggle.com/competitions/rogii-wellbore-geology-prediction>, 2026.

## Domain notes (interpretation)

- This is a **geosteering / log-correlation** task. The expert workflow aligns the lateral's GR trace against the typewell's GR-vs-depth signature; the alignment IS TVT.
- `TVT_input` makes it a **sequence-completion** problem along MD: model sees TVT history up to the evaluation zone, then must continue it.
- Geological formation tops (`ANCC`, `ASTNU`, etc.) are *train-only* features — they're "answers in disguise" and shouldn't be used as inputs at inference; treat them as auxiliary supervision targets if helpful.
- TVT is locally smooth but punctuated by **discontinuities at faults**. Models that produce smooth predictions will lose ground on fault-crossing wells.
