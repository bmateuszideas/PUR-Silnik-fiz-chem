"""
MVP 0D simulator wrapper.

Re-exports Pydantic modele z ``core.types`` i deleguje obliczenia do modułu
``core.simulation`` (manual / solve_ivp).
"""

from __future__ import annotations

from typing import Optional

from ..material_db.models import MaterialSystem
from . import simulation
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
        backend = simulation.get_backend_name(self.config)
        vent_cfg = mold.vent or VentProperties()
        return simulation.simulate(material, process, mold, quality, self.config, backend, vent_cfg)
