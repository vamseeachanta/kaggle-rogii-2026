# Plan for llm-wiki#40: Reservoir-engineering literature ingest into llm-wiki

> **Status:** plan-review
> **Tier:** T3
> **Date:** 2026-05-06
> **Issue:** https://github.com/vamseeachanta/llm-wiki/issues/40
> **Cross-repo:** plan lives in `kaggle-rogii-2026/docs/plans/` (single source of truth during competition planning); implementation artifacts land in `vamseeachanta/llm-wiki` via PR.
> **Review artifacts:** `scripts/review/results/2026-05-06-plan-llm-wiki-40-claude.md` + `-gemini.md` (T3 cross-review pending; Codex unavailable)

---

## Step 1.5 — Reproduction / starting-state verification

Per workspace-hub `CLAUDE.md` 2026-05-06 update, every plan must verify the alleged starting state before drafting. Findings (commands run 2026-05-06):

### llm-wiki structure (verified)
```
wikis/
├── acma-projects/
├── asset-management/
├── cross-links.md
├── engineering/
├── engineering-standards/
├── lng-projects/
├── marine-engineering/
├── maritime-law/
└── naval-architecture/
```
**No existing reservoir-engineering content.** A new `wikis/reservoir-engineering/` slot is unobstructed and follows the existing one-topic-per-dir convention. `seeds/` uses YAML schemas (e.g., `mooring-failures-lng-terminals.yaml`); a `seeds/reservoir-engineering-resources.yaml` could mirror `seeds/naval-architecture-resources.yaml`.

### `/mnt/ace` corpus (verified, supersedes issue body assumptions)

| Claim in original issue body | Reality (2026-05-06) |
|---|---|
| "`/mnt/ace`, 30,499 PDFs" | True for the whole tree, but only ~6% are reservoir-relevant |
| "`/mnt/ace/rock-oil-field/` top candidate" | Only 383 PDFs; skews subsea-pipeline, **not reservoir engineering** |
| Implied: reservoir material is in one place | False; reservoir material is **scattered**: `docs/literature/dde/`, `docs/books/`, `acma-codes/`, `O&G-Standards/`, `client_projects/` |
| Realistic ingestable count: 50–200 | Probably right after license filter, but ~**1,826** raw keyword matches across `/mnt/ace` (much larger raw pool than `rock-oil-field/` alone) |

Sample finds (commercial textbooks — **NOT redistributable**, cite-only):
- `/mnt/ace/docs/literature/dde/petroleum-engineering/Applied Petroleum Reservoir Engineering.pdf`
- `/mnt/ace/docs/literature/dde/Engineering/Fundamentals of reservoir engineering.pdf`
- `/mnt/ace/docs/literature/dde/petroleum-engineering/handbook of petroleum and natural gas.pdf`
- `/mnt/ace/docs/books/Petroleum_Production_Engineering,_Elsevier_(2007).pdf`
- `/mnt/ace/client_projects/.../014 ProductionEngineering/Petroleum_Production_Engineering...`

Standards (cite via `code_id` schema per `workspace-hub/.claude/rules/calc-citation-contract.md`):
- `/mnt/ace/acma-codes/API/API RP 14 F 2008 Electrical Systems...`
- `/mnt/ace/acma-codes/ISO Standards/2005 19901-1 Petroleum and natural gas industries...`
- `/mnt/ace/O&G-Standards/BSI/BS_10432_(2004)_Petroleum_&_natural_gas_Industries...`

### Companion issue
- [vamseeachanta/kaggle-rogii-2026#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5) — competition-specific datasets/papers; complementary in scope.

---

## Resource Intelligence Summary

### Existing repo code (llm-wiki)
- `wikis/`: 9 topic dirs, none reservoir-engineering; `seeds/` has YAML schema convention; `docs/`, `scripts/`, `tests/` exist.
- No prior plan files in llm-wiki (planning infrastructure not bootstrapped there).

### Prior plans / decisions (workspace-hub)
- `workspace-hub/.claude/rules/calc-citation-contract.md` — every standards-derived constant needs a Citation matching `code_id` schema; wiki page at `wikis/standards/<code-id>.md` is the citation target.
- `feedback_skill_before_code.md`, `feedback_no_jargon.md`, `feedback_research_skill_sources.md` (memory) — apply to literature work.
- [`vamseeachanta/workspace-hub#2482`](https://github.com/vamseeachanta/workspace-hub/issues/2482) — vendor-derivative deny-list: nothing under `knowledge/wikis/*/wiki/sources/` should be cited or ingested. Cite the canonical standards page instead.
- [`vamseeachanta/kaggle-rogii-2026#5`](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5) plan — frames research scope; this plan is the broader literature companion.

### Direct evidence (verified by Step 1.5)
See section above.

### Gaps identified
- No reservoir-engineering wiki structure in llm-wiki.
- No catalog of which `/mnt/ace` PDFs are license-clean for ingestion vs cite-only.
- No prior decision on what counts as "ingest-ready" vs "cite-only" for commercial textbooks.
- No bridge between competition-relevant findings ([#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5)) and the broader educational substrate (this plan).

---

## Artifact Map

| Artifact | Path |
|---|---|
| This plan | `kaggle-rogii-2026/docs/plans/2026-05-06-issue-llm-wiki-40-reservoir-engineering-literature.md` |
| Source inventory | `kaggle-rogii-2026/docs/research/reservoir-engineering-corpus.md` (one row per `/mnt/ace` candidate; license + decision) |
| Online sources catalog | `kaggle-rogii-2026/docs/research/reservoir-engineering-online.md` |
| Wiki concept pages (output, ≥5) | `llm-wiki/wikis/reservoir-engineering/concepts/<topic>.md` |
| Wiki methodology pages (output, ≥2) | `llm-wiki/wikis/reservoir-engineering/methodology/<topic>.md` |
| Wiki standards index | `llm-wiki/wikis/reservoir-engineering/standards/<code-id>.md` (per #2471 frontmatter) |
| Wiki seeds (structured) | `llm-wiki/seeds/reservoir-engineering-resources.yaml` (mirrors `naval-architecture-resources.yaml`) |
| Wiki cross-links | `llm-wiki/wikis/cross-links.md` (modified) |
| llm-wiki PR | one PR per delivery wave; targets main |
| Plans index | `kaggle-rogii-2026/docs/plans/README.md` |
| Review (Claude self) | `kaggle-rogii-2026/scripts/review/results/2026-05-06-plan-llm-wiki-40-claude.md` |
| Review (Gemini) | `kaggle-rogii-2026/scripts/review/results/2026-05-06-plan-llm-wiki-40-gemini.md` |

---

## Deliverable

A `wikis/reservoir-engineering/` topic family in `vamseeachanta/llm-wiki` (≥5 concept pages + ≥2 methodology pages + a standards index + a seeds YAML), all license-clean, with a corpus inventory + online-sources catalog as research artifacts in `kaggle-rogii-2026/docs/research/`.

---

## Hypothesis & experimental design

| Field | Statement |
|---|---|
| **Hypothesis** | Online open-access sources alone (university OCW + OAPEN + Springer Open + ROGII whitepapers + USGS) yield enough material to draft 5+ reservoir-engineering concept pages within 2 working sessions, with `/mnt/ace` contributing primarily as cite-only references. |
| **Experiment** | Run Phase 5.1 (corpus inventory) and Phase 5.2 (online survey) in sequence. Count: how many distinct license-clean concept-anchors emerge? Draft 5 pages from the strongest. |
| **Predicted outcome** | Online sources contribute ~80% of the cite-and-paraphrase material; `/mnt/ace` commercial textbooks contribute mostly *citations*, not extracts. Five concept pages emerge in ~2 sessions; methodology pages take a third session. |
| **Decision rule** | If 5 pages drafted in 2 sessions → continue with full ingest plan (methodology, standards, seeds). If < 5 → re-scope: drop methodology pages from this issue, file methodology as separate issue, focus on concept pages only. |

---

## Procedure

### Phase 5.1 — Local corpus inventory (~3 hours)

For each match in `find /mnt/ace -iname "*.pdf" | grep -iE "reservoir|petroleum|...":
1. Read filename + parent dir → guess content category (textbook, standard, paper, course material, vendor brochure).
2. License triage:
   - **Standard** (API / ISO / BSI / DNV): cite via `code_id` schema, never extract; add row to standards index. NO ingestion.
   - **Commercial textbook** (named publisher, copyright notice): cite-only; never copy more than 15 words quoted; never paraphrase a 30+ word displacive summary. NO ingestion.
   - **Open-access paper / OAPEN / public-domain (>70 yr)**: ingest-eligible; record in `docs/research/reservoir-engineering-corpus.md` with row `(path, title, license, category, decision=ingest|cite-only)`.
   - **Unknown** (no clear copyright info): default to cite-only.
3. Write the catalog. Skip directories under `knowledge/wikis/*/wiki/sources/` per [#2482](https://github.com/vamseeachanta/workspace-hub/issues/2482).

### Phase 5.2 — Online survey (~3 hours)

Open-access first:
1. **Stanford Doerr School OCW** + **Texas A&M PETE OCW** + **U Texas Austin Petroleum Engineering** open content. Capture course-syllabi PDFs and open-licensed lecture notes.
2. **Heriot-Watt PE** + **Imperial College Earth Science** open materials.
3. **OAPEN** + **Springer Open** + **MIT OpenCourseWare** earth-and-planetary courses.
4. **arXiv** `physics.geo-ph` + reservoir-engineering tags.
5. **USGS Open-File Reports** in petroleum geology.
6. **ROGII whitepapers** at <https://rogii.com> (cross-ref with [#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5) Phase 5.2 step 0).

Skip: paywalled portions of OnePetro, AAPG Datapages, SPE.

### Phase 5.3 — Draft wiki pages (~5 hours)

≥5 concept pages on reservoir-engineering fundamentals. Suggested topics (final selection during drafting based on corpus):
1. **Porosity** — definition, measurement methods, typical ranges, role in reserve estimation.
2. **Permeability** — Darcy's law, units, isotropy/anisotropy, relation to porosity.
3. **Saturation** — water/oil/gas saturation; capillary pressure curves.
4. **Gamma-ray log interpretation** — natural radioactivity, formation indicators, shale-baseline approach.
5. **Formation tops and stratigraphy** — picks, correlation, dipping layers.

≥2 methodology pages:
1. **Geosteering workflow** — what geologists actually do during drilling.
2. **Log correlation** — how typewell GR is matched to lateral GR.

Each page:
- Original prose (no extracts > 15 words quoted, no displacive summaries > 30 words).
- ≥3 cited sources from the catalogs (mix of standards + open-access + cite-only commercial).
- Cross-link in `wikis/cross-links.md`.
- Apply `calc-citation-contract.md` for any standards-derived numerical claim.

### Phase 5.4 — Seeds YAML + standards index + waved PRs (~2 hours of drafting; PR review-and-merge time is separate)

1. Draft `seeds/reservoir-engineering-resources.yaml` mirroring `seeds/naval-architecture-resources.yaml`.
2. Draft `wikis/reservoir-engineering/standards/<code-id>.md` stubs for each standard cited (frontmatter per [#2471](https://github.com/vamseeachanta/workspace-hub/issues/2471)).
3. Submit PRs in **waves** (NOT one big PR — license-review fatigue is a real risk):
   - **PR 1 — Bootstrap.** `wikis/reservoir-engineering/README.md` + empty subdirs + `seeds/reservoir-engineering-resources.yaml` skeleton. Small, fast to review.
   - **PR 2 — Concept pages 1–2** (porosity, permeability) + citations. Includes the structured license review checklist (see below).
   - **PR 3 — Concept pages 3–5** (saturation, GR log interpretation, formation tops + stratigraphy).
   - **PR 4 — Methodology pages** (geosteering workflow, log correlation).
   - **PR 5 — Standards index + cross-links update.**

Each PR independently reviewable. If a license violation is caught in PR 2, every subsequent PR benefits from the correction.

**Drafting time budget: ~13 hours over 3–4 sessions.** PR review-and-merge cycle adds another ~10–20 hours wall-clock over 3–6 weeks. Real total wall-clock: 25–40 hours over multi-week calendar — aligned with the PLANNING-ROADMAP "background thread from week 1" framing.

---

## Acceptance criteria

- [ ] `kaggle-rogii-2026/docs/research/reservoir-engineering-corpus.md` lists ≥ 50 candidates from `/mnt/ace` with license category + decision.
- [ ] `kaggle-rogii-2026/docs/research/reservoir-engineering-online.md` lists ≥ 15 open-access sources with URL + license + relevance.
- [ ] llm-wiki PR opened with:
  - [ ] ≥ 5 concept pages under `wikis/reservoir-engineering/concepts/`
  - [ ] ≥ 2 methodology pages under `wikis/reservoir-engineering/methodology/`
  - [ ] Standards index stubs for ≥ 3 cited standards
  - [ ] `seeds/reservoir-engineering-resources.yaml`
  - [ ] `wikis/cross-links.md` updated
- [ ] **License compliance** — verifiable via the structured checklist below, NOT by self-attestation:
  - [ ] At most **1 cite-only commercial citation per concept page** (hard cap; commercial textbooks should anchor wiki claims, not dominate them).
  - [ ] PR reviewer fills out a per-page citation table: `(cited source | wiki page section | section/page in source | original wording paraphrased? Y/N)`. Reviewer compares wordings.
  - [ ] Automated check: a script greps each wiki page for any 30+ consecutive-word chunk that also appears in cited PDF text-extracts (where text-extraction is available — open-access PDFs only; commercial PDFs by manual inspection of the relevant section in the PR description).
  - [ ] Zero copied text > 15 words quoted (manual + automated grep on extractable PDFs).
  - [ ] Zero ingestion of cite-only material (no `<extract>` blocks; no >30-word paraphrase blocks).
  - [ ] Zero references to `wikis/*/wiki/sources/` deny-list paths.
- [ ] Citation contract: every standards-derived numerical claim cites a `code_id`.
- [ ] Cross-link from this plan to [vamseeachanta/kaggle-rogii-2026#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5) — modeling-relevant findings flagged as comments on [#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5) when they affect Phase 1 v2 or Phase 4 design.
- [ ] llm-wiki PR review: Codex + Gemini cross-review available at the PR (may run via llm-wiki repo's own review tooling, separate from this plan's review). If unavailable, single-author PR review with explicit acceptance.

---

## Adversarial review summary

| Provider | Verdict | Key findings |
|---|---|---|
| Claude (self) | MAJOR | (1) License-compliance acceptance criterion was unverifiable mechanically — replaced with structured per-page citation table + ≤1 commercial citation cap + automated 30-word grep. (2) PR strategy was a single big-PR — replaced with 5-wave strategy so license review fatigue doesn't accumulate. (3) Planning-bootstrap mixed into Phase 5.4 — extracted to Open Questions as a separate concern. (4) 13-hour budget covered drafting only — clarified that PR review/merge cycle ~doubles wall-clock. |
| Gemini | (pending T3 cross-review — Codex unavailable) | — |
| Codex | not run (CLI broken per `feedback_codex_cli_0_124_upstream_regression.md`) | — |

**Overall result so far:** PASS-CONDITIONAL with **single-degraded review** caveat (T3 normally Claude + Codex + Gemini; Codex blocked). User must accept the degradation at approval per `feedback_permission_gate_blocks_cross_review.md`.

Revisions made based on review:
- License-compliance: structured per-page citation table required in PR description; ≤1 commercial citation cap per concept page; automated 30-word grep on text-extractable PDFs.
- PR strategy: 5 waves (Bootstrap → 2 concept pages → 3 concept pages → 2 methodology pages → standards index).
- Planning-bootstrap moved to Open Questions (separate concern; defer until ≥3 active llm-wiki issues).
- Time budget reframed: 13 hours drafting only; total wall-clock 25–40 hours over multi-week calendar with review-and-iterate.

---

## Risks and open questions

- **Risk: license-error contamination.** Commercial textbooks in `/mnt/ace` are tempting (the user has them, the content is excellent). Strict license discipline required. Mitigation: explicit cite-only flag in the corpus inventory; reviewer specifically checks page drafts for displacive paraphrasing.
- **Risk: scope creep.** Reservoir engineering is a vast field; an ambitious plan tries to cover it all and ships nothing. Mitigation: hard cap at 5 concept + 2 methodology pages for v1 (this issue). Follow-up issues file additional pages as separate, scoped work.
- **Risk: corpus mismatch with issue body.** Step 1.5 already revealed this. Plan now reflects reality. **User confirmation required** at approval time: are subsea-pipeline materials (the bulk of `/mnt/ace/rock-oil-field/`) in scope, or strictly out-of-scope for this reservoir-engineering issue? Default in the plan: **out of scope** (they go in a separate `wikis/subsea-engineering/` someday).
- **Risk: the 30k figure was surfaced to the user as a vague "30,499 PDFs total in /mnt/ace"** in [#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5)'s plan. Mitigation: post a corrective comment on [llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40) summarizing the Step 1.5 findings before user approval, so the approval is informed.
- **Risk: parallel work in `/mnt/ace` ingestion.** [vamseeachanta/workspace-hub#2651](https://github.com/vamseeachanta/workspace-hub/issues/2651) (PPTX→PDF on ace-linux-2) touches a `/mnt/ace` file; not a conflict but worth noting.
- **Open: do we want a `wikis/subsea-engineering/`?** The `/mnt/ace/rock-oil-field/` corpus and `/mnt/ace/doris/training/Subsea Production Systems/` together are a strong subsea-engineering substrate. File as a future issue; out of scope here.
- **Open: what's the right Phase 4 / sequence-model link?** This issue informs but doesn't prescribe Phase 4 design choices. Concrete pointer: when concept pages on "GR log interpretation" and "log correlation" land, comment on [#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7) (Phase 4 plan, when it gets drafted) with the relevant pages.
- **Open: planning infrastructure in llm-wiki.** Currently this plan lives in `kaggle-rogii-2026` for convenience. If llm-wiki grows beyond this issue, llm-wiki should bootstrap its own `docs/plans/`. Defer until ≥3 active llm-wiki issues exist.
- **Open: T3 cross-review.** Codex unavailable. User decides whether to wait for Codex 0.123.0 downgrade or proceed Claude+Gemini-only.

---

## Tier justification

**T3.** Cross-repo deliverable; license-compliance constraints are load-bearing; multiple architectural decisions (wiki layout, citation contract integration, seeds schema) inherited by future llm-wiki contributors; strong dependencies on workspace-hub governance docs (#2471, #2482, calc-citation-contract); multi-week calendar with multiple delivery waves. T3 review (Claude + Codex + Gemini) appropriate, with Codex degradation acknowledged. Estimated effort: 13 hours over 3–4 sessions.
