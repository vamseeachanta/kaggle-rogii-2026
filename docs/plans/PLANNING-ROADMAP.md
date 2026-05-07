# Planning Roadmap — kaggle-rogii-2026

A meta-document. The pattern across all open issues, their dependencies, and the recommended sequencing for both planning (write the plan) and implementation (execute the plan). Updated 2026-05-06.

## Goal of this document

To answer "what's the right next plan to draft?" and "what can be implemented in parallel vs. what's a strict prerequisite?" without having to mentally re-derive the dependency graph each session.

---

## Issue inventory

| # | Title | Tier | Plan status | Implementation status |
|---|---|---|---|---|
| [#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1) | Phase 1 v2 — Heel-as-reference DTW with advancing anchor | T2 | not drafted | blocked on plan |
| [#2](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/2) | Phase 2 — Offset-well features and pad-aware CV | T3 | not drafted | blocked on plan |
| [#3](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/3) | Phase 0.5 — Linear extrapolation baseline | T1 | **plan-review** | awaiting user approval |
| [#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4) | Phase 3 — GBDT regressor over combined features | T2 | not drafted | blocked on plan |
| [#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5) | Research — public datasets and prior art | T2 | not drafted | blocked on plan |
| [#6](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/6) | Submit carry-forward kernel to leaderboard | T1 | not drafted | blocked on [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9) and plan |
| [#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7) | Phase 4 — Sequence model with regime auxiliary head | T3 | not drafted | blocked on plan |
| [#8](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/8) | Phase 5 — Ensembling + submission packaging | T2 | not drafted | blocked on plan |
| [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9) | BUG — Kaggle path-detection infinite loop | T1 | **plan-review** | awaiting user approval |
| [llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40) | Reservoir-engineering literature ingest | T3 | not drafted | blocked on plan |
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

## Recommended drafting order

Draft plans in this order so each draft has stable upstream context:

1. **[#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1) (Phase 1 v2 DTW)** — T2. Foundational. Outputs feature-vector contracts that Phase 3 + Phase 4 plans depend on.
2. **[#2](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/2) (Phase 2 offset wells)** — T3. Independent of [#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1) but introduces leave-pad-out CV that downstream plans inherit.
3. **[#6](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/6) (submit kernel)** — T1. Trivial once [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9) lands; the plan is mostly the submit-then-record-score procedure.
4. **[#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4) (Phase 3 GBDT)** — T2. Consumes [#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1) and [#2](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/2) features; the plan can name the feature contract once those are written.
5. **[#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7) (Phase 4 sequence)** — T3. Highest-uncertainty plan; benefits from having all upstream plans drafted first.
6. **[#8](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/8) (Phase 5 ensemble)** — T2. Mostly recipes; depends on what [#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4) and [#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7) commit to.
7. **[#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5) (research)** — T2. Standalone; can be drafted any time but most useful before [#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7) (literature on sequence models for log correlation).
8. **[llm-wiki#40](https://github.com/vamseeachanta/llm-wiki/issues/40) (literature ingest)** — T3. Multi-week, cross-repo. Not on the competition critical path; planned last.

---

## Recommended implementation order

After all plans are approved, implement in this sequence:

```
Week 1:  #9, #3, #6  (T1 trio — unblock leaderboard, set new floor)
Week 2:  #1 + #2 in parallel
Week 3-4: #4 + finish #2 if not done
Week 5-7: #7 (sequence model, biggest risk)
Week 8-10: integration, #5/research filling gaps
Week 11-13: #8 ensemble + Kaggle submission packaging + final submits
```

Slack: 0 weeks. If Phase 4 takes 6 weeks instead of 3, ensemble work compresses. If anything breaks earlier, slack disappears further.

Mitigation: **always keep a deployable "safe" submission ready.** After [#3](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/3) lands, that's our safe. After each subsequent phase that beats it, the new model becomes the safe and the previous one is the fallback. Two-submission-per-day Kaggle rule means this is cheap.

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
