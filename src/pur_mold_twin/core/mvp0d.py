"""
MVP 0D simulator wrapper.

The class re-exports Pydantic models from ``core.types`` and delegates
calculations to ``core.simulation`` (manual backend) or ``core.simulation_1d``
to keep orchestration separate from numerical details.
"""

from __future__ import annotations

from typing import Optional

from ..material_db.models import MaterialSystem
from . import ode_backends, simulation, simulation_1d
from .types import (
    MoldProperties,
    ProcessConditions,
    QualityTargets,
    SimulationConfig,
    SimulationResult,
    VentProperties,
    WaterBalance,
)

__all__ = [
    "ProcessConditions",
    "MoldProperties",
    "VentProperties",
    "QualityTargets",
    "SimulationConfig",
    "SimulationResult",
    "WaterBalance",
    "MVP0DSimulator",
]


class MVP0DSimulator:
    """High-level wrapper selecting between manual and solve_ivp backends."""

    def __init__(self, config: Optional[SimulationConfig] = None) -> None:
        self.config = config or SimulationConfig()
        # Backwards-compat: expose the core simulation module on the simulator
        # instance so older tests and callers can use `simulator.core_simulation`.
        self.core_simulation = simulation

    def run(
        self,
        material: MaterialSystem,
        process: ProcessConditions,
        mold: MoldProperties,
        quality: Optional[QualityTargets] = None,
    ) -> SimulationResult:
        if process.total_mass <= 0:
            raise ValueError("Total shot mass must be > 0 kg.")
        if mold.cavity_volume_m3 <= 0:
            raise ValueError("Mold cavity volume must be > 0 m^3.")

        quality = quality or QualityTargets()
        backend = ode_backends.get_backend_name(self.config)
        vent_cfg = mold.vent or VentProperties()
        if self.config.dimension == "1d_experimental":
            ctx = simulation.prepare_context(material, process, mold, quality, self.config, vent_cfg)
            trajectory = simulation_1d.run_1d_simulation(ctx)
            return simulation.assemble_result(ctx, trajectory)
        return simulation.simulate(material, process, mold, quality, self.config, backend, vent_cfg)
