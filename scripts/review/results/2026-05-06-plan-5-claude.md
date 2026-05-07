# Adversarial review — Plan #5 (Public datasets and prior art research)

**Reviewer:** Claude (self-review)
**Stance:** Adversarial. Assume defects until proven otherwise.
**Plan:** `docs/plans/2026-05-06-issue-5-research-public-datasets-prior-art.md`
**Date:** 2026-05-06
**Verdict:** **MINOR**

---

## Findings

### Finding 1 (MINOR) — "5 papers post-2023" may be aspirational

**Quote:** "lists ≥ 12 papers (5 of which post-2023)"

**Defect:** ML-for-geosteering is a niche; the post-2023 venn intersection of "wellbore geology + ML + open access" might have fewer than 5 papers. Setting the bar that high risks gaming (counting tangential papers to hit the count) or missing the deadline.

**Recommendation:** Lower to "≥ 12 papers, ≥ 3 post-2023." If post-2023 stays bigger than 3, that's a free win, not a stretch.

**Status:** **Will revise.**

---

### Finding 2 (MINOR) — No explicit step for ROGII's own publications

**Defect:** The plan mentions Kuvaev/Aguilar in passing under Phase 5.2 step 3 ("recent ROGII papers / blog posts by the contest authors") but doesn't elevate it to a named procedure step. ROGII publications likely telegraph the contest organizers' modeling baseline — this is high-information.

**Recommendation:** Promote "Phase 5.2.0 — ROGII organizers' published work" as the *first* step of Phase 5.2, before the broader arXiv search. Concrete sources: ROGII whitepapers at <https://rogii.com>, Kuvaev's Google Scholar profile, Aguilar's LinkedIn presentations.

**Status:** **Will revise.**

---

### Finding 3 (MINOR) — License categorization for top candidates is verifiable in advance

**Defect:** The plan says "license check" as a generic step but doesn't pre-populate what we already know about top-candidate licenses (Force 2020 is CC-BY-4.0; Volve is open under Equinor terms; Geolink is unclear; NLOG is open under TNO). Pre-populating saves an hour and lets the audit go straight to schema-and-scale.

**Recommendation:** Add to the issue body's dataset listing: known license per top candidate. The audit becomes "verify the license matches the published statement," not "discover the license from scratch."

**Status:** Acceptable as-is — can be folded into the audit's first hour. Not worth a plan revision since the Phase 5.1 procedure already accommodates it.

---

### Finding 4 (MINOR) — Tertiary fallback (no datasets cleared) under-specified

**Defect:** "If 0 datasets cleared → skip pre-training; rely on auxiliary losses + multi-task only" is a one-line dismissal. If we end up here, Phase 4 is meaningfully weaker. The plan should at least name a third option: synthetic pre-training corpus generated from the train set (data augmentation: shifting heel/toe boundaries, GR perturbation, fault injection).

**Recommendation:** Add to decision-rule: "If 0 datasets cleared → consider synthetic pre-training (cheap, informative-but-bounded); document as a fallback plan in `docs/prior-art.md`'s closing section."

**Status:** **Will revise.**

---

### Finding 5 (CHECKED, NOT A DEFECT) — Time budget calibration

10 hours over two passes is tight but defensible — research-and-citation work expands to fill available time, and a hard ceiling is more useful than a soft target.

---

### Finding 6 (CHECKED) — Cross-link to llm-wiki#40

The plan correctly delineates competition-specific (this issue) vs educational (llm-wiki#40) scope. Good.

---

## Verdict

**MINOR** — three required revisions: (1) lower post-2023 paper bar to ≥3, (2) elevate ROGII-organizers'-work as Phase 5.2 step 0, (3) add synthetic-pretraining tertiary fallback in decision rule. After revisions, escalate to Gemini cross-review per T2 policy.
