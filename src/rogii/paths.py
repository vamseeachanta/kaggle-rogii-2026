"""Environment-aware path resolution for notebooks and scripts.

Resolves where competition data lives and where outputs should be written,
working both on Kaggle (kernel) and in a local repo checkout.

The historical bug (issue #9): the local branch walked up the directory tree
with an *unbounded* ``while`` loop looking for ``pyproject.toml``. On Kaggle,
where no ``pyproject.toml`` exists above ``/kaggle/working`` and
``Path('/').parent == Path('/')``, this looped forever (the kernel was killed
after 12h by ``CellTimeoutError``). The fix here:

1. Detect Kaggle via the ``KAGGLE_KERNEL_RUN_TYPE`` env var (set on every
   kernel run) rather than by probing a competition-specific input path.
2. Bound the upward walk: stop at the filesystem root and after a maximum
   number of levels, raising ``RuntimeError`` instead of spinning forever.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

COMPETITION_SLUG = "rogii-wellbore-geology-prediction"
KAGGLE_INPUT = Path("/kaggle/input") / COMPETITION_SLUG
KAGGLE_WORKING = Path("/kaggle/working")

# Filenames Kaggle's grader expects vs. local convention.
KAGGLE_OUT_NAME = "submission.csv"

# Default bound on the upward directory walk. Even a deeply nested checkout is
# well under this; the point is simply that the walk *terminates*.
MAX_WALK_LEVELS = 40


@dataclass(frozen=True)
class Env:
    """Resolved environment paths.

    Attributes:
        on_kaggle: True when running inside a Kaggle kernel.
        repo: Repository root (``None`` on Kaggle, where there is no checkout).
        raw: Directory containing the competition's raw data.
        out_dir: Directory to write outputs/submissions to.
        out_name: Filename to use for the submission/output CSV.
    """

    on_kaggle: bool
    repo: Path | None
    raw: Path
    out_dir: Path
    out_name: str


def is_kaggle(env: dict[str, str] | None = None) -> bool:
    """Return True when running inside a Kaggle kernel.

    Kaggle sets ``KAGGLE_KERNEL_RUN_TYPE`` on every kernel run. This is a more
    reliable signal than checking for a competition-specific input path (which
    fails if the slug is mistyped or the data is not mounted).
    """
    env = os.environ if env is None else env
    return env.get("KAGGLE_KERNEL_RUN_TYPE") is not None


def find_repo_root(
    start: Path | None = None,
    sentinel: str = "pyproject.toml",
    max_levels: int = MAX_WALK_LEVELS,
) -> Path:
    """Walk upward from ``start`` until ``sentinel`` is found.

    The walk is **bounded**: it stops at the filesystem root and after
    ``max_levels`` steps, raising ``RuntimeError`` rather than looping forever.

    Args:
        start: Directory to start from (defaults to the current working dir).
        sentinel: Filename marking the repo root (e.g. ``pyproject.toml``).
        max_levels: Maximum number of parent directories to inspect.

    Returns:
        The directory containing ``sentinel``.

    Raises:
        RuntimeError: If ``sentinel`` is not found within the bound.
    """
    current = (Path.cwd() if start is None else Path(start)).resolve()
    for _ in range(max_levels):
        if (current / sentinel).exists():
            return current
        parent = current.parent
        if parent == current:  # reached filesystem root
            break
        current = parent
    raise RuntimeError(
        f"{sentinel!r} not found walking up from "
        f"{(Path.cwd() if start is None else Path(start))} "
        f"(stopped after {max_levels} levels or at filesystem root)"
    )


def resolve_env(
    local_out_name: str = "submission.csv",
    require_kaggle_input: bool = True,
    env: dict[str, str] | None = None,
    start: Path | None = None,
) -> Env:
    """Resolve data and output paths for the current environment.

    On Kaggle, returns the mounted competition input and ``/kaggle/working``.
    Locally, finds the repo root via a bounded upward walk and returns
    ``<repo>/data/raw`` and ``<repo>/submissions``.

    Args:
        local_out_name: Output filename to use when running locally.
        require_kaggle_input: If True, raise when on Kaggle but the competition
            data is not mounted at the expected path.
        env: Environment mapping (defaults to ``os.environ``); for testing.
        start: Starting directory for the local repo walk; for testing.

    Raises:
        RuntimeError: On Kaggle with missing input (when required), or when the
            repo root cannot be found locally within the bounded walk.
    """
    if is_kaggle(env):
        raw = KAGGLE_INPUT
        if require_kaggle_input and not raw.exists():
            raise RuntimeError(
                f"Running on Kaggle but {raw} is not mounted — check the "
                f"kernel-metadata competition_sources / dataset attachment."
            )
        return Env(
            on_kaggle=True,
            repo=None,
            raw=raw,
            out_dir=KAGGLE_WORKING,
            out_name=KAGGLE_OUT_NAME,
        )

    repo = find_repo_root(start=start)
    return Env(
        on_kaggle=False,
        repo=repo,
        raw=repo / "data" / "raw",
        out_dir=repo / "submissions",
        out_name=local_out_name,
    )
