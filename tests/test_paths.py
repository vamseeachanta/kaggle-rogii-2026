"""Tests for rogii.paths — the bounded, env-aware path resolver (issue #9).

The original bug was an *unbounded* upward directory walk that looped forever
on Kaggle. These tests assert the walk terminates and the Kaggle branch is
selected by env var.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rogii import paths


def test_find_repo_root_in_repo_like_tree(tmp_path: Path) -> None:
    """Resolver returns the directory holding the sentinel from a nested cwd."""
    root = tmp_path / "repo"
    nested = root / "notebooks" / "deep"
    nested.mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname='x'\n")

    found = paths.find_repo_root(start=nested)
    assert found == root.resolve()


def test_find_repo_root_terminates_when_no_sentinel(tmp_path: Path) -> None:
    """Walking up with no sentinel anywhere RAISES (bounded) — does not hang.

    pytest enforces this implicitly: an infinite loop would never return, so a
    clean RuntimeError is the proof of termination.
    """
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    with pytest.raises(RuntimeError, match="not found"):
        paths.find_repo_root(start=nested)


def test_find_repo_root_bounded_by_max_levels(tmp_path: Path) -> None:
    """The walk stops after max_levels even when the root is reachable above."""
    root = tmp_path / "repo"
    deep = root
    for i in range(5):
        deep = deep / f"lvl{i}"
    deep.mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname='x'\n")

    # Sentinel is 5 levels up but we only allow 2 — must raise, not loop/find.
    with pytest.raises(RuntimeError, match="not found"):
        paths.find_repo_root(start=deep, max_levels=2)


def test_is_kaggle_true_when_env_var_set() -> None:
    assert paths.is_kaggle({"KAGGLE_KERNEL_RUN_TYPE": "Interactive"}) is True


def test_is_kaggle_false_without_env_var() -> None:
    assert paths.is_kaggle({}) is False


def test_resolve_env_kaggle_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    """With the Kaggle env var set, resolve_env returns the Kaggle paths."""
    fake_env = {"KAGGLE_KERNEL_RUN_TYPE": "Batch"}
    # Pretend the competition input IS mounted so we don't raise.
    monkeypatch.setattr(paths.Path, "exists", lambda self: True)

    env = paths.resolve_env(env=fake_env)
    assert env.on_kaggle is True
    assert env.repo is None
    assert env.raw == paths.KAGGLE_INPUT
    assert env.out_dir == paths.KAGGLE_WORKING
    assert env.out_name == "submission.csv"


def test_resolve_env_kaggle_missing_input_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """On Kaggle but data not mounted -> RuntimeError (no silent fallthrough)."""
    fake_env = {"KAGGLE_KERNEL_RUN_TYPE": "Batch"}
    monkeypatch.setattr(paths.Path, "exists", lambda self: False)
    with pytest.raises(RuntimeError, match="not mounted"):
        paths.resolve_env(env=fake_env)


def test_resolve_env_local_branch(tmp_path: Path) -> None:
    """Off Kaggle, resolve_env locates the repo root and derives data/out dirs."""
    root = tmp_path / "repo"
    nested = root / "notebooks"
    nested.mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname='x'\n")

    env = paths.resolve_env(env={}, start=nested, local_out_name="my.csv")
    assert env.on_kaggle is False
    assert env.repo == root.resolve()
    assert env.raw == root.resolve() / "data" / "raw"
    assert env.out_dir == root.resolve() / "submissions"
    assert env.out_name == "my.csv"
