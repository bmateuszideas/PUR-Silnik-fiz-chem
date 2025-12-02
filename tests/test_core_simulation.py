"""
Tests for the MVP 0D simulator.

Focus: demold window, backend parity (manual vs solve_ivp) oraz diagnostyka wilgotności.
"""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    from scipy.integrate import solve_ivp  # noqa: F401
    SCIPY_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover
    SCIPY_AVAILABLE = False

from pur_mold_twin import (
    MVP0DSimulator,
    MoldProperties,
    ProcessConditions,
    QualityTargets,
    SimulationConfig,
    VentProperties,
)
from pur_mold_twin.material_db.loader import load_material_catalog


CATALOG_PATH = Path("configs/systems/jr_purtec_catalog.yaml")
SYSTEMS = load_material_catalog(CATALOG_PATH)
SYSTEM_R1 = SYSTEMS["SYSTEM_R1"]
TEST_QUALITY = QualityTargets(
    rho_moulded_min=20.0,
    rho_moulded_max=200.0,
    core_temp_max_C=120.0,
    p_max_allowable_bar=10.0,
    H_demold_min_shore=30.0,
    H_24h_min_shore=40.0,
)


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
    total_mass = process.total_mass
    target_rho = SYSTEM_R1.foam_targets.rho_moulded_target
    cavity_volume = total_mass / max(target_rho, 1e-6)
    return MoldProperties(
        cavity_volume_m3=cavity_volume,
        mold_surface_area_m2=0.8,
        mold_mass_kg=120.0,
    )


def test_manual_backend_produces_valid_demold_window() -> None:
    simulator = MVP0DSimulator()
    process = _build_process()
    mold = _build_mold(process)
    result = simulator.run(
        SYSTEM_R1,
        process,
        mold,
        TEST_QUALITY,
    )

    assert len(result.alpha) == simulator.config.steps()
    assert len(result.time_s) == simulator.config.steps()
    alpha = result.alpha
    assert all(alpha[i] >= alpha[i - 1] - 1e-9 for i in range(1, len(alpha)))
    assert result.t_demold_min_s is not None
    assert result.t_demold_max_s is not None
    assert result.t_demold_min_s < result.t_demold_max_s
    assert result.H_demold_shore >= QualityTargets().H_demold_min_shore


@pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not available")
def test_solve_ivp_backend_matches_manual_within_tolerance() -> None:
    manual = MVP0DSimulator()
    solve = MVP0DSimulator(
        SimulationConfig(
            backend="solve_ivp",
            time_step_s=manual.config.time_step_s,
            total_time_s=manual.config.total_time_s,
        )
    )
    process = _build_process()
    mold = _build_mold(process)
    quality = TEST_QUALITY

    manual_result = manual.run(SYSTEM_R1, process, mold, quality)
    solve_result = solve.run(SYSTEM_R1, process, mold, quality)

    assert abs(manual_result.rho_moulded - solve_result.rho_moulded) <= 2.0
    assert abs(manual_result.p_max_Pa - solve_result.p_max_Pa) <= 2.0e4
    assert abs(
        (manual_result.t_demold_opt_s or manual_result.t_demold_min_s or 0.0)
        - (solve_result.t_demold_opt_s or solve_result.t_demold_min_s or 0.0)
    ) <= 12.0


def test_water_risk_increases_with_humidity() -> None:
    simulator = MVP0DSimulator()
    mold = _build_mold(_build_process())
    dry_result = simulator.run(SYSTEM_R1, _build_process(RH_ambient=0.3), mold, TEST_QUALITY)
    humid_result = simulator.run(SYSTEM_R1, _build_process(RH_ambient=0.9), mold, TEST_QUALITY)

    assert humid_result.water_from_rh_kg > dry_result.water_from_rh_kg
    assert humid_result.water_risk_score > dry_result.water_risk_score
    assert humid_result.water_from_polyol_kg == dry_result.water_from_polyol_kg


def test_high_humidity_raises_pressure_and_defect_risk() -> None:
    simulator = MVP0DSimulator()
    mold = _build_mold(_build_process())

    baseline = simulator.run(SYSTEM_R1, _build_process(RH_ambient=0.5), mold, TEST_QUALITY)
    saturated = simulator.run(SYSTEM_R1, _build_process(RH_ambient=1.0), mold, TEST_QUALITY)

    assert saturated.p_max_Pa > baseline.p_max_Pa
    assert saturated.defect_risk >= baseline.defect_risk
    assert saturated.water_risk_score > baseline.water_risk_score


def test_matches_golden_profile():
    fixture_path = Path("tests/fixtures/use_case_1_output.json")
    import json

    with fixture_path.open("r", encoding="utf-8") as handle:
        golden_data = json.load(handle)

    simulator = MVP0DSimulator()
    process = _build_process()
    mold = _build_mold(process)
    result = simulator.run(SYSTEM_R1, process, mold, TEST_QUALITY).to_dict()

    def assert_series_close(key: str, tol: float):
        expected = golden_data[key]
        actual = result[key][::10]
        assert len(expected) == len(actual)
        for e, a in zip(expected, actual):
            assert abs(e - a) <= tol

    assert_series_close("alpha", 0.05)
    assert_series_close("T_core_K", 5.0)
    assert_series_close("p_total_Pa", 1.5e5)
    assert abs(result["rho_moulded"] - golden_data["rho_moulded"]) <= 250.0
    assert abs(result["p_max_Pa"] - golden_data["p_max_Pa"]) <= 2.0e4


def test_extreme_vent_closure():
    simulator = MVP0DSimulator()
    process = _build_process()
    mold = MoldProperties(
        cavity_volume_m3=_build_mold(process).cavity_volume_m3,
        mold_surface_area_m2=0.8,
        mold_mass_kg=120.0,
        vent=None,  # no vents
    )
    result = simulator.run(SYSTEM_R1, process, mold, TEST_QUALITY)
    assert result.p_max_Pa > 0


def test_vent_parameters_clamp_efficiency_and_pressure():
    simulator = MVP0DSimulator()
    process = _build_process()
    base_mold = _build_mold(process)

    baseline = simulator.run(SYSTEM_R1, process, base_mold, TEST_QUALITY)
    aggressive_vent = VentProperties(
        alpha_closure=0.05,
        clog_rate=10.0,
        min_efficiency=0.1,
        base_conductance_m3_per_sPa=1e-7,
        count=1,
    )
    clogged_mold = base_mold.model_copy(update={"vent": aggressive_vent})
    clogged = simulator.run(SYSTEM_R1, process, clogged_mold, TEST_QUALITY)

    assert min(clogged.vent_eff) == pytest.approx(aggressive_vent.min_efficiency, rel=0, abs=1e-9)
    assert clogged.p_max_Pa > baseline.p_max_Pa


def test_extreme_cold_mold_and_high_rh():
    simulator = MVP0DSimulator()
    process = _build_process(RH_ambient=1.0)
    mold = _build_mold(process).model_copy(update={"T_mold_init_C": -10.0})
    result = simulator.run(SYSTEM_R1, process, mold, TEST_QUALITY)
    assert result.t_demold_opt_s is not None
    assert result.water_risk_score > 0.1


def test_invalid_input_raises_value_error():
    simulator = MVP0DSimulator()
    process = _build_process()
    mold = _build_mold(process)
    # Pydantic waliduje na etapie tworzenia ProcessConditions, więc tu oczekujemy ValueError z konstrukcji
    with pytest.raises(ValueError):
        ProcessConditions(
            m_polyol=-1.0,
            m_iso=1.0,
            m_additives=0.0,
            nco_oh_index=1.0,
            T_polyol_in_C=20.0,
            T_iso_in_C=20.0,
            T_mold_init_C=20.0,
            T_ambient_C=20.0,
            RH_ambient=0.5,
            mixing_eff=0.9,
        )
