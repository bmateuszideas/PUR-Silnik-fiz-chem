from __future__ import annotations

from dataclasses import dataclass
from typing import List
import logging

from .kinetics import alpha_derivative, alpha_from_phi, arrhenius_multiplier
from .thermal import initial_core_temperature
from .types import SimulationConfig
from .utils import celsius_to_kelvin, clamp, linspace, zeros_like
from .simulation import SimulationContext, Trajectory, step_kinetics
from .ode_backends import integrate_manual

logger = logging.getLogger(__name__)


@dataclass
class LayerState:
    """
    State for a single layer in the 1D discretization.
    
    Attributes:
        alpha: Degree of cure (0-1)
        phi: Dimensionless reaction progress parameter
        temperature_K: Layer temperature in Kelvin
        rho_kg_per_m3: Local apparent density (optional, for future use)
    """
    alpha: float
    phi: float
    temperature_K: float
    rho_kg_per_m3: float = 0.0


def _init_layers(ctx: SimulationContext, layer_count: int) -> List[LayerState]:
    """
    Initialize layer states with appropriate starting conditions.
    
    Bottom layer (index 0) is closest to mold wall, top layer (index N-1) is core.
    Initial temperature varies linearly from mold temperature to initial core temperature.
    """
    initial_T_core = initial_core_temperature(ctx.process)
    T_mold = celsius_to_kelvin(ctx.process.T_mold_init_C)
    
    layers = []
    for i in range(layer_count):
        # Linear temperature gradient from mold (cold) to core (warm)
        fraction = i / max(layer_count - 1, 1)
        T_init = T_mold + fraction * (initial_T_core - T_mold)
        
        # Use target density if available, else use a default
        rho_init = getattr(ctx.material.foam_targets, 'rho_moulded_target', 50.0)
        
        layers.append(
            LayerState(
                alpha=0.0,
                phi=0.0,
                temperature_K=T_init,
                rho_kg_per_m3=rho_init,
            )
        )
    return layers


def integrate_1d_manual(ctx: SimulationContext) -> Trajectory:
    """
    Manual integration for 1D layered model with conduction and kinetics.
    
    Physics:
    - Each layer evolves kinetics independently based on local temperature
    - Heat conduction between adjacent layers (finite difference)
    - Boundary conditions:
      - Layer 0 (mold wall): exchange with mold via h_core_to_mold
      - Layer N-1 (core): insulated or minimal exchange
    - Exothermic reaction heat generated per layer
    
    Returns trajectory with aggregated metrics (deepest layer represents core).
    """
    cfg = ctx.config
    layer_count = max(getattr(cfg, "layers_count", 1), 1)
    
    # Fallback to 0D if only one layer
    if layer_count == 1:
        logger.debug("1D simulation with 1 layer, falling back to 0D solver")
        return integrate_manual(ctx)

    logger.info(f"Starting 1D simulation with {layer_count} layers")
    
    time = linspace(0.0, cfg.total_time_s, cfg.steps())
    layers = _init_layers(ctx, layer_count)

    # Storage for aggregated time series (for backward compatibility)
    alpha_series = zeros_like(time)
    T_core_series = zeros_like(time)
    T_mold_series = zeros_like(time)
    phi_series = zeros_like(time)
    
    # Storage for layer profiles (optional, for detailed analysis)
    T_layer_profiles = []  # List of lists: T_layer_profiles[time_idx][layer_idx]
    alpha_layer_profiles = []

    # Initial conditions
    alpha_series[0] = layers[-1].alpha
    T_core_series[0] = layers[-1].temperature_K
    T_mold_series[0] = layers[0].temperature_K
    phi_series[0] = layers[-1].phi
    
    T_layer_profiles.append([layer.temperature_K for layer in layers])
    alpha_layer_profiles.append([layer.alpha for layer in layers])

    # Physical parameters
    conductivity = getattr(cfg, "foam_conductivity_W_per_mK", 0.2)
    layer_thickness = 0.01 / layer_count  # Assume 1cm total thickness, adjust as needed
    layer_mass = ctx.mass_total / layer_count
    layer_cp = cfg.foam_cp_J_per_kgK
    
    # Mold parameters for boundary condition
    T_mold_current = celsius_to_kelvin(ctx.process.T_mold_init_C)
    mold_mass = ctx.mold.mold_mass_kg
    mold_cp = ctx.mold.cp_mold_J_per_kgK
    h_core_to_mold = ctx.mold.h_core_to_mold_W_per_m2K
    h_mold_to_ambient = ctx.mold.h_mold_to_ambient_W_per_m2K
    mold_area = ctx.mold.mold_surface_area_m2
    T_ambient = ctx.T_ambient_K

    for idx in range(1, len(time)):
        dt = time[idx] - time[idx - 1]
        
        # Step 1: Update kinetics for each layer
        for layer in layers:
            kinetics = step_kinetics(ctx, layer.alpha, layer.phi, layer.temperature_K, dt)
            layer.phi = clamp(kinetics.phi, 0.0, 1.5)
            layer.alpha = clamp(kinetics.alpha, 0.0, 1.0)

        # Step 2: Compute heat fluxes and update temperatures
        new_temperatures = []
        heat_to_mold_total = 0.0  # For mold temperature update
        
        for layer_idx, layer in enumerate(layers):
            T_current = layer.temperature_K
            
            # Conduction between layers (finite difference)
            q_conduction = 0.0
            
            if layer_idx > 0:
                # Heat from layer below (toward mold)
                T_below = layers[layer_idx - 1].temperature_K
                q_conduction += conductivity * mold_area * (T_below - T_current) / layer_thickness
            else:
                # Bottom layer: exchange with mold
                q_from_mold = h_core_to_mold * mold_area * (T_mold_current - T_current)
                q_conduction += q_from_mold
                heat_to_mold_total -= q_from_mold  # Mold gains what layer loses
            
            if layer_idx < layer_count - 1:
                # Heat from layer above (toward core)
                T_above = layers[layer_idx + 1].temperature_K
                q_conduction += conductivity * mold_area * (T_above - T_current) / layer_thickness
            # Top layer: insulated (no additional boundary condition)
            
            # Reaction heat generation (exothermic)
            dalpha_dt = alpha_derivative(
                layer.phi,
                ctx.exponent,
                arrhenius_multiplier(
                    layer.temperature_K,
                    cfg.reference_temperature_K,
                    cfg.activation_energy_J_per_mol,
                ) * (0.4 + 0.6 * ctx.mixing_factor) / max(ctx.tau_s, 1e-3)
            )
            q_reaction = cfg.reaction_enthalpy_J_per_kg * layer_mass * max(dalpha_dt, 0.0)
            
            # Net heat change
            q_net = q_reaction + q_conduction
            dT_dt = q_net / max(layer_mass * layer_cp, 1e-6)
            
            # Limit temperature change rate for numerical stability
            max_dT = 50.0  # Max 50K per timestep
            dT_dt = clamp(dT_dt, -max_dT/dt, max_dT/dt)
            
            new_temperatures.append(T_current + dT_dt * dt)
        
        # Update layer temperatures
        for layer, T_new in zip(layers, new_temperatures):
            layer.temperature_K = clamp(T_new, 250.0, 600.0)  # Physical bounds
        
        # Step 3: Update mold temperature
        q_mold_to_ambient = h_mold_to_ambient * mold_area * (T_mold_current - T_ambient)
        q_net_mold = heat_to_mold_total - q_mold_to_ambient
        dT_mold_dt = q_net_mold / max(mold_mass * mold_cp, 1e-6)
        T_mold_current = clamp(T_mold_current + dT_mold_dt * dt, 250.0, 600.0)
        
        # Store aggregated values (use deepest layer as "core")
        alpha_series[idx] = layers[-1].alpha
        T_core_series[idx] = layers[-1].temperature_K
        T_mold_series[idx] = T_mold_current
        phi_series[idx] = layers[-1].phi
        
        # Store layer profiles
        T_layer_profiles.append([layer.temperature_K for layer in layers])
        alpha_layer_profiles.append([layer.alpha for layer in layers])

    logger.info(f"1D simulation completed: final core T={T_core_series[-1]:.1f}K, alpha={alpha_series[-1]:.3f}")

    return Trajectory(
        time_s=time,
        alpha=alpha_series,
        T_core_K=T_core_series,
        T_mold_K=T_mold_series,
        phi=phi_series,
    )


def run_1d_simulation(ctx: SimulationContext) -> Trajectory:
    """
    Entry point for 1D simulation.
    
    Routes to appropriate solver based on configuration.
    Currently only manual integration is supported for 1D.
    """
    backend = getattr(ctx.config, "backend", "manual")
    
    if backend != "manual":
        logger.warning(f"1D simulation only supports 'manual' backend, got '{backend}'. Falling back to manual.")
    
    return integrate_1d_manual(ctx)

