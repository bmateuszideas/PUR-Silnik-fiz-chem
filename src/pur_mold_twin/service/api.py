from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..core import MVP0DSimulator, ProcessConditions, MoldProperties, QualityTargets, SimulationConfig
from ..material_db.loader import load_material_catalog
from ..material_db.models import MaterialSystem
from ..optimizer import OptimizationConfig, OptimizerBounds, ProcessOptimizer
from ..logging.features import compute_basic_features
from ..ml.inference import attach_ml_predictions


@dataclass
class APIConfig:
    systems_catalog_path: Optional[str] = "configs/systems/jr_purtec_catalog.yaml"


class APIService:
    """Service wrapper turning JSON-like payloads into domain calls."""

    def __init__(self, config: Optional[APIConfig] = None) -> None:
        self.config = config or APIConfig()
        self._systems: Optional[dict[str, MaterialSystem]] = None

    def _load_systems(self) -> dict[str, MaterialSystem]:
        if self._systems is None:
            if not self.config.systems_catalog_path:
                raise RuntimeError("systems_catalog_path is not configured")
            self._systems = load_material_catalog(self.config.systems_catalog_path)
        return self._systems

    def _resolve_system(self, payload: Dict[str, Any]) -> MaterialSystem:
        if "system" in payload and isinstance(payload["system"], dict):
            return MaterialSystem(**payload["system"])
        system_id = payload.get("system_id")
        if not system_id:
            raise ValueError("Either 'system' or 'system_id' field must be provided.")
        systems = self._load_systems()
        if system_id not in systems:
            raise ValueError(f"Unknown system_id '{system_id}'")
        return systems[system_id]

    def simulate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Run a simulation from a JSON-like payload."""

        system = self._resolve_system(payload)
        process = ProcessConditions(**payload["process"])
        mold = MoldProperties(**payload["mold"])
        quality = QualityTargets(**payload.get("quality", {})) if payload.get("quality") else QualityTargets()
        sim_cfg = SimulationConfig(**payload.get("simulation", {})) if payload.get("simulation") else SimulationConfig()

        simulator = MVP0DSimulator(sim_cfg)
        result = simulator.run(system, process, mold, quality)
        result_dict = result.to_dict()

        # Optional ML predictions (best-effort)
        try:
            features_df = compute_basic_features(
                result_dict,
                measured=None,
                qc=None,
                process={
                    "T_polyol_in_C": process.T_polyol_in_C,
                    "T_iso_in_C": process.T_iso_in_C,
                    "T_mold_init_C": process.T_mold_init_C,
                    "T_ambient_C": process.T_ambient_C,
                    "RH_ambient": process.RH_ambient,
                    "mixing_eff": process.mixing_eff,
                },
            )
            features_row = dict(features_df.iloc[0])
            result_dict = attach_ml_predictions(result_dict, features_row)
        except Exception:
            pass

        return result_dict

    def optimize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Run process optimization from a JSON-like payload."""

        system = self._resolve_system(payload)
        process = ProcessConditions(**payload["process"])
        mold = MoldProperties(**payload["mold"])
        quality = QualityTargets(**payload.get("quality", {})) if payload.get("quality") else QualityTargets()

        opt_cfg = payload.get("optimizer_config") or {}
        bounds = opt_cfg.pop("bounds", {}) if isinstance(opt_cfg, dict) else {}
        bounds_model = OptimizerBounds(**bounds) if bounds else OptimizerBounds()
        opt_config = OptimizationConfig(bounds=bounds_model, **opt_cfg)

        optimizer = ProcessOptimizer()
        result = optimizer.optimize(system, process, mold, quality, opt_config)
        baseline = result.baseline
        optimized = result.best_constraints

        def _metrics(constraints) -> dict:
            if constraints is None:
                return {}
            return {
                "quality_status": constraints.quality_status,
                "pressure_status": constraints.pressure_status,
                "t_demold_opt_s": constraints.t_demold_opt_s,
                "p_max_bar": constraints.p_max_bar,
                "rho_moulded": constraints.rho_moulded,
                "H_demold_shore": constraints.H_demold_shore,
                "defect_risk": constraints.defect_risk,
            }

        return {
            "baseline": _metrics(baseline),
            "optimized": _metrics(optimized),
            "candidate": result.best_candidate.model_dump() if result.best_candidate else None,
        }

