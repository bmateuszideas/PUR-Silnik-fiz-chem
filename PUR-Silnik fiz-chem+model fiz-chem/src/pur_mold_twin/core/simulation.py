from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

import math

from ..material_db.models import MaterialSystem

try:  # SciPy jest wymagana dla backendu solve_ivp, ale moze nie byc zainstalowana w trybie minimalnym
    from scipy.integrate import solve_ivp
except ModuleNotFoundError:  # pragma: no cover
    solve_ivp = None

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


def integrate_manual(ctx: SimulationContext) -> Trajectory:
    cfg = ctx.config
    time = linspace(0.0, cfg.total_time_s, cfg.steps())
    alpha = zeros_like(time)
    phi = zeros_like(time)
    T_core = zeros_like(time)
    T_mold = zeros_like(time)

    T_core_current = initial_core_temperature(ctx.process)
    T_mold_current = celsius_to_kelvin(ctx.process.T_mold_init_C)

    alpha[0] = 0.0
    T_core[0] = T_core_current
    T_mold[0] = T_mold_current

    for idx in range(1, len(time)):
        dt = time[idx] - time[idx - 1]
        arrhenius_factor = arrhenius_multiplier(
            T_core_current,
            cfg.reference_temperature_K,
            cfg.activation_energy_J_per_mol,
        )
        rate_modifier = arrhenius_factor * (0.4 + 0.6 * ctx.mixing_factor)
        phi[idx] = max(
            phi[idx - 1] + (dt * rate_modifier) / max(ctx.tau_s, 1e-3),
            0.0,
        )
        alpha_value = alpha_from_phi(phi[idx], ctx.exponent)
        alpha[idx] = alpha_value

        dalpha_dt = max(0.0, (alpha_value - alpha[idx - 1]) / max(dt, 1e-9))
        heat_release = cfg.reaction_enthalpy_J_per_kg * ctx.mass_total * dalpha_dt
        heat_to_mold = (
            ctx.mold.h_core_to_mold_W_per_m2K
            * ctx.mold.mold_surface_area_m2
            * (T_core_current - T_mold_current)
        )
        dT_core_dt = (heat_release - heat_to_mold) / max(ctx.mass_total * cfg.foam_cp_J_per_kgK, 1e-6)
        dT_mold_dt = (
            heat_to_mold
            - ctx.mold.h_mold_to_ambient_W_per_m2K
            * ctx.mold.mold_surface_area_m2
            * (T_mold_current - ctx.T_ambient_K)
        ) / max(ctx.mold.mold_mass_kg * ctx.mold.cp_mold_J_per_kgK, 1e-6)

        T_core_current += dT_core_dt * dt
        T_mold_current += dT_mold_dt * dt
        T_core[idx] = T_core_current
        T_mold[idx] = T_mold_current

    return Trajectory(time_s=time, alpha=alpha, T_core_K=T_core, T_mold_K=T_mold, phi=phi)


def integrate_solve_ivp(ctx: SimulationContext) -> Trajectory:
    if solve_ivp is None:  # pragma: no cover
        raise RuntimeError("Backend 'solve_ivp' wymaga zainstalowanego pakietu scipy.")
    cfg = ctx.config
    time = linspace(0.0, cfg.total_time_s, cfg.steps())
    y0 = [
        0.0,
        initial_core_temperature(ctx.process),
        celsius_to_kelvin(ctx.process.T_mold_init_C),
    ]

    def ode(t, y):
        phi_value, T_core_current, T_mold_current = y
        arrhenius_factor = arrhenius_multiplier(
            T_core_current,
            cfg.reference_temperature_K,
            cfg.activation_energy_J_per_mol,
        )
        dphi_dt = max(
            (arrhenius_factor * (0.4 + 0.6 * ctx.mixing_factor)) / max(ctx.tau_s, 1e-3),
            0.0,
        )
        dalpha_dt = alpha_derivative(phi_value, ctx.exponent, dphi_dt)
        dalpha_dt = max(dalpha_dt, 0.0)
        heat_release = cfg.reaction_enthalpy_J_per_kg * ctx.mass_total * dalpha_dt
        heat_to_mold = (
            ctx.mold.h_core_to_mold_W_per_m2K
            * ctx.mold.mold_surface_area_m2
            * (T_core_current - T_mold_current)
        )
        dT_core_dt = (heat_release - heat_to_mold) / max(ctx.mass_total * cfg.foam_cp_J_per_kgK, 1e-6)
        dT_mold_dt = (
            heat_to_mold
            - ctx.mold.h_mold_to_ambient_W_per_m2K
            * ctx.mold.mold_surface_area_m2
            * (T_mold_current - ctx.T_ambient_K)
        ) / max(ctx.mold.mold_mass_kg * ctx.mold.cp_mold_J_per_kgK, 1e-6)
        return [dphi_dt, dT_core_dt, dT_mold_dt]

    method = getattr(cfg, "solve_ivp_method", "Radau")
    rtol = getattr(cfg, "solve_ivp_rtol", 1e-6)
    atol = getattr(cfg, "solve_ivp_atol", 1e-8)
    solution = solve_ivp(
        ode,
        (0.0, cfg.total_time_s),
        y0,
        method=method,
        t_eval=time,
        rtol=rtol,
        atol=atol,
    )
    if not solution.success:
        raise RuntimeError(f"solve_ivp backend failed: {solution.message}")

    phi = [max(val, 0.0) for val in solution.y[0]]
    alpha = [alpha_from_phi(val, ctx.exponent) for val in phi]
    T_core = list(solution.y[1])
    T_mold = list(solution.y[2])
    return Trajectory(time_s=list(solution.t), alpha=alpha, T_core_K=T_core, T_mold_K=T_mold, phi=phi)


def simulate(material, process, mold, quality, config, backend: str, vent_cfg) -> "SimulationResult":
    ctx = prepare_context(material, process, mold, quality, config, vent_cfg=vent_cfg)
    if backend == "solve_ivp":
        trajectory = integrate_solve_ivp(ctx)
    else:
        trajectory = integrate_manual(ctx)
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
    n_air = ctx.n_air_initial
    n_co2_current = 0.0
    n_pentane_liquid = ctx.n_pentane_total
    n_pentane_gas = 0.0

    headspace0 = headspace_volume(cfg, ctx.cavity_volume, min(ctx.effective_liquid_volume, ctx.cavity_volume))
    p_air0, p_co20, p_pentane0, p_total0 = compute_pressures(
        n_air=n_air,
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

        target_co2 = min(
            ctx.moles_co2_total,
            ctx.moles_co2_total * (alpha_value ** 1.1) * ctx.gas_release_eff,
        )
        delta_co2 = max(0.0, target_co2 - n_co2_current)
        n_co2_current += delta_co2

        evap_rate = pentane_evap_rate(T_core_value, cfg)
        delta_pentane = min(n_pentane_liquid, evap_rate * n_pentane_liquid * dt)
        n_pentane_liquid -= delta_pentane
        n_pentane_gas += delta_pentane

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
        vent_eff[idx] = vent_eff_value

        (
            p_air_current,
            p_co2_current,
            p_pentane_current,
            p_total_current,
        ) = compute_pressures(
            n_air=n_air,
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
                n_air=n_air,
                n_co2=n_co2_current,
                n_pentane=n_pentane_gas,
                temperature_K=T_core_value,
                headspace_volume=headspace,
            )

        if vent_closure_time is None and vent_eff_value <= 0.1:
            vent_closure_time = float(time[idx])

        gas_volume = (
            (n_co2_current + n_pentane_gas)
            * GAS_CONSTANT
            * T_core_value
            / STANDARD_PRESSURE_PA
        )
        total_volume = ctx.effective_liquid_volume + gas_volume
        effective_volume = min(total_volume, ctx.cavity_volume)
        fill_ratio[idx] = clamp(
            total_volume / max(ctx.cavity_volume, 1e-12),
            0.0,
            1.5,
        )
        rho[idx] = ctx.mass_total / max(effective_volume, 1e-9)
        n_co2[idx] = n_co2_current
        p_air[idx] = p_air_current
        p_co2[idx] = p_co2_current
        p_pentane[idx] = p_pentane_current
        p_total[idx] = p_total_current
        p_max_value = max(p_max_value, p_total_current)

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
def get_backend_name(config: "SimulationConfig") -> str:
    backend = getattr(config, "backend", "manual")
    if backend not in {"manual", "solve_ivp"}:
        raise ValueError(f"Unknown simulation backend '{backend}'.")
    return backend
