# Adversarial review — Plan #3 (Phase 0.5 linear extrapolation)

**Reviewer:** Claude (self-review)
**Stance:** Adversarial. Assume the plan has defects until proven otherwise. No praise; no restatement; only what's wrong, missing, or risky.
**Plan reviewed:** `docs/plans/2026-05-06-issue-3-linear-extrapolation.md`
**Plan SHA:** local pre-commit (will record after first commit)
**Date:** 2026-05-06
**Verdict:** **MINOR**

---

## Findings

### Finding 1 (MINOR) — Predicted outcome "6–10 ft" is hand-wavy

**Quote:** "Aggregate RMSE for linear (best `n_recent`) lands in **6–10 ft**, vs carry-forward 11.53."

**Defect:** The 6–10 ft band is not derived from any observation. The plan offers no model of why linear should land specifically in that range. If linear lands at 11 ft (a 0.5 ft improvement) the plan would technically still be "in the predicted band's neighborhood," which makes the prediction unfalsifiable in practice.

**Recommendation:** Drop the numeric band. Predict only direction: "linear improves on carry-forward (lower aggregate RMSE) on ≥ 6/10 wells." That is the load-bearing claim and is fully falsifiable.

**Status:** Plan keeps the band as a *expected* number for self-calibration but the **decision rule uses only the wins-count threshold**, which is unambiguous. Acceptable but flagged.

---

### Finding 2 (MINOR) — `n_recent` sweep has unspecified handling for short heels

**Quote:** "sweep `n_recent ∈ {50, 100, 200, 500, ALL_HEEL}` … heel rows < `n_recent` → fall back to carry-forward for that well; record fall-back rate"

**Defect:** "ALL_HEEL" is well-specific (avg ~1,750 heel rows but variable). The sweep order matters: if we report best-of-sweep, we're cherry-picking. The plan should commit *in advance* to one canonical `n_recent` for the floor decision, or report the median across the sweep, not the best.

**Recommendation:** Decision rule uses **a fixed `n_recent = 200`** (the plan's prior, named in the issue body). Other values reported for context but do not flip the floor decision. Otherwise we're optimizing on the same 10 wells we're evaluating on — an explicit data-leak in the methodology.

**Status:** **Will revise** — the plan's "decision rule" line will be updated before posting to GH to lock `n_recent = 200` as the canonical value for the floor decision. Sweep stays for diagnostic context.

---

### Finding 3 (MINOR) — Slope blow-up risk under-specified

**Quote:** "Linear extrap may exceed reasonable TVT bounds on long laterals — clip to `[heel_min - margin, heel_max + margin]` where margin = 1.5 × heel_drift."

**Defect:** The clip is named in the Risks section but **not** in Acceptance criteria. An implementer could ship without it. If a single noisy heel produces a 20,000-ft TVT projection, RMSE for that well dominates the aggregate and silently kills the experiment.

**Recommendation:** Promote clipping to an Acceptance criterion: "Each well's predicted TVT in the eval zone is clipped to `[heel_min - 1.5 × heel_drift, heel_max + 1.5 × heel_drift]`."

**Status:** **Will revise.**

---

### Finding 4 (MINOR) — Sample size of 10 is small for a binary "wins on majority" rule

**Defect:** With n=10 wells, the binomial 95% CI for "linear beats carry-forward on 6/10" is roughly [0.26, 0.88] — i.e., even a 6/10 outcome is consistent with linear being only 26% likely to win in the population. We risk locking in a "winning" floor based on coin-flip noise.

**Recommendation:** State sample-size limitation explicitly in the decisions.md write-up. If 6/10 wins, plan a follow-up at n=50 wells before treating linear as the durable floor (cheap; the existing harness scales linearly in well count).

**Status:** Acceptable to ship at n=10 for now (T1 cost); the decisions.md update will note the limitation.

---

### Finding 5 (CHECKED, NOT A DEFECT) — RNG seed match

**Quote:** "Same 10 wells as `10_dtw_alignment.ipynb` (verifiable by `wells` list match)."

**Verification:** Read `10_dtw_alignment.ipynb` cell `evaluate`: `rng = np.random.default_rng(0)` then `sample_wells = list(rng.choice(wells, size=10, replace=False))`. Reproduces deterministically. Plan's claim is verified — same wells will be drawn.

---

### Finding 6 (NOT A DEFECT) — Resource intel source count

Counted: `00_baseline_carry_forward.ipynb`, `10_dtw_alignment.ipynb`, `correlation.py`, `decisions.md`, `roadmap.md`, issue body = 6 distinct sources. Meets ≥3 minimum.

---

## Items checked but not flagged

- File-existence claims: all paths the plan creates are confirmed missing (`src/rogii/models/` does not exist); all paths cited as existing are verified present.
- Carry-forward RMSE 11.53 number: matches `docs/decisions.md` 2026-05-05 entry verbatim.
- Tier classification: T1 justified — single module, single notebook, no infra changes.

---

## Verdict

**MINOR.** Three required revisions before posting:
1. Decision rule locks `n_recent = 200` for the floor decision (Finding 2).
2. Clipping is an acceptance criterion (Finding 3).
3. decisions.md write-up acknowledges n=10 sample-size limitation (Finding 4).

After revisions, the plan can post to GH issue [#3](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/3) with `status:plan-review`. **User approval gate is load-bearing — never self-approve.**
