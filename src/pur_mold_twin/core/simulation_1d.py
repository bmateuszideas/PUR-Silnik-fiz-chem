from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .kinetics import alpha_derivative, alpha_from_phi, arrhenius_multiplier
from .thermal import initial_core_temperature
from .types import SimulationConfig
from .utils import celsius_to_kelvin, clamp, linspace, zeros_like
from .simulation import SimulationContext, Trajectory, step_kinetics
from .ode_backends import integrate_manual


@dataclass
class LayerState:
    alpha: float
    phi: float
    temperature_K: float


def _init_layers(ctx: SimulationContext, layer_count: int) -> List[LayerState]:
    initial_T = initial_core_temperature(ctx.process)
    return [
        LayerState(
            alpha=0.0,
            phi=0.0,
            temperature_K=initial_T,
        )
        for _ in range(layer_count)
    ]


def integrate_1d_manual(ctx: SimulationContext) -> Trajectory:
    cfg = ctx.config
    layer_count = max(getattr(cfg, "layers_count", 1), 1)
    if layer_count == 1:
        return integrate_manual(ctx)

    time = linspace(0.0, cfg.total_time_s, cfg.steps())
    layers = _init_layers(ctx, layer_count)

    alpha_series = zeros_like(time)
    T_core_series = zeros_like(time)
    T_mold_series = zeros_like(time)
    phi_series = zeros_like(time)

    alpha_series[0] = 0.0
    T_core_series[0] = layers[-1].temperature_K
    T_mold_series[0] = celsius_to_kelvin(ctx.process.T_mold_init_C)
    phi_series[0] = 0.0

    conductivity = getattr(cfg, "foam_conductivity_W_per_mK", 0.2)
    layer_mass = ctx.mass_total / layer_count

    for idx in range(1, len(time)):
        dt = time[idx] - time[idx - 1]
        for layer in layers:
            kinetics = step_kinetics(ctx, layer.alpha, layer.phi, layer.temperature_K, dt)
            layer.phi = clamp(kinetics.phi, 0.0, 1.5)
            layer.alpha = clamp(kinetics.alpha, 0.0, 1.0)

        new_temperatures = []
        for layer_idx, layer in enumerate(layers):
            T_current = layer.temperature_K
            neighbors = []
            if layer_idx > 0:
                neighbors.append(layers[layer_idx - 1].temperature_K)
            if layer_idx < layer_count - 1:
                neighbors.append(layers[layer_idx + 1].temperature_K)
            delta_T = 0.0
            for neighbor_T in neighbors:
                delta_T += conductivity * (neighbor_T - T_current)
            heat_release = (
                cfg.reaction_enthalpy_J_per_kg
                * (ctx.mass_total / layer_count)
                * alpha_derivative(
                    layer.phi,
                    ctx.exponent,
                    arrhenius_multiplier(
                        layer.temperature_K,
                        cfg.reference_temperature_K,
                        cfg.activation_energy_J_per_mol,
                    ),
                )
            )
            dT_dt = (heat_release + delta_T) / max(layer_mass * cfg.foam_cp_J_per_kgK, 1e-6)
            new_temperatures.append(T_current + dT_dt * dt)
        for layer, T_new in zip(layers, new_temperatures):
            layer.temperature_K = T_new

        alpha_series[idx] = layers[-1].alpha
        T_core_series[idx] = layers[-1].temperature_K
        T_mold_series[idx] = layers[0].temperature_K
        phi_series[idx] = layers[-1].phi

    return Trajectory(
        time_s=time,
        alpha=alpha_series,
        T_core_K=T_core_series,
        T_mold_K=T_mold_series,
        phi=phi_series,
    )


def run_1d_simulation(ctx: SimulationContext) -> Trajectory:
    return integrate_1d_manual(ctx)
