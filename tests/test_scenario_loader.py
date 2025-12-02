import pytest
from pathlib import Path

try:
    from ruamel.yaml import YAML  # noqa: F401
    RUAMEL_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover
    RUAMEL_AVAILABLE = False

try:
    import pydantic  # noqa: F401
    PYDANTIC_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover
    PYDANTIC_AVAILABLE = False

from pur_mold_twin.configs import load_process_scenario, load_quality_preset


pytestmark = pytest.mark.skipif(
    not (RUAMEL_AVAILABLE and PYDANTIC_AVAILABLE),
    reason="ruamel.yaml/pydantic not installed",
)


def test_load_process_scenario_round_trip():
    scenario = load_process_scenario(Path("configs/scenarios/use_case_1.yaml"))
    assert scenario.system_id == "SYSTEM_R1"
    assert scenario.process.m_polyol == 1.0
    assert scenario.mold.mold_mass_kg == 120.0
    assert scenario.quality.H_24h_min_shore == 55.0


def test_load_quality_preset_default():
    quality = load_quality_preset(Path("configs/quality/default.yaml"))
    assert quality.H_demold_min_shore == 40.0
    assert quality.defect_risk_max == pytest.approx(0.1)
