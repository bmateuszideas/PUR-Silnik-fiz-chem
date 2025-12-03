import pytest
from pathlib import Path

from pur_mold_twin import MVP0DSimulator, ProcessConditions, MoldProperties, QualityTargets
from pur_mold_twin.material_db.loader import load_material_catalog
from pur_mold_twin.core.ode_backends import integrate_system, solve_ivp

CATALOG_PATH = Path("configs/systems/jr_purtec_catalog.yaml")
SYSTEM_R1 = load_material_catalog(CATALOG_PATH)["SYSTEM_R1"]


def _build_ctx():
    sim = MVP0DSimulator()
    proc = ProcessConditions(
        m_polyol=1.0,
        m_iso=1.05,
        m_additives=0.0,
        nco_oh_index=1.05,
        T_polyol_in_C=25.0,
        T_iso_in_C=25.0,
        T_mold_init_C=40.0,
        T_ambient_C=22.0,
        RH_ambient=0.5,
        mixing_eff=0.9,
    )
    mold = MoldProperties(cavity_volume_m3=0.001, mold_surface_area_m2=0.8, mold_mass_kg=120.0)
    quality = QualityTargets()
    vent_cfg = mold.vent or quality
    ctx = sim.core_simulation.prepare_context(SYSTEM_R1, proc, mold, quality, sim.config, vent_cfg=vent_cfg)
    return ctx


def test_manual_smoke():
    ctx = _build_ctx()
    traj = integrate_system(ctx, backend="manual")
    assert len(traj.time_s) > 1
    assert len(traj.alpha) == len(traj.time_s)
    assert all(isinstance(x, float) for x in traj.time_s)


@pytest.mark.skipif(solve_ivp is None, reason="scipy not installed")
def test_solveivp_smoke():
    ctx = _build_ctx()
    traj = integrate_system(ctx, backend="solve_ivp")
    assert len(traj.time_s) > 1
    assert len(traj.alpha) == len(traj.time_s)
