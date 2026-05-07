# Way Forward — kaggle-rogii-2026

Session-handoff document. Snapshot of project state and the next moves, written 2026-05-07. Read this first when resuming.

## Where we are

The project is **comprehensively planned but not yet implementing**. 8 plans across 3 repos are drafted; 1 is approved; the rest await user approval. The strategic shape is settled: a research-and-data **gating phase** (Wave 1) precedes modeling implementation (Wave 3), with T1 unblockers (Wave 2) running in parallel.

### Repo locations

| Resource | Path |
|---|---|
| Kaggle competition repo | <https://github.com/vamseeachanta/kaggle-rogii-2026> (public) |
| Local clone | `/mnt/local-analysis/kaggle-rogii-2026/` |
| Dataset | `/mnt/ace/kaggle-rogii-2026/data/raw/` (~1.3 GB, 2,327 files; gitignored) |
| Kernel on Kaggle | `aceengineer/rogii-baseline-carry-forward-tvt-input` (broken; see [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9)) |
| Companion repo (literature) | <https://github.com/vamseeachanta/llm-wiki> (public) |
| Companion repo (public data) | <https://github.com/vamseeachanta/worldenergydata> (public, mature workflow) |

### Auth setup

- Kaggle CLI: OAuth via `kaggle auth login` (lands at `~/.kaggle/credentials.json`, NOT legacy `kaggle.json`).
- Kaggle username: `aceengineer` (separate from GitHub `vamseeachanta`).
- Identity verification on Kaggle: done.

## Current empirical anchors (don't lose these)

| Datapoint | Value |
|---|---|
| Carry-forward floor RMSE | **11.53 ft** on 10-well train sample |
| Phase 1 v1 (typewell-only correlation) RMSE | 297.86 ft (lost 0/10 wells) — see `docs/decisions.md` for diagnosis |
| Train wells | 773 |
| Hidden test wells | ~200 |
| Median rows per well | ~6,400 (1 ft MD step) |
| Eval-zone fraction | 72.7% per well (`TVT_input` is heel-only) |
| TVT range per typical well | ~500 ft |
| Two coordinate systems | TVT in typewell-frame (~+11,500 ft); Z in TVD (~−9,400 ft); alignment maps Z(MD) → TVT(MD) |

## Plan inventory

```
Wave 1 — Research-and-data (gating; must land before Wave 3 plans drafted)
  kaggle-rogii-2026#5  research catalog                 T2  plan-review
  llm-wiki#40           reservoir literature ingest      T3  plan-review (drafts in kaggle repo; PR-migrate to llm-wiki after approval)
  worldenergydata#392   public well-log datasets         T3  plan-review (drafts in kaggle repo; PR-migrate to worldenergydata after approval)

Wave 2 — T1 unblockers (parallelizable with Wave 1)
  kaggle-rogii-2026#3   Phase 0.5 linear extrap          T1  PLAN-APPROVED ✅  (ready to implement)
  kaggle-rogii-2026#9   Kaggle path-detection bug fix    T1  plan-review
  kaggle-rogii-2026#6   submit baseline kernel           T1  plan-review (gated on #9)
  workspace-hub#2651    PPTX → PDF on ace-linux-2        T1  not drafted (cross-machine)

Wave 3 — Modeling tail (planning blocked behind Wave 1 satisfaction)
  kaggle-rogii-2026#1   Phase 1 v2 heel-DTW              T2  plan-review (existing draft; may need revision post-Wave-1)
  kaggle-rogii-2026#2   Phase 2 offset wells             T3  plan-review (existing draft; may need revision post-Wave-1)
  kaggle-rogii-2026#4   Phase 3 GBDT                     T2  plan deferred
  kaggle-rogii-2026#7   Phase 4 sequence model           T3  plan deferred
  kaggle-rogii-2026#8   Phase 5 ensemble                 T2  plan deferred
```

Canonical roadmap: [`docs/plans/PLANNING-ROADMAP.md`](PLANNING-ROADMAP.md).
Plans index: [`docs/plans/README.md`](README.md).

## Recommended next session — exact sequence

1. **User approves Wave 1 trio** ([#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5) + [llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40) + [worldenergydata#392](https://github.com/vamseeachanta/worldenergydata/issues/392)). Approval commands are in each issue's plan-review comment. This is the gating unlock for the rest of the project.
2. **User approves Wave 2 unblockers** ([#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9), [#6](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/6)) so the Kaggle leaderboard floor lands while research runs.
3. **In parallel, implement [#3](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/3)** (Phase 0.5 linear extrapolation) — already approved; deterministic 30–60 min experiment that gives us a stronger floor than carry-forward.
4. **Implement [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9)** — Kaggle path-detection bug fix; re-push kernel; submit via CLI to record the leaderboard floor.
5. **Phase 6.0 plan migrations** (post-Wave-1 approval): clone llm-wiki and worldenergydata, copy plans into their `docs/plans/` dirs, register in their indices, open PRs.
6. **Wave 1 implementation** runs concurrently across three repos; coordinate weekly user-satisfaction check-in before unlocking Wave 3 plan-drafting for [#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4)/[#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7)/[#8](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/8).

## Cross-repo coordination

Three plan-files currently live in `kaggle-rogii-2026/docs/plans/` for single-source-of-truth-during-planning convenience but have canonical homes elsewhere. After user approval, they migrate per Phase 6.0 (in [worldenergydata#392](https://github.com/vamseeachanta/worldenergydata/issues/392) plan; same pattern applies to [llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40)):

- `2026-05-06-issue-llm-wiki-40-reservoir-engineering-literature.md` → `vamseeachanta/llm-wiki/docs/plans/2026-05-06-issue-40-reservoir-engineering-literature.md` (after llm-wiki bootstraps its own `docs/plans/`).
- `2026-05-06-issue-worldenergydata-392-well-logs-datasets.md` → `vamseeachanta/worldenergydata/docs/plans/2026-05-06-issue-392-well-logs-public-datasets.md` (worldenergydata's `docs/plans/` already exists).

## Known constraints / known issues

- **Codex CLI 0.124.0 is broken upstream** (`feedback_codex_cli_0_124_upstream_regression.md`). T2/T3 plans currently ship with single-degraded review (Claude self only or Claude + Gemini). Workaround: downgrade to 0.123.0 or wait for upstream fix; tracked at [vamseeachanta/workspace-hub#2479](https://github.com/vamseeachanta/workspace-hub/issues/2479). User must explicitly accept the degradation when approving any T2/T3 plan.
- **Kaggle competition rules permit external public data** under permissive licenses (CC-BY, CC0, public-domain). The Wave 1 datasets must clear this bar before being usable in the final submission notebook. License-clearance is a hard gate inside Wave 1.
- **Final submission internet-disabled** — pre-trained weights / external data must be uploaded as Kaggle Datasets or Kaggle Models before final submission. Tracked in [#8](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/8) Phase 5 plan (deferred).
- **`gh issue create &` in parallel reverses numbering** — recorded as `feedback_parallel_gh_issue_create_reverses_numbers.md`. Audit issue titles by `--json` immediately after any parallel batch.
- **Path.parent walk needs a sentinel** — recorded as `feedback_path_parent_infinite_loop.md`. Cost of missing this on Kaggle: 12 h of free-tier compute. Always bound upward path walks.

## Memory pointers

- `~/.claude/projects/.../memory/project_kaggle_rogii_2026.md` — top-level project memory; updated 2026-05-06 with Wave 1/2/3 gating structure and corrected issue-number mapping.
- `feedback_parallel_gh_issue_create_reverses_numbers.md` — parallel-create reverse-numbering hazard.
- `feedback_path_parent_infinite_loop.md` — sentinel-walk discipline.

## Decisions log (read this for *why* choices were made)

`docs/decisions.md` is append-only and keeps the *why* behind every load-bearing choice (storage location, team policy, Phase 1 v1 negative result, etc.). Read it before re-opening any settled question.

## Don't re-derive

- The Step 1.5 "reproduce alleged failure" verification step (workspace-hub `CLAUDE.md` 2026-05-06) is the most valuable when it disconfirms the issue body's framing. Three plans this session ([llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40), [worldenergydata#392](https://github.com/vamseeachanta/worldenergydata/issues/392), implicitly the path bug investigation) had their shapes meaningfully changed by Step 1.5 findings. Don't skip it on future plans.
- Adversarial self-review with the workspace-hub adversarial-stance contract caught MAJOR-class issues on 4/8 plans this session — issues that would have been costly to fix post-implementation. Don't downgrade self-review even when no second-pair-of-eyes is available.
- The carry-forward floor (11.53 ft RMSE) is *much* harder to beat than the original roadmap assumed. Phase 1 v2 plans take this into account; Wave 3 modeling plans must keep it in mind.

## Final commit at exit

This document, the inventory state, the PLANNING-ROADMAP, and the plan files all reflect the 2026-05-07 exit state. Resume by reading this file + PLANNING-ROADMAP + memory pointers in that order.
