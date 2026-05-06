# Plan for #NNN: Issue Title

> **Status:** draft | adversarial-reviewed | plan-review | plan-approved
> **Tier:** T1 | T2 | T3
> **Date:** YYYY-MM-DD
> **Issue:** https://github.com/vamseeachanta/kaggle-rogii-2026/issues/NNN
> **Review artifacts:** `scripts/review/results/YYYY-MM-DD-plan-NNN-claude.md` (T1) or +codex.md, +gemini.md for T2/T3

---

## Resource Intelligence Summary

Three-source minimum (issue body counts as one). State concrete findings, not vague "I searched."

### Existing repo code
- File path: relevant function/notebook found. State "no existing implementation" if nothing relevant.

### Prior plans / decisions
- `docs/decisions.md` 2026-MM-DD entry — states X.
- `docs/plans/<earlier-plan>.md` — covers Y.

### Data findings
<!-- For ML: distributions, statistics, structural facts about the dataset that anchor the experiment. -->
- Verified from `notebooks/N_data_inspection.ipynb`: median Z, p90 W.

### Gaps identified
- What must be built from scratch. Each gap is a testable claim.

---

## Artifact Map

| Artifact | Path |
|---|---|
| This plan | `docs/plans/YYYY-MM-DD-issue-NNN-slug.md` |
| Implementation | `src/rogii/...` |
| Notebook | `notebooks/...` |
| Tests | `tests/test_...py` |
| Review (Claude) | `scripts/review/results/YYYY-MM-DD-plan-NNN-claude.md` |
| Review (Codex)  | `scripts/review/results/YYYY-MM-DD-plan-NNN-codex.md` (T2/T3 only) |
| Review (Gemini) | `scripts/review/results/YYYY-MM-DD-plan-NNN-gemini.md` (T2/T3 only) |

---

## Deliverable

One sentence. What will exist after this issue is done that does not exist now.

---

## Hypothesis & experimental design

The empirical-ML analog of TDD. Every plan must articulate:

| Field | Statement |
|---|---|
| **Hypothesis** | A concrete numeric claim. |
| **Experiment** | Dataset, comparison, metric. |
| **Predicted outcome** | The number we'd bet on. |
| **Decision rule** | If outcome ≥ X, do A; if outcome < X, do B. |

If you can't articulate a falsifiable prediction, the right next step is a discovery issue, not this one.

---

## Pseudocode (T2/T3 only)

T1 plans skip this section and link to the files-to-change table.

```
function name(...):
    # 5-15 lines max
```

---

## Files to Change

| Action | Path | Reason |
|---|---|---|
| Create | `src/rogii/...` | main implementation |
| Create | `notebooks/...` | empirical harness |
| Modify | `docs/decisions.md` | record outcome |
| Update | `docs/plans/README.md` | add this plan to index |

---

## Acceptance criteria

Concrete, machine-checkable bullets where possible.

- [ ] `<file>` exists and imports cleanly.
- [ ] Notebook runs end-to-end on the sample wells set.
- [ ] Reported metric (RMSE / accuracy / etc.) recorded in `docs/decisions.md`.
- [ ] If hypothesis is supported: next phase issue updated with the new floor.
- [ ] If refuted: plan documents what we learned and what to try next.

---

## Adversarial review summary

Filled in after Step 3. Do not post to GitHub until populated.

| Provider | Verdict | Key findings |
|---|---|---|
| Claude (self) | APPROVE / MINOR / MAJOR | summary |
| Codex (T2/T3) | APPROVE / MINOR / MAJOR | summary |
| Gemini (T2/T3) | APPROVE / MINOR / MAJOR | summary |

**Overall result:** PASS / FAIL (re-draft required)

Revisions made based on review:
- (list)

---

## Risks and open questions

- **Risk:** ...
- **Open:** ... (flag for user during approval)

---

## Tier justification

**T1 / T2 / T3** — one-sentence reason.
