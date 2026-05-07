# Adversarial review — Plan worldenergydata#392 (Public well-log datasets ingest)

**Reviewer:** Claude (self-review)
**Stance:** Adversarial. Assume defects until proven otherwise.
**Plan:** `kaggle-rogii-2026/docs/plans/2026-05-06-issue-worldenergydata-392-well-logs-datasets.md`
**Date:** 2026-05-06
**Verdict:** **MAJOR**

---

## Findings

### Finding 1 (MAJOR) — BSEE coordination with [worldenergydata#365](https://github.com/vamseeachanta/worldenergydata/issues/365) is left open

**Quote:** Risks section: "Cross-issue duplication with [worldenergydata#365] if BSEE has well-log subset. Mitigation: read [#365](https://github.com/vamseeachanta/worldenergydata/issues/365) plan during Phase 6.1; if BSEE well-logs covered there, exclude from this issue."

**Defect:** "Read [#365](https://github.com/vamseeachanta/worldenergydata/issues/365) plan and decide later" is not a coordination strategy — it's a delay. Two issues that may overlap should *now* commit to a clear scope split, before either ships, otherwise we get duplicate modules and re-work.

**Recommendation:** Lock the scope split here:
- **This issue ([#392](https://github.com/vamseeachanta/worldenergydata/issues/392)) explicitly EXCLUDES BSEE well-log data.** Force 2020, Volve, Geolink, NLOG, OSDU subsets only.
- **[#365](https://github.com/vamseeachanta/worldenergydata/issues/365) owns the BSEE well-log subset** (or, if [#365](https://github.com/vamseeachanta/worldenergydata/issues/365) is broader BSEE work, a follow-up issue under #365's umbrella).
- Cross-link both issues with the explicit non-overlap clause so future contributors don't re-merge them.

**Status:** **Will revise** — decision locked in Risks (no longer Open) and added to "Out of scope" framing.

---

### Finding 2 (MINOR) — Volve "ship as cite-only if license unclear" pattern is inconsistent with the package's purpose

**Quote:** "if redistribution is unclear, ship Volve as cite-only (records reference the dataset by URL but don't include data)."

**Defect:** A `worldenergydata.well_logs.data_collection.volve_dataset` module that returns no data — only URLs — is hard to justify. Consumers expect data; cite-only-without-data is a cite, which belongs in `docs/research/`, not in the data-collection layer. If the license is unclear, the right move is to NOT ship a Volve module at all, and instead document the dataset in the audit doc + open a follow-up issue for license clarification.

**Recommendation:** Remove "ship as cite-only with URL only" from the mitigation. Replace with: "if license unclear or unsure, skip the module entirely; document in `docs/research/well-logs-datasets.md` with `license_category=unclear, decision=skip`; file a follow-up issue for license clarification."

**Status:** **Will revise.**

---

### Finding 3 (MINOR) — Plan home-repo decision should be locked, not Open

**Quote:** "Open: plan home repo — drafted in kaggle-rogii-2026 for this turn's expediency; PR's into worldenergydata after approval."

**Defect:** The implementer needs to know where the canonical plan lives before starting work. "Open" here delays the decision unnecessarily — the answer is straightforward.

**Recommendation:** Lock the migration path: "After user approval of this plan, draft a PR to `vamseeachanta/worldenergydata` adding `docs/plans/2026-05-06-issue-392-well-logs-public-datasets.md` (mirroring this file's content) and registering it in `docs/plans/README.md`. The kaggle-rogii-2026 copy then links to the worldenergydata copy as primary; this is a temporary planning fixture only."

**Status:** **Will revise** — move from Open Questions to a concrete "Plan migration" subsection under Procedure.

---

### Finding 4 (MINOR) — Tests don't include a "data does not contain PII" check

**Defect:** Public well-log datasets sometimes contain operator names, well-license-numbers, lat/lon precise enough to identify a specific lease — these are public, but they are *also* metadata that downstream consumers might inadvertently use as features and leak something not intended (e.g., predicting "is this an Equinor well" instead of "is this a sandstone"). The plan's test list doesn't include a smoke check for this.

**Recommendation:** Add a test: `test_records_do_not_include_operator_or_lease_metadata` — verifies the loaded WellLogRecord schema does not surface operator-identifiable fields. (Note: this is about *what fields the schema exposes*, not about removing data from the source files themselves; the source data is public and stays as it is.)

**Status:** Acceptable — the schema as drafted only exposes geophysical data and provenance fields, not operator/lease metadata. The test would be redundant given the schema is constrained. Not a revision; flagged for awareness.

---

### Finding 5 (CHECKED, NOT A DEFECT) — Step 1.5 thoroughness

The verification step verified worldenergydata's package convention, plan template style, deny-list, and companion issues. Found a meaningful new piece of information: no existing `well_logs/` package, plus the package-vs-nested-under-drilling question. Doing the work it was designed to do.

---

### Finding 6 (CHECKED) — Wave-PR strategy aligned with [llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40) sibling plan

Same wave structure (bootstrap → first dataset → second → etc.). Consistency across the gating-phase trio's plans is helpful for reviewers.

---

## Verdict

**MAJOR** — three required revisions: (1) lock BSEE scope-split with [#365](https://github.com/vamseeachanta/worldenergydata/issues/365) instead of deferring, (2) drop "ship as cite-only without data" pattern in favour of "skip + follow-up," (3) lock plan home-repo migration path in a concrete Procedure subsection. Plus one acceptable-as-flagged note about schema-constrained PII safety. After revisions, escalate to Gemini cross-review per T3 policy. Plan can land with single-degraded review (Claude + Gemini, no Codex) per `feedback_permission_gate_blocks_cross_review.md`, with explicit user acceptance.
