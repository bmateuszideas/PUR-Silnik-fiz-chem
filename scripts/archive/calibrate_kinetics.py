"""
Calibrate Arrhenius/empirical kinetics parameters using TDS times.

Usage:
    python scripts/calibrate_kinetics.py --config configs/scenarios/use_case_1.yaml --cream 15 --gel 60 --rise 110

This script is intentionally minimal: it tweaks SimulationConfig fields
(`reaction_order`, `activation_energy`, `reference_temperature_K`) to match
target cream/gel/rise times by minimizing absolute errors via least_squares.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

from pur_mold_twin.calibration.cost import CalibrationTargets, aggregate_cost
from pur_mold_twin.calibration.fit import fit_parameters
from pur_mold_twin.configs import load_process_scenario
from pur_mold_twin.core import MVP0DSimulator, SimulationConfig
from pur_mold_twin.material_db.loader import load_material_catalog


def _simulate_with_params(base_sim: SimulationConfig, params: Dict[str, float], scenario) -> dict:
    sim_cfg = base_sim.model_copy(update=params)
    sim = MVP0DSimulator(sim_cfg)
    result = sim.run(
        scenario.system,
        scenario.process,
        scenario.mold,
        scenario.quality,
    )
    return result.to_dict()


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate kinetics parameters to TDS times.")
    parser.add_argument("--config", required=True, type=Path, help="Scenario YAML (system/process/mold/quality).")
    parser.add_argument("--systems", type=Path, default=Path("configs/systems/jr_purtec_catalog.yaml"))
    parser.add_argument("--cream", type=float, help="Target cream time [s]")
    parser.add_argument("--gel", type=float, help="Target gel time [s]")
    parser.add_argument("--rise", type=float, help="Target rise time [s]")
    args = parser.parse_args()

    scenario = load_process_scenario(args.config)
    systems = load_material_catalog(args.systems)
    scenario.system = systems[scenario.system_id]  # attach material system for convenience

    base_sim_cfg = scenario.simulation
    targets = CalibrationTargets(
        t_cream_s=args.cream,
        t_gel_s=args.gel,
        t_rise_s=args.rise,
    )

    init_params = {
        "reaction_order": base_sim_cfg.reaction_order,
        "activation_energy_J_per_mol": base_sim_cfg.activation_energy_J_per_mol,
        "reference_temperature_K": base_sim_cfg.reference_temperature_K,
    }

    def simulate_fn(params: Dict[str, float]) -> dict:
        return _simulate_with_params(base_sim_cfg, params, scenario)

    result = fit_parameters(init_params, simulate_fn, targets)
    print("Success:", result.success, "-", result.message)
    print("Best params:")
    for k, v in result.params.items():
        print(f"  {k}: {v}")
    print("Cost breakdown:", result.breakdown)


if __name__ == "__main__":
    main()
