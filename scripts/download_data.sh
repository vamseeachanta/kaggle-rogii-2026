#!/usr/bin/env bash
# Download the ROGII Wellbore Geology competition dataset.
# Prereqs: ~/.kaggle/kaggle.json (chmod 600), competition rules accepted on Kaggle.

set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel)
RAW_DIR="${REPO_ROOT}/data/raw"
COMP="rogii-wellbore-geology-prediction"

if [[ ! -f "${HOME}/.kaggle/kaggle.json" ]]; then
    echo "ERROR: ~/.kaggle/kaggle.json not found." >&2
    echo "  1. Visit https://www.kaggle.com/settings and click 'Create New Token'." >&2
    echo "  2. mkdir -p ~/.kaggle && mv kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json" >&2
    exit 1
fi

mkdir -p "${RAW_DIR}"
cd "${RAW_DIR}"

echo "Downloading ${COMP} into ${RAW_DIR}..."
uv run --with kaggle kaggle competitions download -c "${COMP}" -p "${RAW_DIR}"

ARCHIVE="${RAW_DIR}/${COMP}.zip"
if [[ ! -f "${ARCHIVE}" ]]; then
    echo "ERROR: expected archive ${ARCHIVE} not found after download." >&2
    echo "Common cause: competition rules not yet accepted on Kaggle." >&2
    exit 1
fi

echo "Extracting archive..."
uv run --with "" python -c "import zipfile, sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" \
    "${ARCHIVE}" "${RAW_DIR}"

echo "Done. Contents of ${RAW_DIR}:"
ls -la "${RAW_DIR}" | head -20
echo "Run 'uv run scripts/verify_data.py' to sanity-check the download."
