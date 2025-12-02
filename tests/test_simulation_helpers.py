from __future__ import annotations

from pathlib import Path

from pur_mold_twin import MoldProperties, MVP0DSimulator, ProcessConditions, QualityTargets, VentProperties
from pur_mold_twin.core.simulation import (
    GasState,
    step_gas_state,
    step_heat_transfer,
    step_kinetics,
)
from pur_mold_twin.core.utils import celsius_to_kelvin
from pur_mold_twin.material_db.loader import load_material_catalog


CATALOG_PATH = Path("configs/systems/jr_purtec_catalog.yaml")
SYSTEM_R1 = load_material_catalog(CATALOG_PATH)["SYSTEM_R1"]


def _build_process(RH_ambient: float = 0.5) -> ProcessConditions:
    return ProcessConditions(
        m_polyol=1.0,
        m_iso=1.05,
        m_additives=0.0,
        nco_oh_index=1.05,
        T_polyol_in_C=25.0,
        T_iso_in_C=25.0,
        T_mold_init_C=40.0,
        T_ambient_C=22.0,
        RH_ambient=RH_ambient,
        mixing_eff=0.9,
    )


def _build_mold(process: ProcessConditions) -> MoldProperties:
    target_rho = SYSTEM_R1.foam_targets.rho_moulded_target
    cavity_volume = process.total_mass / max(target_rho, 1e-6)
    return MoldProperties(
        cavity_volume_m3=cavity_volume,
        mold_surface_area_m2=0.8,
        mold_mass_kg=120.0,
    )


def _build_ctx(mixing_eff: float = 0.9):
    simulator = MVP0DSimulator()
    process = _build_process()
    process = process.model_copy(update={"mixing_eff": mixing_eff})
    mold = _build_mold(process)
    quality = QualityTargets()
    vent_cfg = mold.vent or VentProperties()
    ctx = simulator.core_simulation.prepare_context(
        SYSTEM_R1,
        process,
        mold,
        quality,
        simulator.config,
        vent_cfg=vent_cfg,
    )
    return ctx, vent_cfg


def test_step_kinetics_handles_zero_dt() -> None:
    ctx, _ = _build_ctx()
    result = step_kinetics(ctx, alpha_prev=0.0, phi_prev=0.0, T_core_current=300.0, dt=0.0)
    assert result.phi == 0.0
    assert result.alpha == 0.0
    assert result.dalpha_dt == 0.0


def test_step_heat_transfer_cools_core_when_no_heat() -> None:
    ctx, _ = _build_ctx(mixing_eff=1.0)
    heat_result = step_heat_transfer(
        ctx,
        T_core_current=celsius_to_kelvin(60.0),
        T_mold_current=celsius_to_kelvin(40.0),
        heat_release_W=0.0,
        dt=1.0,
    )
    assert heat_result.T_core_K < celsius_to_kelvin(60.0)
    assert heat_result.T_mold_K > celsius_to_kelvin(40.0)


def test_step_gas_state_limits_fill_ratio_and_updates_pressures() -> None:
    ctx, vent_cfg = _build_ctx()
    state = GasState(
        n_air=ctx.n_air_initial,
        n_co2=0.0,
        n_pentane_liquid=ctx.n_pentane_total,
        n_pentane_gas=0.0,
    )

    result = step_gas_state(
        ctx,
        vent_cfg=vent_cfg,
        state=state,
        alpha_value=1.0,
        T_core_value=celsius_to_kelvin(55.0),
        dt=1.0,
    )

    assert 0.0 < result.fill_ratio <= 1.5
    assert result.density > 0.0
    assert result.p_total_Pa > 0.0
    assert result.state.n_pentane_liquid < state.n_pentane_liquid
    assert result.vent_eff <= 1.0
