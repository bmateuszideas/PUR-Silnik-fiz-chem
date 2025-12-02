"""
Cost functions for calibration and validation.

Functions operate on lightweight dict-like simulation outputs (matching
`SimulationResult.to_dict()`) and reference measurements loaded by
`calibration.loader`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple

import numpy as np


def _interpolate(time_s: Sequence[float], values: Sequence[float], target_time: float) -> float:
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


def rmse_core_temperature(sim_time_s: Sequence[float], sim_T_core_K: Sequence[float], ref: Iterable[dict]) -> float:
    """RMSE [K] between simulated T_core profile and reference points (time_s, T_core_C)."""

    if not ref:
        return 0.0
    errors = []
    for row in ref:
        t = float(row["time_s"])
        T_ref_K = float(row["T_core_C"]) + 273.15
        T_sim = _interpolate(sim_time_s, sim_T_core_K, t)
        errors.append((T_sim - T_ref_K) ** 2)
    return float(np.mean(errors) ** 0.5) if errors else 0.0


def abs_error_scalar(sim_value: float, ref_value: float) -> float:
    return abs(float(sim_value) - float(ref_value))


@dataclass
class CalibrationTargets:
    t_cream_s: Optional[float] = None
    t_gel_s: Optional[float] = None
    t_rise_s: Optional[float] = None
    T_core_profile: Optional[Iterable[dict]] = None
    p_max_bar: Optional[float] = None
    rho_moulded: Optional[float] = None


def aggregate_cost(sim: dict, targets: CalibrationTargets, weights: Optional[dict] = None) -> Tuple[float, dict]:
    """
    Compute aggregate cost and component breakdown.

    Args:
        sim: simulation result as dict (SimulationResult.to_dict()).
        targets: calibration targets.
        weights: optional per-metric weights.
    Returns:
        (total_cost, breakdown)
    """

    weights = weights or {}
    breakdown = {}
    total = 0.0

    if targets.T_core_profile:
        rmse = rmse_core_temperature(sim["time_s"], sim["T_core_K"], targets.T_core_profile)
        breakdown["rmse_T_core_K"] = rmse
        total += weights.get("rmse_T_core_K", 1.0) * rmse

    if targets.p_max_bar is not None:
        err = abs_error_scalar(sim.get("p_max_Pa", 0.0) / 100_000.0, targets.p_max_bar)
        breakdown["p_max_bar_abs"] = err
        total += weights.get("p_max_bar_abs", 1.0) * err

    if targets.rho_moulded is not None:
        err = abs_error_scalar(sim.get("rho_moulded", 0.0), targets.rho_moulded)
        breakdown["rho_moulded_abs"] = err
        total += weights.get("rho_moulded_abs", 1.0) * err

    # cream/gel/rise times if present in sim
    for key, target_value in [
        ("t_cream_s", targets.t_cream_s),
        ("t_gel_s", targets.t_gel_s),
        ("t_rise_s", targets.t_rise_s),
    ]:
        if target_value is None:
            continue
        sim_value = sim.get(key)
        if sim_value is None:
            continue
        err = abs_error_scalar(sim_value, target_value)
        breakdown[key + "_abs"] = err
        total += weights.get(key + "_abs", 1.0) * err

    return total, breakdown
