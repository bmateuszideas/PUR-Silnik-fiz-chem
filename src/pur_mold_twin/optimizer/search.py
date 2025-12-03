"""
Random/grid search style Process Optimizer for PUR-MOLD-TWIN.

The initial implementation follows TODO1 §9-10 by sampling inlet
temperatures and demold time, running MVP 0D simulations, and filtering the
results through quality constraints and diagnostic flags.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import random

from pydantic import BaseModel, Field, field_validator

from ..core import MVP0DSimulator, ProcessConditions, QualityTargets, SimulationConfig
from ..core.mvp0d import SimulationResult
from .constraints import ConstraintReport, evaluate_constraints


class OptimizerBounds(BaseModel):
    """Numerical ranges for decision variables."""

    T_polyol_C: Tuple[float, float] = (20.0, 30.0)
    T_iso_C: Tuple[float, float] = (20.0, 30.0)
    T_mold_C: Tuple[float, float] = (35.0, 50.0)
    t_demold_s: Tuple[float, float] = (240.0, 600.0)

    def clamp(self, value: float, bounds: Tuple[float, float]) -> float:
        return max(bounds[0], min(bounds[1], value))

    @field_validator("T_polyol_C", "T_iso_C", "T_mold_C", "t_demold_s")
    def _validate_bounds(cls, value: Tuple[float, float]) -> Tuple[float, float]:
        if value[1] <= value[0]:
            raise ValueError(f"Upper bound {value[1]} must be greater than lower bound {value[0]}.")
        return value


class OptimizationConfig(BaseModel):
    """Configuration knobs for the optimizer search routine."""

    samples: int = Field(40, gt=0)
    random_seed: Optional[int] = None
    bounds: OptimizerBounds = Field(default_factory=OptimizerBounds)
    t_cycle_max_s: float = Field(600.0, gt=0)
    prefer_lower_pressure: bool = True


@dataclass
class OptimizationCandidate:
    """Concrete decision variables evaluated by the optimizer."""

    T_polyol_in_C: float
    T_iso_in_C: float
    T_mold_init_C: float
    t_demold_s: float


@dataclass
class CandidateEvaluation:
    """Stores metrics for a single candidate evaluation."""

    candidate: OptimizationCandidate
    objective: float
    constraints: ConstraintReport
    feasible: bool
    t_demold_window: Tuple[Optional[float], Optional[float]]
    p_max_bar: float
    quality_status: str


@dataclass
class OptimizationResult:
    """Final optimizer output with the best feasible candidate."""

    best_candidate: OptimizationCandidate
    best_simulation: SimulationResult
    best_constraints: ConstraintReport
    evaluations: List[CandidateEvaluation]

    @property
    def feasible(self) -> bool:
        return self.best_constraints.feasible


class ProcessOptimizer:
    """Random search optimizer built on top of the MVP 0D simulator."""

    def __init__(
        self,
        simulator: Optional[MVP0DSimulator] = None,
        sim_config: Optional[SimulationConfig] = None,
    ) -> None:
        self.simulator = simulator or MVP0DSimulator(config=sim_config)

    def optimize(
        self,
        material,
        base_process: ProcessConditions,
        mold,
        quality: QualityTargets,
        config: Optional[OptimizationConfig] = None,
    ) -> OptimizationResult:
        config = config or OptimizationConfig()
        rng = random.Random(config.random_seed)

        evaluations: List[CandidateEvaluation] = []
        best_idx = None
        best_objective = float("inf")
        best_result: Optional[SimulationResult] = None
        best_candidate: Optional[OptimizationCandidate] = None
        best_constraints: Optional[ConstraintReport] = None

        for _ in range(max(1, config.samples)):
            candidate = self._sample_candidate(rng, config.bounds)
            process_variant = base_process.model_copy(
                update={
                    "T_polyol_in_C": candidate.T_polyol_in_C,
                    "T_iso_in_C": candidate.T_iso_in_C,
                    "T_mold_init_C": candidate.T_mold_init_C,
                }
            )
            sim_result = self.simulator.run(material, process_variant, mold, quality)
            constraints = evaluate_constraints(
                result=sim_result,
                quality=quality,
                candidate_demold_s=candidate.t_demold_s,
                t_cycle_max_s=config.t_cycle_max_s,
            )
            objective = self._objective_value(
                candidate=candidate,
                result=sim_result,
                constraints=constraints,
                prefer_lower_pressure=config.prefer_lower_pressure,
            )
            evaluation = CandidateEvaluation(
                candidate=candidate,
                objective=objective,
                constraints=constraints,
                feasible=constraints.feasible,
                t_demold_window=constraints.demold_window,
                p_max_bar=sim_result.p_max_Pa / 100_000.0,
                quality_status=sim_result.quality_status,
            )
            evaluations.append(evaluation)

            if objective < best_objective:
                best_objective = objective
                best_idx = len(evaluations) - 1
                best_result = sim_result
                best_candidate = candidate
                best_constraints = constraints

        if best_idx is None or best_result is None or best_candidate is None or best_constraints is None:
            raise RuntimeError("Optimizer failed to evaluate any candidates.")

        return OptimizationResult(
            best_candidate=best_candidate,
            best_simulation=best_result,
            best_constraints=best_constraints,
            evaluations=evaluations,
        )

    def _sample_candidate(
        self, rng: random.Random, bounds: OptimizerBounds
    ) -> OptimizationCandidate:
        return OptimizationCandidate(
            T_polyol_in_C=float(rng.uniform(*bounds.T_polyol_C)),
            T_iso_in_C=float(rng.uniform(*bounds.T_iso_C)),
            T_mold_init_C=float(rng.uniform(*bounds.T_mold_C)),
            t_demold_s=float(rng.uniform(*bounds.t_demold_s)),
        )

    @staticmethod
    def _objective_value(
        candidate: OptimizationCandidate,
        result: SimulationResult,
        constraints: ConstraintReport,
        prefer_lower_pressure: bool,
    ) -> float:
        base_value = candidate.t_demold_s
        if prefer_lower_pressure:
            base_value += 0.05 * (result.p_max_Pa / 100_000.0)
        if not constraints.feasible:
            penalty_scale = 1e5 * max(1.0, constraints.penalty)
            return base_value + penalty_scale
        return base_value
