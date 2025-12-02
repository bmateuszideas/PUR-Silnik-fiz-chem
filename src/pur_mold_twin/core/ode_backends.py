from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

try:  # SciPy is required only for the solve_ivp backend
    from scipy.integrate import solve_ivp
except ModuleNotFoundError:  # pragma: no cover
    solve_ivp = None

from .kinetics import alpha_derivative, alpha_from_phi, arrhenius_multiplier
from .thermal import initial_core_temperature
from .utils import celsius_to_kelvin, linspace, zeros_like
from .simulation import SimulationContext, Trajectory, step_heat_transfer, step_kinetics

if TYPE_CHECKING:  # pragma: no cover
    from .types import SimulationConfig


SUPPORTED_BACKENDS = {"manual", "solve_ivp", "sundials", "jax"}


def get_backend_name(config: "SimulationConfig") -> str:
    backend = getattr(config, "backend", "manual")
    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(f"Unknown simulation backend '{backend}'.")
    return backend


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
        kinetics = step_kinetics(ctx, alpha[idx - 1], phi[idx - 1], T_core_current, dt)
        phi[idx] = kinetics.phi
        alpha[idx] = kinetics.alpha

        heat_release = cfg.reaction_enthalpy_J_per_kg * ctx.mass_total * kinetics.dalpha_dt
        heat_transfer = step_heat_transfer(
            ctx=ctx,
            T_core_current=T_core_current,
            T_mold_current=T_mold_current,
            heat_release_W=heat_release,
            dt=dt,
        )

        T_core_current = heat_transfer.T_core_K
        T_mold_current = heat_transfer.T_mold_K
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


def integrate_sundials(ctx: SimulationContext) -> Trajectory:
    try:  # pragma: no cover - dependency optional
        from scikits.odes import odeint
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(
            "Backend 'sundials' wymaga zainstalowanego pakietu scikits.odes "
            "przez extras pur-mold-twin[sundials]."
        ) from exc

    cfg = ctx.config
    time = linspace(0.0, cfg.total_time_s, cfg.steps())
    y0 = [
        0.0,
        initial_core_temperature(ctx.process),
        celsius_to_kelvin(ctx.process.T_mold_init_C),
    ]

    def rhs(t, y, ydot):
        phi_value = float(y[0])
        T_core_current = float(y[1])
        T_mold_current = float(y[2])
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
        ydot[0] = dphi_dt
        ydot[1] = dT_core_dt
        ydot[2] = dT_mold_dt

    try:
        solution = odeint(
            rhs,
            y0,
            time,
            atol=getattr(cfg, "sundials_atol", 1e-8),
            rtol=getattr(cfg, "sundials_rtol", 1e-6),
            mxsteps=int(getattr(cfg, "sundials_max_steps", 500000)),
        )
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"SUNDIALS backend failed: {exc}") from exc

    values = getattr(solution, "values", None)
    times = getattr(solution, "times", None)
    if values is None:
        if isinstance(solution, tuple) and len(solution) >= 2:
            times = solution[0]
            values = solution[1]
        else:
            values = solution
    if values is None:
        raise RuntimeError("SUNDIALS backend returned no state values.")

    def _to_list(seq: Sequence[float]) -> list[float]:
        return [float(x) for x in seq]

    phi = [max(float(row[0]), 0.0) for row in values]
    alpha = [alpha_from_phi(val, ctx.exponent) for val in phi]
    T_core = [float(row[1]) for row in values]
    T_mold = [float(row[2]) for row in values]
    time_series = _to_list(times if times is not None else time)
    if len(time_series) != len(alpha):
        # fallback to requested time grid if solver returned different length
        time_series = _to_list(time)[: len(alpha)]
    return Trajectory(time_s=time_series, alpha=alpha, T_core_K=T_core, T_mold_K=T_mold, phi=phi)


def integrate_jax(ctx: SimulationContext) -> Trajectory:
    try:  # pragma: no cover - dependency optional
        import jax.numpy as jnp
        from jax import numpy as _jnp  # noqa: F401  # to emphasise requirement
        from diffrax import Kvaerno5, ODETerm, SaveAt, diffeqsolve
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(
            "Backend 'jax' wymaga zainstalowanych pakietow jax i diffrax "
            "przez extras pur-mold-twin[jax]."
        ) from exc

    cfg = ctx.config
    time = linspace(0.0, cfg.total_time_s, cfg.steps())
    y0 = jnp.array(
        [
            0.0,
            initial_core_temperature(ctx.process),
            celsius_to_kelvin(ctx.process.T_mold_init_C),
        ],
        dtype=jnp.float64,
    )

    def rhs(t, y, args):
        phi_value = y[0]
        T_core_current = y[1]
        T_mold_current = y[2]
        arrhenius_factor = arrhenius_multiplier(
            float(T_core_current),
            cfg.reference_temperature_K,
            cfg.activation_energy_J_per_mol,
        )
        dphi_dt = jnp.maximum(
            (arrhenius_factor * (0.4 + 0.6 * ctx.mixing_factor)) / jnp.maximum(ctx.tau_s, 1e-3),
            0.0,
        )
        dalpha_dt = alpha_derivative(float(phi_value), ctx.exponent, float(dphi_dt))
        dalpha_dt = max(dalpha_dt, 0.0)
        heat_release = cfg.reaction_enthalpy_J_per_kg * ctx.mass_total * dalpha_dt
        heat_to_mold = (
            ctx.mold.h_core_to_mold_W_per_m2K
            * ctx.mold.mold_surface_area_m2
            * (float(T_core_current) - float(T_mold_current))
        )
        dT_core_dt = (heat_release - heat_to_mold) / max(ctx.mass_total * cfg.foam_cp_J_per_kgK, 1e-6)
        dT_mold_dt = (
            heat_to_mold
            - ctx.mold.h_mold_to_ambient_W_per_m2K
            * ctx.mold.mold_surface_area_m2
            * (float(T_mold_current) - ctx.T_ambient_K)
        ) / max(ctx.mold.mold_mass_kg * ctx.mold.cp_mold_J_per_kgK, 1e-6)
        return jnp.array([dphi_dt, dT_core_dt, dT_mold_dt], dtype=jnp.float64)

    term = ODETerm(rhs)
    solver = Kvaerno5()
    saveat = SaveAt(ts=jnp.array(time, dtype=jnp.float64))
    try:
        sol = diffeqsolve(
            term,
            solver,
            t0=0.0,
            t1=cfg.total_time_s,
            dt0=cfg.time_step_s,
            y0=y0,
            saveat=saveat,
        )
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"JAX backend failed: {exc}") from exc

    ys = sol.ys
    phi = [max(float(val[0]), 0.0) for val in ys]
    alpha = [alpha_from_phi(val, ctx.exponent) for val in phi]
    T_core = [float(val[1]) for val in ys]
    T_mold = [float(val[2]) for val in ys]
    return Trajectory(time_s=list(time), alpha=alpha, T_core_K=T_core, T_mold_K=T_mold, phi=phi)


def integrate_system(ctx: SimulationContext, backend: str | None = None) -> Trajectory:
    if backend is None:
        backend = get_backend_name(ctx.config)

    if backend == "manual":
        return integrate_manual(ctx)
    if backend == "solve_ivp":
        return integrate_solve_ivp(ctx)
    if backend == "sundials":
        return integrate_sundials(ctx)
    if backend == "jax":
        return integrate_jax(ctx)
    raise ValueError(f"Unknown simulation backend '{backend}'.")
