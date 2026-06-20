"""Tests for rogii.features.spatial (issue #2, Phase 2).

The spatial math is asserted on tiny, hand-checkable synthetic inputs:
- KDTree K-NN returns the correct nearest neighbours and excludes the query well,
- inverse-distance weighting matches a hand computation,
- a neighbour's TVT(MD) projects correctly into a target MD frame,
- offset-feature summaries (weighted mean / variance / tilt) are exact on a
  two-neighbour example,
- DBSCAN pad clustering groups close wells and isolates far ones,
- leave-pad-out folds hold out an *entire* pad with no leakage of pad-mates.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from rogii.features.spatial import (
    SpatialIndex,
    assign_pads,
    inverse_distance_weights,
    lateral_midpoint,
    leave_pad_out_folds,
    offset_tvt_features,
    project_neighbour_tvt,
    well_midpoints,
)


# ---------------------------------------------------------------------------
# Midpoints + KDTree K-NN
# ---------------------------------------------------------------------------


def _well(x: float, y: float, n: int = 5) -> pd.DataFrame:
    """A trivial horizontal-well frame whose X/Y mean is exactly (x, y)."""
    return pd.DataFrame(
        {
            "MD": np.arange(n, dtype=float),
            "X": np.full(n, x),
            "Y": np.full(n, y),
            "Z": np.zeros(n),
            "TVT": np.arange(n, dtype=float),
        }
    )


def test_lateral_midpoint_is_mean() -> None:
    df = pd.DataFrame({"X": [0.0, 10.0], "Y": [0.0, 4.0]})
    assert lateral_midpoint(df) == (5.0, 2.0)


def test_knn_returns_nearest_and_excludes_self() -> None:
    # A target at origin; neighbours at increasing distance.
    wells = {
        "A": _well(0.0, 0.0),
        "B": _well(1.0, 0.0),  # dist 1
        "C": _well(0.0, 2.0),  # dist 2
        "D": _well(3.0, 4.0),  # dist 5
        "E": _well(10.0, 0.0),  # dist 10
    }
    mids = well_midpoints(wells)
    idx = SpatialIndex(mids)

    res = idx.query("A", k=3)
    assert res.wells == ["B", "C", "D"]  # nearest 3, self excluded
    assert np.allclose(res.distances, [1.0, 2.0, 5.0])
    assert "A" not in res.wells


def test_knn_exclude_set_drops_padmates() -> None:
    wells = {
        "A": _well(0.0, 0.0),
        "B": _well(1.0, 0.0),
        "C": _well(0.0, 2.0),
        "D": _well(3.0, 4.0),
    }
    idx = SpatialIndex(well_midpoints(wells))
    # Exclude B (e.g. a pad-mate): nearest two become C then D.
    res = idx.query("A", k=2, exclude={"B"})
    assert res.wells == ["C", "D"]


def test_knn_query_under_one_second_at_scale() -> None:
    import time

    rng = np.random.default_rng(0)
    n = 800
    xs = rng.uniform(0, 1e5, n)
    ys = rng.uniform(0, 1e5, n)
    wells = {f"w{i:04d}": _well(xs[i], ys[i]) for i in range(n)}
    idx = SpatialIndex(well_midpoints(wells))
    t0 = time.perf_counter()
    for w in list(wells)[:50]:
        idx.query(w, k=8)
    dt = time.perf_counter() - t0
    assert dt < 1.0  # acceptance: spatial query < 1s on full train set


# ---------------------------------------------------------------------------
# Distance weighting
# ---------------------------------------------------------------------------


def test_inverse_distance_weights_hand_checked() -> None:
    # eps=0: weights proportional to 1/d -> 1/1, 1/2, 1/4 = 4:2:1 of total 7.
    w = inverse_distance_weights(np.array([1.0, 2.0, 4.0]), eps=0.0)
    assert np.allclose(w, [4 / 7, 2 / 7, 1 / 7])
    assert w.sum() == pytest.approx(1.0)


def test_inverse_distance_single_neighbour_weight_one() -> None:
    w = inverse_distance_weights(np.array([5.0]))
    assert w == pytest.approx([1.0])


# ---------------------------------------------------------------------------
# Trajectory projection
# ---------------------------------------------------------------------------


def test_project_neighbour_tvt_linear_interp() -> None:
    # Neighbour: TVT = 2*MD over MD in [0,10]; project onto target MD 2.5, 7.5.
    nb = pd.DataFrame({"MD": [0.0, 5.0, 10.0], "TVT": [0.0, 10.0, 20.0]})
    out = project_neighbour_tvt(np.array([2.5, 7.5]), nb)
    assert np.allclose(out, [5.0, 15.0])


def test_project_neighbour_tvt_no_extrapolation() -> None:
    nb = pd.DataFrame({"MD": [0.0, 10.0], "TVT": [0.0, 20.0]})
    out = project_neighbour_tvt(np.array([-5.0, 5.0, 99.0]), nb)
    assert np.isnan(out[0]) and np.isnan(out[2])
    assert out[1] == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# Offset feature emission
# ---------------------------------------------------------------------------


def test_offset_features_two_neighbours_exact() -> None:
    # Target rows at MD 0,1,2.
    target = pd.DataFrame({"MD": [0.0, 1.0, 2.0]})
    # Neighbour P at distance 1: TVT = MD + 0 -> [0,1,2].
    # Neighbour Q at distance 3: TVT = MD + 10 -> [10,11,12].
    nbP = pd.DataFrame({"MD": [-1.0, 5.0], "TVT": [-1.0, 5.0]})  # TVT = MD
    nbQ = pd.DataFrame({"MD": [-1.0, 5.0], "TVT": [9.0, 15.0]})  # TVT = MD + 10
    neigh = {"P": nbP, "Q": nbQ}
    dist = np.array([1.0, 3.0])

    feats = offset_tvt_features(target, neigh, dist, eps=0.0)

    # Plain mean per row: (MD + (MD+10)) / 2 = MD + 5 -> [5,6,7].
    assert np.allclose(feats["offset_mean"].to_numpy(), [5.0, 6.0, 7.0])

    # Inverse-distance weights eps=0: 1/1 : 1/3 = 3:1 of total 4 -> wP=.75, wQ=.25.
    # wmean = .75*MD + .25*(MD+10) = MD + 2.5 -> [2.5, 3.5, 4.5].
    assert np.allclose(feats["offset_wmean"].to_numpy(), [2.5, 3.5, 4.5])

    # Cross-neighbour variance (population/np.nanvar): values MD and MD+10 differ
    # by 10, so var = (10/2)^2 = 25 every row.
    assert np.allclose(feats["offset_var"].to_numpy(), [25.0, 25.0, 25.0])

    # Median tilt dTVT/dMD: both neighbours have slope 1 -> tilt = 1 everywhere.
    assert np.allclose(feats["offset_tilt"].to_numpy(), [1.0, 1.0, 1.0])

    # Both neighbours cover every row.
    assert (feats["offset_n"].to_numpy() == 2).all()


def test_offset_features_partial_coverage_counts() -> None:
    target = pd.DataFrame({"MD": [0.0, 100.0]})
    # Neighbour covers only MD near 0, not 100 -> contributes to row 0 only.
    near = pd.DataFrame({"MD": [-1.0, 1.0], "TVT": [0.0, 2.0]})
    feats = offset_tvt_features(target, {"N": near}, np.array([2.0]))
    assert feats["offset_n"].to_numpy().tolist() == [1, 0]
    assert np.isnan(feats["offset_wmean"].to_numpy()[1])


def test_offset_features_no_neighbours() -> None:
    target = pd.DataFrame({"MD": [0.0, 1.0]})
    feats = offset_tvt_features(target, {}, np.array([]))
    assert (feats["offset_n"] == 0).all()
    assert feats["offset_wmean"].isna().all()


# ---------------------------------------------------------------------------
# Pad clustering + leave-pad-out CV (LEAKAGE SAFETY)
# ---------------------------------------------------------------------------


def _mids(coords: dict[str, tuple[float, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        [(w, x, y) for w, (x, y) in coords.items()], columns=["well", "X", "Y"]
    ).set_index("well")


def test_assign_pads_groups_close_isolates_far() -> None:
    # Two tight clusters ~100 ft apart, plus a far loner ~50k ft away.
    mids = _mids(
        {
            "A": (0.0, 0.0),
            "B": (100.0, 0.0),  # within 2000 ft of A -> same pad
            "C": (50000.0, 0.0),
            "D": (50100.0, 0.0),  # within 2000 ft of C -> same pad
            "Z": (200000.0, 0.0),  # isolated -> own singleton pad
        }
    )
    pads = assign_pads(mids, eps=2000.0, min_samples=1)
    assert pads["A"] == pads["B"]
    assert pads["C"] == pads["D"]
    assert pads["A"] != pads["C"]
    assert pads["Z"] != pads["A"] and pads["Z"] != pads["C"]
    assert (pads >= 0).all()  # no DBSCAN noise label


def test_leave_pad_out_is_disjoint_partition_and_leakproof() -> None:
    mids = _mids(
        {
            "A": (0.0, 0.0),
            "B": (100.0, 0.0),
            "C": (50000.0, 0.0),
            "D": (50100.0, 0.0),
            "Z": (200000.0, 0.0),
        }
    )
    pads = assign_pads(mids, eps=2000.0, min_samples=1)
    folds = leave_pad_out_folds(pads)

    all_wells = set(mids.index)
    seen_test: set[str] = set()
    for f in folds:
        test, train = set(f.test_wells), set(f.train_wells)
        # Disjoint partition of all wells.
        assert test.isdisjoint(train)
        assert test | train == all_wells
        # LEAKAGE SAFETY: for every test well, its entire pad is held out, i.e.
        # no pad-mate of any test well appears in the training fold.
        for w in test:
            padmates = {o for o in all_wells if pads[o] == pads[w]}
            assert padmates.isdisjoint(train), f"pad of {w} leaked into train"
        seen_test |= test

    # Every well is tested exactly once across the folds.
    assert seen_test == all_wells
    n_pads = pads.nunique()
    assert len(folds) == n_pads


def test_leave_pad_out_deterministic_order() -> None:
    mids = _mids({"A": (0.0, 0.0), "B": (5000.0, 0.0), "C": (10000.0, 0.0)})
    pads = assign_pads(mids, eps=1000.0)
    f1 = [f.pad for f in leave_pad_out_folds(pads)]
    f2 = [f.pad for f in leave_pad_out_folds(pads)]
    assert f1 == f2 == sorted(f1)
