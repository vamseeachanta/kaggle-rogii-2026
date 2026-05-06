#!/usr/bin/env bash
# Download the ROGII Wellbore Geology competition dataset.
# Prereqs:
#   - Kaggle CLI authenticated. Either:
#       legacy:  ~/.kaggle/kaggle.json   (username + key pair)
#       OAuth:   ~/.kaggle/credentials.json   (from `kaggle auth login`)
#       env-var: KAGGLE_API_TOKEN or KAGGLE_API_V1_TOKEN_PATH
#   - Competition rules accepted on Kaggle
#   - data/raw symlink set up (run scripts/bootstrap_data_dir.sh first if cloning fresh)

set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel)
RAW_DIR_LINK="${REPO_ROOT}/data/raw"
COMP="rogii-wellbore-geology-prediction"

if [[ ! -L "${RAW_DIR_LINK}" ]]; then
    echo "ERROR: ${RAW_DIR_LINK} is not a symlink." >&2
    echo "  Run scripts/bootstrap_data_dir.sh to create the data/ symlinks first." >&2
    exit 1
fi

RAW_DIR=$(readlink -f "${RAW_DIR_LINK}")
echo "Data target: ${RAW_DIR}"

# Probe auth via a lightweight call that requires credentials but transfers no data.
echo "Verifying Kaggle auth..."
if ! uv run --quiet --with kaggle kaggle competitions list -s rogii >/dev/null 2>&1; then
    echo "ERROR: Kaggle CLI auth failed." >&2
    echo "  Either run 'kaggle auth login' (OAuth) or place a kaggle.json at ~/.kaggle/kaggle.json (legacy)." >&2
    echo "  See https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md#authentication" >&2
    exit 1
fi

mkdir -p "${RAW_DIR}"

echo "Downloading ${COMP}..."
uv run --with kaggle kaggle competitions download -c "${COMP}" -p "${RAW_DIR}"

ARCHIVE="${RAW_DIR}/${COMP}.zip"
if [[ ! -f "${ARCHIVE}" ]]; then
    echo "ERROR: expected archive ${ARCHIVE} not found after download." >&2
    echo "Common cause: competition rules not yet accepted on Kaggle." >&2
    exit 1
fi

echo "Extracting archive..."
uv run python -c "import zipfile, sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" \
    "${ARCHIVE}" "${RAW_DIR}"

echo "Done. Top-level contents of ${RAW_DIR}:"
ls -la "${RAW_DIR}" | head -20
echo
echo "Run 'uv run scripts/verify_data.py' to sanity-check the download."
