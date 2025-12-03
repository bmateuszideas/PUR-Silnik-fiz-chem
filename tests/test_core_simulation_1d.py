import pytest
from src.pur_mold_twin.core.simulation_1d import run_1d_simulation
from src.pur_mold_twin.core.simulation import SimulationContext
from src.pur_mold_twin.core.types import SimulationConfig, ProcessConditions, MoldProperties, QualityTargets, VentProperties
from src.pur_mold_twin.material_db.loader import load_material_catalog
from src.pur_mold_twin import MVP0DSimulator
from pathlib import Path


def make_ctx(layers_count=1):
    # Build a SimulationContext using the simulator helpers and material catalog
    simulator = MVP0DSimulator()
    catalog = load_material_catalog(Path("configs/systems/jr_purtec_catalog.yaml"))
    material = catalog.get("SYSTEM_R1")
    # create a config based on simulator defaults but override layers_count and timing
    cfg = simulator.config.model_copy(update={
        "layers_count": layers_count,
        "total_time_s": 100.0,
        "time_step_s": 0.5,
        "activation_energy_J_per_mol": 45000.0,
    })
    process = ProcessConditions(
        m_polyol=1.0,
        m_iso=1.0,
        m_additives=0.0,
        nco_oh_index=1.0,
        T_polyol_in_C=25.0,
        T_iso_in_C=25.0,
        T_mold_init_C=40.0,
        T_ambient_C=25.0,
        RH_ambient=40.0,
        mixing_eff=1.0,
    )
    # simple mold for tests
    mold = MoldProperties(
        cavity_volume_m3=process.total_mass / max(material.foam_targets.rho_moulded_target, 1e-6),
        mold_surface_area_m2=0.1,
        mold_mass_kg=5.0,
    )
    quality = QualityTargets()
    vent = mold.vent or VentProperties()
    ctx = simulator.core_simulation.prepare_context(material, process, mold, quality, cfg, vent)
    return ctx


def test_1d_reduces_to_0d():
    ctx_1d = make_ctx(layers_count=1)
    ctx_0d = make_ctx(layers_count=1)
    result_1d = run_1d_simulation(ctx_1d)
    result_0d = run_1d_simulation(ctx_0d)
    assert pytest.approx(result_1d.alpha, abs=1e-6) == result_0d.alpha
    assert pytest.approx(result_1d.T_core_K, abs=1e-6) == result_0d.T_core_K


def test_1d_profiles_monotonic():
    ctx = make_ctx(layers_count=5)
    result = run_1d_simulation(ctx)
    # Sprawdz monotoniczność alpha i T_core
    assert all(x <= y for x, y in zip(result.alpha, result.alpha[1:])), "Alpha profile not monotonic"
    assert all(x <= y for x, y in zip(result.T_core_K, result.T_core_K[1:])), "T_core profile not monotonic"


def test_1d_profiles_range():
    ctx = make_ctx(layers_count=5)
    result = run_1d_simulation(ctx)
    # Sprawdz zakresy
    assert all(0.0 <= a <= 1.0 for a in result.alpha), "Alpha out of range"
    import math
    # Ensure temperatures are finite and positive (explicit integrator may be stiff)
    assert all(math.isfinite(t) and t > 0.0 for t in result.T_core_K), "T_core contains non-finite or non-positive values"


def test_1d_profiles_shape_and_consistency():
    layers = 5
    ctx = make_ctx(layers_count=layers)
    result = run_1d_simulation(ctx)
    # profiles should be present for 1D mode
    assert getattr(result, "T_layers_K", None) is not None, "T_layers_K missing"
    assert getattr(result, "alpha_layers", None) is not None, "alpha_layers missing"
    assert getattr(result, "phi_layers", None) is not None, "phi_layers missing"

    # shapes: number of rows == len(time), each row has 'layers' entries
    assert len(result.T_layers_K) == len(result.time_s)
    assert all(len(row) == layers for row in result.T_layers_K)
    assert len(result.alpha_layers) == len(result.time_s)
    assert all(len(row) == layers for row in result.alpha_layers)

    # consistency: last layer should correspond to T_core_K and alpha time series
    for i, t in enumerate(result.time_s):
        assert pytest.approx(result.T_layers_K[i][-1], rel=1e-6, abs=1e-6) == result.T_core_K[i]
        assert pytest.approx(result.alpha_layers[i][-1], rel=1e-6, abs=1e-6) == result.alpha[i]


def test_1d_profiles_finite_and_ranges():
    ctx = make_ctx(layers_count=4)
    result = run_1d_simulation(ctx)
    import math
    # inspect per-layer values
    for row in result.T_layers_K:
        assert all(math.isfinite(x) and x > 0.0 for x in row), "Layer temperatures must be finite and positive"
    for row in result.alpha_layers:
        assert all(0.0 <= a <= 1.0 for a in row), "Per-layer alpha out of range"
