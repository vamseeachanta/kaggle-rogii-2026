# Plan for #6: Submit carry-forward baseline kernel to Kaggle leaderboard

> **Status:** plan-review
> **Tier:** T1
> **Date:** 2026-05-06
> **Issue:** https://github.com/vamseeachanta/kaggle-rogii-2026/issues/6
> **Review artifacts:** `scripts/review/results/2026-05-06-plan-6-claude.md`

---

## Resource Intelligence Summary

### Existing repo code
- [`kaggle/baseline-carry-forward/kernel-metadata.json`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/kaggle/baseline-carry-forward/kernel-metadata.json) — id `aceengineer/rogii-baseline-carry-forward-tvt-input`, `competition_sources` includes the slug, internet disabled.
- [`notebooks/00_baseline_carry_forward.ipynb`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/notebooks/00_baseline_carry_forward.ipynb) — currently buggy ([#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9)). Fix lands first.

### Prior plans / decisions
- `docs/plans/2026-05-06-issue-9-kaggle-path-detection-fix.md` — must merge before this issue can succeed.
- Local-CV result from `notebooks/00_baseline_carry_forward.ipynb`: 11.53 ft RMSE on 10-well sample (visible test set has only 3 wells, all from training).

### Direct evidence
- 2026-05-06 v1 kernel run: 12 h `RUNNING` → killed by Kaggle's max-execution-duration limit. No submission produced.
- Competition rules accepted (verified earlier: `userHasEntered: True`).
- Identity verification done 2026-05-06.

### Gaps identified
- No leaderboard score recorded yet.
- No automation around "submit + record score." Manual today.

---

## Artifact Map

| Artifact | Path |
|---|---|
| This plan | `docs/plans/2026-05-06-issue-6-submit-baseline-leaderboard.md` |
| Updated kernel run | `aceengineer/rogii-baseline-carry-forward-tvt-input` v2 (after [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9)) |
| Decisions log | `docs/decisions.md` |
| Plans index | `docs/plans/README.md` |
| Review (Claude self) | `scripts/review/results/2026-05-06-plan-6-claude.md` |

---

## Deliverable

A recorded Kaggle leaderboard score for the carry-forward baseline, captured in `docs/decisions.md` and on this issue.

---

## Hypothesis & experimental design

| Field | Statement |
|---|---|
| **Hypothesis** | After [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9) lands, re-pushing the kernel and submitting via `kaggle competitions submit -c ... -k ... -v <ver> -f submission.csv` produces a valid leaderboard score within 5 minutes of submit. |
| **Experiment** | Run the workflow end-to-end. Record the score. |
| **Predicted outcome** | Leaderboard RMSE in **the 8–20 ft range** (the hidden test set is presumably wider in distribution than our 10-well sample, but the carry-forward strategy is robust to scale). Rank: **bottom-third**, since 78 teams have at least one submission and our baseline is the simplest possible. |
| **Decision rule** | Score recorded → close issue. Submit fails → reopen with diagnostics. |

---

## Files to Change

| Action | Path | Reason |
|---|---|---|
| Modify | `docs/decisions.md` | append leaderboard score and rank |
| Comment | issue [#6](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/6) | record score and link kernel version |
| Modify | `docs/plans/README.md` | add this plan to the index |

No code changes — admin only.

---

## Acceptance criteria

- [ ] [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9) is `done` (kernel runs to completion).
- [ ] `kaggle competitions submit -c rogii-wellbore-geology-prediction -k aceengineer/rogii-baseline-carry-forward-tvt-input -v <ver> -f submission.csv -m "carry-forward floor"` returns success.
- [ ] `kaggle competitions submissions rogii-wellbore-geology-prediction` lists the submission with a numeric public score.
- [ ] Score and rank recorded in `docs/decisions.md` 2026-05-06 entry under "Phase 0 floor."
- [ ] Issue [#6](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/6) closed with the score in a comment.

---

## Adversarial review summary

| Provider | Verdict | Key findings |
|---|---|---|
| Claude (self) | APPROVE | One MINOR documentation note (predicted-band 8–20 ft is wide); doesn't block since decision rule doesn't depend on it. No required revisions. |

**Overall result:** PASS

Revisions made based on review:
- None required.

---

## Risks and open questions

- **Risk:** even after [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9) lands, the kernel may fail for an unrelated reason (e.g., dataset format change, Kaggle infra). Mitigation: the [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9) plan's acceptance criterion already covers this — a non-completing v2 kernel reopens [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9), not this issue.
- **Risk:** the public-leaderboard score is computed on a subset of the hidden test set and may not match the private score (final). Mitigation: don't read too much into the public score. Use it as a "we submitted at all" signal.
- **Open:** should we use Kaggle's submission-message field as a structured tag (e.g., "v2 carry-forward {sha}") so future-us can correlate submissions to commits? Yes — adopt as convention. Will land in this issue's implementation.

---

## Tier justification

**T1.** Pure-admin issue. No code change, no infrastructure, no model. Single CLI call after [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9) lands. Two-line `docs/decisions.md` update. Plan exists for traceability, not for technical depth.
