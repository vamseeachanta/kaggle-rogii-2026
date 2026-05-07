# Adversarial review — Plan #2 (Phase 2 Offset-well features and pad-aware CV)

**Reviewer:** Claude (self-review)
**Stance:** Adversarial. Assume defects until proven otherwise.
**Plan:** `docs/plans/2026-05-06-issue-2-phase2-offset-wells.md`
**Date:** 2026-05-06
**Verdict:** **MAJOR**

---

## Findings

### Finding 1 (MAJOR) — Projection geometry has no validity guard

**Quote:** "For each MD in target, find the 'corresponding' MD in neighbor … nearest 3D point in neighbor's path."

**Defect:** The plan acknowledges (in Risks) that this can produce nonsensical correspondence when wells diverge. But the feature module emits the result unconditionally. Downstream models will treat a 200-ft 3D-distance match the same as a 5-ft match. That's noise pretending to be signal.

**Recommendation:** Emit a per-row `offset_geometric_validity` feature alongside the others — e.g., a bool that's `True` when min 3D distance < 500 ft, else `False`. Better: emit the raw min-3D-distance and let the model learn the cutoff. The plan already proposes `offset_dist_min_3d`; explicitly document this as the validity gate that downstream models must respect.

**Status:** **Will revise** — add explicit guidance under "emit_offset_features" that `offset_dist_min_3d` is the validity-confidence channel and downstream code SHOULD condition on it (interaction features, gating, or down-weighting).

---

### Finding 2 (MAJOR) — Inference-time pad-assignment unspecified

**Defect:** Pad detection is described as DBSCAN over train wells. The plan does not say how a hidden test well's pad assignment works at inference. Possibilities:
- Re-run DBSCAN over (train + test) at inference time → pads can shift, train pad IDs become invalid for cached features.
- Assign each test well to its nearest train pad → simple but ignores test-well-cluster structure.
- Treat each test well as a singleton → loses some neighbor signal but is consistent.

The plan has no recipe. This is a *reproducibility* defect: at submit time, behavior depends on undocumented choice.

**Recommendation:** Lock the choice now: **at inference, each test well is assigned to the train pad whose centroid is nearest within `eps_ft`; if no pad centroid is within `eps_ft`, the test well is a singleton (its own pad).** This preserves train pad identity, doesn't shift cached features, and degrades gracefully for isolated test wells.

**Status:** **Will revise** — add subsection "Inference-time procedure" under the pads module.

---

### Finding 3 (MINOR) — `eps_ft = 1500` magic number

Same pattern as Plan #1 Finding 4 / Plan #3 Finding 2. Plan proposes sweep but doesn't lock the canonical value in the decision rule.

**Recommendation:** Add to decision rule: "Headline decision uses `eps_ft = 1500`. Other values reported diagnostically only."

**Status:** **Will revise.**

---

### Finding 4 (MINOR) — KDTree-on-midpoints will miss path-crossing wells

**Defect:** Two wells whose midpoints are 3,000 ft apart but whose paths cross within 100 ft of each other will be invisible to the midpoint KDTree. The plan acknowledges this in Open Questions.

**Recommendation:** No revision needed; v2 of this module can switch to path-distance index. But document expected pad-detection-correlated failures in the notebook output ("offset feature density per well"), so we know to look here when the offset signal underperforms on certain wells.

**Status:** Acceptable — covered in Open Questions.

---

### Finding 5 (CHECKED, NOT A DEFECT) — Hypothesis bar appropriately low

≥ 4/10 wins is a *contributing-feature* bar, not a *winning-feature* bar. Calibrated correctly for a feature class that we expect to be conditional ("when the well is in a dense pad").

---

### Finding 6 (CHECKED) — Tier escalation appropriate

T3 is justified: cross-cutting CV strategy, multiple architectural decisions inherited downstream. Single-degraded review (Claude + Gemini, no Codex) is the best we can do given the upstream tooling state, with explicit user acceptance documented.

---

## Verdict

**MAJOR** — two structural revisions required (Findings 1 and 2). After revisions, escalate to Gemini cross-review per T3 policy. Plan can land with single-degraded review (Claude + Gemini) per `feedback_permission_gate_blocks_cross_review.md`, contingent on user acceptance at approval time.
