# Modeling roadmap — ROGII Wellbore Geology Prediction

13 weeks (2026-05-05 → 2026-08-05). Three modeling tracks; pick which to develop first after sample-data exploration.

## Phase 0 — Floor anchor (Week 1)

Goal: produce a valid Kaggle submission within session 1, so we have a leaderboard datapoint to beat.

- **Approach.** "Carry-forward" baseline: predict TVT[t] = last observed TVT_input value for that well, for every row in the evaluation zone. No ML.
- **Why.** Kaggle's `TVT_input` is the target left-truncated at the evaluation zone. Carry-forward is the trivial completion.
- **Expected RMSE.** Loose — TVT drifts, so this will be poor on long evaluation zones with structural geology changes. But it bounds "doing literally nothing."
- **Artifact.** `notebooks/00_baseline_carry_forward.ipynb` and a Kaggle Notebook submission off the same code.

## Phase 1 — DTW alignment baseline (Weeks 2–3)

Goal: encode the expert workflow as a model and beat the Phase-0 floor by a wide margin.

- **Approach.** For each well, dynamic-time-warping (DTW) align the lateral GR(MD) signal to the typewell GR(TVT) signal over the *known* zone, then extrapolate the alignment into the evaluation zone using the trajectory geometry (X, Y, Z).
- **Why.** This mirrors what geologists do manually. Captures the "GR signature in the lateral matches a depth in the typewell" structural prior, which row-wise regression misses.
- **Risks.** DTW is sensitive to noise; faults break monotonicity. Need windowed DTW with constraints, plus a fallback for fault-crossings.
- **Open question.** Is there a single typewell per lateral, or does it vary along MD? (Answer in `data/raw/` after download.)
- **Artifact.** `notebooks/10_dtw_alignment.ipynb`, `src/rogii/features/correlation.py`.

## Phase 2 — Feature engineering + GBDT (Weeks 4–6)

Goal: structured-data baseline with hand-crafted geology features and a gradient-boosted regressor.

- **Approach.** Per-row features:
  - Trajectory: MD, X, Y, Z, dZ/dMD (dip), inclination from previous rows.
  - Logs: GR with windowed stats (rolling mean/std, dGR/dMD, peak-trough features).
  - Typewell-correlation: best-match TVT in the typewell over a sliding GR window, plus the correlation strength itself.
  - Geological context: distance from formation tops *as inferred from the typewell labels* (cannot use train-only formation-depth columns at inference).
  - History: TVT_input values up to the evaluation entry, last-observed value, slope.
- **Models.** LightGBM regressor first; XGBoost / CatBoost for ensemble candidates.
- **CV strategy.** Leave-one-well-out CV — strict, slow, but mirrors the test split.
- **Artifact.** `src/rogii/features/`, `src/rogii/models/gbdt.py`, `notebooks/20_gbdt_baseline.ipynb`.

## Phase 3 — Sequence model (Weeks 7–10)

Goal: a model that predicts the TVT trajectory along MD as a sequence, conditioned on lateral logs + typewell.

- **Candidates** (in increasing complexity):
  1. 1D-CNN encoder over GR + MD-derivatives, regression head per MD position.
  2. Bi-directional GRU/LSTM over the lateral, with the typewell as a separate cross-attention key/value bank.
  3. Small transformer (decoder-only along MD) with the typewell as encoder context — explicitly mirrors the alignment task.
  4. State-space (e.g., Mamba) for long laterals if RNN/transformer hit memory walls.
- **Training data.** Per-well sequences truncated at varying points to simulate the evaluation-zone NaN pattern.
- **Auxiliary losses.** Predict formation labels (from the typewell `Geology` column, propagated via the alignment) as a multi-task signal — leverages train-only formation tops without leaking them at inference.
- **Artifact.** `src/rogii/models/sequence.py`, `notebooks/30_sequence_model.ipynb`.

## Phase 4 — Ensembling + submission packaging (Weeks 11–13)

- Stack: weighted blend of GBDT + sequence model + DTW baseline.
- Calibration: per-well bias correction using the known (pre-evaluation-zone) TVT history.
- Robustness: stress-test on synthetic fault scenarios; add a fault-detection head if discontinuity-handling moves the needle.
- Submission packaging:
  - Pretrained weights uploaded as a Kaggle Dataset (internet is disabled at submit time).
  - Notebook ≤9 h runtime; profile end-to-end before final week.
  - Submit a "safe" model and a "best" model on the last day to keep one in reserve.

## Cross-cutting concerns

- **Reproducibility.** Every notebook seeds RNGs. Every artifact is keyed to a git SHA + dataset MD5.
- **Compute.** Local first (CPU + any GPU on `ace-linux-1`/`ace-linux-2`); Kaggle's free GPU only for the submission notebook.
- **Internet-disabled submission.** All external assets (pretrained weights, geological reference tables) must be uploaded as Kaggle Datasets/Models before final submission.
- **Identity verification.** User must complete this on Kaggle before the first submission. Defer to mid-Phase-1.

## Open questions to answer from the sample data

- How long are evaluation zones (rows per well)?
- Is the typewell unique per lateral or shared across many?
- How prevalent are fault discontinuities in the training set?
- Are the formation-top columns (`ANCC`, `ASTNU`, …) consistent across all wells, or sparse?
- What is the noise floor on `GR`?
- What is the typical absolute scale of TVT (helps us interpret RMSE numbers)?
