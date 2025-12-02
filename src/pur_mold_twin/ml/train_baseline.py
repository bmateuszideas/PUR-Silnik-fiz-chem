"""
Training entry point for baseline ML models (optional extras).

Usage:
    python -m pur_mold_twin.ml.train_baseline --features data/ml/features.parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    import pandas as pd  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    pd = None

from .baseline import build_baseline_models


def main() -> None:
    parser = argparse.ArgumentParser(description="Train baseline ML models.")
    parser.add_argument("--features", required=True, type=Path, help="Path to features.parquet")
    args = parser.parse_args()

    if pd is None:
        raise ImportError("pandas is required to train baselines; install with pur-mold-twin[ml]")
    df = pd.read_parquet(args.features)
    models = build_baseline_models()
    # Minimal stub: fit only if targets present
    if "defect_risk" in df.columns:
        models.defect_risk_regressor.fit(df.drop(columns=["defect_risk"], errors="ignore"), df["defect_risk"])
    if "any_defect" in df.columns:
        models.defect_classifier.fit(df.drop(columns=["any_defect"], errors="ignore"), df["any_defect"])
    print("Baseline training completed (stub).")


if __name__ == "__main__":
    main()
