#!/usr/bin/env bash
# One-time per machine: link data/{raw,interim,processed} to a large-disk location.
# Default target: /mnt/ace/<repo-name>/data/. Override with DATA_ROOT env var if needed.

set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel)
REPO_NAME=$(basename "${REPO_ROOT}")
DATA_ROOT=${DATA_ROOT:-/mnt/ace/${REPO_NAME}/data}

echo "Repo:      ${REPO_ROOT}"
echo "DATA_ROOT: ${DATA_ROOT}"

if [[ ! -d $(dirname "${DATA_ROOT}") ]]; then
    parent=$(dirname "${DATA_ROOT}")
    echo "ERROR: ${parent} does not exist on this machine." >&2
    echo "  Re-run with DATA_ROOT pointing at a writable disk:" >&2
    echo "  DATA_ROOT=/path/to/large-disk/${REPO_NAME}/data ./scripts/bootstrap_data_dir.sh" >&2
    exit 1
fi

mkdir -p "${DATA_ROOT}"/{raw,interim,processed}

cd "${REPO_ROOT}"
for d in raw interim processed; do
    if [[ -L "data/${d}" ]]; then
        echo "data/${d} already a symlink → $(readlink data/${d}) — skipping"
        continue
    fi
    if [[ -d "data/${d}" && -n $(ls -A "data/${d}" 2>/dev/null) ]]; then
        echo "ERROR: data/${d} is a non-empty directory. Move its contents first." >&2
        exit 1
    fi
    rm -rf "data/${d}"
    ln -s "${DATA_ROOT}/${d}" "data/${d}"
    echo "linked data/${d} → ${DATA_ROOT}/${d}"
done

echo
echo "Done. Symlinks:"
ls -la data/
