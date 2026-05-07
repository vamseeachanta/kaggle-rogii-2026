# Adversarial review — Plan #9 (Kaggle path-detection infinite-loop fix)

**Reviewer:** Claude (self-review)
**Stance:** Adversarial. Assume the plan has defects until proven otherwise. No praise; no restatement; only what's wrong, missing, or risky.
**Plan reviewed:** `docs/plans/2026-05-06-issue-9-kaggle-path-detection-fix.md`
**Plan SHA:** local pre-commit (will record after first commit)
**Date:** 2026-05-06
**Verdict:** **MINOR**

---

## Findings

### Finding 1 (MINOR) — `KAGGLE_KERNEL_RUN_TYPE` is asserted, not verified

**Quote:** "Kaggle sets `KAGGLE_KERNEL_RUN_TYPE` env var on every kernel run. That's a more reliable signal than checking for `/kaggle/input/<slug>`."

**Defect:** The plan asserts this env var exists without citing Kaggle docs or providing a probe-kernel result. If Kaggle has renamed, deprecated, or scoped this env var (e.g., only set on Notebook kernels, not Script kernels), the fix flips silently to the local branch on Kaggle and the user gets a `RuntimeError('pyproject.toml not found...')` — which is at least loud, but still a wrong diagnosis surfaced to the user.

**Recommendation:** Either (a) verify `KAGGLE_KERNEL_RUN_TYPE` by pushing a 5-line probe notebook that prints all `KAGGLE_*` env vars (cheap; one extra Kaggle run), or (b) use a belt-and-suspenders check: `_is_kaggle = lambda: bool(os.environ.get('KAGGLE_KERNEL_RUN_TYPE')) or Path('/kaggle/input').exists()`. The fallback to `/kaggle/input` (the *parent*, not the per-comp child) catches the case where the env var is unset but Kaggle's standard mount is present.

**Status:** **Will revise** — adopt the belt-and-suspenders form. Cheap, zero-cost in the happy path, robust in the unhappy path.

---

### Finding 2 (MINOR) — 5-minute wall-clock acceptance is arbitrary

**Quote:** "Kernel re-pushed to Kaggle; `kaggle kernels status` shows `KernelWorkerStatus.COMPLETE` within 5 minutes wall-clock from start of run (excluding queue time)."

**Defect:** The carry-forward notebook locally completes in < 1 second on the visible 3-well sample. On Kaggle's hidden ~200-well test set, it'd be ~67× more I/O — still seconds, not minutes. But Kaggle adds container cold-start, package imports, data mount, kernel kernel boot. The honest figure is "< 2 minutes execution," not 5. Setting acceptance at 5 min hides regressions: if a future bug makes the notebook 4× slower, the criterion still passes.

**Recommendation:** Tighten to **2 min wall-clock excluding queue time**, with a separate explicit metric "kernel time-on-clock minus dataset mount time."

**Status:** **Will revise.**

---

### Finding 3 (MINOR) — Error message in fail-fast path points to one cause among several

**Quote:** `RuntimeError(f'Running on Kaggle but {RAW} is not mounted. Check kernel-metadata.json competition_sources and that competition rules are accepted.')`

**Defect:** The plan's own Risks section names a *different* possible cause (data-mount race, where the path eventually appears but `Path.exists()` was called too early). The error message names two causes (metadata, rules) but not the third (timing). A debugger seeing this error would investigate the wrong things.

**Recommendation:** Broaden the message — include all three known causes plus a "or Kaggle data-mount timing" hint. Or be honest about uncertainty: name the symptom, not specific causes.

**Status:** **Will revise.**

---

### Finding 4 (NOT A DEFECT, but worth flagging) — `10_dtw_alignment.ipynb` deferred

The plan explicitly defers fixing the same bug in `notebooks/10_dtw_alignment.ipynb` to "alongside [#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1) Phase 1 v2." This is intentional scoping (T1 single-file fix), but creates a known-bad-pattern in main. If [#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1) takes weeks, the broken notebook sits there.

**Recommendation:** No revision required for this plan, but file a follow-up issue tagged "tech-debt" pointing at `10_dtw_alignment.ipynb`. Ensures the bug doesn't get lost if [#1](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1) is slow to land.

**Status:** Acceptable. The follow-up issue can be filed at implementation time, not plan time.

---

### Finding 5 (CHECKED, NOT A DEFECT) — Diagnosis confidence

The plan claims the `else` branch was entered (i.e., `Path('/kaggle/input/<slug>').exists()` returned False). Verified by inspecting the if-branch: it contains only string assignments and `print` calls — no loops, no I/O — so it cannot hang. If the cell hung (which `CellTimeoutError` confirms), the else branch was definitely entered. Diagnosis is sound.

---

### Finding 6 (CHECKED, NOT A DEFECT) — Source count

Counted: notebook 00, notebook 10, kernel-metadata.json, kernel logs (live fetch), plan #3 (template/conventions), `feedback_path_parent_infinite_loop.md` memory entry = 6 distinct sources. Meets ≥3 minimum.

---

## Items checked but not flagged

- `notebooks/10_dtw_alignment.ipynb` does have the same `while not (repo / 'pyproject.toml').exists(): repo = repo.parent` pattern (verified by grep). Plan's claim is correct.
- `kaggle/baseline-carry-forward/kernel-metadata.json` `competition_sources` is correct (verified earlier this session).
- T1 classification: single notebook cell rewrite, no new modules, deterministic fix. Justified.

---

## Verdict

**MINOR.** Three required revisions before posting:
1. Belt-and-suspenders Kaggle detection (Finding 1): `os.environ.get('KAGGLE_KERNEL_RUN_TYPE')` OR `Path('/kaggle/input').exists()`.
2. Tighten acceptance criterion to 2 min wall-clock (Finding 2).
3. Broaden the fail-fast error message to acknowledge timing as a possible cause (Finding 3).

After revisions, post on [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9) with `status:plan-review`. **User approval gate is load-bearing — never self-approve.**
