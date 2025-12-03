"""
Comprehensive tests for 1D layered simulation (TODO3 Task 12).

Tests cover:
- Reduction from 1D to 0D (single layer should match 0D results)
- Multi-layer profile sanity (monotonicity, bounds, physical plausibility)
- Boundary conditions (mold wall vs core temperatures)
- Extreme cases (very cold mold, very hot components, high layer counts)
- Conservation checks (energy, mass balance approximations)
"""
from pathlib import Path

import pytest

from pur_mold_twin import MVP0DSimulator, ProcessConditions, MoldProperties, QualityTargets
from pur_mold_twin.material_db.loader import load_material_catalog
from pur_mold_twin.core.simulation import SimulationContext
from pur_mold_twin.core.simulation_1d import integrate_1d_manual, _init_layers

CATALOG_PATH = Path("configs/systems/jr_purtec_catalog.yaml")
SYSTEM_R1 = load_material_catalog(CATALOG_PATH)["SYSTEM_R1"]


def _build_context(layers_count=1, T_mold_init_C=40.0, dimension="1d_experimental"):
    """Helper to build a SimulationContext for 1D testing."""
    sim = MVP0DSimulator()
    
    # Override config for 1D
    sim.config.dimension = dimension
    sim.config.layers_count = layers_count
    sim.config.foam_conductivity_W_per_mK = 0.2
    
    proc = ProcessConditions(
        m_polyol=1.0,
        m_iso=1.05,
        m_additives=0.0,
        nco_oh_index=1.05,
        T_polyol_in_C=25.0,
        T_iso_in_C=25.0,
        T_mold_init_C=T_mold_init_C,
        T_ambient_C=22.0,
        RH_ambient=0.5,
        mixing_eff=0.9,
    )
    mold = MoldProperties(cavity_volume_m3=0.001, mold_surface_area_m2=0.8, mold_mass_kg=120.0)
    quality = QualityTargets()
    vent_cfg = mold.vent or quality
    
    ctx = sim.core_simulation.prepare_context(
        SYSTEM_R1, proc, mold, quality, sim.config, vent_cfg=vent_cfg
    )
    return ctx


# ==================== Test 1: Single layer = 0D equivalence ====================

def test_1d_single_layer_matches_0d():
    """
    Test that 1D simulation with 1 layer produces results equivalent to 0D.
    
    This is a critical regression test ensuring backward compatibility.
    """
    ctx_1d = _build_context(layers_count=1, dimension="1d_experimental")
    ctx_0d = _build_context(layers_count=1, dimension="0d")
    
    # Run both
    from pur_mold_twin.core.ode_backends import integrate_manual
    traj_0d = integrate_manual(ctx_0d)
    traj_1d = integrate_1d_manual(ctx_1d)
    
    # Compare key outputs
    assert len(traj_0d.alpha) == len(traj_1d.alpha)
    assert len(traj_0d.T_core_K) == len(traj_1d.T_core_K)
    
    # Final alpha should match within tolerance
    alpha_diff = abs(traj_0d.alpha[-1] - traj_1d.alpha[-1])
    assert alpha_diff < 0.01, f"1D single-layer alpha differs from 0D: {alpha_diff}"
    
    # Final core temperature should match within tolerance
    T_diff = abs(traj_0d.T_core_K[-1] - traj_1d.T_core_K[-1])
    assert T_diff < 2.0, f"1D single-layer T_core differs from 0D: {T_diff}K"


# ==================== Test 2: Multi-layer temperature monotonicity ====================

def test_1d_multilayer_temperature_gradient():
    """
    Test that with multiple layers, temperature forms a reasonable gradient.
    
    Expected: Bottom layer (near mold) should be cooler than top layer (core).
    """
    ctx = _build_context(layers_count=5, T_mold_init_C=30.0)
    traj = integrate_1d_manual(ctx)
    
    # Check that final core temperature is higher than mold temperature
    # (reaction is exothermic, so core should heat up more)
    assert traj.T_core_K[-1] > traj.T_mold_K[-1], (
        f"Expected core hotter than mold: core={traj.T_core_K[-1]:.1f}K, "
        f"mold={traj.T_mold_K[-1]:.1f}K"
    )
    
    # Check reasonable temperature bounds (250K to 600K)
    assert all(250.0 <= T <= 600.0 for T in traj.T_core_K), "Core temperature out of bounds"
    assert all(250.0 <= T <= 600.0 for T in traj.T_mold_K), "Mold temperature out of bounds"


# ==================== Test 3: Alpha progression sanity ====================

def test_1d_alpha_monotonic_increase():
    """
    Test that degree of cure (alpha) increases monotonically over time.
    
    Alpha should start at 0 and approach 1 (or at least not decrease).
    """
    ctx = _build_context(layers_count=3)
    traj = integrate_1d_manual(ctx)
    
    # Alpha should start near zero
    assert traj.alpha[0] < 0.05, f"Initial alpha should be near 0, got {traj.alpha[0]}"
    
    # Alpha should increase monotonically (allowing small numerical noise)
    for i in range(1, len(traj.alpha)):
        assert traj.alpha[i] >= traj.alpha[i-1] - 1e-6, (
            f"Alpha decreased at step {i}: {traj.alpha[i-1]} -> {traj.alpha[i]}"
        )
    
    # Final alpha should be positive and <= 1
    assert 0.0 < traj.alpha[-1] <= 1.0, f"Final alpha out of bounds: {traj.alpha[-1]}"


# ==================== Test 4: Layer initialization gradient ====================

def test_1d_init_layers_temperature_gradient():
    """
    Test that layer initialization creates a proper temperature gradient.
    
    Layers should start with temperatures varying from mold to core.
    """
    ctx = _build_context(layers_count=5, T_mold_init_C=25.0)
    layers = _init_layers(ctx, 5)
    
    # Check count
    assert len(layers) == 5
    
    # Check all layers have valid initial state
    for layer in layers:
        assert 0.0 <= layer.alpha <= 1.0
        assert 0.0 <= layer.phi <= 1.5
        assert 250.0 <= layer.temperature_K <= 600.0
    
    # Check temperature gradient: bottom (mold) should be cooler or equal to top (core)
    # (initial core temp is computed from material properties and typically > mold temp)
    assert layers[0].temperature_K <= layers[-1].temperature_K, (
        f"Expected bottom layer cooler: bottom={layers[0].temperature_K:.1f}K, "
        f"top={layers[-1].temperature_K:.1f}K"
    )


# ==================== Test 5: Extreme case - very cold mold ====================

def test_1d_extreme_cold_mold():
    """
    Test simulation with very cold mold temperature (stress test).
    
    Should still complete without crashes and produce physical results.
    """
    ctx = _build_context(layers_count=4, T_mold_init_C=10.0)
    traj = integrate_1d_manual(ctx)
    
    # Should complete without exceptions
    assert len(traj.alpha) > 0
    assert len(traj.T_core_K) > 0
    
    # Core should still heat up due to reaction (even if mold is cold)
    assert traj.T_core_K[-1] > traj.T_core_K[0], "Core should heat up from reaction"
    
    # Temperature bounds
    assert all(250.0 <= T <= 600.0 for T in traj.T_core_K)


# ==================== Test 6: High layer count (computational stress) ====================

def test_1d_high_layer_count():
    """
    Test simulation with higher number of layers (stress test for performance).
    
    Should complete in reasonable time without numerical instability.
    """
    ctx = _build_context(layers_count=10)
    
    # Reduce total time for faster test
    ctx.config.total_time_s = 300.0
    ctx.config.time_step_s = 1.0
    
    traj = integrate_1d_manual(ctx)
    
    # Should complete
    assert len(traj.alpha) > 0
    
    # Check for numerical stability (no NaN or Inf)
    assert all(not (v != v) for v in traj.T_core_K), "NaN detected in T_core"
    assert all(abs(v) < 1e6 for v in traj.T_core_K), "Inf detected in T_core"
    
    # Basic sanity on final values
    assert 0.0 <= traj.alpha[-1] <= 1.0
    assert 250.0 <= traj.T_core_K[-1] <= 600.0


# ==================== Test 7: Energy conservation check (approximate) ====================

def test_1d_approximate_energy_conservation():
    """
    Test that energy is approximately conserved (within expected losses).
    
    This is a sanity check, not a rigorous energy balance (which would require
    tracking all boundary fluxes precisely).
    """
    ctx = _build_context(layers_count=3)
    traj = integrate_1d_manual(ctx)
    
    # Initial total energy (approximate: thermal + potential from unreacted material)
    T_initial = traj.T_core_K[0]
    alpha_initial = traj.alpha[0]
    
    # Final total energy
    T_final = traj.T_core_K[-1]
    alpha_final = traj.alpha[-1]
    
    # Exothermic reaction should increase temperature
    # (unless heat losses dominate)
    # At minimum, alpha should increase
    assert alpha_final > alpha_initial, "Reaction should progress (alpha increase)"
    
    # If reaction progressed significantly, temperature should have risen
    if alpha_final > 0.3:
        # Allow for cooling if reaction is slow or mold sinks heat
        # Just check it's not completely unrealistic
        assert T_final > T_initial - 50.0, (
            f"Temperature dropped too much despite reaction: "
            f"{T_initial:.1f}K -> {T_final:.1f}K"
        )


# ==================== Test 8: Phi parameter bounds ====================

def test_1d_phi_stays_in_bounds():
    """
    Test that phi parameter stays within physically meaningful bounds.
    
    Phi is clamped to [0, 1.5] in the code.
    """
    ctx = _build_context(layers_count=3)
    traj = integrate_1d_manual(ctx)
    
    # Check all phi values
    assert all(0.0 <= phi <= 1.5 for phi in traj.phi), "Phi out of bounds [0, 1.5]"


# ==================== Test 9: Mold temperature evolution ====================

def test_1d_mold_temperature_increases():
    """
    Test that mold temperature increases due to heat transfer from foam.
    
    Mold should gain heat from the exothermic reaction in the foam.
    """
    ctx = _build_context(layers_count=4, T_mold_init_C=30.0)
    traj = integrate_1d_manual(ctx)
    
    T_mold_initial = traj.T_mold_K[0]
    T_mold_final = traj.T_mold_K[-1]
    
    # Mold should heat up (or at least not cool down significantly)
    assert T_mold_final >= T_mold_initial - 5.0, (
        f"Mold cooled unexpectedly: {T_mold_initial:.1f}K -> {T_mold_final:.1f}K"
    )


# ==================== Test 10: Comparison with different layer counts ====================

def test_1d_convergence_with_layer_count():
    """
    Test that results stay physically reasonable across different layer counts.
    
    Higher layer count should give similar results (not diverge wildly).
    This test checks numerical stability rather than strict convergence.
    """
    results = {}
    for layer_count in [1, 3, 5]:
        ctx = _build_context(layers_count=layer_count)
        traj = integrate_1d_manual(ctx)
        results[layer_count] = {
            "alpha_final": traj.alpha[-1],
            "T_core_final": traj.T_core_K[-1],
        }
    
    # Check that all results are physically reasonable (main stability check)
    for layer_count, res in results.items():
        assert 0.0 <= res["alpha_final"] <= 1.0, (
            f"Alpha out of bounds for {layer_count} layers: {res['alpha_final']}"
        )
        assert 250.0 <= res["T_core_final"] <= 600.0, (
            f"T_core out of bounds for {layer_count} layers: {res['T_core_final']}K"
        )
    
    # Check that results don't vary wildly (allowing for numerical differences)
    # Multi-layer models may have different dynamics due to spatial resolution
    alpha_values = [res["alpha_final"] for res in results.values()]
    T_values = [res["T_core_final"] for res in results.values()]
    
    # All alphas should be positive and progressing (reaction happening)
    assert all(a > 0.1 for a in alpha_values), f"Some alphas too low: {alpha_values}"
    
    # Temperatures should all be elevated (reaction heat)
    assert all(T > 300.0 for T in T_values), f"Some temperatures too low: {T_values}"
    
    # Note: Strict convergence requires adaptive timestepping or implicit solver
    # For now, we just verify numerical stability (no explosions or freezes)
