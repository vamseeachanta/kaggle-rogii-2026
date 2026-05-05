"""Sanity-check the downloaded ROGII competition dataset.

Expected per Kaggle's data tab (2026-05-05):
    files: 2,327
    size:  ~1.33 GB
    layout: train/, test/, sample_submission.csv, AI_wellbore_geology_prediction_task_en.pptx
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    raw = repo_root / "data" / "raw"
    if not raw.exists():
        print(f"FAIL: {raw} does not exist. Run scripts/download_data.sh first.")
        return 1

    files = [p for p in raw.rglob("*") if p.is_file()]
    total_bytes = sum(p.stat().st_size for p in files)
    total_gb = total_bytes / (1024**3)

    train_csvs = list((raw / "train").glob("*__horizontal_well.csv")) if (raw / "train").exists() else []
    test_csvs = list((raw / "test").glob("*__horizontal_well.csv")) if (raw / "test").exists() else []
    typewells = list(raw.rglob("*__typewell.csv"))
    pptx = list(raw.glob("AI_wellbore_geology_prediction_task_en.pptx"))
    sample = raw / "sample_submission.csv"

    print(f"Path:              {raw}")
    print(f"Total files:       {len(files):,}")
    print(f"Total size:        {total_gb:.2f} GB")
    print(f"Train wells:       {len(train_csvs)}")
    print(f"Test wells:        {len(test_csvs)}")
    print(f"Typewell files:    {len(typewells)}")
    print(f"sample_submission: {'OK' if sample.exists() else 'MISSING'}")
    print(f"Task PPTX:         {'OK' if pptx else 'MISSING'}")

    failures: list[str] = []
    if len(files) < 2000:
        failures.append(f"file count {len(files)} below expected ~2,327")
    if total_gb < 1.0:
        failures.append(f"total size {total_gb:.2f} GB below expected ~1.33 GB")
    if not sample.exists():
        failures.append("sample_submission.csv missing")
    if not pptx:
        failures.append("task brief PPTX missing")

    if failures:
        print("\nFAIL:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nOK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
