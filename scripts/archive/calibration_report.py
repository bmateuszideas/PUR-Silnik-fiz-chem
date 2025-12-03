"""
Report whether a measured shot fits tolerances defined in docs/CALIBRATION.md.

Inputs:
- Measured CSV with at least: time_s, T_core_C; optional p_total_bar, demold_time_s.
- Simulation JSON from `run-sim --save-json`.

Outputs:
- Prints tolerances and PASS/FAIL per metric.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from compare_shot import compare

# Tolerances (can be refined/parametrized)
T_CORE_RMSE_LIMIT = 5.0  # K (approx C)
P_MAX_BAR_LIMIT = 0.75  # bar absolute delta
T_DEMOLD_DELTA_LIMIT = 60.0  # seconds


def main() -> None:
    parser = argparse.ArgumentParser(description="Check shot tolerances vs CALIBRATION.md limits.")
    parser.add_argument("--measured", required=True, type=Path, help="CSV with measured data (time_s, T_core_C, ...).")
    parser.add_argument("--sim", required=True, type=Path, help="Simulation JSON output.")
    args = parser.parse_args()

    summary, _ = compare(args.measured, args.sim)

    verdicts = []
    verdicts.append(
        ("RMSE T_core", summary["rmse_T_core_C"], T_CORE_RMSE_LIMIT, summary["rmse_T_core_C"] is not None)
    )
    verdicts.append(
        ("Delta p_max", summary["delta_p_max_bar"], P_MAX_BAR_LIMIT, summary["delta_p_max_bar"] is not None)
    )
    verdicts.append(
        ("Delta t_demold", summary["delta_t_demold_s"], T_DEMOLD_DELTA_LIMIT, summary["delta_t_demold_s"] is not None)
    )

    print("=== Calibration Report ===")
    overall = True
    for name, value, limit, present in verdicts:
        if not present:
            print(f"{name}: N/A (missing data)")
            overall = False
            continue
        status = "PASS" if value <= limit else "FAIL"
        if status == "FAIL":
            overall = False
        print(f"{name}: {value:.3f} vs limit {limit:.3f} => {status}")

    print("Overall status:", "PASS" if overall else "FAIL")


if __name__ == "__main__":
    main()
