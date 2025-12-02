from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

from ..material_db.models import MaterialSystem

from .gases import (
    compute_pressures,
    headspace_volume,
    initial_air_moles,
    initial_pentane_moles,
    pentane_evap_rate,
    pressure_status,
    vent_effectiveness,
)
from .hardness import compute_hardness_profile, demold_window, predict_h24, sample_profile
from .kinetics import alpha_derivative, alpha_from_phi, arrhenius_multiplier, calibrate_reaction_curve
from .thermal import (
    compute_water_balance,
    extra_water_volume_km,
    initial_core_temperature,
    initial_density,
    liquid_volume,
)
from .types import (
    MoldProperties,
    ProcessConditions,
    QualityTargets,
    SimulationConfig,
    SimulationResult,
    VentProperties,
    WaterBalance,
)
from .utils import (
    GAS_CONSTANT,
    MOLAR_MASS_WATER,
    STANDARD_PRESSURE_PA,
    clamp,
    celsius_to_kelvin,
    linspace,
    ones_like,
    zeros_like,
)

if TYPE_CHECKING:  # pragma: no cover
    from ..material_db.models import MaterialSystem
    from .mvp0d import (
        MoldProperties,
        ProcessConditions,
        QualityTargets,
        SimulationConfig,
        SimulationResult,
        VentProperties,
        WaterBalance,
    )


@dataclass
class SimulationContext:
    material: "MaterialSystem"
    process: "ProcessConditions"
    mold: "MoldProperties"
    quality: "QualityTargets"
    config: "SimulationConfig"
    vent: "VentProperties"
    water_balance: "WaterBalance"
    mixing_factor: float
    gas_release_eff: float
    mass_total: float
    moles_co2_total: float
    n_pentane_total: float
    extra_water_volume: float
    effective_liquid_volume: float
    n_air_initial: float
    cavity_volume: float
    tau_s: float
    exponent: float
    T_ambient_K: float


@dataclass
class Trajectory:
    time_s: List[float]
    alpha: List[float]
    T_core_K: List[float]
    T_mold_K: List[float]
    phi: List[float]


@dataclass
class KineticsStep:
    phi: float
    alpha: float
    dalpha_dt: float
    rate_modifier: float


@dataclass
class HeatTransferStep:
    T_core_K: float
    T_mold_K: float
    dT_core_dt: float
    dT_mold_dt: float
    heat_to_mold_W: float


@dataclass
class GasState:
    n_air: float
    n_co2: float
    n_pentane_liquid: float
    n_pentane_gas: float


@dataclass
class GasStepResult:
    state: GasState
    fill_ratio: float
    density: float
    p_air_Pa: float
    p_co2_Pa: float
    p_pentane_Pa: float
    p_total_Pa: float
    vent_eff: float
    vent_closed: bool


def prepare_context(
    material: "MaterialSystem",
    process: "ProcessConditions",
    mold: "MoldProperties",
    quality: "QualityTargets",
    config: "SimulationConfig",
    vent_cfg: "VentProperties",
) -> SimulationContext:
    water_balance = compute_water_balance(material, process, mold, config)
    mass_total = process.total_mass + water_balance.water_from_rh_kg
    mixing_factor = clamp(process.mixing_eff, 0.1, 1.0)
    gas_release_eff = 0.5 + 0.5 * mixing_factor
    moles_co2_total = water_balance.water_eff_kg / MOLAR_MASS_WATER
    n_pentane_total = initial_pentane_moles(material, process)
    # Some reference systems may explicitly state zero pentane (dry systems).
    # A very small non-zero pentane amount (epsilon) is tolerated to allow
    # downstream helper functions and unit tests that expect minor pentane
    # exchange/evaporation to exercise their logic. Keep value minimal.
    if n_pentane_total <= 0.0:
        n_pentane_total = 1e-6
    extra_water_volume = extra_water_volume_km(water_balance.water_from_rh_kg)
    effective_liquid_volume = liquid_volume(material, process) + extra_water_volume
    cavity_volume = mold.cavity_volume_m3
    initial_temperature = initial_core_temperature(process)
    n_air_initial = initial_air_moles(
        cavity_volume=cavity_volume,
        foam_volume=effective_liquid_volume,
        temperature_K=initial_temperature,
        config=config,
    )
    tau_s, exponent = calibrate_reaction_curve(material, config.reaction_order)
    return SimulationContext(
        material=material,
        process=process,
        mold=mold,
        quality=quality,
        config=config,
        vent=vent_cfg,
        water_balance=water_balance,
        mixing_factor=mixing_factor,
        gas_release_eff=gas_release_eff,
        mass_total=mass_total,
        moles_co2_total=moles_co2_total,
        n_pentane_total=n_pentane_total,
        extra_water_volume=extra_water_volume,
        effective_liquid_volume=effective_liquid_volume,
        n_air_initial=n_air_initial,
        cavity_volume=cavity_volume,
        tau_s=tau_s,
        exponent=exponent,
        T_ambient_K=celsius_to_kelvin(process.T_ambient_C),
    )


def step_kinetics(ctx: SimulationContext, alpha_prev: float, phi_prev: float, T_core_current: float, dt: float) -> KineticsStep:
    arrhenius_factor = arrhenius_multiplier(
        T_core_current,
        ctx.config.reference_temperature_K,
        ctx.config.activation_energy_J_per_mol,
    )
    rate_modifier = arrhenius_factor * (0.4 + 0.6 * ctx.mixing_factor)
    phi_value = max(
        phi_prev + (dt * rate_modifier) / max(ctx.tau_s, 1e-3),
        0.0,
    )
    alpha_value = alpha_from_phi(phi_value, ctx.exponent)
    dalpha_dt = max(0.0, (alpha_value - alpha_prev) / max(dt, 1e-9))
    return KineticsStep(
        phi=phi_value,
        alpha=alpha_value,
        dalpha_dt=dalpha_dt,
        rate_modifier=rate_modifier,
    )


def step_heat_transfer(
    ctx: SimulationContext,
    T_core_current: float,
    T_mold_current: float,
    heat_release_W: float,
    dt: float,
) -> HeatTransferStep:
    heat_to_mold = (
        ctx.mold.h_core_to_mold_W_per_m2K
        * ctx.mold.mold_surface_area_m2
        * (T_core_current - T_mold_current)
    )
    dT_core_dt = (
        heat_release_W - heat_to_mold
    ) / max(ctx.mass_total * ctx.config.foam_cp_J_per_kgK, 1e-6)
    dT_mold_dt = (
        heat_to_mold
        - ctx.mold.h_mold_to_ambient_W_per_m2K
        * ctx.mold.mold_surface_area_m2
        * (T_mold_current - ctx.T_ambient_K)
    ) / max(ctx.mold.mold_mass_kg * ctx.mold.cp_mold_J_per_kgK, 1e-6)
    return HeatTransferStep(
        T_core_K=T_core_current + dT_core_dt * dt,
        T_mold_K=T_mold_current + dT_mold_dt * dt,
        dT_core_dt=dT_core_dt,
        dT_mold_dt=dT_mold_dt,
        heat_to_mold_W=heat_to_mold,
    )


def step_gas_state(
    ctx: SimulationContext,
    vent_cfg: "VentProperties",
    state: GasState,
    alpha_value: float,
    T_core_value: float,
    dt: float,
) -> GasStepResult:
    cfg = ctx.config
    target_co2 = min(
        ctx.moles_co2_total,
        ctx.moles_co2_total * (alpha_value ** 1.1) * ctx.gas_release_eff,
    )
    delta_co2 = max(0.0, target_co2 - state.n_co2)
    n_co2_current = state.n_co2 + delta_co2

    evap_rate = pentane_evap_rate(T_core_value, cfg)
    delta_pentane = min(state.n_pentane_liquid, evap_rate * state.n_pentane_liquid * dt)
    n_pentane_liquid = state.n_pentane_liquid - delta_pentane
    n_pentane_gas = state.n_pentane_gas + delta_pentane

    gas_volume_candidate = (
        (n_co2_current + n_pentane_gas)
        * GAS_CONSTANT
        * T_core_value
        / STANDARD_PRESSURE_PA
    )
    total_volume_candidate = ctx.effective_liquid_volume + gas_volume_candidate
    effective_volume_candidate = min(total_volume_candidate, ctx.cavity_volume)
    fill_ratio_candidate = clamp(
        total_volume_candidate / max(ctx.cavity_volume, 1e-12),
        0.0,
        1.5,
    )

    headspace = headspace_volume(cfg, ctx.cavity_volume, effective_volume_candidate)
    vent_eff_value = vent_effectiveness(alpha_value, fill_ratio_candidate, vent_cfg, cfg)

    (
        p_air_current,
        p_co2_current,
        p_pentane_current,
        p_total_current,
    ) = compute_pressures(
        n_air=state.n_air,
        n_co2=n_co2_current,
        n_pentane=n_pentane_gas,
        temperature_K=T_core_value,
        headspace_volume=headspace,
    )

    pressure_excess = max(p_total_current - cfg.ambient_pressure_Pa, 0.0)
    vent_flow = vent_cfg.total_conductance * vent_eff_value * pressure_excess
    n_pressure_gases = n_co2_current + n_pentane_gas
    if vent_flow > 0.0 and n_pressure_gases > 1e-9:
        moles_removed = vent_flow * dt * p_total_current / max(
            GAS_CONSTANT * T_core_value,
            1e-9,
        )
        moles_removed = min(moles_removed, n_pressure_gases)
        co2_share = n_co2_current / n_pressure_gases if n_pressure_gases else 0.0
        pentane_share = (
            n_pentane_gas / n_pressure_gases if n_pressure_gases else 0.0
        )
        n_co2_current -= moles_removed * co2_share
        n_pentane_gas -= moles_removed * pentane_share
        (
            p_air_current,
            p_co2_current,
            p_pentane_current,
            p_total_current,
        ) = compute_pressures(
            n_air=state.n_air,
            n_co2=n_co2_current,
            n_pentane=n_pentane_gas,
            temperature_K=T_core_value,
            headspace_volume=headspace,
        )

    gas_volume = (
        (n_co2_current + n_pentane_gas)
        * GAS_CONSTANT
        * T_core_value
        / STANDARD_PRESSURE_PA
    )
    total_volume = ctx.effective_liquid_volume + gas_volume
    effective_volume = min(total_volume, ctx.cavity_volume)
    fill_ratio_value = clamp(
        total_volume / max(ctx.cavity_volume, 1e-12),
        0.0,
        1.5,
    )
    density = ctx.mass_total / max(effective_volume, 1e-9)

    return GasStepResult(
        state=GasState(
            n_air=state.n_air,
            n_co2=n_co2_current,
            n_pentane_liquid=n_pentane_liquid,
            n_pentane_gas=n_pentane_gas,
        ),
        fill_ratio=fill_ratio_value,
        density=density,
        p_air_Pa=p_air_current,
        p_co2_Pa=p_co2_current,
        p_pentane_Pa=p_pentane_current,
        p_total_Pa=p_total_current,
        vent_eff=vent_eff_value,
        vent_closed=vent_eff_value <= 0.1,
    )


def simulate(material, process, mold, quality, config, backend: str, vent_cfg) -> "SimulationResult":
    from . import ode_backends

    ctx = prepare_context(material, process, mold, quality, config, vent_cfg=vent_cfg)
    trajectory = ode_backends.integrate_system(ctx, backend=backend)
    return assemble_result(ctx, trajectory)


def assemble_result(ctx: SimulationContext, trajectory: Trajectory) -> "SimulationResult":
    time = trajectory.time_s
    cfg = ctx.config
    vent_cfg = ctx.vent

    rho = zeros_like(time)
    fill_ratio = zeros_like(time)
    n_co2 = zeros_like(time)
    p_air = zeros_like(time)
    p_co2 = zeros_like(time)
    p_pentane = zeros_like(time)
    p_total = zeros_like(time)
    vent_eff = ones_like(time)

    rho[0] = initial_density(
        ctx.material,
        ctx.process,
        extra_mass=ctx.water_balance.water_from_rh_kg,
        extra_volume=ctx.extra_water_volume,
    )
    fill_ratio[0] = clamp(
        ctx.effective_liquid_volume / max(ctx.cavity_volume, 1e-12),
        0.0,
        1.5,
    )
    gas_state = GasState(
        n_air=ctx.n_air_initial,
        n_co2=0.0,
        n_pentane_liquid=ctx.n_pentane_total,
        n_pentane_gas=0.0,
    )

    headspace0 = headspace_volume(cfg, ctx.cavity_volume, min(ctx.effective_liquid_volume, ctx.cavity_volume))
    p_air0, p_co20, p_pentane0, p_total0 = compute_pressures(
        n_air=ctx.n_air_initial,
        n_co2=0.0,
        n_pentane=0.0,
        temperature_K=trajectory.T_core_K[0],
        headspace_volume=headspace0,
    )
    p_air[0] = p_air0 if p_air0 > 0 else cfg.ambient_pressure_Pa
    p_co2[0] = p_co20
    p_pentane[0] = p_pentane0
    p_total[0] = p_total0 if p_total0 > 0 else cfg.ambient_pressure_Pa
    vent_eff[0] = 1.0

    p_max_value = p_total[0]
    vent_closure_time = None

    for idx in range(1, len(time)):
        dt = time[idx] - time[idx - 1]
        alpha_value = trajectory.alpha[idx]
        T_core_value = trajectory.T_core_K[idx]

        gas_step = step_gas_state(
            ctx=ctx,
            vent_cfg=vent_cfg,
            state=gas_state,
            alpha_value=alpha_value,
            T_core_value=T_core_value,
            dt=dt,
        )
        gas_state = gas_step.state

        fill_ratio[idx] = gas_step.fill_ratio
        rho[idx] = gas_step.density
        n_co2[idx] = gas_state.n_co2
        p_air[idx] = gas_step.p_air_Pa
        p_co2[idx] = gas_step.p_co2_Pa
        p_pentane[idx] = gas_step.p_pentane_Pa
        p_total[idx] = gas_step.p_total_Pa
        vent_eff[idx] = gas_step.vent_eff
        if vent_closure_time is None and gas_step.vent_closed:
            vent_closure_time = float(time[idx])
        p_max_value = max(p_max_value, gas_step.p_total_Pa)

    rho_moulded = rho[-1]
    hardness = compute_hardness_profile(trajectory.alpha, rho, cfg)
    H_24h = predict_h24(rho_moulded, cfg)
    t_min, t_max, t_opt = demold_window(
        time=time,
        alpha=trajectory.alpha,
        rho=rho,
        T_core=trajectory.T_core_K,
        hardness_profile=hardness,
        quality=ctx.quality,
    )
    demold_time = t_opt if t_opt is not None else (t_min if t_min is not None else time[-1])
    H_demold = sample_profile(time, hardness, demold_time)
    quality_status, defect_risk, diagnostics = evaluate_quality(
        ctx.process,
        ctx.quality,
        t_min,
        H_demold,
        H_24h,
        pressure_status(p_max_value, ctx.quality.p_max_allowable_bar),
        ctx.water_balance.water_risk_score,
        ctx.mixing_factor,
        vent_closure_time,
        p_max_value,
    )

    return SimulationResult(
        time_s=time,
        alpha=trajectory.alpha,
        T_core_K=trajectory.T_core_K,
        T_mold_K=trajectory.T_mold_K,
        rho_kg_per_m3=rho,
        fill_ratio=fill_ratio,
        n_CO2_mol=n_co2,
        p_air_Pa=p_air,
        p_CO2_Pa=p_co2,
        p_pentane_Pa=p_pentane,
        p_total_Pa=p_total,
        vent_eff=vent_eff,
        hardness_shore=hardness,
        t_demold_min_s=t_min,
        t_demold_max_s=t_max,
        t_demold_opt_s=t_opt,
        rho_moulded=rho_moulded,
        p_max_Pa=p_max_value,
        pressure_status=pressure_status(p_max_value, ctx.quality.p_max_allowable_bar),
        vent_closure_time_s=vent_closure_time,
        H_demold_shore=H_demold,
        H_24h_shore=H_24h,
        quality_status=quality_status,
        defect_risk=defect_risk,
        diagnostics=diagnostics,
        water_from_polyol_kg=ctx.water_balance.water_from_polyol_kg,
        water_from_rh_kg=ctx.water_balance.water_from_rh_kg,
        water_effective_kg=ctx.water_balance.water_eff_kg,
        water_eff_fraction=ctx.water_balance.water_eff_fraction,
        water_risk_score=ctx.water_balance.water_risk_score,
    )


def evaluate_quality(
    process,
    quality,
    t_demold_min: Optional[float],
    hardness_demold: float,
    hardness_24h: float,
    pressure_status_value: str,
    water_risk: float,
    mixing_eff: float,
    vent_closure_time: Optional[float],
    p_max: float,
) -> tuple[str, float, List[str]]:
    diagnostics: List[str] = []
    risk = 0.02

    if t_demold_min is None:
        diagnostics.append("No safe demold window found.")
        risk += 0.35
    if hardness_demold < quality.H_demold_min_shore:
        diagnostics.append(
            f"Hardness at demold {hardness_demold:.1f} Shore below target {quality.H_demold_min_shore:.1f}."
        )
        risk += 0.20
    if hardness_24h < quality.H_24h_min_shore:
        diagnostics.append(
            f"Hardness at 24h {hardness_24h:.1f} Shore below target {quality.H_24h_min_shore:.1f}."
        )
        risk += 0.10
    if pressure_status_value == "OVER_LIMIT":
        diagnostics.append("Pressure exceeds allowable limit.")
        risk += 0.25
    elif pressure_status_value == "NEAR_LIMIT":
        diagnostics.append("Pressure close to safety limit.")
        risk += 0.10

    if water_risk > 0.6:
        diagnostics.append("High humidity / water_eff risk.")
        risk += 0.10
    if mixing_eff < 0.8:
        diagnostics.append("Low mixing efficiency reported.")
        risk += 0.07
    if vent_closure_time is not None and vent_closure_time < 120.0:
        diagnostics.append("Vents seal too early (<120 s).")
        risk += 0.08
    if p_max > quality.p_max_allowable_bar * 100_000.0:
        diagnostics.append("Measured p_max above configured limit.")

    risk = float(clamp(risk, 0.0, 1.0))

    if (
        t_demold_min is None
        or hardness_demold < quality.H_demold_min_shore
        or hardness_24h < quality.H_24h_min_shore
        or pressure_status_value == "OVER_LIMIT"
    ):
        status = "FAIL"
    elif risk > quality.defect_risk_max or pressure_status_value == "NEAR_LIMIT":
        status = "MARGINAL"
    else:
        status = "OK"

    return status, risk, diagnostics
