"""
Compare measured shot logs with simulation output and report error metrics.

Usage:
    python scripts/compare_shot.py --measured measurements/core_temp.csv --sim sim_output.json

Expected inputs:
- Measured CSV (at minimum: time_s, T_core_C; optionally p_total_bar, demold_time_s)
- Simulation JSON exported by `pur-mold-twin run-sim --save-json ...`
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Tuple

import pandas as pd


def _interpolate(time_s: List[float], values: List[float], target_time: float) -> float:
    if not time_s:
        return 0.0
    if target_time <= time_s[0]:
        return values[0]
    if target_time >= time_s[-1]:
        return values[-1]
    for idx in range(1, len(time_s)):
        if target_time <= time_s[idx]:
            t0, t1 = time_s[idx - 1], time_s[idx]
            v0, v1 = values[idx - 1], values[idx]
            span = t1 - t0 or 1e-9
            fraction = (target_time - t0) / span
            return float(v0 + fraction * (v1 - v0))
    return values[-1]


def compute_rmse(measured: pd.Series, simulated: pd.Series, times: pd.Series) -> float:
    errors = []
    for t, m in zip(times, measured):
        s = _interpolate(simulated.index.to_list(), simulated.to_list(), float(t))
        errors.append((s - float(m)) ** 2)
    return (sum(errors) / len(errors)) ** 0.5 if errors else 0.0


def compare(measured_csv: Path, sim_json: Path) -> Tuple[dict, dict]:
    measured_df = pd.read_csv(measured_csv)
    sim = json.loads(sim_json.read_text(encoding="utf-8"))
    time_s = sim.get("time_s", [])
    T_core_K = sim.get("T_core_K", [])
    sim_temp_C = pd.Series([v - 273.15 for v in T_core_K], index=time_s)

    metrics = {}

    if {"time_s", "T_core_C"}.issubset(measured_df.columns):
        metrics["rmse_T_core_C"] = compute_rmse(
            measured_df["T_core_C"],
            sim_temp_C,
            measured_df["time_s"],
        )

    if "p_total_bar" in measured_df.columns and "p_total_Pa" in sim:
        metrics["delta_p_max_bar"] = abs(max(sim["p_total_Pa"]) / 100_000.0 - measured_df["p_total_bar"].max())

    if "demold_time_s" in measured_df.columns and sim.get("t_demold_opt_s") is not None:
        metrics["delta_t_demold_s"] = abs(float(sim["t_demold_opt_s"]) - float(measured_df["demold_time_s"].iloc[0]))

    summary = {
        "rmse_T_core_C": metrics.get("rmse_T_core_C", None),
        "delta_p_max_bar": metrics.get("delta_p_max_bar", None),
        "delta_t_demold_s": metrics.get("delta_t_demold_s", None),
    }
    return summary, metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare measured shot logs with simulation output.")
    parser.add_argument("--measured", required=True, type=Path, help="CSV file with measured data.")
    parser.add_argument("--sim", required=True, type=Path, help="Simulation JSON output (run-sim --save-json).")
    args = parser.parse_args()

    summary, details = compare(args.measured, args.sim)
    print("=== Comparison Metrics ===")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
