"""
Simple calibration routine using SciPy least_squares.

Designed to be used with a user-provided `simulate` callback that accepts
SimulationConfig overrides and returns a SimulationResult-like dict.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Sequence

import numpy as np
from scipy.optimize import least_squares

from .cost import CalibrationTargets, aggregate_cost


SimulationCallback = Callable[[Dict[str, float]], dict]


@dataclass
class CalibrationResult:
    params: Dict[str, float]
    cost: float
    breakdown: dict
    success: bool
    message: str


def fit_parameters(
    param_init: Dict[str, float],
    simulate: SimulationCallback,
    targets: CalibrationTargets,
    weights: Dict[str, float] | None = None,
    bounds: tuple[Sequence[float], Sequence[float]] | None = None,
) -> CalibrationResult:
    """
    Calibrate selected SimulationConfig parameters by minimizing aggregate cost.

    Args:
        param_init: initial guess for parameters to tune (dict of name->value).
        simulate: callback that accepts param dict and returns SimulationResult-like dict.
        targets: calibration targets (times, temperatures, p_max, rho).
        weights: optional weights for cost aggregation.
        bounds: optional (lower, upper) bounds for least_squares.
    """

    keys = list(param_init.keys())
    x0 = np.array([param_init[k] for k in keys], dtype=float)

    def residuals(x: np.ndarray) -> np.ndarray:
        params = {k: float(v) for k, v in zip(keys, x)}
        sim = simulate(params)
        cost, breakdown = aggregate_cost(sim, targets, weights)
        # spread total cost into individual components for optimizer diversity
        if breakdown:
            return np.array(list(breakdown.values()), dtype=float)
        return np.array([cost], dtype=float)

    result = least_squares(
        residuals,
        x0,
        bounds=bounds if bounds else (-np.inf, np.inf),
        max_nfev=200,
    )
    final_params = {k: float(v) for k, v in zip(keys, result.x)}
    sim = simulate(final_params)
    total_cost, breakdown = aggregate_cost(sim, targets, weights)
    return CalibrationResult(
        params=final_params,
        cost=total_cost,
        breakdown=breakdown,
        success=result.success,
        message=result.message,
    )
