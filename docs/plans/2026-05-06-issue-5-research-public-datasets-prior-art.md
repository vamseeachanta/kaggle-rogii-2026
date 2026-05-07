# Plan for #5: Research — public datasets and prior art for wellbore geology

> **Status:** plan-review
> **Tier:** T2
> **Date:** 2026-05-06
> **Issue:** https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5
> **Review artifacts:** `scripts/review/results/2026-05-06-plan-5-claude.md` + `-gemini.md` (T2 cross-review pending; Codex unavailable)

---

## Resource Intelligence Summary

### Existing repo code / docs
- [`docs/competition-overview.md`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/docs/competition-overview.md) — task spec, frames the modeling problem.
- [`docs/task-brief.md`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/docs/task-brief.md) — Slide 9 ("lateral GR has higher resolution than typewell GR") and Slides 12–13 (offset wells) are the strongest in-document hints; literature should validate or refute these.
- No existing `docs/prior-art.md` or research artifacts.

### Companion issue
- [vamseeachanta/llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40) covers the broader reservoir-engineering literature (textbooks, coursework, fundamentals). This issue ([#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5)) covers the *competition-specific* slice: directly-usable public datasets and ML-for-geosteering papers. The two outputs cross-reference.

### Prior decisions
- Kaggle competition rules permit "freely & publicly available external data ... including pre-trained models." Confirmed in `docs/competition-overview.md`. So pre-training on, e.g., Force 2020 is allowed if licenses permit redistribution.
- `feedback_dark_intelligence_excel.md` and the user's no-shortcuts preference: no scraping behind paywalls, no proxying around access controls.

### Direct evidence (verified 2026-05-06)
- `gh repo view vamseeachanta/llm-wiki` returned PUBLIC + main branch + existing `docs/, scripts/, seeds/, tests/, wikis/` structure.
- `/mnt/ace` has a `rock-oil-field/` directory (per filesystem listing 2026-05-06) that the user has identified as a likely source of reservoir-engineering material.

### Gaps identified
- No catalog of competition-relevant public datasets.
- No survey of ML-for-geosteering papers post-2020.
- No license-aware ingest plan for datasets we'd want to use as pre-training corpora.
- No pointer between [#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5) findings and downstream modeling plans ([#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1), [#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7), [#8](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/8)).

---

## Artifact Map

| Artifact | Path |
|---|---|
| This plan | `docs/plans/2026-05-06-issue-5-research-public-datasets-prior-art.md` |
| Output (primary) | `docs/prior-art.md` |
| Output (per-source dossier) | `docs/research/datasets/<slug>.md` (one per dataset that warrants depth) |
| Output (literature) | `docs/research/papers.md` |
| Plans index | `docs/plans/README.md` |
| Review (Claude self) | `scripts/review/results/2026-05-06-plan-5-claude.md` |
| Review (Gemini) | `scripts/review/results/2026-05-06-plan-5-gemini.md` |

---

## Deliverable

A `docs/prior-art.md` document and supporting `docs/research/` directory that catalogs the competition-relevant public datasets and ML-for-geosteering literature, each with a license note, a relevance score, and a concrete ingest decision (use as pre-training / use as validation / skip).

---

## Hypothesis & experimental design

| Field | Statement |
|---|---|
| **Hypothesis** | At least **two** of {Force 2020 Well-Log Lithology, Equinor Volve, Geolink Open North Sea, NLOG} contain GR + facies/formation labels at the well-row level under a license that permits redistribution as a Kaggle Dataset upload. If so, they're usable as a Phase 4 pre-training corpus. |
| **Experiment** | License-and-content audit each candidate dataset. Verify at the row-level: (a) GR present, (b) facies/lithology labels present, (c) license permits redistribution. |
| **Predicted outcome** | Force 2020 and Geolink survive; Volve has GR but unclear license; NLOG is open but heterogeneous. We'll have **at least one** dataset cleared for pre-training. |
| **Decision rule** | If ≥ 1 dataset cleared and looks structurally similar to ROGII (lateral wells with GR, formation tops) → seed Phase 4 sequence model with pre-training on it. If 0 datasets cleared → fall back to **synthetic pre-training** (data augmentation on the 773 train wells: heel/toe-boundary shifts, GR perturbation, fault injection, near-neighbor mixup) — bounded but informative. Last resort: rely on auxiliary losses + multi-task only. Document the gap loudly in `docs/prior-art.md`'s closing section so future iterations can revisit. |

---

## Files to Change

| Action | Path | Reason |
|---|---|---|
| Create | `docs/prior-art.md` | top-level summary doc |
| Create | `docs/research/datasets.md` | dataset catalog with per-row license + relevance |
| Create | `docs/research/papers.md` | ML-for-geosteering paper survey |
| Create | `docs/research/datasets/<slug>.md` | per-dataset deep-dives (variable count) |
| Modify | `docs/plans/README.md` | add this plan to the index |
| Comment | downstream issues ([#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1), [#2](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/2), [#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7), [#8](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/8)) | post pointers when relevant findings affect their plans |

---

## Procedure (T2 — empirical, not test-driven)

For T2 ML-research issues, the "TDD test list" is replaced by an explicit procedure:

### Phase 5.1: Dataset audit (~3 hours)

For each candidate dataset listed in [#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5)'s issue body:

1. **License check**: read the dataset license. Categorize as: `redistributable / single-use / paywalled / unclear`. Skip everything that isn't `redistributable` for pre-training purposes.
2. **Schema check**: download a single sample (or read schema docs). Verify GR, formation tops, X/Y/Z trajectory columns exist.
3. **Scale check**: how many wells? Median rows per well? Compare to ROGII's 773 train wells × ~6,400 rows.
4. **Domain check**: is the geology comparable (e.g., shale plays, North Sea, etc.) to ROGII's apparent domain (US onshore unconventional, inferred from formation names like ANCC, ASTNU, EGFDU, BUDA)?
5. **Decision**: pre-training corpus / validation set / skip.

Record results in `docs/research/datasets.md` as a table.

### Phase 5.2: Paper survey (~3 hours)

0. **ROGII organizers' published work — start here.** Search Google Scholar / Semantic Scholar for Igor Kuvaev, Rafael Aguilar, John Granmayeh (the named contest authors per `docs/competition-overview.md`). Read whitepapers and blog posts at <https://rogii.com>. The organizers' own publications strongly telegraph the modeling baseline they expect; finding their preferred technique up front shapes every downstream plan. Highest information-per-minute step in the survey.
1. **arXiv** search: `physics.geo-ph` + `stat.ML` intersection on terms `["wellbore", "geosteering", "log correlation", "lithology classification", "TVT", "true vertical thickness"]`. Filter to 2022–2026.
2. **OnePetro free portion**: SPE-numbered papers with open access flag; same search terms.
3. **Recent ML-for-geology** preprints — broader sweep of related literature.
4. For each paper that looks relevant, write a 2–4 sentence summary in `docs/research/papers.md`: technique used, dataset, headline result, applicability to ROGII.

### Phase 5.3: Synthesis (~2 hours)

1. Write `docs/prior-art.md`: top-of-funnel summary cross-referencing dataset catalog + paper survey, with a "where this changes our roadmap" section.
2. Comment on downstream issues with concrete pointers ("plan [#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7) should consider technique X from [paper Y]").
3. Update [`docs/roadmap.md`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/docs/roadmap.md) Phase 4 section if a dominant published approach emerges.

### Phase 5.4: Second pass (Week 5, before Phase 4 starts) (~2 hours)

Targeted re-search focused on sequence models for log correlation. Update `docs/research/papers.md` and notify [#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7) plan author of any breaking findings.

**Total time budget: ~10 hours over two passes.**

---

## Acceptance criteria

- [ ] `docs/prior-art.md` exists, summarizes dataset catalog + paper survey, names a top-1 and top-2 dataset for pre-training (or explicitly states "no dataset cleared").
- [ ] `docs/research/datasets.md` lists ≥ 8 candidate datasets (the 7 named in the issue body + at least 1 discovered during the audit) with license / relevance / decision per row.
- [ ] `docs/research/papers.md` lists ≥ 12 papers (≥ 3 of which post-2023) with summary + applicability per paper.
- [ ] At least one downstream issue ([#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1), [#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7), or [#8](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/8)) has a comment pointing to a specific finding from this research.
- [ ] All cited datasets have license category recorded (no "unclear" without a follow-up action).
- [ ] No Kaggle competition rules violated (no use of paywalled material; pre-training only on verifiably-redistributable data).
- [ ] Cross-review: Gemini review present at `scripts/review/results/2026-05-06-plan-5-gemini.md`. Codex unavailable; user accepts single-degraded review at approval time.

---

## Adversarial review summary

| Provider | Verdict | Key findings |
|---|---|---|
| Claude (self) | MINOR | (1) "5 papers post-2023" was aspirational — lowered to ≥3. (2) ROGII organizers' own publications elevated to Phase 5.2 step 0 (highest information-per-minute). (3) "0 datasets cleared" fallback under-specified — added synthetic-pretraining tertiary plan. |
| Gemini | (pending T2 cross-review — Codex unavailable) | — |
| Codex | not run (CLI broken) | — |

**Overall result so far:** PASS-CONDITIONAL (Claude self-review revisions applied; awaits Gemini cross-review for T2 closure).

Revisions made based on review:
- Acceptance criterion: ≥12 total papers, ≥3 post-2023 (was ≥5).
- Phase 5.2 step 0: ROGII-organizer publications search promoted to first.
- Decision rule: synthetic-pretraining tertiary fallback added between "≥1 cleared" and "0 cleared and skip-entirely."

---

## Risks and open questions

- **Risk:** literature rabbit hole. Mitigation: 10-hour budget across two passes; if a single dataset audit takes > 1 hour, defer it (file as new issue) rather than blow the budget.
- **Risk:** OnePetro paywall. The richest source of geosteering papers is paywalled. Mitigation: rely on the open subset; supplement with arXiv preprints; cite paywalled work as "secondary" without using its specific results.
- **Risk:** "redistributable" license interpretation is dataset-specific. Some datasets are CC-BY-NC (research-only); for a Kaggle competition this is gray. Mitigation: be conservative — only use datasets clearly marked CC-BY, CC0, or public-domain. Note CC-BY-NC datasets in the catalog with "research-only; do not redistribute as Kaggle Dataset" annotation.
- **Risk:** the most relevant published approach might be the contest organizers' own ROGII paper / patent. Mitigation: explicitly search for ROGII publications by Kuvaev / Aguilar; note any restrictions on citing/replicating proprietary methods.
- **Open:** at what point do we *download* the pre-training dataset, vs just *cite* it? Answer: download only if we commit to using it (Phase 4 plan-approval gate). This issue is research-only.
- **Open:** should the cross-link to [llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40) be tighter — e.g., a shared `docs/research/datasets.md` schema across both repos? Defer; v1 of [#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5) optimizes for competition-relevance, [llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40) optimizes for educational substrate. Different audiences.
- **Open: Codex review unavailable.** User decides whether to wait for Codex 0.123.0 downgrade or proceed with Claude+Gemini-only.

---

## Tier justification

**T2.** Cross-cutting research output that informs ≥3 downstream modeling issues; non-trivial license analysis; decision on pre-training corpus is partly load-bearing for Phase 4. Empirical-procedure-driven (no TDD), but the procedure is structured and falsifiable. Cross-provider review (Claude + Gemini) appropriate. Estimated effort: 10 hours over two passes.
