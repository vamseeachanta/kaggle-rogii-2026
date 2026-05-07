# Plan for worldenergydata#392: Public well-log datasets — Kaggle ROGII companion ingest

> **Status:** plan-review
> **Tier:** T3
> **Date:** 2026-05-06
> **Issue:** https://github.com/vamseeachanta/worldenergydata/issues/392
> **Cross-repo:** plan drafted in `kaggle-rogii-2026/docs/plans/` (single source of truth during competition planning); will be PR'd into `worldenergydata/docs/plans/2026-05-06-issue-392-well-logs-public-datasets.md` and registered in worldenergydata's plans-index README after user approval.
> **Review artifacts:** `scripts/review/results/2026-05-06-plan-worldenergydata-392-claude.md` + `-gemini.md` (T3 cross-review pending; Codex unavailable per `feedback_codex_cli_0_124_upstream_regression.md`)

---

## Step 1.5 — Reproduction / starting-state verification (verified 2026-05-06)

### worldenergydata repo maturity
- 40+ existing plans in `docs/plans/` (verified by index README listing); active issue tracker at #392.
- `src/worldenergydata/` has 20+ top-level packages including `bsee/`, `cost/`, `drilling/`, `drilling_pressure_management/`, `eia/`, `eia_us/`, `economics/`, `analysis/`, `decommissioning/`. **No existing `well_logs/` package.**
- Existing data-collection convention pattern (verified from `cost/data_collection/public_dataset.py`):
  - `<domain>/data_collection/<source>_dataset.py` — one module per ingested public source
  - `<domain>/data_collection/calibration_schema.py` (or `<domain>/schema.py`) — typed schema for the domain's primary record
  - `<domain>/data_collection/public_dataset.py` — unified loader
  - Tests: `tests/unit/<domain>/test_<surface>.py`
- Plan template style follows workspace-hub's `_template-issue-plan.md` (verified by reading [`#334 plan`](https://github.com/vamseeachanta/worldenergydata/blob/main/docs/plans/2026-04-21-issue-334-annual-operator-disclosures-dataset.md)).
- `.legal-deny-list.yaml` extends workspace-root deny-list with worldenergydata-specific patterns (ENIGMA codename, Databricks references). Public dataset ingest must avoid any pattern matching these.

### Companion issues
- [`worldenergydata#365`](https://github.com/vamseeachanta/worldenergydata/issues/365) — BSEE binary tier decompression + ingest pipeline (unlocks 2.7 GB). Overlaps if BSEE has well-log subset; coordinate to avoid duplicate work.
- [`worldenergydata#361`](https://github.com/vamseeachanta/worldenergydata/issues/361) — adopt calc-citation-contract for worldenergydata calc outputs. Apply to any standards-derived constants this issue introduces.
- [`vamseeachanta/kaggle-rogii-2026#5`](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5) — Kaggle-side research catalog. Companion in the Wave-1 gating phase.
- [`vamseeachanta/llm-wiki#40`](https://github.com/vamseeachanta/llm-wiki/issues/40) — reservoir-engineering literature substrate. Companion in Wave-1.

### Key decision deferred to plan body
The original issue body proposed `src/worldenergydata/well_logs/` as a sibling to `drilling/`. Step 1.5 confirms this is consistent with worldenergydata's package-per-domain convention. **Open question:** could it instead live as `drilling/well_logs/`? Drilling is operational (rig data, pressure management); well-logs are post-acquisition geophysical signatures. They're related but distinct. **Plan default: sibling package**; user override at approval.

### Step 1.5 scope notes
- Did NOT verify dataset licenses live; that's Phase 6.1 of this plan's procedure (auditing each dataset).
- Did NOT clone the repo locally; all verification via GitHub API. If we proceed to implementation, clone will be needed.

---

## Resource Intelligence Summary

### Existing repo code (verified Step 1.5)
- `src/worldenergydata/cost/data_collection/public_dataset.py` — reference pattern for curated public-data modules (license-cited per record).
- `src/worldenergydata/cost/data_collection/calibration_schema.py` — reference pattern for typed schema with provenance.
- `src/worldenergydata/bsee/` — existing BSEE ingest; possibly contains well-log subset relevant to this issue (needs confirmation).
- `src/worldenergydata/drilling/` and `src/worldenergydata/drilling_pressure_management/` — operational drilling data; distinct from well-log signature data this issue handles.
- No existing `well_logs/` package, no existing well-log schema.

### Standards
- Calc-citation-contract from [`worldenergydata#361`](https://github.com/vamseeachanta/worldenergydata/issues/361) applies to any standards-derived numerical claim (e.g., GR API unit calibration constants from API RP 33).
- API RP 33 (well-log standards) — likely under cite-only license.

### LLM-wiki pages consulted
- None yet — `wikis/reservoir-engineering/` doesn't exist (per [llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40) Step 1.5 verification). The wiki pages drafted under [llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40) will inform downstream usage but aren't required to start this issue.

### Documents consulted
- [`vamseeachanta/kaggle-rogii-2026/docs/competition-overview.md`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/docs/competition-overview.md) — defines the ROGII task and required column schema (MD, X, Y, Z, GR, formation tops, TVT). Sets the bar for what "Kaggle-relevant" well-log data looks like.
- `worldenergydata/docs/plans/2026-04-21-issue-334-annual-operator-disclosures-dataset.md` — reference plan style and depth.
- ROGII competition rules — pre-trained models / external data permitted with cite + license-clean basis.

### Gaps identified
- No `well_logs/` package or schema exists.
- No license audit for {Force 2020, Volve, Geolink, NLOG, BSEE-well-log-subset, OSDU-subset} has been done in this repo.
- No bridge from worldenergydata's data-collection layer into the Kaggle competition's notebook execution environment (Kaggle Notebooks need data uploaded as Kaggle Datasets — this plan does NOT cover that step; tracked as a separate cross-repo concern).
- No verification of how Volve well logs are structured (Volve is a multi-TB field dataset; we want only the well-log subset, ~few GB).

### Direct evidence
**Repo state** (verified 2026-05-06T23:xxZ via `gh api`):
- EXISTS: `src/worldenergydata/cost/data_collection/public_dataset.py`
- EXISTS: `src/worldenergydata/bsee/`
- EXISTS: `src/worldenergydata/drilling/`
- MISSING (new — this plan creates): `src/worldenergydata/well_logs/`

**Issue states** (verified 2026-05-06):
- `#392` — OPEN — `feat(data): public well-log datasets for wellbore geology — Kaggle ROGII companion ingest`
- `#365` — OPEN — `feat(data): BSEE binary tier decompression + ingest pipeline (unlocks 2.7 GB)`
- `#361` — OPEN — `feat(provenance): adopt calc-citation-contract for worldenergydata calc outputs`
- `kaggle-rogii-2026#5` — OPEN, plan-review
- `llm-wiki#40` — OPEN, plan-review

---

## Artifact Map

| Artifact | Path |
|---|---|
| This plan (drafting) | `kaggle-rogii-2026/docs/plans/2026-05-06-issue-worldenergydata-392-well-logs-datasets.md` |
| This plan (final home, after approval) | `worldenergydata/docs/plans/2026-05-06-issue-392-well-logs-public-datasets.md` |
| Schema | `worldenergydata/src/worldenergydata/well_logs/schema.py` |
| Per-dataset loaders | `worldenergydata/src/worldenergydata/well_logs/data_collection/{force2020,geolink,volve,nlog}_dataset.py` |
| Unified loader | `worldenergydata/src/worldenergydata/well_logs/data_collection/public_dataset.py` |
| Tests | `worldenergydata/tests/unit/well_logs/test_*.py` |
| License audit | `worldenergydata/docs/research/well-logs-datasets.md` |
| Plans index update | `worldenergydata/docs/plans/README.md` |
| Review (Claude self) | `kaggle-rogii-2026/scripts/review/results/2026-05-06-plan-worldenergydata-392-claude.md` |
| Review (Gemini) | `kaggle-rogii-2026/scripts/review/results/2026-05-06-plan-worldenergydata-392-gemini.md` |

---

## Deliverable

A new `src/worldenergydata/well_logs/` package providing typed schema + per-dataset loaders for at least 2 license-clean public well-log datasets (out of {Force 2020, Volve well-log subset, Geolink, NLOG}), with full TDD coverage and a license-audit doc — enabling downstream consumers (including the Kaggle ROGII Notebook submission) to pre-train models on well-row-level GR + lithology data.

---

## Hypothesis & experimental design

| Field | Statement |
|---|---|
| **Hypothesis** | At least **2 of {Force 2020, Volve well-log subset, Geolink, NLOG}** have a redistributable license + row-level GR + lithology/formation labels + can be ingested as worldenergydata modules within ~3 sessions. |
| **Experiment** | Phase 6.1 license audit + Phase 6.2 schema verification + Phase 6.3 first ingest. Measure: per-dataset license clarity (clear / unclear / paywalled), row-level GR present (Y/N), label coverage (% of rows). |
| **Predicted outcome** | **Force 2020 clears** (CC-BY-4.0, well-known open dataset). **Geolink probably clears** (commonly cited as open; license needs verification). **Volve clears** under Equinor terms but the well-log subset must be carefully extracted from a multi-TB field dataset. **NLOG clears** (Dutch open data via TNO). Expected: 2–4 datasets cleared. |
| **Decision rule** | **≥ 2 datasets cleared and ingested with full TDD coverage** → close issue; declare Wave-1 data-substrate sufficient. **< 2 cleared** → re-scope: open follow-up issues for the unclear ones; ship what cleared; document the gap as a known limitation in the prior-art doc. |

---

## Pseudocode

### `src/worldenergydata/well_logs/schema.py`

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass(frozen=True)
class WellLogRecord:
    """One well-log measurement at one MD position.
    
    Schema designed to match the union of common public well-log datasets;
    optional fields are NaN/None when not present in the source.
    """
    well_id: str               # source-namespaced unique identifier
    source: str                # 'force2020' | 'volve' | 'geolink' | 'nlog' | ...
    md_ft: float               # measured depth, feet
    x_ft: Optional[float] = None
    y_ft: Optional[float] = None
    z_ft: Optional[float] = None         # TVD
    gr_api: Optional[float] = None
    lithology: Optional[str] = None       # source-specific label, NOT normalized in v1
    formation_top: Optional[str] = None
    license: str = field(default="")     # CC-BY-4.0 | CC0 | public-domain | <other>
    citation: str = field(default="")    # source citation per record
```

### `src/worldenergydata/well_logs/data_collection/force2020_dataset.py`

```python
"""Force 2020 Well-Log Lithology dataset loader.

License: CC-BY-4.0 (verified <date> via dataset DOI page).
Source: <DOI / URL>.
Citation format: <publisher>, <year>, "<dataset name>", DOI: <doi>.

Target: ~95 wells with GR + lithology labels at well-row level.
"""

def load_force2020(*, root: Path | None = None) -> Iterator[WellLogRecord]:
    """Stream WellLogRecord per row.
    
    Memory-efficient (streams rather than loading all rows at once).
    Validates expected columns; raises if schema drift detected.
    """
```

### `src/worldenergydata/well_logs/data_collection/public_dataset.py`

```python
def load_public_well_logs(
    sources: list[str] | None = None,        # default: all license-clean
    license_filter: str | None = "redistributable",
) -> Iterator[WellLogRecord]:
    """Unified loader. Yields records from all selected sources."""
    
def list_available_datasets() -> list[dict]:
    """Returns metadata about each registered dataset, including license."""
```

---

## Files to Change

| Action | Path | Reason |
|---|---|---|
| Create | `src/worldenergydata/well_logs/__init__.py` | package init |
| Create | `src/worldenergydata/well_logs/schema.py` | `WellLogRecord` |
| Create | `src/worldenergydata/well_logs/data_collection/__init__.py` | sub-package init |
| Create | `src/worldenergydata/well_logs/data_collection/force2020_dataset.py` | loader |
| Create | `src/worldenergydata/well_logs/data_collection/geolink_dataset.py` | loader |
| Create | `src/worldenergydata/well_logs/data_collection/volve_dataset.py` | loader for well-log subset |
| Create | `src/worldenergydata/well_logs/data_collection/nlog_dataset.py` | loader |
| Create | `src/worldenergydata/well_logs/data_collection/public_dataset.py` | unified loader |
| Create | `tests/unit/well_logs/__init__.py` | test package init |
| Create | `tests/unit/well_logs/test_schema.py` | schema tests |
| Create | `tests/unit/well_logs/test_force2020.py` | dataset tests (1 per dataset) |
| Create | `tests/unit/well_logs/test_geolink.py` | … |
| Create | `tests/unit/well_logs/test_volve.py` | … |
| Create | `tests/unit/well_logs/test_nlog.py` | … |
| Create | `tests/unit/well_logs/test_public_dataset.py` | unified-loader tests |
| Create | `docs/research/well-logs-datasets.md` | license audit + per-dataset notes |
| Modify | `src/worldenergydata/__init__.py` | add `well_logs` export |
| Modify | `docs/plans/README.md` | register this plan |
| Possibly modify | `pyproject.toml` | add minimal data-loading deps if needed (pandas presumably already there; LAS file parser may be needed) |

---

## Procedure

### Phase 6.1 — License audit (~3 hours)

For each candidate dataset:
1. Read the published license at the canonical source (DOI page, dataset publisher's terms).
2. Categorize: `CC-BY-4.0 | CC0 | public-domain | research-only-no-redistribution | paywalled | unclear`.
3. Record in `docs/research/well-logs-datasets.md` with source URL + license excerpt + access-method notes.
4. Decision: ingest (redistributable) / cite-only (research-only) / skip (paywalled or unclear).

### Phase 6.2 — Schema verification (~2 hours)

For each dataset cleared in Phase 6.1:
1. Download a single sample (one well's worth of data; never the full dataset yet).
2. Verify GR present, MD present, lithology/formation labels present.
3. Identify schema drift between sources (e.g., GR units: API vs gAPI; MD units: ft vs m).
4. Record per-dataset normalization rules in the audit doc.

### Phase 6.3 — First ingest (TDD-driven; ~5 hours per dataset, parallel)

Per dataset (Force 2020 first as the highest-confidence open dataset):
1. Write `tests/unit/well_logs/test_<dataset>.py` first (TDD: tests describe the expected schema and behavior).
2. Write `src/worldenergydata/well_logs/data_collection/<dataset>_dataset.py` until tests pass.
3. Add a row to the unified loader registry.
4. Smoke-test: load 100 records, verify schema validity.

### Phase 6.4 — Public API + docs (~2 hours)

1. `src/worldenergydata/well_logs/data_collection/public_dataset.py`: unified loader matching cost/HSE pattern.
2. `src/worldenergydata/__init__.py`: export `well_logs` symbol.
3. Module-level docstring at `src/worldenergydata/well_logs/__init__.py`: how to use the loader.
4. README update if applicable.

### Phase 6.5 — PR waves (matching llm-wiki#40 pattern)

5 waves, smallest first, to keep PR review manageable:
- **PR 1** — Bootstrap: package skeleton + schema + license-audit doc. ~150 lines.
- **PR 2** — Force 2020 loader + tests.
- **PR 3** — Second cleared dataset loader + tests.
- **PR 4** — Optional third dataset (if cleared).
- **PR 5** — Unified loader + public API + plans-index update.

**Total time budget: ~15 hours drafting; PR review-and-merge cycle adds ~10–20 hours wall-clock over 4–8 weeks.**

### Phase 6.0 — Plan migration (immediately after user approval, ~30 min)

The plan was drafted in `kaggle-rogii-2026/docs/plans/` for single-source-of-truth-during-planning convenience. Its canonical home is worldenergydata. After user approval applies `status:plan-approved` to [worldenergydata#392](https://github.com/vamseeachanta/worldenergydata/issues/392):

1. Clone `vamseeachanta/worldenergydata` locally.
2. Create branch `plan/issue-392-well-logs-public-datasets`.
3. Copy the plan content to `docs/plans/2026-05-06-issue-392-well-logs-public-datasets.md` (drop the cross-repo-fixture wording in the header; canonical path is now self-referential).
4. Update `docs/plans/README.md` to register the new plan row.
5. Open PR; once merged, the kaggle-rogii-2026 copy is updated to a one-line stub linking to the worldenergydata canonical: `> See https://github.com/vamseeachanta/worldenergydata/blob/main/docs/plans/2026-05-06-issue-392-well-logs-public-datasets.md`.

The migration step is a **prerequisite to Phase 6.1**. Implementation work happens in worldenergydata against the canonical plan; the kaggle-rogii-2026 stub exists only so the kaggle planning index stays complete.

---

## Tests (T3 TDD list — full)

| Test name | What it verifies |
|---|---|
| `test_well_log_record_validates_md_monotonic` | MD increasing within a well |
| `test_well_log_record_handles_missing_lithology` | None lithology accepted; record still valid |
| `test_well_log_record_license_field_required` | empty license string raises |
| `test_force2020_loader_well_count_matches_source` | known well count from publisher |
| `test_force2020_loader_gr_distribution_sane` | GR mean within expected API band (0–300) |
| `test_force2020_loader_lithology_labels_present` | non-empty lithology in ≥ 95% of rows |
| `test_force2020_license_string_correct` | record.license == "CC-BY-4.0" |
| `test_geolink_loader_returns_correct_well_count` | (analogous) |
| `test_volve_loader_skips_seismic_files` | only well-log files loaded, not SEG-Y |
| `test_volve_loader_well_count` | (analogous) |
| `test_nlog_loader_handles_dutch_metadata` | non-ASCII Dutch strings round-trip cleanly |
| `test_public_dataset_combines_all_sources` | unified loader yields records from all registered datasets |
| `test_public_dataset_filters_by_license` | `license_filter="CC-BY-4.0"` excludes other-licensed records |
| `test_each_loader_validates_against_legal_deny_list` | no record contains ENIGMA / Databricks patterns |
| `test_each_loader_streams_not_loads_all` | iterator behavior verified (memory-bound) |
| `test_list_available_datasets_returns_all` | registry returns all + license metadata |

---

## Acceptance criteria

- [ ] All TDD tests pass: `uv run pytest tests/unit/well_logs/`
- [ ] No regression in worldenergydata's broader test suite.
- [ ] ≥ 2 datasets cleared, ingested, and tested.
- [ ] `docs/research/well-logs-datasets.md` lists ≥ 4 audited datasets with license category + decision per row.
- [ ] **Legal deny-list compliance:** no record contains ENIGMA / Databricks / other deny-list patterns (automated test).
- [ ] **Calc-citation-contract** adopted for any standards-derived constant (e.g., GR API unit calibration); single Citation per constant.
- [ ] Public Python query API parity with `cost/data_collection/public_dataset.py` pattern.
- [ ] Wave-PR strategy followed: 5 PRs, each independently reviewable.
- [ ] Cross-link to [`vamseeachanta/kaggle-rogii-2026#5`](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5) and [`vamseeachanta/llm-wiki#40`](https://github.com/vamseeachanta/llm-wiki/issues/40) on closing comment.
- [ ] worldenergydata's `docs/plans/README.md` index includes a row for this plan.
- [ ] Cross-review: Gemini review at `scripts/review/results/2026-05-06-plan-worldenergydata-392-gemini.md`. Codex unavailable; user accepts single-degraded review at approval time.

---

## Adversarial review summary

| Provider | Verdict | Key findings |
|---|---|---|
| Claude (self) | MAJOR | (1) BSEE coordination with [#365](https://github.com/vamseeachanta/worldenergydata/issues/365) was Open instead of locked — committed: this issue EXCLUDES BSEE; [#365](https://github.com/vamseeachanta/worldenergydata/issues/365) owns BSEE well-log subset. (2) "Cite-only with URL only" Volve mitigation was inconsistent with the package's purpose — replaced with "skip + follow-up issue if license unclear." (3) Plan home-repo migration was Open — locked into a concrete Phase 6.0 procedure subsection. |
| Gemini | (pending T3 cross-review — Codex unavailable per `feedback_codex_cli_0_124_upstream_regression.md`) | — |
| Codex | not run (CLI broken) | — |

**Overall result so far:** PASS-CONDITIONAL with **single-degraded review** caveat (T3 normally Claude + Codex + Gemini; Codex blocked). User must accept the degradation at approval time per `feedback_permission_gate_blocks_cross_review.md`.

Revisions made based on review:
- BSEE scope-split locked: this issue excludes BSEE; non-overlap with [#365](https://github.com/vamseeachanta/worldenergydata/issues/365) committed in Risks.
- Volve license fallback: skip + follow-up issue (not "cite-only no-data module").
- Plan home-repo migration: Phase 6.0 procedure subsection added; Open Question removed (struck-through with reference to the procedure).

---

## Risks and open questions

- **Risk: Volve license complexity.** Equinor's release license is not standard CC; permits "use for research and educational purposes" but redistribution-as-Kaggle-Dataset terms are unclear. Mitigation: read the license verbatim during Phase 6.1; **if license is unclear or restrictive, SKIP the Volve module entirely** — document in `docs/research/well-logs-datasets.md` with `license_category=unclear, decision=skip`, and file a follow-up issue for license clarification. We do NOT ship a no-data "cite-only" data-collection module (that belongs in research docs, not the data-collection layer).
- **Risk: Multi-TB Volve dataset.** Even if license-clean, the full dataset is ~5 TB (mostly seismic). We need only the well-log subset. Mitigation: Phase 6.2 verifies the well-log subset is ~few GB. If the subset can't be cleanly extracted, defer Volve to a follow-up issue.
- **Risk: Geolink license unverified.** Often cited as open but the actual license terms need direct verification. Mitigation: Phase 6.1 priority — read terms before any ingestion.
- **Risk: NLOG Dutch metadata.** Field names, formation labels in Dutch. Mitigation: don't normalize; preserve original as `lithology_raw` + add an English-translation field in v2 if needed.
- **Risk: Schema drift between sources.** GR in API units universally; lithology labels are source-specific (no universal vocabulary). Mitigation: v1 keeps lithology source-specific; v2 may add a normalization layer (out of scope here).
- **BSEE scope-split with [`worldenergydata#365`](https://github.com/vamseeachanta/worldenergydata/issues/365) (LOCKED, no longer Open):** This issue ([#392](https://github.com/vamseeachanta/worldenergydata/issues/392)) **explicitly EXCLUDES BSEE well-log data**. Force 2020, Volve well-log subset, Geolink, NLOG, OSDU subsets only. [#365](https://github.com/vamseeachanta/worldenergydata/issues/365) owns the BSEE well-log subset (or files a sub-issue under #365's umbrella for it). Cross-link both issues with the non-overlap note when this plan goes to review. **Decision committed in plan, not deferred.**
- **Open: package location** — `src/worldenergydata/well_logs/` (sibling) vs `src/worldenergydata/drilling/well_logs/` (nested under drilling). Default: sibling. User confirms at approval.
- **Open: pre-trained-model storage** — not in scope here. Models trained on these datasets, when needed for Kaggle submission, are uploaded as Kaggle Datasets directly (Kaggle requires this for internet-disabled Code Competition). Track as separate concern in the Kaggle modeling plans.
- ~~Open: plan home repo~~ — **LOCKED**: see "Plan migration" subsection under Procedure.
- **Open: Codex T3 cross-review unavailable.** User decides whether to wait for Codex 0.123.0 downgrade or proceed Claude+Gemini-only.

---

## Tier justification

**T3.** Cross-cutting work: new top-level package; multi-dataset; license-compliance is load-bearing; calc-citation-contract integration; coordination with [`worldenergydata#361`](https://github.com/vamseeachanta/worldenergydata/issues/361)/[`#365`](https://github.com/vamseeachanta/worldenergydata/issues/365); cross-repo (kaggle-rogii-2026 + llm-wiki + worldenergydata). Wave-PR strategy required to manage review surface area. T3 multi-provider review appropriate, with Codex degradation acknowledged. Estimated effort: 15 hours drafting; 25–35 hours total wall-clock with reviews and iteration over multi-week calendar.
