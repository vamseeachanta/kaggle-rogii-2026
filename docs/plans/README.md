# Issue planning workflow — kaggle-rogii-2026

Adapts the workspace-hub `issue-planning-mode` workflow to a Kaggle ML competition repo. Lighter than the parent process where the parent's overhead doesn't earn its keep, but preserves the load-bearing user-approval gate.

Parent reference: `workspace-hub/docs/plans/README.md` (full onboarding guide).

## Workflow

```
1. INTAKE & RESOURCE INTEL — search prior plans, existing src/notebooks, related issues
2. DRAFT PLAN              — copy _template-issue-plan.md → YYYY-MM-DD-issue-NNN-slug.md
3. ADVERSARIAL REVIEW      — single-author for T1; multi-provider for T2/T3
4. POST & LABEL            — comment on issue, add `status:plan-review`
5. HARD STOP               — wait for user approval (never self-approve)
6. USER APPROVES           — label changes to `status:plan-approved`
7. IMPLEMENT               — empirical-design discipline: predict outcome, run experiment, compare
8. CLOSE                   — commit, push, summarize on issue, close
```

## Complexity tiers

| Tier | Use case | Adversarial review | Plan length |
|---|---|---|---|
| **T1** | < 1 hr experiments, single notebook, baseline tweaks | Single-author (Claude self-review) | Short |
| **T2** | New module, multiple files, evaluation harness | 2-provider (Claude + Codex *or* Claude + Gemini) | Standard |
| **T3** | Architecture decisions, new modeling track, CV strategy change | 3-provider (Claude + Codex + Gemini) | Full |

When to escalate from T1: any issue whose outcome will be hard to reverse, or whose decisions will be inherited by later phases.

## ML-specific adaptations

Standard "TDD test list" doesn't quite fit empirical ML. The replacement:

**Experimental design with falsifiable predictions** — for every plan, list:
- The hypothesis (a concrete numeric claim).
- The experiment (data, comparison, metric).
- The predicted outcome (a number we'd be willing to bet on).
- The decision rule (what we do if the outcome lands above / below the predicted band).

Plans that can't articulate a falsifiable prediction usually mean the next experiment is "look at the data first" — which is fine but should be its own discovery issue.

## User-approval gate (load-bearing)

Per workspace-hub feedback (`feedback_never_offer_to_self_label_plan_approved.md`): never self-approve in chat, never pre-authorize downstream agents. The `status:plan-approved` label is applied by the **user** in their own session, not by the implementing agent.

After plan posting:

```bash
# User runs:
gh issue edit NNN --remove-label "status:plan-review" --add-label "status:plan-approved"
```

The implementer waits for this label transition before touching any code.

## Plan index

| Issue | Plan | Tier | Status |
|---|---|---|---|
| [#3](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/3) | [2026-05-06 Phase 0.5 — Linear extrapolation baseline](2026-05-06-issue-3-linear-extrapolation.md) | T1 | **plan-approved** ✅ |
| [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9) | [2026-05-06 BUG — Kaggle path-detection infinite-loop fix](2026-05-06-issue-9-kaggle-path-detection-fix.md) | T1 | plan-review |
| [#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1) | [2026-05-06 Phase 1 v2 — Heel-as-reference DTW with advancing anchor](2026-05-06-issue-1-phase1-v2-heel-dtw.md) | T2 | plan-review |
| [#2](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/2) | [2026-05-06 Phase 2 — Offset-well features and pad-aware CV](2026-05-06-issue-2-phase2-offset-wells.md) | T3 | plan-review |
| [#6](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/6) | [2026-05-06 Submit carry-forward baseline kernel to leaderboard](2026-05-06-issue-6-submit-baseline-leaderboard.md) | T1 | plan-review |
| [#5](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/5) | [2026-05-06 Research — public datasets and prior art](2026-05-06-issue-5-research-public-datasets-prior-art.md) | T2 | plan-review |

See [PLANNING-ROADMAP.md](PLANNING-ROADMAP.md) for the full dependency graph and recommended drafting/implementation sequencing.
