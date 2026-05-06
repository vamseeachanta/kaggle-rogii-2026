# Plan for #1: Phase 0.5 — Linear extrapolation baseline

> **Status:** plan-review
> **Tier:** T1
> **Date:** 2026-05-06
> **Issue:** https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1
> **Review artifacts:** `scripts/review/results/2026-05-06-plan-1-claude.md`

---

## Resource Intelligence Summary

### Existing repo code
- `notebooks/00_baseline_carry_forward.ipynb` — carry-forward baseline (the floor to beat: **11.53 ft RMSE on 10-well sample**).
- `notebooks/10_dtw_alignment.ipynb` — eval harness pattern (`load(well)`, sample 10 random wells, compute per-well RMSE, aggregate). The new notebook should mirror this exactly so the comparison is apples-to-apples (same RNG seed, same well subset).
- `src/rogii/features/correlation.py` exposes a `rmse(y_true, y_pred)` helper that's NaN-safe — reuse rather than re-implement.
- `src/rogii/models/` does **not** exist yet; this plan creates it.

### Prior plans / decisions
- `docs/decisions.md` 2026-05-05 entry "Phase 1 v1 finding": carry-forward = 11.53, correlation = 297.86, "v2 needs ... linear extrapolation as the real baseline to clear (not literal carry-forward)" — direct motivation for this issue.
- `docs/roadmap.md` Phase 0 currently lists carry-forward only; the floor needs upgrading.

### Data findings (verified)
- 773 train wells; median ~6,400 rows/well at 1 ft MD spacing.
- `TVT_input` non-null fraction = 0.273 → average heel = ~1,750 rows; some wells will be smaller.
- TVT range per well typically ~500 ft of drift (e.g., well `000d7d20` 11236 → 11756, 520 ft).
- Heel `TVT_input` is observed continuously at 1 ft step in MD — slope of last N points is well-defined.

### Gaps identified
- No `src/rogii/models/` package.
- No code to fit a slope from heel `(MD, TVT_input)` and project forward.
- No comparison harness that runs multiple baselines side-by-side on the same wells.

---

## Artifact Map

| Artifact | Path |
|---|---|
| This plan | `docs/plans/2026-05-06-issue-1-linear-extrapolation.md` |
| Implementation | `src/rogii/models/linear_extrap.py` |
| Package init | `src/rogii/models/__init__.py` |
| Notebook | `notebooks/05_linear_extrapolation.ipynb` |
| Decisions log update | `docs/decisions.md` |
| Plans index update | `docs/plans/README.md` |
| Review (Claude self) | `scripts/review/results/2026-05-06-plan-1-claude.md` |

---

## Deliverable

A `predict_linear_extrap(h, n_recent)` function and an evaluation notebook that benchmark linear extrapolation of the heel's last-N TVT_input slope against the carry-forward floor on the same 10-well sample used by `10_dtw_alignment.ipynb`.

---

## Hypothesis & experimental design

| Field | Statement |
|---|---|
| **Hypothesis** | Linear extrapolation from the last ~200 heel rows beats carry-forward on the majority of wells, because most wells drift through the toe rather than staying flat. |
| **Experiment** | Same 10-well sample (RNG seed = 0, same `wells = list(rng.choice(wells, 10, replace=False))` call as in `10_dtw_alignment.ipynb`). Compute per-well eval-zone RMSE for carry-forward and linear extrapolation across `n_recent ∈ {50, 100, 200, 500, ALL_HEEL}`. Metric is RMSE on the eval-zone rows only. |
| **Predicted outcome** | Linear wins on **≥ 6 / 10 wells** at `n_recent = 200`. The aggregate-RMSE band 6–10 ft is a self-calibration prior (not used in the decision rule) — the rule looks only at the wins-count, which is fully falsifiable. |
| **Decision rule** | **Canonical n_recent = 200** (locked in advance to avoid data-leak from sweep cherry-picking). If linear @ n_recent=200 wins on ≥ 6 / 10 → adopt as the new Phase 0 floor; update issue [#2](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/2) to retarget Phase 1 v2 against the new bar. If wins on < 6 / 10 → keep carry-forward as floor; record per-well failure mode and consider regime-classifier before Phase 1 v2. Other `n_recent` values are reported for diagnostic context only — they cannot flip the floor decision. |

---

## Files to Change

| Action | Path | Reason |
|---|---|---|
| Create | `src/rogii/models/__init__.py` | new package |
| Create | `src/rogii/models/linear_extrap.py` | `predict_linear_extrap(h, n_recent)` + `predict_carry_forward(h)` for shared harness |
| Create | `notebooks/05_linear_extrapolation.ipynb` | eval harness, sweep over `n_recent`, comparison table |
| Modify | `docs/decisions.md` | append outcome and floor decision |
| Modify | `docs/plans/README.md` | add this plan to the index |
| Modify | `docs/roadmap.md` (only if hypothesis supported) | update Phase 0 floor with linear extrap |

---

## Acceptance criteria

- [ ] `from rogii.models.linear_extrap import predict_linear_extrap` works from a notebook in this repo.
- [ ] `notebooks/05_linear_extrapolation.ipynb` runs end-to-end via `nbclient` with no errors.
- [ ] Comparison table prints per-well RMSE for both methods at every `n_recent` value swept.
- [ ] Aggregate (mean) RMSE recorded in `docs/decisions.md` 2026-05-06 entry.
- [ ] Decision-rule branch is followed: either (a) issue [#2](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/2) updated with new floor, OR (b) carry-forward kept as floor with documented reason.
- [ ] Same 10 wells as `10_dtw_alignment.ipynb` (verifiable by `wells` list match).
- [ ] Each well's predicted TVT in the eval zone is **clipped** to `[heel_min - 1.5 × heel_drift, heel_max + 1.5 × heel_drift]` to prevent slope blow-up; clip-rate per well reported.
- [ ] Decisions.md entry **explicitly notes the n=10 sample-size limitation** and proposes a follow-up at n=50 wells if linear becomes the new floor.

---

## Adversarial review summary

| Provider | Verdict | Key findings |
|---|---|---|
| Claude (self) | MINOR | (1) Linear assumes constant slope through toe, but real wells curve — flag in risk section. (2) `n_recent` chosen by hand-tuning — note that we sweep multiple values to mitigate. (3) Sharp-stopping wells (drift then flatten) will hurt linear under RMSE — accept as informative failure mode. (4) Heel < n_recent edge case must fall back gracefully — required handling in implementation. |

**Overall result:** PASS

Revisions from review:
- Added decision-rule branch for "< 6 / 10 wells beat" so we don't rubber-stamp the result either way.
- Added explicit edge-case requirement: heel rows < `n_recent` → fall back to carry-forward for that well; record fall-back rate in the comparison table.
- Locked the same 10 wells as `10_dtw_alignment.ipynb` so this comparison can be merged with v1's results without re-running v1.

---

## Risks and open questions

- **Risk:** Wells where the heel's last 200 rows have noisy slope (e.g., a small dip change just before PS) will project a bad direction into the toe. Mitigation: report per-well RMSE so we can characterize the failure mode; sweep `n_recent` to show robustness.
- **Risk:** Linear extrap may exceed reasonable TVT bounds on long laterals — clip to `[heel_min - margin, heel_max + margin]` where margin = 1.5 × heel_drift. Open question: is a clip a feature or a bug? Will revisit if it makes the difference between "wins" and "loses."
- **Open:** Should we compute slope from `(MD, TVT_input)` raw, or first smooth `TVT_input` with a rolling median? v1 ships raw; smoothing variant deferred to Phase 1 v2.
- **Open:** A regime-classifier (Slide 7: increasing / decreasing / constant) could beat both unconditionally. Out of scope for this T1 issue; flagged as a Phase 0.6 candidate if Phase 0.5 itself is borderline.

---

## Tier justification

**T1.** Single new module (~50 lines), single notebook (~5 cells), no new infrastructure, ≤ 60 min wall-clock. Outcome decides one parameter (the floor RMSE) used by [#2](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/2); not load-bearing for any other phase.
