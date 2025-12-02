from __future__ import annotations

from typing import TYPE_CHECKING

from .utils import LIQUID_WATER_DENSITY_KG_PER_M3, clamp, celsius_to_kelvin

if TYPE_CHECKING:  # pragma: no cover
    from ..material_db.models import MaterialSystem
    from .types import MoldProperties, ProcessConditions, SimulationConfig


def initial_core_temperature(process: "ProcessConditions") -> float:
    mix_mass = process.m_polyol + process.m_iso
    if mix_mass <= 0:
        return celsius_to_kelvin((process.T_polyol_in_C + process.T_iso_in_C) * 0.5)
    weighted = (
        process.m_polyol * celsius_to_kelvin(process.T_polyol_in_C)
        + process.m_iso * celsius_to_kelvin(process.T_iso_in_C)
    ) / mix_mass
    return weighted


def liquid_volume(material: "MaterialSystem", process: "ProcessConditions") -> float:
    vol_polyol = process.m_polyol / max(material.polyol.density_kg_per_m3, 1e-6)
    vol_iso = process.m_iso / max(material.isocyanate.density_kg_per_m3, 1e-6)
    vol_additives = process.m_additives / max(material.polyol.density_kg_per_m3, 1e-6)
    return vol_polyol + vol_iso + vol_additives


def initial_density(
    material: "MaterialSystem",
    process: "ProcessConditions",
    extra_mass: float = 0.0,
    extra_volume: float = 0.0,
) -> float:
    mass_total = process.total_mass + extra_mass
    volume = liquid_volume(material, process) + extra_volume
    return mass_total / max(volume, 1e-6)


def compute_water_balance(
    material: "MaterialSystem",
    process: "ProcessConditions",
    mold: "MoldProperties",
    config: "SimulationConfig",
):
    from .types import WaterBalance  # local import to avoid circular dependency

    base_water = process.m_polyol * material.polyol.water_fraction
    rh_fraction = process.rh_fraction

    if rh_fraction <= config.rh_reference:
        rh_mass = 0.0
    else:
        saturation = (rh_fraction - config.rh_reference) / max(1e-6, 1.0 - config.rh_reference)
        saturation = clamp(saturation, 0.0, 1.0)
        rh_mass = (
            config.surface_moisture_capacity_kg_per_m2
            * mold.mold_surface_area_m2
            * saturation
        )

    water_eff = max(base_water + rh_mass, 0.0)
    eff_fraction = water_eff / max(process.m_polyol, 1e-9)
    base_fraction = base_water / max(process.m_polyol, 1e-9)
    delta_fraction = max(0.0, eff_fraction - base_fraction)
    risk = clamp(
        delta_fraction / max(config.water_risk_delta_fraction, 1e-9),
        0.0,
        1.0,
    )
    return WaterBalance(
        water_from_polyol_kg=base_water,
        water_from_rh_kg=rh_mass,
        water_eff_kg=water_eff,
        water_eff_fraction=eff_fraction,
        water_risk_score=risk,
    )


def extra_water_volume_km(water_from_rh_kg: float) -> float:
    if water_from_rh_kg <= 0:
        return 0.0
    return water_from_rh_kg / LIQUID_WATER_DENSITY_KG_PER_M3
