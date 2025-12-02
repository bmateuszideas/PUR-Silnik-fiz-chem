"""
Feature engineering for simulation + measurement logs.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd


def _max_with_time(values: list[float], times: list[float]) -> tuple[Optional[float], Optional[float]]:
    if not values or not times:
        return None, None
    arr = np.asarray(values, dtype=float)
    idx = int(np.nanargmax(arr))
    return float(arr[idx]), float(times[idx] if idx < len(times) else np.nan)


def _window_stats(series: pd.Series, time: pd.Series, upper_s: float) -> tuple[Optional[float], Optional[float]]:
    if series.empty or time.empty:
        return None, None
    mask = time <= upper_s
    if not mask.any():
        return None, None
    window = series[mask]
    times = time[mask]
    if window.empty:
        return None, None
    avg = float(window.mean())
    if len(window) > 1:
        slope = float(np.polyfit(times, window, 1)[0])
    else:
        slope = None
    return avg, slope


def compute_basic_features(
    sim: Dict[str, Any],
    measured: Optional[pd.DataFrame] = None,
    qc: Optional[Dict[str, Any]] = None,
    process: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Compute a feature set combining simulation outputs, measurements and QC labels.
    Names mirror docs/ML_LOGGING.md to keep schema stable.
    """

    sim_time = sim.get("time_s", []) or []
    sim_T_core = sim.get("T_core_K", []) or []
    sim_p_total = sim.get("p_total_Pa", []) or []

    sim_T_max_K, sim_T_t_at_max_s = _max_with_time(sim_T_core, sim_time)
    sim_p_max_Pa, sim_p_t_at_max_s = _max_with_time(sim_p_total, sim_time)

    features: Dict[str, Any] = {
        "sim_T_core_max_C": (sim_T_max_K - 273.15) if sim_T_max_K is not None else None,
        "sim_T_core_t_at_max_s": sim_T_t_at_max_s,
        "sim_p_max_bar": (sim_p_max_Pa / 100_000.0) if sim_p_max_Pa is not None else None,
        "sim_p_t_at_max_s": sim_p_t_at_max_s,
        "sim_rho_moulded": sim.get("rho_moulded"),
        "sim_t_demold_opt_s": sim.get("t_demold_opt_s"),
        "sim_defect_risk": sim.get("defect_risk"),
    }

    if measured is not None and not measured.empty:
        if {"time_s", "T_core_C"}.issubset(measured.columns):
            meas_T_max = float(measured["T_core_C"].max())
            idx_max = measured["T_core_C"].idxmax()
            meas_t_at_max = float(measured.loc[idx_max, "time_s"]) if idx_max in measured.index else None
            avg_0_120, slope_0_60 = _window_stats(
                measured["T_core_C"].reset_index(drop=True), measured["time_s"].reset_index(drop=True), upper_s=120.0
            )
            features["meas_T_core_max_C"] = meas_T_max
            features["meas_T_core_t_at_max_s"] = meas_t_at_max
            features["meas_T_core_avg_0_120_C"] = avg_0_120
            features["meas_T_core_slope_0_60_C_per_s"] = slope_0_60
            if features["sim_T_core_max_C"] is not None:
                features["delta_T_core_max_C"] = meas_T_max - features["sim_T_core_max_C"]
        if {"time_s", "p_total_bar"}.issubset(measured.columns):
            meas_p_max = float(measured["p_total_bar"].max())
            idx_p_max = measured["p_total_bar"].idxmax()
            meas_p_t_at_max = float(measured.loc[idx_p_max, "time_s"]) if idx_p_max in measured.index else None
            _, p_slope_0_60 = _window_stats(
                measured["p_total_bar"].reset_index(drop=True), measured["time_s"].reset_index(drop=True), upper_s=60.0
            )
            features["meas_p_max_bar"] = meas_p_max
            features["meas_p_t_at_max_s"] = meas_p_t_at_max
            features["meas_p_slope_0_60_bar_per_s"] = p_slope_0_60
            if features["sim_p_max_bar"] is not None:
                features["delta_p_max_bar"] = meas_p_max - features["sim_p_max_bar"]

    if qc:
        features["qc_rho_moulded"] = qc.get("rho_moulded")
        features["qc_H_demold"] = qc.get("H_demold")
        features["qc_H_24h"] = qc.get("H_24h")
        defects = qc.get("defects") or []
        features["any_defect"] = int(bool(defects))
        if qc.get("defect_risk_operator") is not None:
            features["defect_risk"] = qc.get("defect_risk_operator")
        elif qc.get("defect_risk") is not None:
            features["defect_risk"] = qc.get("defect_risk")

    if process:
        features["proc_T_polyol_in_C"] = process.get("T_polyol_in_C")
        features["proc_T_iso_in_C"] = process.get("T_iso_in_C")
        features["proc_T_mold_init_C"] = process.get("T_mold_init_C")
        features["proc_RH_ambient"] = process.get("RH_ambient")
        features["proc_mixing_eff"] = process.get("mixing_eff")
        if process.get("t_demold_actual_s") and features.get("sim_t_demold_opt_s") is not None:
            features["delta_t_demold_s"] = process["t_demold_actual_s"] - features["sim_t_demold_opt_s"]

    return pd.DataFrame([features])
