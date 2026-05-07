# Adversarial review — Plan #1 (Phase 1 v2 Heel-anchored DTW)

**Reviewer:** Claude (self-review)
**Stance:** Adversarial. Assume defects until proven otherwise.
**Plan:** `docs/plans/2026-05-06-issue-1-phase1-v2-heel-dtw.md`
**Date:** 2026-05-06
**Verdict:** **MAJOR**

---

## Findings

### Finding 1 (MAJOR) — Pseudocode references undefined helper functions

**Quote:** Pseudocode uses `correlate_q_in_band(q, ref_gr, ref_depth, anchor, radius_ft)`, `correlate_at_positions(q, heel_gr_at_candidates)`, `heel_tvt_at(best_heel_md)` without defining their signatures.

**Defect:** An implementer reading this plan can't begin without making API decisions that aren't reviewed. The whole point of T2 plans is that the architecture is settled at plan time, not at implementation time. Right now the plan ducks the API question by hiding it inside helper-function names.

**Recommendation:** Add an explicit "Helper functions" subsection to the pseudocode that lists each helper with type signature and one-line responsibility. Two extra paragraphs in the plan; saves an implementation rewrite.

**Status:** **Will revise.**

---

### Finding 2 (MINOR) — Predicted RMSE band 5–9 ft is unsupported

Same shape of defect as caught in Plan #3 review. The decision rule already uses wins-count only, so this is documentation-only weakness. Acceptable but worth flagging.

**Status:** Acceptable; no revision required.

---

### Finding 3 (MINOR) — TDD list misses synthetic-fault test

**Defect:** The plan flags faults as a risk but the test list has no test that exercises a fault scenario (e.g., a synthetic well with a TVT discontinuity). The implementation could silently mishandle faults and pass all 7 tests.

**Recommendation:** Add `test_predict_tvt_multi_ref_synthetic_fault` — synthetic well with a TVT jump partway through the toe; expect the prediction to either track the post-fault TVT or fall back to anchor. Either is fine; what matters is *not* hanging or returning NaN.

**Status:** **Will revise** — add the test row.

---

### Finding 4 (MINOR) — `corr_threshold = 0.6` magic number

**Defect:** Same pattern as Phase 0.5 `n_recent` — single value chosen by hand, sweep proposed in Risks. Decision rule should explicitly lock this value to avoid sweep cherry-picking.

**Recommendation:** Add to decision rule: "Headline decision uses `corr_threshold = 0.6`. Other thresholds reported as diagnostic context only."

**Status:** **Will revise.**

---

### Finding 5 (CHECKED, NOT A DEFECT) — Higher bar than Phase 0.5

Phase 0.5 decision rule is wins ≥ 6/10; this plan is wins ≥ 7/10. Justification: Phase 1 v2 is materially more sophisticated and should clear a noticeably higher bar to justify its complexity. Defensible.

---

### Finding 6 (CHECKED, NOT A DEFECT) — Source count and consistency

Counted 7 distinct sources in resource intel. Meets ≥3 minimum. Cross-references to plan #3 and roadmap consistent.

---

## Verdict

**MAJOR** — one structural revision required (Finding 1: helper-function signatures). Two MINOR revisions ride along (Findings 3, 4). After revisions, escalate to Gemini cross-review per T2 policy.
