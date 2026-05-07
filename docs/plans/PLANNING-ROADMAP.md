# Planning Roadmap — kaggle-rogii-2026

A meta-document. The pattern across all open issues, their dependencies, and the recommended sequencing for both planning (write the plan) and implementation (execute the plan). Updated 2026-05-06.

## Goal of this document

To answer "what's the right next plan to draft?" and "what can be implemented in parallel vs. what's a strict prerequisite?" without having to mentally re-derive the dependency graph each session.

---

## Issue inventory

| # | Title | Tier | Plan status | Implementation status |
|---|---|---|---|---|
| [#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1) | Phase 1 v2 — Heel-as-reference DTW with advancing anchor | T2 | **plan-review** | awaits user approval; impl gated on research-and-data phase |
| [#2](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/2) | Phase 2 — Offset-well features and pad-aware CV | T3 | **plan-review** | awaits user approval; impl gated on research-and-data phase |
| [#3](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/3) | Phase 0.5 — Linear extrapolation baseline | T1 | **plan-approved** ✅ | ready to implement |
| [#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4) | Phase 3 — GBDT regressor over combined features | T2 | **plan deferred** | not drafting until research-and-data phase landed |
| [#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5) | Research — public datasets and prior art (Kaggle-side catalog) | T2 | **plan-review** | **GATING — block on this + #40 + worldenergydata#392** |
| [#6](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/6) | Submit carry-forward kernel to leaderboard | T1 | **plan-review** | blocked on [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9); admin only |
| [#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7) | Phase 4 — Sequence model with regime auxiliary head | T3 | **plan deferred** | not drafting until research-and-data phase landed |
| [#8](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/8) | Phase 5 — Ensembling + submission packaging | T2 | **plan deferred** | not drafting until research-and-data phase landed |
| [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9) | BUG — Kaggle path-detection infinite loop | T1 | **plan-review** | T1 unblocker; can land independently |
| [llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40) | Reservoir-engineering literature ingest | T3 | **plan-review** | **GATING — research substrate** |
| [worldenergydata#392](https://github.com/vamseeachanta/worldenergydata/issues/392) | Public well-log datasets (Kaggle ROGII companion ingest) | T3 | not drafted (worldenergydata-side) | **GATING — public-data substrate** |
| [workspace-hub#2651](https://github.com/vamseeachanta/workspace-hub/issues/2651) | PPTX → PDF on ace-linux-2 | T1 | not drafted (tracked in workspace-hub) | blocked on machine handoff |

---

## Dependency graph

Reading: an arrow `A → B` means "B depends on A's output."

```
#9 (path bug) ──┬─→ #6 (submit baseline kernel) ──→ leaderboard floor recorded
                │
                └─→ #1, #7 (any future Kaggle kernel run uses this pattern)

#3 (linear extrap) ──→ Phase 0 floor updated (or not)
                  └─→ informs #1's bar to clear

#1 (Phase 1 v2 DTW) ────┬─→ #4 (Phase 3 GBDT) consumes DTW outputs as features
                        ├─→ #7 (Phase 4 sequence) uses DTW as soft prior
                        └─→ #8 (Phase 5 ensemble) blends DTW into final stack

#2 (Phase 2 offset wells) ──┬─→ #4 (Phase 3 GBDT) consumes neighbor features
                            ├─→ #7 (Phase 4 sequence) uses neighbor TVT as cross-attn
                            └─→ #8 (Phase 5 ensemble) blends offset prediction

#4 (Phase 3 GBDT) ────────┬─→ #7 (Phase 4 sequence) — GBDT residuals as aux signal
                          └─→ #8 (Phase 5 ensemble)

#7 (Phase 4 sequence) ────→ #8 (Phase 5 ensemble)

#5 (research) ────────────→ informs #1, #2, #7 modeling choices (parallel input,
                            not strict prerequisite)

#40 llm-wiki literature ──→ informs #5 (parallel input)

#2651 PPTX→PDF ───────────→ adds figures to docs/task-brief; informs #5
                            (independent of code work)
```

---

## Critical path

The critical path to a competitive leaderboard submission is:

```
#9 → #6           (≤ 1 day; unblock leaderboard floor)
#3                (≤ 1 day; new floor to beat)
#1 + #2 (parallel) (1–2 weeks; modeling tracks A and B)
#4                (1 week; structured-data baseline)
#7                (3–4 weeks; sequence model — biggest unknown)
#8                (1–2 weeks; final blending)
```

Optimistic finish: ~7 weeks of work. Aggressive but feasible inside the 13-week window if Phase 4 doesn't blow up.

---

## What can be done in parallel

- **[#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1) (DTW) and [#2](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/2) (offset wells)** are independent in implementation and can be developed simultaneously. Both feed into [#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4) and [#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7). This is where parallelism pays the most.
- **[#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5) (research) and [llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40)** are read-mostly, cross-cutting, and can run as a background thread (one or two sessions/week) regardless of where modeling work is.
- **[#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9) (path bug) and [#3](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/3) (linear extrap)** are independent T1s and can be implemented in either order or simultaneously after both plans are approved.

---

## Recommended drafting + implementation order — **revised 2026-05-06 (gating-phase strategy)**

User direction (2026-05-06, second clarification): "for planning any of this technical work, we should get good research and data. so llm-wiki readiness (into the llm-wiki repo), and any public related data into worldenergydata is very important. Let us do a thorough research and planning for these issues; following these issues being executed to satisfaction, we will have to then start planning the other work."

The research-and-data trio is now a **hard gate** on the modeling-tail planning. The "best solution" mandate means we don't draft modeling architecture in a vacuum; we draft it *after* the literature substrate and the public-data ingestion exist.

### Wave 1 — Research-and-data (gating; must execute to user satisfaction before Wave 3)

Three issues across three repos, drafted and reviewed thoroughly:

1. **[vamseeachanta/kaggle-rogii-2026#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5)** (T2) — Kaggle-side research catalog. Plan drafted, awaits approval.
2. **[vamseeachanta/llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40)** (T3) — reservoir-engineering literature substrate. Plan drafted, awaits approval.
3. **[vamseeachanta/worldenergydata#392](https://github.com/vamseeachanta/worldenergydata/issues/392)** (T3, expected) — public well-log dataset ingest. **Plan to draft next session** in `worldenergydata/docs/plans/` per that repo's conventions.

Wave 1 is "executed to satisfaction" when all three issues are closed (or have shipped meaningful first-wave output: e.g., llm-wiki PR 1+2 merged, worldenergydata first dataset module merged, prior-art catalog with named pre-training corpus).

### Wave 2 — T1 unblockers (can run concurrently with Wave 1; admin-light)

4. **[#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9)** — Kaggle path-detection bug fix. Plan drafted.
5. **[#3](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/3)** — Phase 0.5 linear-extrapolation baseline. Plan-approved. Cheap floor experiment.
6. **[#6](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/6)** — Submit carry-forward kernel to leaderboard (gated on [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9)). Plan drafted.
7. **[workspace-hub#2651](https://github.com/vamseeachanta/workspace-hub/issues/2651)** — PPTX → PDF on ace-linux-2.

These are independent of Wave 1 and represent zero-cost progress while research+data work runs in the background.

### Wave 3 — Modeling tracks (planning blocked behind Wave 1 satisfaction)

Plans for [#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1) and [#2](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/2) already exist (in `plan-review`) but their *implementation* is gated on Wave 1. Plans for [#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4), [#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7), [#8](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/8) are **deferred** (not drafted yet). Drafting will be informed by what Wave 1 finds — e.g., if pre-training corpora exist, the [#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7) sequence-model plan looks different from if they don't.

8. **[#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1) (Phase 1 v2 DTW)** — T2. Existing plan may need revision after Wave 1.
9. **[#2](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/2) (Phase 2 offset wells)** — T3. Existing plan may need revision after Wave 1.
10. **[#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4) (Phase 3 GBDT)** — T2. To draft after Wave 1.
11. **[#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7) (Phase 4 sequence)** — T3. To draft after Wave 1.
12. **[#8](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/8) (Phase 5 ensemble)** — T2. To draft after Wave 1 + after [#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4)/[#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7) are settled.

---

## Implementation order — gating-phase calendar

```
Weeks 1–3:  Wave 1 (research-and-data gating phase) + Wave 2 (T1 unblockers in parallel)
            - #5 catalog drafted and first-pass complete.
            - #40 PR 1 (bootstrap) + PR 2 (concept pages 1–2) merged.
            - worldenergydata#392 plan drafted, first dataset module merged.
            - #9, #3, #6, #2651 implementations close out (T1 admin).

Wave 1 satisfaction checkpoint (≈ end of week 3):
  - User reviews Wave 1 outputs and confirms "executed to satisfaction."
  - At checkpoint, draft plans for #4, #7, #8 informed by Wave 1 findings.
  - Revise #1 and #2 plans if needed based on Wave 1 (e.g., new datasets,
    new methodology references).

Weeks 4–7:  Wave 3 modeling implementation
            - #1 (Phase 1 v2 DTW) — informed by literature.
            - #2 (Phase 2 offset wells) — informed by literature.
            - #4 (Phase 3 GBDT) — drafted post-Wave-1.

Weeks 8–11: #7 (Phase 4 sequence model) — pre-trained on ingested datasets
            if any cleared license; otherwise auxiliary-only.

Weeks 12–13: #8 (Phase 5 ensemble + submission packaging) — final submit.
```

Strategic principle: **the "best solution" mandate means modeling decisions are anchored in literature and data, not invented in isolation.** Wave 1 is the irreducible cost of that mandate. The modeling work in Wave 3 inherits a curated substrate; without Wave 1, it would inherit only the user's intuition and the task brief.

Mitigation: **always keep a deployable "safe" submission ready.** After [#3](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/3) implementation lands, that's our safe. After each subsequent phase beats it, the new model becomes the safe and the previous one becomes the fallback. The two-submission-per-day Kaggle rule means this rolling-safe pattern is cheap.

---

## Cross-provider review policy

Per `docs/plans/README.md`:

| Tier | Review |
|---|---|
| **T1** | Single-author (Claude self-review). Cheap discipline; 30–60 min total. |
| **T2** | Claude + 1 other (Codex *or* Gemini). Most plans below fall here. |
| **T3** | Claude + Codex + Gemini. Reserve for [#2](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/2), [#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7), [llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40). |

**Constraint: Codex CLI 0.124.0 is broken** (`feedback_codex_cli_0_124_upstream_regression.md`). Until downgraded to 0.123.0 or upstream fix lands, Codex review is unavailable. Mitigation:

- T2 plans get Claude self + Gemini review.
- T3 plans get Claude self + Gemini, marked as "single-degraded provider review" per `feedback_permission_gate_blocks_cross_review.md`. User decides whether to wait for Codex or accept degraded review.
- Gemini review requires `GEMINI_CLI_TRUST_WORKSPACE=true` per `feedback_gemini_trust_env_blocks_reviews.md`. The kaggle-rogii-2026 repo doesn't yet have a Gemini wrapper script; drafting a minimal one is the gate before T2/T3 plans can proceed to multi-provider review.

---

## Living document

Append to this file as plans land or the dependency graph changes. Each plan's row in the inventory table updates: `not drafted` → `plan-review` → `plan-approved` → `in-progress` → `done`.
