# Modeling roadmap — ROGII Wellbore Geology Prediction

13 weeks (2026-05-05 → 2026-08-05). Updated 2026-05-05 after dataset download and PPTX task-brief extraction. Five phases; Phase 0 already complete.

---

## What we know about the data (anchors every modeling decision below)

From `docs/competition-overview.md`, `docs/task-brief.md`, and the verified dataset on disk:

- **773 train wells, ~200 hidden test wells.** Visible test sample is 3 wells (placeholders).
- **Per well: ~6,400 rows of horizontal-well data at ≈1 ft MD spacing**, p90 = 7,766 rows. Lateral length ~1.2–1.5 mi.
- **Eval zone is 72.7% of every well, including train.** `TVT_input` is heel-only (~27%) for both train and test wells. `TVT` (the target) is fully populated only in train. *We can train on the exact shape we predict — no synthetic truncation needed.*
- **Two coordinate systems in play.** Formation-top columns (`ANCC`, `ASTNU`, `ASTNL`, `EGFDU`, `EGFDL`, `BUDA`) are in **TVD** (negative ft, ~−9,400). Target `TVT` is in the **typewell's depth frame** (positive ft, ~+11,500). The geosteering function is `Z(MD) → TVT(MD)` — an alignment, not a regression.
- **Typewell:** ~1,300 rows × `{TVT, GR, Geology}`. Geology labels are **richer** than the train-only formation-top columns (e.g., `LBHL`, `LTHL`, `LTGT`, `MNSS` appear in typewells but not as horizontal-well column headers).
- **One typewell per horizontal well** (Slide 4 of the task brief).
- **GR resolution asymmetry (Slide 9).** Lateral GR has *higher resolution* than typewell GR — a load-bearing modeling hint baked into the brief by ROGII themselves.
- **Three drilling regimes (Slide 7).** TVT increasing / decreasing / constant. Regime is observable from the trajectory and from the GR-vs-typewell match direction.
- **Offset wells matter (Slides 12–13).** Neighboring wells (same X/Y region) share geological dip patterns; an offset well's TVT trajectory is a usable prior for the current well.
- **Metric: RMSE** on dTVT = manual − predicted, computed across all eval-zone points and all wells (Slide 14).

---

## Phase 0 — Floor anchor ✅ DONE (2026-05-05)

Goal: produce a valid Kaggle submission within session 1 to anchor a leaderboard floor and prove the submission pipeline.

- **Approach.** Carry-forward: predict `TVT[t] = last observed TVT_input value`. No ML.
- **Result.** `submissions/00_carry_forward_submission.csv` (14,151 rows on the visible test set). Format validated; eval-zone start matches data inspection exactly.
- **Limitation.** Carry-forward only beats wells where TVT stays roughly constant in the toe. For climbing/descending laterals (the common case) it's badly biased.
- **Artifact.** `notebooks/00_baseline_carry_forward.ipynb`.
- **Next step.** Submit this on Kaggle once identity verification clears, just to bank a leaderboard score and validate format end-to-end on the real hidden test set.

## Phase 1 — Multi-reference DTW alignment (Weeks 1–2, current)

Goal: encode the expert geosteering workflow as a deterministic model and beat the Phase-0 floor by a wide margin.

- **Core insight (revised after task brief).** The toe of each well must be aligned against **two reference series**, not just the typewell:
  1. **Lateral heel** of the same well (rows 0..PS) — `GR(MD) ↔ TVT_input(MD)` is a direct, in-well correspondence at higher resolution than the typewell. Slide 9 calls this out explicitly.
  2. **Typewell** `GR(TVT) ↔ Geology(TVT)` — the canonical depth reference for the area.
- **Approach.**
  1. Build a "GR-keyed depth map" from the heel: a function that maps GR signature → TVT, learned from rows where both are observed.
  2. Build the same map from the typewell.
  3. For each toe row, compute a candidate TVT from each map (with windowed DTW for noise-robustness) and combine — weighted by local correlation strength and trajectory consistency.
  4. Constrain the alignment to be **monotone within a regime** (climbing / descending / staying), with regime breaks allowed at trajectory dip-changes.
- **Trajectory regularization.** TVT must vary smoothly with the trajectory. Use `Z(MD)` and `dZ/dMD` to bound TVT drift; a sudden TVT jump unsupported by trajectory or formation tops is suspect.
- **Risks.** DTW sensitive to noise; faults break monotonicity. Mitigate with windowed DTW + Sakoe–Chiba band, plus a fault-crossing fallback that re-anchors using the typewell.
- **Open questions, prioritized.**
  1. How prevalent are wells where heel-only-DTW already nails the toe (i.e., is heel-self-correlation the dominant signal)?
  2. Where DTW fails, is it noise, fault, or out-of-typewell-range geology?
  3. What's the right fusion weight between heel-DTW and typewell-DTW?
- **Artifact.** `notebooks/10_dtw_alignment.ipynb`, `src/rogii/features/correlation.py`, `src/rogii/models/dtw.py`.

## Phase 2 — Offset-well priors (Weeks 3–4)

Goal: turn neighboring-well trajectories into a feature class that conditions every downstream model.

- **Why this is its own phase, not a feature inside Phase 1.** The task brief promotes offset wells from "stretch goal" to "primary signal" (Slides 12–13). Pad-aware modeling needs a spatial index, a coordinate-transformation layer, and a separate validation strategy (leave-pad-out CV) — not just one more feature column.
- **Approach.**
  1. Build a spatial index over (X, Y) of all train wells.
  2. For each test well, retrieve the K=3–10 nearest train wells by minimum 2D distance to the lateral path.
  3. For each neighbor, project its `TVT(MD)` trajectory into the test well's MD frame using the trajectory geometry (X, Y, Z, azimuth, dip).
  4. Emit features per test row:
     - Median / quantiles of neighbors' TVT at this projected position.
     - Variance across neighbors (a confidence proxy).
     - Median dip rate (dTVT / dMD) across neighbors — captures shared geological tilt.
  5. Use as features in Phase 3 GBDT and as a soft prior in Phase 4 sequence model.
- **CV.** Leave-pad-out (group wells by inferred pad clusters), not leave-one-well-out — wells in the same pad have correlated geology and would leak.
- **Artifact.** `src/rogii/features/offset_wells.py`, `src/rogii/util/spatial.py`, `notebooks/15_offset_well_features.ipynb`.

## Phase 3 — Feature engineering + GBDT (Weeks 5–6)

Goal: structured-data baseline that combines DTW outputs and offset-well features into a row-level regressor.

- **Approach.** Per-row features:
  - **DTW outputs** from Phase 1: best-match TVT (heel-DTW), best-match TVT (typewell-DTW), correlation strengths, regime label (incr/decr/const).
  - **Offset-well features** from Phase 2.
  - **Trajectory:** MD, X, Y, Z, `dZ/dMD` (dip), inclination, distance from PS.
  - **Logs:** GR with rolling stats, `dGR/dMD`, peak-trough motifs.
  - **History:** rolling stats of `TVT_input` over the heel; last-observed value; slope of last-N samples.
  - **Geological context:** distance to typewell formation tops (forbidden to use train-only formation-depth columns at inference).
- **Models.** LightGBM first; XGBoost / CatBoost for ensemble.
- **CV.** Leave-pad-out, same as Phase 2.
- **Artifact.** `src/rogii/features/`, `src/rogii/models/gbdt.py`, `notebooks/20_gbdt_baseline.ipynb`.

## Phase 4 — Sequence model with regime-classification head (Weeks 7–10)

Goal: a model that predicts the TVT trajectory along MD as a sequence, conditioned on lateral logs + typewell + offset-well prior.

- **Architecture options** (increasing complexity):
  1. 1D-CNN encoder over `GR, dGR/dMD, dZ/dMD, TVT_input` per MD position; regression head + auxiliary regime-classification head.
  2. Bi-directional GRU/LSTM over the lateral, with the typewell + offset-well prior as cross-attention banks.
  3. Decoder-only transformer along MD, two cross-attention keys: (typewell GR/Geology) and (concatenated nearest-neighbor TVT trajectories).
  4. State-space (e.g., Mamba) if RNN/transformer hit memory walls on the longest 9k-row laterals.
- **Multi-task supervision** (each loss weighted, scheduled):
  - **Primary:** TVT regression (RMSE matches the metric).
  - **Auxiliary 1: regime classification** — three classes, increasing / decreasing / constant, derived from `dTVT/dMD` thresholds. Per Slide 7.
  - **Auxiliary 2: typewell formation label** — predict the `Geology` label that the alignment maps each MD row to. Provides geological grounding without leaking train-only formation-top columns.
- **Training data.** Per-well sequences with the heel/toe split exactly as observed in train. No synthetic truncation needed.
- **Artifact.** `src/rogii/models/sequence.py`, `notebooks/30_sequence_model.ipynb`.

## Phase 5 — Ensembling + submission packaging (Weeks 11–13)

- **Stack.** Weighted blend of (DTW alignment) + (GBDT) + (sequence model). Likely sequence model dominates with GBDT as residual corrector and DTW as anchor.
- **Calibration.** Per-well bias correction using the known heel TVT history — every well's first eval-zone prediction must agree with the last heel value to within sub-foot.
- **Robustness.** Stress-test on synthetic fault scenarios. Add a fault-detection head only if discontinuity handling materially moves the score.
- **Submission packaging.**
  - Pretrained weights uploaded as a Kaggle Dataset (internet is disabled at submit time).
  - Notebook end-to-end runtime profiled to < 9 h on Kaggle's hardware before the final week.
  - Submit a "safe" baseline (DTW + GBDT, deterministic) AND a "best" model on the last day to keep a fallback if a bug breaks the best run.

---

## Cross-cutting concerns

- **Reproducibility.** Every notebook seeds RNGs. Every artifact keys to a git SHA + dataset MD5. Each model checkpoint named with phase, CV fold, seed, and SHA.
- **Validation strategy hierarchy.**
  - **Phase 1 (DTW):** leave-one-well-out (each well stands alone).
  - **Phase 2+:** leave-pad-out — required because offset-well features leak across wells in the same pad.
  - **Final blend:** leave-pad-out + temporal split if drilling dates are inferable.
- **Compute.** Local first (CPU + any GPU on ace-linux-1 / ace-linux-2). Kaggle's free P100/T4 only for the submission notebook itself.
- **Internet-disabled at submit.** All external assets (pretrained weights, geological reference tables, fitted features) must be uploaded as Kaggle Datasets/Models before the final submission run.
- **Identity verification.** User must complete this on Kaggle before any submission. Defer to mid-Phase 1.
- **PDF of task brief.** Conversion deferred to ace-linux-2 — see [vamseeachanta/workspace-hub#2651](https://github.com/vamseeachanta/workspace-hub/issues/2651).

## Open questions still on the table

- How prevalent are fault discontinuities in the training set?
- Are pads detectable from (X, Y) clustering, or do we need explicit pad metadata?
- What's the typical noise floor on GR?
- Are train-only formation-top columns (`ANCC`, `ASTNU`, …) sparse or fully populated? Sparse columns hint at faults / formation absence.
- Is the typewell coordinate frame consistent across wells (same `TVT=0` reference) or per-pad?
