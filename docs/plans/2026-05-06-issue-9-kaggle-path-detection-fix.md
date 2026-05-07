# Plan for #9: BUG — baseline notebook hangs on Kaggle (path-detection infinite loop)

> **Status:** plan-review
> **Tier:** T1
> **Date:** 2026-05-06
> **Issue:** https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9
> **Review artifacts:** `scripts/review/results/2026-05-06-plan-9-claude.md`

---

## Resource Intelligence Summary

### Existing repo code
- [`notebooks/00_baseline_carry_forward.ipynb`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/notebooks/00_baseline_carry_forward.ipynb) — the file that hung. Cell `paths` (cell 1) contains the bug:
  ```python
  if KAGGLE_INPUT.exists():
      ...
  else:
      repo = Path.cwd().resolve()
      while not (repo / 'pyproject.toml').exists():
          repo = repo.parent       # infinite loop at /
  ```
- [`notebooks/10_dtw_alignment.ipynb`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/notebooks/10_dtw_alignment.ipynb) — has the **same** path-walk pattern but no Kaggle branch. Not yet pushed to Kaggle so the bug hasn't fired there, but the local-only walk would still hang in any environment without `pyproject.toml` upstream. Out-of-scope for this T1 fix; flagged as a follow-up to be addressed alongside [#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1) (Phase 1 v2).
- [`kaggle/baseline-carry-forward/kernel-metadata.json`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/kaggle/baseline-carry-forward/kernel-metadata.json) — verified: `"competition_sources": ["rogii-wellbore-geology-prediction"]` is present. The kernel-metadata is correct; the bug is in the notebook's defensive-fallback logic.

### Prior plans / decisions
- New memory entry `feedback_path_parent_infinite_loop.md` (this session) records the lesson generally; this fix is the local instantiation.
- [`scripts/review/results/2026-05-06-plan-3-claude.md`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/scripts/review/results/2026-05-06-plan-3-claude.md) — adjacent plan-review pattern to mirror.

### Direct evidence
- Kaggle kernel logs (fetched 2026-05-06 via `kaggle kernels logs`):
  > `nbclient.exceptions.CellTimeoutError: A cell timed out while it was being executed, after 43200 seconds.`
  
  Cell preview matched the `paths` cell exactly. Confirms the hang was in path detection, not modeling or I/O.
- Final kernel status: `KernelWorkerStatus.CANCEL_ACKNOWLEDGED` with failure message `"Your notebook was stopped because it exceeded the max allowed execution duration."`

### Gaps identified
- No environment-detection helper exists in the repo. Notebooks duplicate the path-detection logic.
- No sentinel-bounded path-walk helper.
- No CI / smoke test for "notebook runs end-to-end on Kaggle-like sandboxed paths."

---

## Artifact Map

| Artifact | Path |
|---|---|
| This plan | `docs/plans/2026-05-06-issue-9-kaggle-path-detection-fix.md` |
| Implementation | `notebooks/00_baseline_carry_forward.ipynb` (paths cell) |
| Review (Claude self) | `scripts/review/results/2026-05-06-plan-9-claude.md` |
| Plans index update | `docs/plans/README.md` |

---

## Deliverable

A baseline notebook whose path-detection cell terminates in milliseconds on Kaggle (passes when data is mounted; fails fast with an informative error if it isn't), and runs unchanged locally.

---

## Hypothesis & experimental design

| Field | Statement |
|---|---|
| **Hypothesis** | Switching environment detection from `Path('/kaggle/input/<slug>').exists()` to the `KAGGLE_KERNEL_RUN_TYPE` env var, plus a bounded path walk locally, fixes the hang and lets the kernel complete in < 5 min on Kaggle. |
| **Experiment** | Re-push kernel via `kaggle kernels push -p kaggle/baseline-carry-forward/`. Poll status. Compare wall-clock to the 12-hour-then-killed v1. |
| **Predicted outcome** | New kernel run completes with status `COMPLETE` within 5 min wall-clock; submission auto-fires from CLI; leaderboard score appears in the `competitions submissions` listing. |
| **Decision rule** | If `COMPLETE` < 5 min and submission registers → close [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9), unblock [#6](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/6). If still hangs → reopen with a different theory (data-mount race? `competition_sources` ignored? need to inspect Kaggle kernel filesystem). |

---

## Pseudocode (revised path-detection cell)

```python
import os
from pathlib import Path

COMP_SLUG = 'rogii-wellbore-geology-prediction'

def _is_kaggle() -> bool:
    # Belt-and-suspenders: env var preferred (Kaggle's documented signal), but
    # /kaggle/input parent (not the per-comp child) is a robust fallback if
    # Kaggle ever renames or scopes the env var.
    return bool(os.environ.get('KAGGLE_KERNEL_RUN_TYPE')) or Path('/kaggle/input').exists()

def _find_repo_root(start: Path, marker: str = 'pyproject.toml', max_levels: int = 10) -> Path:
    p = start.resolve()
    for _ in range(max_levels):
        if (p / marker).exists():
            return p
        if p.parent == p:
            raise RuntimeError(f'{marker} not found walking up from {start}; likely running outside the repo')
        p = p.parent
    raise RuntimeError(f'{marker} not found within {max_levels} levels above {start}')

if _is_kaggle():
    RAW = Path(f'/kaggle/input/{COMP_SLUG}')
    OUT_DIR = Path('/kaggle/working')
    OUT_NAME = 'submission.csv'
    if not RAW.exists():
        raise RuntimeError(
            f'Running on Kaggle but {RAW} is not mounted. Possible causes: '
            f'(1) kernel-metadata.json competition_sources missing or wrong slug, '
            f'(2) competition rules not yet accepted on Kaggle, '
            f'(3) data-mount race — Kaggle had not finished mounting at this point in the run.'
        )
    print('Environment: Kaggle')
else:
    repo = _find_repo_root(Path.cwd())
    RAW = repo / 'data' / 'raw'
    OUT_DIR = repo / 'submissions'
    OUT_NAME = '00_carry_forward_submission.csv'
    print('Environment: local — repo at', repo)

OUT_DIR.mkdir(exist_ok=True)
print('RAW resolves to:', RAW.resolve())
print('Will write to: ', OUT_DIR / OUT_NAME)
```

Two structural changes from v1:
1. `_is_kaggle()` — explicit env-var check, not a path-existence heuristic. Set by Kaggle on every kernel run.
2. `_find_repo_root()` — bounded walk with a sentinel (`p.parent == p`). Maximum 10 levels.

---

## Files to Change

| Action | Path | Reason |
|---|---|---|
| Modify | `notebooks/00_baseline_carry_forward.ipynb` | replace the paths cell with the bounded version |
| Modify | `docs/plans/README.md` | add this plan to the index |

Out of scope for this T1: refactor `_is_kaggle()` / `_find_repo_root()` into `src/rogii/util/env.py`. Worth doing later when ≥2 notebooks need it; track as a separate enhancement issue when [#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1) Phase 1 v2 lands and `10_dtw_alignment.ipynb` needs the same fix.

---

## Acceptance criteria

- [ ] Notebook executes locally end-to-end via `nbclient` and produces the same `submissions/00_carry_forward_submission.csv` (14,151 rows, identical to current).
- [ ] Kernel re-pushed to Kaggle; `kaggle kernels status` shows `KernelWorkerStatus.COMPLETE` within **2 minutes** of execution wall-clock (excluding queue time and dataset mount). The carry-forward computation is a few-MB read + a row-wise loop — locally < 1 s — so a 2 min ceiling on Kaggle leaves room for cold-start without hiding regressions.
- [ ] `submission.csv` appears in `kaggle competitions submissions rogii-wellbore-geology-prediction`.
- [ ] Leaderboard score recorded in `docs/decisions.md` 2026-05-06 entry and on [#6](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/6).
- [ ] Failure-mode test: changing `_is_kaggle()` to always return True locally (manual one-line edit, then revert) raises `RuntimeError` immediately rather than hanging.

---

## Adversarial review summary

| Provider | Verdict | Key findings |
|---|---|---|
| Claude (self) | MINOR | (1) `KAGGLE_KERNEL_RUN_TYPE` asserted not verified — adopt belt-and-suspenders detection. (2) 5-min acceptance is too loose — tighten to 2 min. (3) Fail-fast error message points to two causes among three — broaden to include data-mount-timing. |

**Overall result:** PASS

Revisions made based on review:
- Belt-and-suspenders Kaggle detection: env var OR `/kaggle/input` parent existence.
- Acceptance criterion tightened from 5 min → 2 min wall-clock execution time.
- Fail-fast error message broadened to name all three known failure modes.

---

## Risks and open questions

- **Risk:** `KAGGLE_KERNEL_RUN_TYPE` is the right env var per Kaggle's docs, but if Kaggle changes naming we'll silently fall through to the local branch. Mitigation: the local branch's bounded walk now fails fast rather than hanging, so the worst case is a clear error not a 12-hour silent hang.
- **Risk:** The original failure cause may not be "Kaggle didn't mount the data." It could be that `Path.exists()` was racing against a slow data mount and returned False before the data finished mounting. The new code's fail-fast path will catch this with a clear error too — but won't auto-recover. If this is the actual cause, a wait-for-data retry loop would be more robust. Defer until we observe the failure mode again.
- **Risk:** `10_dtw_alignment.ipynb` has the same path-walk pattern but is not fixed in this issue. It hasn't run on Kaggle yet so the bug hasn't fired. Will be addressed alongside [#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1) Phase 1 v2 implementation.
- **Open:** Should we also push a tiny "hello world" Kaggle kernel to confirm `KAGGLE_KERNEL_RUN_TYPE` is set before relying on it? Cheap (5-line notebook) and de-risks the fix. Defer unless the first re-push of the fixed notebook fails again.

---

## Tier justification

**T1.** Single-file fix (~30 lines of notebook source replaced), clear acceptance, no infrastructure churn, no new modules, no shared code. Fix is deterministic and well-understood from the kernel logs. Refactor-to-shared-util is explicitly out of scope.
