# Plan for #1: Phase 1 v2 — Heel-as-reference DTW with advancing anchor

> **Status:** plan-review
> **Tier:** T2
> **Date:** 2026-05-06
> **Issue:** https://github.com/vamseeachanta/kaggle-rogii-2026/issues/1
> **Review artifacts:** `scripts/review/results/2026-05-06-plan-1-claude.md`

---

## Resource Intelligence Summary

### Existing repo code
- [`src/rogii/features/correlation.py`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/src/rogii/features/correlation.py) — v1 implementation. Three functions: `resample_to_step`, `best_match_depth`, `predict_tvt_via_correlation`, plus an `rmse` helper. v1 is reusable as the inner correlation primitive but the orchestration (anchor + reference selection) needs to be rewritten.
- [`notebooks/10_dtw_alignment.ipynb`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/notebooks/10_dtw_alignment.ipynb) — eval harness pattern: load 10 wells via `rng = np.random.default_rng(0)`, compute per-well RMSE, aggregate. Mirror this exactly so the comparison stays apples-to-apples.
- [`notebooks/00_baseline_carry_forward.ipynb`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/notebooks/00_baseline_carry_forward.ipynb) — carry-forward floor pattern.

### Prior plans / decisions
- `docs/decisions.md` 2026-05-05 entry "Phase 1 v1 finding": carry-forward = 11.53 ft, typewell-only correlation = 297.86 ft. Three causes named for v1 failure: static anchor, typewell ambiguity, no per-row prior.
- `docs/plans/2026-05-06-issue-3-linear-extrapolation.md` (#3, plan-review) — if approved, may update the bar from 11.53 ft to whatever linear extrapolation lands at. **This plan does not depend on #3 outcome — only the bar-to-clear changes.**
- `docs/roadmap.md` Phase 1 entry — multi-reference DTW is the core mechanism, not a baseline.

### Data findings
- 773 train wells; median ~6,400 rows; 1 ft MD step.
- `TVT_input` heel-known fraction = 0.273 → average heel = ~1,750 rows (variance unknown; some wells will be much smaller).
- TVT range per well typically ~500 ft; per-row drift typically ≪ 1 ft/MD.
- Task brief Slide 9: lateral GR has higher resolution than typewell GR — explicit hint to use heel-self-correlation.

### Direct evidence (verified 2026-05-06)
- v1 `predict_tvt_via_correlation` signature accepts `(lateral_md, lateral_gr, eval_mask, ref_depth, ref_gr, *, window_size, last_known_tvt, drift_per_ft)` — keep this for backward compatibility; add new orchestration function on top.
- `notebooks/10_dtw_alignment.ipynb`: same 10 wells via `rng.choice(wells, size=10, replace=False)` with seed 0. Verified deterministic.

### Gaps identified
- No multi-reference orchestration (heel + typewell with priority).
- No advancing anchor (current implementation uses fixed heel-exit anchor).
- No regime-aware bound on search radius.
- No way to handle "heel doesn't cover toe geology" gracefully — current code falls back to wide-search (which is exactly the v1 failure mode).

---

## Artifact Map

| Artifact | Path |
|---|---|
| This plan | `docs/plans/2026-05-06-issue-1-phase1-v2-heel-dtw.md` |
| Implementation (refactor) | `src/rogii/features/correlation.py` |
| Implementation (new) | `src/rogii/models/heel_dtw.py` |
| Tests | `tests/features/test_correlation.py`, `tests/models/test_heel_dtw.py` |
| Notebook | `notebooks/12_heel_anchored_dtw.ipynb` |
| Decisions log | `docs/decisions.md` |
| Plans index | `docs/plans/README.md` |
| Review (Claude self) | `scripts/review/results/2026-05-06-plan-1-claude.md` |
| Review (Gemini) | `scripts/review/results/2026-05-06-plan-1-gemini.md` (T2 cross-review) |

---

## Deliverable

A `predict_tvt_multi_ref` function that aligns each toe-row GR window against (heel-of-same-well, typewell) reference series with an advancing anchor and ≤30 ft search radius, plus a notebook benchmarking it against the Phase 0.5 floor on the same 10-well sample.

---

## Hypothesis & experimental design

| Field | Statement |
|---|---|
| **Hypothesis** | Heel-as-primary + advancing anchor + 30 ft search radius beats the Phase 0 floor (carry-forward 11.53 ft, or linear-extrap if [#3](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/3) lowers it) on the majority of wells. |
| **Experiment** | Same 10-well sample as `notebooks/10_dtw_alignment.ipynb` (RNG seed 0). For each well: predict TVT with heel-DTW (toe windows aligned against heel GR + heel TVT_input), with typewell-DTW as a fallback when heel correlation falls below threshold. Compute eval-zone RMSE. Compare to current floor. |
| **Predicted outcome** | Heel-DTW beats current floor on **≥ 7 / 10 wells**. Aggregate RMSE land at **5–9 ft** (vs current 11.53). |
| **Decision rule** | **Canonical params: `window_size=51, search_radius_ft=30, corr_threshold=0.6, k_recent=200`** (locked in advance to avoid sweep cherry-pick). Wins on ≥ 7/10 → adopt as new floor; update [#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4) to use these features. Wins on 5–6/10 → keep as one of two competing baselines (use whichever per-well; the "regime classifier" track from Phase 4 may decide between them). Wins on < 5/10 → root-cause the failure modes; consider whether the heel-correlation approach is fundamentally wrong. Other parameter combinations reported as diagnostic context only — they cannot flip the headline decision. |

---

## Pseudocode

```
function predict_tvt_multi_ref(lateral_md, lateral_gr, tvt_input, typewell_tvt, typewell_gr,
                                window_size=51, search_radius_ft=30, corr_threshold=0.6):
    """Multi-reference DTW with advancing anchor."""
    # Build heel reference: positions where TVT_input is observed
    heel_mask = ~isnan(tvt_input)
    heel_md = lateral_md[heel_mask]
    heel_gr = lateral_gr[heel_mask]
    heel_tvt = tvt_input[heel_mask]
    
    # Resample typewell to 1 ft TVT step (matches lateral 1 ft MD step)
    tw_tvt_grid, tw_gr_grid = resample_to_step(typewell_tvt, typewell_gr, step=1.0)
    
    # Resample heel onto a 1 ft MD step (already 1 ft step in practice)
    
    # Build a heel-keyed map: TVT(heel_md) → look up TVT for any heel MD position
    
    out = full(N, NaN)
    out[heel_mask] = tvt_input[heel_mask]   # passthrough on heel
    
    anchor_tvt = heel_tvt[-1]               # start anchor at heel-exit TVT
    eval_indices = where(~heel_mask)
    
    for i in eval_indices:
        q = lateral_gr[max(0, i-half):i+half+1]   # toe window around current MD
        if len(q) < window_size//2: 
            out[i] = anchor_tvt; continue
        
        # Heel reference: search heel positions whose TVT is within search_radius of anchor
        heel_candidates = heel_mask & abs(heel_tvt - anchor_tvt) <= search_radius_ft
        if heel_candidates.any():
            best_heel_md, heel_corr = correlate_at_positions(q, heel_gr_at_candidates)
            heel_pred_tvt = heel_tvt_at(best_heel_md)
        else:
            heel_corr = -inf; heel_pred_tvt = NaN
        
        # Typewell reference: search typewell positions within radius of anchor
        tw_candidates = abs(tw_tvt_grid - anchor_tvt) <= search_radius_ft
        if tw_candidates.any():
            best_tw_idx, tw_corr = correlate_in_window(q, tw_gr_grid[tw_candidates])
            tw_pred_tvt = tw_tvt_grid[tw_candidates][best_tw_idx]
        else:
            tw_corr = -inf; tw_pred_tvt = NaN
        
        # Pick the higher-correlation reference
        if heel_corr >= corr_threshold:
            out[i] = heel_pred_tvt
        elif tw_corr >= corr_threshold:
            out[i] = tw_pred_tvt
        else:
            out[i] = anchor_tvt   # both references too weak; carry forward
        
        anchor_tvt = out[i]   # advance the anchor
    
    return out
```

Key invariants:
- `anchor_tvt` is updated row-by-row → search radius is interpreted as "± search_radius_ft from previous prediction," not "± from heel exit."
- Fallback to carry-forward when both references' correlations fall below `corr_threshold`. This bounds the worst case at the Phase 0 floor.
- Search radius is in TVT feet, not in indices — independent of step size.

### Helper function signatures (T2 plan-time decisions)

These primitives go in `src/rogii/features/correlation.py` so both the orchestration and tests can call them directly:

```python
def correlate_q_in_band(
    q: np.ndarray,                # (window_size,) query GR window
    ref_gr: np.ndarray,           # (M,) reference GR
    ref_depth: np.ndarray,        # (M,) reference depth (TVT or heel-MD)
    anchor: float,                # depth value to anchor the search at
    radius_ft: float,             # search half-width in depth-feet
    *,
    step_ft: float = 1.0,         # depth step in ref_depth (uniform)
) -> tuple[float, float]:
    """Slide q across ref_gr within [anchor-radius, anchor+radius] depth band.
    Returns (best_depth, best_pearson_correlation).
    Raises ValueError if window > band; returns (anchor, -inf) if band is empty."""

def heel_reference_view(
    lateral_md: np.ndarray,
    lateral_gr: np.ndarray,
    tvt_input: np.ndarray,        # NaN over eval zone
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Materialize the heel as a (depth, gr, sort-by-tvt) reference.
    Returns (heel_tvt_sorted, heel_gr_sorted_by_tvt, heel_md_sorted_by_tvt)."""

def typewell_reference_view(
    typewell_tvt: np.ndarray,
    typewell_gr: np.ndarray,
    *,
    step_ft: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Resample typewell to uniform step. Returns (tvt_grid, gr_grid)."""
```

Why three helpers and not one: the heel and typewell references have different native sampling (heel is uniform-MD; typewell is uniform-TVT). The view functions normalize each into the (depth, gr) interface that `correlate_q_in_band` expects, so the orchestration becomes a one-line dispatch over a list of references rather than a ladder of if-branches.

---

## Files to Change

| Action | Path | Reason |
|---|---|---|
| Modify | `src/rogii/features/correlation.py` | Extract `correlate_q_in_band(q, ref_gr, ref_depth, anchor, radius_ft)` from current `best_match_depth`; this is the inner primitive shared by heel + typewell branches |
| Create | `src/rogii/models/__init__.py` | new package |
| Create | `src/rogii/models/heel_dtw.py` | `predict_tvt_multi_ref(...)` orchestration |
| Create | `tests/features/test_correlation.py` | unit tests for `correlate_q_in_band` |
| Create | `tests/models/test_heel_dtw.py` | unit tests for `predict_tvt_multi_ref` (synthetic well; deterministic) |
| Create | `notebooks/12_heel_anchored_dtw.ipynb` | benchmark harness (mirror `10_dtw_alignment.ipynb`) |
| Modify | `docs/decisions.md` | append outcome and floor decision |
| Modify | `docs/plans/README.md` | add this plan to the index |
| Modify | `notebooks/10_dtw_alignment.ipynb` | apply path-detection fix from [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9) (deferred there; pull in here once [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9) lands) |

---

## Tests (T2 TDD list)

Synthetic-data tests for the inner correlation primitive and the orchestration function. No Kaggle-data tests (those are integration; covered by the notebook).

| Test name | What it verifies | Input | Expected |
|---|---|---|---|
| `test_correlate_q_in_band_finds_exact_match` | Identical query in reference returns its center index | q = ref[100:151], ref same | best_idx = 125 |
| `test_correlate_q_in_band_respects_anchor` | Search confined to ±radius of anchor | anchor = 50, radius = 10 | best_idx ∈ [40, 60] |
| `test_correlate_q_in_band_zero_window` | Constant GR window returns 0 correlation, not crash | q = [5, 5, 5, ...] | corr ≈ 0, no exception |
| `test_predict_tvt_multi_ref_synthetic_match` | Synthetic well with periodic GR, heel covers the same period as toe | constructed | predictions within ±1 ft of truth |
| `test_predict_tvt_multi_ref_anchor_advances` | After 100 rows, anchor moves with predictions | gradient TVT | anchor_history is monotone |
| `test_predict_tvt_multi_ref_falls_back_to_anchor` | Both references too weak → carry-forward | random GR | predictions = last anchor for low-corr rows |
| `test_predict_tvt_multi_ref_no_heel` | Empty heel (degenerate) | tvt_input all NaN | falls back to typewell-only |
| `test_predict_tvt_multi_ref_synthetic_fault` | Synthetic well with TVT discontinuity in toe | TVT jumps at known MD | predictions either track post-fault TVT or stay at anchor — never NaN, never crash |

---

## Acceptance criteria

- [ ] All new unit tests pass: `uv run pytest tests/`
- [ ] Local CV: aggregate RMSE on the 10-well sample is reported in `docs/decisions.md`.
- [ ] Per-well comparison table (heel-DTW vs Phase 0 floor) in the notebook.
- [ ] Wins-count recorded; decision-rule branch followed (adopt / keep-as-alternative / reject).
- [ ] If adopted: [#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4) (Phase 3 GBDT) issue updated with the new feature contract.
- [ ] Path-detection fix from [#9](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/9) propagated into `notebooks/10_dtw_alignment.ipynb` (one-line replacement).
- [ ] No regression: original v1 `notebooks/10_dtw_alignment.ipynb` still runs (with the path fix); v2 notebook is additive.
- [ ] **Cross-provider review:** Gemini review artifact present at `scripts/review/results/2026-05-06-plan-1-gemini.md` before approval (T2 requirement). If Gemini unavailable, plan can be approved with single-degraded-provider review per `feedback_permission_gate_blocks_cross_review.md` — explicit user acceptance required.

---

## Adversarial review summary

| Provider | Verdict | Key findings |
|---|---|---|
| Claude (self) | MAJOR | (1) Pseudocode used undefined helpers — added explicit signatures. (2) TDD list missed synthetic-fault test — added. (3) `corr_threshold` magic number — locked at 0.6 in decision rule. |
| Gemini | (pending T2 cross-review — Codex unavailable per `feedback_codex_cli_0_124_upstream_regression.md`) | — |
| Codex | not run (CLI broken) | — |

**Overall result so far:** PASS-CONDITIONAL (Claude self-review revisions applied; awaits Gemini cross-review for T2 closure).

Revisions made based on review:
- Helper-function signatures added under "Pseudocode → Helper function signatures (T2 plan-time decisions)".
- `test_predict_tvt_multi_ref_synthetic_fault` added to TDD list.
- Decision rule locks canonical parameters; sweep is diagnostic-only.

---

## Risks and open questions

- **Risk:** the heel may not cover the toe's geology — when the lateral leaves the formation logged in the heel, heel-DTW degenerates. Mitigation: typewell fallback. Open: how often does this happen? Diagnostic in the notebook should flag wells where typewell-fallback was used > 50% of toe rows.
- **Risk:** correlation threshold `corr_threshold=0.6` is a hand-tuned magic number. Mitigation: sweep over {0.4, 0.5, 0.6, 0.7} but lock 0.6 for the headline decision (no cherry-pick). Note in decisions.md.
- **Risk:** advancing-anchor is sensitive to a single bad prediction — if row N predicts wildly, all subsequent rows search around the wrong place. Mitigation: the `corr_threshold` fallback (use anchor instead) prevents wild predictions from being committed to the anchor history when correlation is weak. Open: should we also add a sanity bound (`|new_anchor - old_anchor| ≤ K * step` per row)?
- **Risk:** runtime on 10 wells; v1 took ~35 s/well; multi-ref likely 1.5×–2×. Aggregate ~6–12 min on 10 wells. Acceptable. If we run on all 773 train wells later, that's hours; profile and optimize before then (Phase 4 will need this).
- **Open:** at what point does it pay to switch to a real DTW library (`dtaidistance`, `tslearn`)? My instinct: post Phase 4 if we're in the top-10% of leaderboard. Until then, our simpler correlator is sufficient and avoids dependency baggage.
- **Open:** should heel-DTW use a *normalized* GR (z-score over a window) instead of raw GR? Sensor-scale differences across wells could reduce cross-correlation strength. Defer to a Phase 1 v2.1 if v2 disappoints.

---

## Tier justification

**T2.** Refactors one existing module + adds one new module + adds two test files + adds one notebook. Multiple files, deterministic correctness criteria for the inner primitive (TDD-able) plus an empirical decision for the headline (hypothesis-test-able). One existing public-API function (`predict_tvt_via_correlation`) preserved for backward compatibility; new orchestration is additive. Cross-provider review (Claude + Gemini) required per workflow. Estimated effort: 1–2 sessions.
