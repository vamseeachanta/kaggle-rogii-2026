# Adversarial review — Plan llm-wiki#40 (Reservoir-engineering literature ingest)

**Reviewer:** Claude (self-review)
**Stance:** Adversarial. Assume defects until proven otherwise.
**Plan:** `kaggle-rogii-2026/docs/plans/2026-05-06-issue-llm-wiki-40-reservoir-engineering-literature.md`
**Date:** 2026-05-06
**Verdict:** **MAJOR**

---

## Findings

### Finding 1 (MAJOR) — License-compliance acceptance criterion is unverifiable mechanically

**Quote:** "License compliance: zero copied text > 15 words quoted; zero displacive summaries > 30 words; zero ingestion of cite-only material."

**Defect:** "Zero displacive summaries" is a judgment call that no test or grep can verify. A reviewer reading 5 wiki pages can miss a paraphrased section that a co-author would catch. With the high stakes (commercial-textbook material, redistribution license), unverifiable criteria are how lawsuits happen later.

**Recommendation:** Add a **structured review checklist** as part of the PR template:
- For each cited commercial source: note the section/page being cited; the wiki page's claim attributable to it; the original wording (in private notes, not the wiki); the wiki's wording. Reviewer compares both.
- Run a script that flags any 30+ consecutive-word chunk in wiki pages that also appears in any cited commercial textbook (would require OCR / text-extraction; if too costly, fall back to the manual checklist).
- Promote "limit cite-only commercial citations to ≤1 per concept page" to a hard rule, not a guideline.

**Status:** **Will revise** — add the structured checklist as an Acceptance criterion sub-item; cap commercial-citation count.

---

### Finding 2 (MAJOR) — PR strategy is unspecified

**Defect:** Phase 5.4 says "Submit PR to vamseeachanta/llm-wiki main" — singular. Adding 5+ wiki pages, 2 methodology pages, a standards index, a seeds YAML, and modifying cross-links.md in **one PR** likely produces a 500+ line diff that's hard to review. PR-review fatigue → rubber-stamp → license errors slip in.

**Recommendation:** Define a **wave-by-wave PR strategy**:
- PR 1: Bootstrap (`wikis/reservoir-engineering/` empty dir + README, `seeds/reservoir-engineering-resources.yaml` skeleton). Small, easy to review.
- PR 2: First 2 concept pages (porosity, permeability) + their citations. License audit per page.
- PR 3: Next 3 concept pages.
- PR 4: 2 methodology pages.
- PR 5: Standards index + cross-links update.

Each PR independently reviewable. If license violation found in PR 2, future PRs benefit from the lesson.

**Status:** **Will revise** — replace "submit PR" with the wave structure.

---

### Finding 3 (MINOR) — `Files to Change` doesn't list llm-wiki planning bootstrap explicitly

**Defect:** Phase 5.4 step 3 says "Bootstrap llm-wiki/docs/plans/ infrastructure if absent (mirror kaggle-rogii-2026 pattern)." But the Files-to-Change table doesn't include those bootstrap files. An implementer could read the table only and miss this.

**Recommendation:** Defer the bootstrap to a separate llm-wiki issue (it's its own concern and clutters this plan). Drop it from Phase 5.4 and note it in Open Questions.

**Status:** **Will revise** — clean separation of concerns.

---

### Finding 4 (MINOR) — 13-hour budget excludes review and revision time

**Defect:** Time budget is 13 hours of *drafting* time. Real T3 work includes adversarial review iteration (typically 1–3 cycles per PR), re-drafting after Gemini review finds issues, etc. Real wall-clock for 5 PRs reviewed and merged is more like 25–40 hours over 3–6 weeks.

**Recommendation:** State the 13 hours as drafting only; flag that PR review + iteration roughly doubles wall-clock; align with the project critical-path budget in PLANNING-ROADMAP.

**Status:** **Will revise** — clarify budget framing.

---

### Finding 5 (CHECKED, NOT A DEFECT) — Step 1.5 done thoroughly

The Step 1.5 verification surfaced three substantive findings (rock-oil-field is the wrong subdir; 1,826 keyword matches across /mnt/ace; commercial textbooks dominate the find list). All three reshape the plan. Step 1.5 is doing the work it was designed to do. ✓

---

### Finding 6 (CHECKED) — Subsea-vs-reservoir scope is explicitly user-gated

The plan flags the subsea-pipeline corpus as out-of-scope by default but invites user confirmation at approval time. That's the right pattern for a scope question that's genuinely ambiguous in the issue body.

---

## Verdict

**MAJOR** — two structural revisions required: (1) license-compliance review checklist + commercial-citation cap, (2) wave-by-wave PR strategy. Two minor cleanups (planning-bootstrap separation, budget framing). After revisions, escalate to Gemini cross-review per T3 policy. Plan can land with single-degraded review (Claude + Gemini, no Codex) per `feedback_permission_gate_blocks_cross_review.md`, with explicit user acceptance.
