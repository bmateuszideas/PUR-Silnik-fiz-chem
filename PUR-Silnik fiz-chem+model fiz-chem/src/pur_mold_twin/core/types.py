from __future__ import annotations

from typing import Any, List, Optional, Literal, Tuple

from pydantic import BaseModel, Field, validator

from .utils import STANDARD_PRESSURE_PA, clamp

try:  # pint jest opcjonalny; jesli brak, przyjmujemy wartosci numeryczne
    import pint  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    pint = None  # type: ignore

if pint:  # pragma: no branch
    _UREG = pint.UnitRegistry()
    _PINT_QUANTITY = pint.Quantity
else:  # pragma: no cover
    _UREG = None
    _PINT_QUANTITY = tuple()  # type: ignore


def _coerce_quantity(value: Any, unit: str) -> float:
    if _UREG and isinstance(value, _PINT_QUANTITY):
        return float(value.to(unit).magnitude)
    return float(value)


class ProcessConditions(BaseModel):
    m_polyol: float = Field(..., gt=0, description="Mass of polyol [kg]")
    m_iso: float = Field(..., gt=0, description="Mass of isocyanate [kg]")
    m_additives: float = Field(0.0, ge=0, description="Mass of additives [kg]")
    nco_oh_index: float = Field(1.0, gt=0, description="Stoichiometric index")
    T_polyol_in_C: float = Field(23.0, ge=-50.0, description="Polyol inlet temperature [°C]")
    T_iso_in_C: float = Field(23.0, ge=-50.0, description="ISO inlet temperature [°C]")
    T_mold_init_C: float = Field(45.0, ge=-50.0, description="Initial mold temperature [°C]")
    T_ambient_C: float = Field(25.0, ge=-50.0, description="Ambient temperature [°C]")
    RH_ambient: float = Field(0.50, description="Ambient RH (0-1 or percent)")
    mixing_eff: float = Field(1.0, ge=0.0, le=1.0, description="Mixing efficiency 0-1")

    @property
    def total_mass(self) -> float:
        return self.m_polyol + self.m_iso + self.m_additives

    @property
    def rh_fraction(self) -> float:
        value = self.RH_ambient
        return clamp(value, 0.0, 1.0)

    @validator("RH_ambient")
    def _validate_rh(cls, value: float) -> float:
        # Allow either 0-1 fraction or 0-100 percent.
        if value > 1.0:
            value *= 0.01
        if not 0.0 <= value <= 1.0:
            raise ValueError("RH_ambient must be between 0 and 1 (or 0-100%).")
        return value

    @validator("T_polyol_in_C", "T_iso_in_C", "T_mold_init_C", "T_ambient_C", pre=True)
    def _convert_process_temperatures(cls, value: Any) -> float:
        return _coerce_quantity(value, "degC")


class VentProperties(BaseModel):
    count: int = Field(2, ge=0)
    area_per_vent_m2: float = Field(5e-5, gt=0)
    base_conductance_m3_per_sPa: float = Field(5e-7, gt=0)
    alpha_closure: float = Field(0.85, gt=0.0, le=1.0)
    clog_rate: float = Field(2.2, gt=0)
    min_efficiency: float = Field(0.02, ge=0.0, le=1.0)

    @property
    def total_conductance(self) -> float:
        return max(self.count, 0) * self.base_conductance_m3_per_sPa


class MoldProperties(BaseModel):
    cavity_volume_m3: float = Field(..., gt=0)
    mold_surface_area_m2: float = Field(..., gt=0)
    mold_mass_kg: float = Field(..., gt=0)
    cp_mold_J_per_kgK: float = Field(900.0, gt=0)
    h_core_to_mold_W_per_m2K: float = Field(140.0, gt=0)
    h_mold_to_ambient_W_per_m2K: float = Field(40.0, gt=0)
    vent: Optional[VentProperties] = None


class QualityTargets(BaseModel):
    alpha_demold_min: float = Field(0.75, ge=0.0, le=1.0)
    rho_moulded_min: float = Field(35.0, gt=0)
    rho_moulded_max: float = Field(45.0, gt=0)
    core_temp_max_C: float = Field(80.0)
    p_max_allowable_bar: float = Field(5.0, gt=0)
    H_demold_min_shore: float = Field(40.0, gt=0)
    H_24h_min_shore: float = Field(50.0, gt=0)
    defect_risk_max: float = Field(0.10, ge=0.0, le=1.0)

    @validator("rho_moulded_max")
    def _rho_bounds(cls, value: float, values: dict) -> float:
        if "rho_moulded_min" in values and value <= values["rho_moulded_min"]:
            raise ValueError("rho_moulded_max must be greater than rho_moulded_min.")
        return value

    @validator("core_temp_max_C", pre=True)
    def _convert_core_temp(cls, value: Any) -> float:
        return _coerce_quantity(value, "degC")

    @validator("p_max_allowable_bar", pre=True)
    def _convert_pressure_bar(cls, value: Any) -> float:
        return _coerce_quantity(value, "bar")

    @validator("rho_moulded_min", "rho_moulded_max", pre=True)
    def _convert_density(cls, value: Any) -> float:
        return _coerce_quantity(value, "kilogram / meter ** 3")


class SimulationConfig(BaseModel):
    total_time_s: float = Field(600.0, gt=0)
    time_step_s: float = Field(0.5, gt=0)
    reference_temperature_K: float = Field(298.15, gt=0)
    activation_energy_J_per_mol: float = Field(45_000.0, gt=0)
    reaction_order: float = Field(1.6, gt=0)
    reaction_enthalpy_J_per_kg: float = Field(100_000.0)
    foam_cp_J_per_kgK: float = Field(1_600.0, gt=0)
    rh_reference: float = Field(0.45, ge=0.0, lt=1.0)
    surface_moisture_capacity_kg_per_m2: float = Field(0.012, ge=0)
    water_risk_delta_fraction: float = Field(0.004, gt=0)
    ambient_pressure_Pa: float = Field(STANDARD_PRESSURE_PA, gt=0)
    min_headspace_fraction: float = Field(0.4, gt=0.0, lt=1.0)
    pentane_evap_base_rate: float = Field(0.12, ge=0.0)
    pentane_evap_onset_K: float = Field(308.15, gt=0)
    pentane_evap_temp_slope: float = Field(0.08, ge=0.0)
    vent_relief_scale: float = Field(0.6, ge=0.0)
    hardness_base_shore: float = Field(5.0)
    hardness_alpha_gain: float = Field(65.0, ge=0.0)
    hardness_density_gain: float = Field(0.45, ge=0.0)
    hardness_density_ref: float = Field(35.0, gt=0)
    hardness_24h_bonus: float = Field(4.0)
    backend: Literal["manual", "solve_ivp"] = "manual"
    solve_ivp_method: str = "Radau"
    solve_ivp_rtol: float = Field(1e-6, gt=0)
    solve_ivp_atol: float = Field(1e-8, gt=0)

    def steps(self) -> int:
        return int(self.total_time_s / self.time_step_s) + 1

    @validator("total_time_s")
    def _validate_total_time(cls, value: float, values: dict) -> float:
        time_step = values.get("time_step_s")
        if time_step and value <= time_step:
            raise ValueError("total_time_s must be greater than time_step_s.")
        return value

    @validator("reference_temperature_K", "pentane_evap_onset_K", pre=True)
    def _convert_kelvin_fields(cls, value: Any) -> float:
        return _coerce_quantity(value, "kelvin")

    @validator("ambient_pressure_Pa", pre=True)
    def _convert_pressure_pa(cls, value: Any) -> float:
        return _coerce_quantity(value, "pascal")


class SimulationResult(BaseModel):
    time_s: List[float] = Field(default_factory=list)
    alpha: List[float] = Field(default_factory=list)
    T_core_K: List[float] = Field(default_factory=list)
    T_mold_K: List[float] = Field(default_factory=list)
    rho_kg_per_m3: List[float] = Field(default_factory=list)
    fill_ratio: List[float] = Field(default_factory=list)
    n_CO2_mol: List[float] = Field(default_factory=list)
    p_air_Pa: List[float] = Field(default_factory=list)
    p_CO2_Pa: List[float] = Field(default_factory=list)
    p_pentane_Pa: List[float] = Field(default_factory=list)
    p_total_Pa: List[float] = Field(default_factory=list)
    vent_eff: List[float] = Field(default_factory=list)
    hardness_shore: List[float] = Field(default_factory=list)
    t_demold_min_s: Optional[float] = None
    t_demold_max_s: Optional[float] = None
    t_demold_opt_s: Optional[float] = None
    rho_moulded: float = 0.0
    p_max_Pa: float = 0.0
    pressure_status: str = "UNKNOWN"
    vent_closure_time_s: Optional[float] = None
    H_demold_shore: float = 0.0
    H_24h_shore: float = 0.0
    quality_status: str = "UNKNOWN"
    defect_risk: float = 0.0
    diagnostics: List[str] = Field(default_factory=list)
    water_from_polyol_kg: float = 0.0
    water_from_rh_kg: float = 0.0
    water_effective_kg: float = 0.0
    water_eff_fraction: float = 0.0
    water_risk_score: float = 0.0

    def to_dict(self) -> dict:
        return self.model_dump()


class WaterBalance(BaseModel):
    water_from_polyol_kg: float
    water_from_rh_kg: float
    water_eff_kg: float
    water_eff_fraction: float
    water_risk_score: float
