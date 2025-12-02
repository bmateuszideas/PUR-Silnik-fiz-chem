"""
Constraint evaluation utilities for the Process Optimizer.

These helpers are kept separate from the search logic so they can be imported
in CLI/tests without pulling in random search implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from ..core.mvp0d import QualityTargets, SimulationResult


@dataclass
class ConstraintReport:
    """Summary of constraint evaluation for a single optimization candidate."""

    feasible: bool
    violations: List[str]
    penalty: float
    window_ok: bool
    demold_time_s: float
    demold_window: Tuple[Optional[float], Optional[float]]


def evaluate_constraints(
    result: SimulationResult,
    quality: QualityTargets,
    candidate_demold_s: float,
    t_cycle_max_s: float,
) -> ConstraintReport:
    """
    Check hard constraints for a single candidate.

    Returns:
        ConstraintReport indicating feasibility, violations and penalty term that
        downstream optimizers can use when computing objective values.
    """

    violations: List[str] = []
    penalty = 0.0

    if candidate_demold_s > t_cycle_max_s:
        violations.append(
            f"Demold time {candidate_demold_s:.1f}s exceeds cycle limit {t_cycle_max_s:.1f}s."
        )
        penalty += (candidate_demold_s - t_cycle_max_s) / max(t_cycle_max_s, 1e-6)

    if candidate_demold_s > float(result.time_s[-1]):
        violations.append(
            "Demold time lies beyond simulated horizon "
            f"({candidate_demold_s:.1f}s > {result.time_s[-1]:.1f}s)."
        )
        penalty += 1.0

    window_ok = _demold_in_window(result, candidate_demold_s)
    if not window_ok:
        violations.append("Demold target outside predicted safe window.")
        penalty += 1.5

    if result.quality_status == "FAIL":
        violations.append("Simulation quality status FAIL.")
        penalty += 1.0
    elif result.quality_status == "MARGINAL":
        penalty += 0.4

    hardness_at = _sample_series(result.time_s, result.hardness_shore, candidate_demold_s)
    if hardness_at < quality.H_demold_min_shore:
        violations.append(
            f"Hardness {hardness_at:.1f} Shore at demold < target {quality.H_demold_min_shore:.1f}."
        )
        penalty += 0.8

    alpha_at = _sample_series(result.time_s, result.alpha, candidate_demold_s)
    if alpha_at < quality.alpha_demold_min:
        violations.append(
            f"Alpha {alpha_at:.2f} at demold < target {quality.alpha_demold_min:.2f}."
        )
        penalty += 0.6

    p_limit = quality.p_max_allowable_bar * 100_000.0
    if result.p_max_Pa > p_limit:
        violations.append(
            f"Pressure {result.p_max_Pa/100000:.2f} bar exceeds limit {quality.p_max_allowable_bar:.2f} bar."
        )
        penalty += (result.p_max_Pa - p_limit) / max(p_limit, 1.0)

    if result.defect_risk > quality.defect_risk_max:
        violations.append(
            f"Defect risk {result.defect_risk:.2f} > limit {quality.defect_risk_max:.2f}."
        )
        penalty += result.defect_risk - quality.defect_risk_max

    feasible = len(violations) == 0
    return ConstraintReport(
        feasible=feasible,
        violations=violations,
        penalty=penalty,
        window_ok=window_ok,
        demold_time_s=candidate_demold_s,
        demold_window=(result.t_demold_min_s, result.t_demold_max_s),
    )


def _demold_in_window(result: SimulationResult, demold_s: float) -> bool:
    if result.t_demold_min_s is None or result.t_demold_max_s is None:
        return False
    return result.t_demold_min_s <= demold_s <= result.t_demold_max_s


def _sample_series(
    time_s: Sequence[float],
    values: Sequence[float],
    target_time: float,
) -> float:
    """Simple linear interpolation helper."""

    if not time_s:
        return float(values[-1] if values else 0.0)
    if target_time <= time_s[0]:
        return float(values[0])
    if target_time >= time_s[-1]:
        return float(values[-1])
    for idx in range(1, len(time_s)):
        if target_time <= time_s[idx]:
            t0, t1 = time_s[idx - 1], time_s[idx]
            v0, v1 = values[idx - 1], values[idx]
            span = t1 - t0 or 1e-9
            fraction = (target_time - t0) / span
            return float(v0 + fraction * (v1 - v0))
    return float(values[-1])
