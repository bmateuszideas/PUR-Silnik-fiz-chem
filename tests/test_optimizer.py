"""
Tests for ProcessOptimizer and constraint evaluation.
"""

from __future__ import annotations

from pathlib import Path

from pur_mold_twin import (
    MVP0DSimulator,
    OptimizationConfig,
    OptimizationResult,
    OptimizerBounds,
    ProcessOptimizer,
    QualityTargets,
)
from pur_mold_twin.configs import load_process_scenario
from pur_mold_twin.material_db.loader import load_material_catalog
from pur_mold_twin.optimizer.search import OptimizationCandidate
from pur_mold_twin.optimizer.constraints import ConstraintReport, evaluate_constraints


CATALOG = Path("configs/systems/jr_purtec_catalog.yaml")
SCENARIO = Path("configs/scenarios/use_case_1.yaml")


def _scenario_bundle():
    scenario = load_process_scenario(SCENARIO)
    systems = load_material_catalog(CATALOG)
    return scenario, systems[scenario.system_id]


def test_optimizer_regression_case():
    scenario, system = _scenario_bundle()
    optimizer = ProcessOptimizer(MVP0DSimulator(scenario.simulation))
    base_process = scenario.process
    config = OptimizationConfig(samples=3, random_seed=1)
    result = optimizer.optimize(system, base_process, scenario.mold, scenario.quality, config)

    assert result.best_simulation.quality_status in {"OK", "MARGINAL", "FAIL"}
    # Regression: ensure we don't regress to zero/NaN outputs
    assert result.best_simulation.p_max_Pa > 0
    assert result.best_simulation.rho_moulded > 0


def test_process_optimizer_returns_feasible_candidate() -> None:
    scenario, system = _scenario_bundle()
    optimizer = ProcessOptimizer(MVP0DSimulator(scenario.simulation))
    base_process = scenario.process
    bounds = OptimizerBounds(
        T_polyol_C=(base_process.T_polyol_in_C - 0.1, base_process.T_polyol_in_C + 0.1),
        T_iso_C=(base_process.T_iso_in_C - 0.1, base_process.T_iso_in_C + 0.1),
        T_mold_C=(base_process.T_mold_init_C - 0.1, base_process.T_mold_init_C + 0.1),
        t_demold_s=(280.0, 360.0),
    )
    config = OptimizationConfig(
        samples=3,
        random_seed=123,
        bounds=bounds,
    )
    result: OptimizationResult = optimizer.optimize(
        system,
        base_process,
        scenario.mold,
        scenario.quality,
        config,
    )

    assert len(result.evaluations) == config.samples
    assert result.best_simulation.time_s
    assert isinstance(result.best_candidate.T_polyol_in_C, float)


def test_constraints_detect_overtime_demold() -> None:
    scenario, system = _scenario_bundle()
    simulator = MVP0DSimulator(scenario.simulation)
    relaxed_quality = QualityTargets(
        alpha_demold_min=scenario.quality.alpha_demold_min - 0.05,
        rho_moulded_min=scenario.quality.rho_moulded_min - 10,
        rho_moulded_max=scenario.quality.rho_moulded_max + 10,
        p_max_allowable_bar=scenario.quality.p_max_allowable_bar + 2.0,
        core_temp_max_C=scenario.quality.core_temp_max_C + 10.0,
    )
    result = simulator.run(system, scenario.process, scenario.mold, relaxed_quality)

    constraints = evaluate_constraints(
        result=result,
        quality=relaxed_quality,
        candidate_demold_s=result.time_s[-1] + 100.0,  # beyond horizon + cycle limit
        t_cycle_max_s=600.0,
    )

    assert not constraints.feasible
    assert any("exceeds cycle limit" in msg or "beyond simulated horizon" in msg for msg in constraints.violations)


def test_objective_penalizes_pressure_when_preferred() -> None:
    scenario, system = _scenario_bundle()
    optimizer = ProcessOptimizer(MVP0DSimulator(scenario.simulation))
    relaxed_quality = scenario.quality.model_copy(
        update={"p_max_allowable_bar": 10.0, "defect_risk_max": 1.0}
    )

    low_pressure_result = optimizer.simulator.run(
        system, scenario.process, scenario.mold, relaxed_quality
    )
    high_pressure_process = scenario.process.model_copy(update={"RH_ambient": 1.0})
    high_pressure_result = optimizer.simulator.run(
        system, high_pressure_process, scenario.mold, relaxed_quality
    )

    assert high_pressure_result.p_max_Pa > low_pressure_result.p_max_Pa

    candidate_time = (
        low_pressure_result.t_demold_opt_s
        or low_pressure_result.t_demold_min_s
        or 300.0
    )
    dummy_constraints = ConstraintReport(
        feasible=True,
        violations=[],
        penalty=0.0,
        window_ok=True,
        demold_time_s=candidate_time,
        demold_window=(candidate_time - 5.0, candidate_time + 5.0),
    )

    base_candidate = OptimizationCandidate(
        T_polyol_in_C=high_pressure_process.T_polyol_in_C,
        T_iso_in_C=high_pressure_process.T_iso_in_C,
        T_mold_init_C=high_pressure_process.T_mold_init_C,
        t_demold_s=candidate_time,
    )

    low_objective = optimizer._objective_value(
        candidate=base_candidate,
        result=low_pressure_result,
        constraints=dummy_constraints,
        prefer_lower_pressure=True,
    )
    high_objective = optimizer._objective_value(
        candidate=base_candidate,
        result=high_pressure_result,
        constraints=dummy_constraints,
        prefer_lower_pressure=True,
    )

    assert high_objective > low_objective

    no_pressure_bias = optimizer._objective_value(
        candidate=base_candidate,
        result=high_pressure_result,
        constraints=dummy_constraints,
        prefer_lower_pressure=False,
    )
    assert no_pressure_bias == optimizer._objective_value(
        candidate=base_candidate,
        result=low_pressure_result,
        constraints=dummy_constraints,
        prefer_lower_pressure=False,
    )
