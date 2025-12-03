"""
Utility script to build feature parquet files from simulation JSON + measured logs.

Usage:
    python scripts/build_dataset.py --sim out/sim.json --logs logs/sample/ --output data/ml/features.parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pur_mold_twin.data.dataset import build_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ML feature set from simulation + measurements.")
    parser.add_argument("--sim", type=Path, required=True, help="Simulation JSON exported by run-sim.")
    parser.add_argument(
        "--logs",
        type=Path,
        required=True,
        help="Directory with meta/process/qc + sensors CSV, or a standalone measurements CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/ml/features.parquet"),
        help="Destination Parquet file (directories created if missing).",
    )
    args = parser.parse_args()

    features, saved_path = build_dataset(args.sim, args.logs, args.output)
    print(f"Saved features to {saved_path} (rows={len(features)}, cols={len(features.columns)})")


if __name__ == "__main__":
    main()
