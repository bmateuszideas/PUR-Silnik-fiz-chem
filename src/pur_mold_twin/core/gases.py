from __future__ import annotations

from typing import TYPE_CHECKING

from .utils import (
    GAS_CONSTANT,
    MOLAR_MASS_PENTANE,
    STANDARD_PRESSURE_PA,
    clamp,
)

if TYPE_CHECKING:  # pragma: no cover
    from .types import MoldProperties, SimulationConfig, VentProperties


def initial_pentane_moles(material, process) -> float:
    pentane_mass = process.m_polyol * material.polyol.pentane_fraction
    return max(pentane_mass, 0.0) / MOLAR_MASS_PENTANE


def initial_air_moles(cavity_volume: float, foam_volume: float, temperature_K: float, config: "SimulationConfig") -> float:
    headspace = headspace_volume(config, cavity_volume, foam_volume)
    temp = max(temperature_K, 250.0)
    return config.ambient_pressure_Pa * headspace / (GAS_CONSTANT * temp)


def headspace_volume(config: "SimulationConfig", cavity_volume: float, foam_volume: float) -> float:
    min_headspace = config.min_headspace_fraction * cavity_volume
    return max(cavity_volume - foam_volume, max(min_headspace, 1e-6))


def compute_pressures(n_air: float, n_co2: float, n_pentane: float, temperature_K: float, headspace_volume: float) -> tuple[float, float, float, float]:
    temp = max(temperature_K, 250.0)
    volume = max(headspace_volume, 1e-9)
    p_air = n_air * GAS_CONSTANT * temp / volume
    p_co2 = n_co2 * GAS_CONSTANT * temp / volume
    p_pentane = n_pentane * GAS_CONSTANT * temp / volume
    return p_air, p_co2, p_pentane, p_air + p_co2 + p_pentane


def vent_effectiveness(alpha: float, fill_ratio: float, vent: "VentProperties", config: "SimulationConfig") -> float:
    alpha_term = max(
        0.0,
        1.0 - (alpha / max(vent.alpha_closure, 1e-3)) ** vent.clog_rate,
    )
    fill_penalty = 1.0 / (
        1.0 + max(0.0, fill_ratio - 1.0) * config.vent_relief_scale
    )
    efficiency = max(vent.min_efficiency, alpha_term * fill_penalty)
    return clamp(efficiency, vent.min_efficiency, 1.0)


def pentane_evap_rate(temperature_K: float, config: "SimulationConfig") -> float:
    if temperature_K <= config.pentane_evap_onset_K:
        return 0.0
    delta = temperature_K - config.pentane_evap_onset_K
    return config.pentane_evap_base_rate * (1.0 - pow(2.718281828459045, -config.pentane_evap_temp_slope * delta))


def pressure_status(p_max_Pa: float, p_max_allowable_bar: float) -> str:
    limit_Pa = p_max_allowable_bar * 100_000.0
    if limit_Pa <= 0:
        return "UNKNOWN"
    ratio = p_max_Pa / limit_Pa
    if ratio < 0.9:
        return "SAFE"
    if ratio <= 1.0:
        return "NEAR_LIMIT"
    return "OVER_LIMIT"
