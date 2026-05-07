# Plan for #2: Phase 2 — Offset-well features and pad-aware CV

> **Status:** plan-review
> **Tier:** T3
> **Date:** 2026-05-06
> **Issue:** https://github.com/vamseeachanta/kaggle-rogii-2026/issues/2
> **Review artifacts:** `scripts/review/results/2026-05-06-plan-2-claude.md` + `-gemini.md`. **Codex review unavailable** per `feedback_codex_cli_0_124_upstream_regression.md`; this plan ships with single-degraded-provider review (Claude self + Gemini) per `feedback_permission_gate_blocks_cross_review.md`. User acceptance of the degradation required at approval time.

---

## Resource Intelligence Summary

### Existing repo code
- No spatial-index code in repo yet (`src/rogii/util/` does not exist).
- [`docs/competition-overview.md`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/docs/competition-overview.md) — confirms each well has X, Y, Z, MD columns.
- [`docs/task-brief.md`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/docs/task-brief.md) — Slides 12–13 explicitly: "geology of an offset well can help predict the geology of the current well; geological dips behave similarly in neighboring wells."
- [`docs/roadmap.md`](https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/docs/roadmap.md) Phase 2 — promotes offset-well features from "stretch goal" to first-class signal.

### Prior plans / decisions
- `docs/decisions.md` 2026-05-05 entries — establish carry-forward floor (11.53 ft) and Phase 1 v1 negative result.
- This plan introduces **leave-pad-out CV** for the first time. All downstream plans ([#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4), [#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7), [#8](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/8)) will inherit this CV strategy; document it carefully here.

### Data findings (verified 2026-05-06)
- 773 train wells.
- Each well has 6,400-row median MD (1 ft step). X / Y are the lateral path coordinates in feet.
- Neighbors-by-2D-distance is well-defined: lateral midpoint can be `(X.mean(), Y.mean())` or the heel/toe pair. Default to **lateral midpoint** for spatial indexing because it's a single point and represents the well's footprint.
- The brief's Slide 10 ("Map view of all training and validation wells") and Slide 11 ("3D view") imply the wells are spatially clustered into pads — typical onshore drilling layout. Need to verify cluster structure empirically before locking pad detection parameters.

### External references (none required for this plan)
None — pad detection and KDTree spatial indexing are bread-and-butter. The novel work is the *coordinate projection* (next section).

### Gaps identified
- No spatial indexing infrastructure.
- No pad detection.
- No leave-pad-out CV utility.
- No coordinate projection: how do we transform a neighbor well's `TVT(MD)` curve into the target well's MD frame, given that MD is a 1-D coordinate along an arbitrarily-curved path? **This is the hardest sub-problem.**

---

## Artifact Map

| Artifact | Path |
|---|---|
| This plan | `docs/plans/2026-05-06-issue-2-phase2-offset-wells.md` |
| Spatial utility | `src/rogii/util/spatial.py` |
| Pad detection | `src/rogii/util/pads.py` |
| Offset features | `src/rogii/features/offset_wells.py` |
| Leave-pad-out CV | `src/rogii/cv/leave_pad_out.py` |
| Tests | `tests/util/test_spatial.py`, `tests/util/test_pads.py`, `tests/features/test_offset_wells.py`, `tests/cv/test_leave_pad_out.py` |
| Notebook (sanity-check + viz) | `notebooks/20_offset_well_features.ipynb` |
| Notebook (offset-only baseline) | `notebooks/22_offset_only_baseline.ipynb` |
| Decisions log | `docs/decisions.md` |
| Plans index | `docs/plans/README.md` |
| Review (Claude self) | `scripts/review/results/2026-05-06-plan-2-claude.md` |
| Review (Gemini) | `scripts/review/results/2026-05-06-plan-2-gemini.md` |

---

## Deliverable

A spatial-index + pad-detection + neighbor-feature toolkit that, given a target well, retrieves K nearest train wells by 2D lateral footprint, projects their TVT trajectories into the target's MD frame, and emits per-row features (median, quantiles, variance, dip rate). Plus a leave-pad-out CV utility usable by every downstream model plan.

---

## Hypothesis & experimental design

| Field | Statement |
|---|---|
| **Hypothesis** | "Predict TVT as the median TVT of the K=5 nearest neighbors at the same MD" beats Phase 0 floor on a substantial fraction of wells, confirming that the offset-well signal is real (not just a regularization feature). |
| **Experiment** | Same 10-well sample (RNG seed 0). Compute neighbor-median prediction for each toe row. Measure RMSE vs Phase 0 floor. |
| **Predicted outcome** | Offset-only baseline beats Phase 0 floor on **≥ 4 / 10 wells**. Aggregate RMSE land at **8–12 ft**. We do *not* expect offset-only to dominate — the value is conditional ("when the well is in a dense pad, the neighbor signal is strong"). |
| **Decision rule** | **Canonical params: `K=5, eps_ft=1500, min_samples=3` for DBSCAN; midpoint-KDTree for neighbor selection** (locked in advance to avoid sweep cherry-pick). Wins on ≥ 4/10 → offset-well features confirmed real; proceed to wire them into Phase 3 [#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4). Wins on < 4/10 → suspect projection geometry is wrong; investigate before consuming downstream. Other parameter combinations reported as diagnostic context only. |

---

## Pseudocode (for the four modules)

### `src/rogii/util/spatial.py`

```
class WellSpatialIndex:
    def __init__(self, wells_df):
        # wells_df has columns: well, X_mid, Y_mid, X_heel, Y_heel, X_toe, Y_toe
        self._tree_mid = KDTree(wells_df[['X_mid', 'Y_mid']])
        self._tree_path = KDTree(stacked path-points across wells)  # for "min distance from lateral path"
        self._wells = wells_df['well'].to_numpy()
    
    def k_nearest_by_midpoint(self, target_well, k):
        # default; cheap
        ...
    
    def k_nearest_by_path(self, target_well, k):
        # min-distance-to-lateral-path; more expensive but captures wells whose
        # paths overlap even if midpoints are far
        ...
```

### `src/rogii/util/pads.py`

```
def detect_pads(wells_df, eps_ft=1500.0, min_samples=3):
    """DBSCAN on midpoints. eps_ft picks the cluster radius."""
    coords = wells_df[['X_mid', 'Y_mid']].to_numpy()
    labels = DBSCAN(eps=eps_ft, min_samples=min_samples).fit_predict(coords)
    # noise points (label = -1) become singleton "pads" with synthetic ids
    return assign_pad_ids(labels)


def assign_test_well_to_pad(test_xy, train_pads_df, eps_ft=1500.0):
    """Inference-time pad assignment for a held-out test well.
    
    Each pad has a centroid (mean of member-well midpoints). Assign the test
    well to the train pad whose centroid is nearest within eps_ft. If no pad
    is within eps_ft, assign a new singleton pad id (synthetic, > all train ids).
    
    Why not re-DBSCAN with train + test combined: that would shift train pad
    ids, invalidate cached features, and break reproducibility between train
    fit and test predict.
    """
```

**Inference-time procedure (locks reproducibility):**
1. At training time, compute pads on train-only midpoints. Store `(pad_id, centroid_xy)` pairs alongside per-well features.
2. At inference, hold the train pad set fixed. For each test well, call `assign_test_well_to_pad`.
3. Test-well singleton pads degrade gracefully: their offset features are computed from their K nearest train wells regardless of pad-mate status (the spatial KDTree doesn't care about pad ids; pads are only used for CV partitioning, not for neighbor selection).

### `src/rogii/features/offset_wells.py`

```
def project_neighbor_to_target_md(target_traj, neighbor_traj):
    """For each MD in target, find the 'corresponding' MD in neighbor.
    
    Approach: for each row in target, find the nearest 3D point in neighbor's path
    (by Euclidean distance in (X, Y, Z) space). Return neighbor.TVT at that nearest
    point, plus the 3D distance as a confidence metric.
    """
    nbr_kdtree = KDTree(neighbor_traj[['X', 'Y', 'Z']])
    distances, indices = nbr_kdtree.query(target_traj[['X', 'Y', 'Z']])
    return neighbor_traj['TVT'].iloc[indices].to_numpy(), distances


def emit_offset_features(target_well, all_wells, spatial_index, k=5):
    """For each MD in target_well, emit features derived from K nearest neighbors."""
    neighbors = spatial_index.k_nearest_by_midpoint(target_well, k)
    nbr_tvts = []  # list of (N_target,) arrays, one per neighbor
    nbr_dists = []
    for nbr_well in neighbors:
        tvt, dist = project_neighbor_to_target_md(target_traj, neighbor_traj_for(nbr_well))
        nbr_tvts.append(tvt)
        nbr_dists.append(dist)
    nbr_tvts = stack(nbr_tvts)        # (k, N_target)
    nbr_dists = stack(nbr_dists)
    
    return DataFrame({
        'offset_tvt_median': median(nbr_tvts, axis=0),
        'offset_tvt_p25': quantile(nbr_tvts, 0.25, axis=0),
        'offset_tvt_p75': quantile(nbr_tvts, 0.75, axis=0),
        'offset_tvt_std': std(nbr_tvts, axis=0),
        'offset_dist_min_3d': min(nbr_dists, axis=0),       # validity-confidence channel
        'offset_dist_mean_3d': mean(nbr_dists, axis=0),
        'offset_dtvt_dmd_median': median(np.diff_axis0(nbr_tvts), axis=0),  # neighbor dip rate
    })
```

**Validity-confidence contract (downstream models MUST respect):**

`offset_dist_min_3d` is the per-row validity channel. Small distance (< 500 ft) → projection is geologically credible; large distance (> 2,000 ft) → projection is metric-only and likely uncorrelated with target geology. Phase 3 ([#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4)) and Phase 4 ([#7](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/7)) downstream MUST consume this channel as either:

1. A direct input feature (let GBDT learn the cutoff), or
2. An interaction term: `offset_tvt_median × indicator(offset_dist_min_3d < 500)` (force the down-weighting), or
3. A masking signal: rows with `offset_dist_min_3d > 2000` zero-out the offset features entirely.

This avoids the "noise-pretending-to-signal" failure mode where downstream models learn to trust offset features unconditionally and then perform poorly on test wells with no nearby train neighbors.

### `src/rogii/cv/leave_pad_out.py`

```
def leave_pad_out_splits(wells_df, pad_col='pad_id'):
    """Yields (train_wells, val_wells) pairs grouped by pad."""
    for pad_id in unique(wells_df[pad_col]):
        val = wells_df[wells_df[pad_col] == pad_id]['well']
        train = wells_df[wells_df[pad_col] != pad_id]['well']
        yield list(train), list(val)
```

---

## Files to Change

| Action | Path | Reason |
|---|---|---|
| Create | `src/rogii/util/__init__.py` | new package |
| Create | `src/rogii/util/spatial.py` | KDTree spatial index |
| Create | `src/rogii/util/pads.py` | DBSCAN pad detection |
| Create | `src/rogii/features/offset_wells.py` | projection + feature emission |
| Create | `src/rogii/cv/__init__.py` | new package |
| Create | `src/rogii/cv/leave_pad_out.py` | leave-pad-out splitter |
| Create | `tests/util/test_spatial.py` | KDTree synthetic tests |
| Create | `tests/util/test_pads.py` | DBSCAN synthetic tests |
| Create | `tests/features/test_offset_wells.py` | projection + feature tests |
| Create | `tests/cv/test_leave_pad_out.py` | splitter tests |
| Create | `notebooks/20_offset_well_features.ipynb` | viz: pad clusters, neighbor projections, feature distributions |
| Create | `notebooks/22_offset_only_baseline.ipynb` | offset-median baseline benchmark |
| Modify | `docs/decisions.md` | append outcome and CV-policy decision |
| Modify | `docs/plans/README.md` | add this plan to the index |

---

## Tests (T3 TDD list — full)

| Test name | What it verifies |
|---|---|
| `test_well_spatial_index_finds_self` | Querying a well in the train set returns itself first |
| `test_well_spatial_index_distance_monotone` | Distances returned in ascending order |
| `test_detect_pads_dense_cluster` | 10 wells within 500 ft → all assigned to one pad |
| `test_detect_pads_sparse_singletons` | Wells > eps_ft apart → each its own pad |
| `test_detect_pads_noise_label_handled` | DBSCAN noise points (label = -1) get unique synthetic pad IDs |
| `test_project_neighbor_exact_overlap` | Two wells with identical paths → projection is identity |
| `test_project_neighbor_orthogonal_path` | Neighbor whose path is perpendicular → 3D distances large; should still produce a valid (if low-confidence) projection |
| `test_emit_offset_features_no_neighbors` | Isolated well (no pad-mates) → graceful fallback (NaN features or wider search) |
| `test_emit_offset_features_shape` | Output DataFrame has N_target rows, 7 columns |
| `test_leave_pad_out_no_overlap` | Train and val sets share no wells |
| `test_leave_pad_out_all_wells_covered` | Every well appears in exactly one val fold across all splits |
| `test_offset_median_baseline_synthetic_wells` | Pre-built synthetic pad with known TVT pattern → median prediction within tolerance |

---

## Acceptance criteria

- [ ] All new unit tests pass: `uv run pytest tests/`
- [ ] `notebooks/20_offset_well_features.ipynb` runs end-to-end and produces:
  - [ ] Pad-cluster map (X-Y scatter, colored by pad ID).
  - [ ] Histogram of pad sizes.
  - [ ] One example target well with its 5 nearest neighbors plotted in 3D.
  - [ ] Distribution of offset-feature values across all train rows.
- [ ] `notebooks/22_offset_only_baseline.ipynb` reports per-well RMSE for offset-only prediction vs Phase 0 floor.
- [ ] Decision-rule branch followed in `docs/decisions.md`.
- [ ] If hypothesis confirmed: [#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4) Phase 3 issue updated to specify the offset-feature names + types in its feature contract.
- [ ] Leave-pad-out CV utility used in at least one downstream test (proves the API is correct).
- [ ] Cross-review: Gemini review present at `scripts/review/results/2026-05-06-plan-2-gemini.md`. Codex unavailable; user accepts single-degraded-provider review.

---

## Adversarial review summary

| Provider | Verdict | Key findings |
|---|---|---|
| Claude (self) | MAJOR | (1) Projection geometry had no validity guard — added `offset_dist_min_3d` validity-confidence contract that downstream models MUST respect. (2) Inference-time pad-assignment unspecified — added explicit recipe (assign-to-nearest-pad-within-eps; singletons otherwise). (3) `eps_ft` magic number — locked at 1500 in decision rule. |
| Gemini | (pending T3 cross-review — Codex unavailable) | — |
| Codex | not run (CLI broken per `feedback_codex_cli_0_124_upstream_regression.md`) | — |

**Overall result so far:** PASS-CONDITIONAL with **single-degraded review** caveat (T3 normally requires Claude + Codex + Gemini; Codex blocked). User must accept the degradation at approval time per `feedback_permission_gate_blocks_cross_review.md`.

Revisions made based on review:
- Added "Validity-confidence contract" subsection under `emit_offset_features`.
- Added `assign_test_well_to_pad` and "Inference-time procedure" subsection under `pads.py`.
- Decision rule locks canonical params (K=5, eps_ft=1500, min_samples=3); sweep is diagnostic-only.

---

## Risks and open questions

- **Risk: projection geometry is the hardest part.** Nearest-3D-point projection assumes the two wells are drilling through similar geological layers at similar depths. When a target well climbs and a neighbor descends, the nearest-3D-point will be "wrong" geologically even if it's right metrically. Open: should projection use trajectory tangent matching (find the neighbor MD where its tangent direction matches the target's tangent)? Defer; v1 ships with nearest-3D-point.
- **Risk: pad detection eps_ft = 1500 is a guess.** Real pads in onshore drilling are typically 500–2000 ft across. Mitigation: sweep eps_ft ∈ {500, 1000, 1500, 2000} and report pad-count distribution; lock 1500 as canonical for headline decision.
- **Risk: the visible test set has 3 wells; the hidden test set has ~200.** Pad detection on train won't include test wells. At inference time, the test well joins the spatial index but might be in a "new pad" with no train pad-mates. Mitigation: `k_nearest_by_midpoint` falls back to typewell-based-only features. Open: how often does this happen on the hidden test set? Unanswerable without the hidden set.
- **Risk: synthetic feature names introduce coupling with [#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4) (Phase 3 GBDT).** If we rename `offset_tvt_median` later, [#4](https://github.com/vamseeachanta/kaggle-rogii-2026/issues/4)'s plan and code break. Mitigation: feature names are part of the public contract — name them carefully now. Document in `src/rogii/features/offset_wells.py` docstring as "stable API per Phase 2 plan #2."
- **Open:** at what point should we use *path distance* (line-to-line) rather than midpoint-point distance? Probably yes; defer to v2. Tracking as Open question, not in scope for this issue.
- **Open:** should pad clustering happen on (X, Y) of midpoints, or on full lateral footprints (e.g., bounding box)? Midpoint is simpler; paths cross or come close → midpoint distance can mislead. Defer to v2 if pad-detection-correlated failures emerge.
- **Open: Codex review unavailable.** User decides whether to wait for Codex 0.123.0 downgrade per [vamseeachanta/workspace-hub#2479](https://github.com/vamseeachanta/workspace-hub/issues/2479) or proceed with Claude+Gemini-only.

---

## Tier justification

**T3.** New util package + new feature module + new CV package + new pad detection + 4 test files + 2 notebooks. Multiple architectural decisions (projection geometry, pad-detection params, K choice) will be inherited by all downstream phases. CV strategy change has cross-cutting effects. Deserves the highest review tier even if Codex is unavailable. Estimated effort: 3–5 sessions.
