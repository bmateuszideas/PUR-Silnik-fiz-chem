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

from pur_mold_twin.material_db.loader import load_material_catalog, load_material_system


pytestmark = pytest.mark.skipif(
    not (RUAMEL_AVAILABLE and PYDANTIC_AVAILABLE),
    reason="ruamel.yaml/pydantic not installed",
)


def test_load_material_catalog_returns_named_systems():
    catalog = load_material_catalog(Path("configs/systems/jr_purtec_catalog.yaml"))
    assert "SYSTEM_R1" in catalog
    assert catalog["SYSTEM_R1"].polyol.oh_number_mgKOH_per_g == 250.0


def test_load_material_system_single_file(tmp_path: Path):
    sample = tmp_path / "system.yaml"
    sample.write_text(
        "---\n"
        "system_id: TEST_SYSTEM\n"
        "description: Test system\n"
        "polyol:\n"
        "  name: POLYOL\n"
        "  oh_number_mgKOH_per_g: 200\n"
        "  functionality: 3.0\n"
        "  density_kg_per_m3: 1000\n"
        "  viscosity_mPa_s: 500\n"
        "  water_fraction: 0.01\n"
        "  pentane_fraction: 0.0\n"
        "isocyanate:\n"
        "  name: ISO\n"
        "  nco_percent: 31\n"
        "  functionality: 2.7\n"
        "  density_kg_per_m3: 1200\n"
        "  viscosity_mPa_s: 200\n"
        "foam_targets:\n"
        "  rho_free_rise_target: 30\n"
        "  rho_moulded_target: 40\n"
        "mechanical_targets:\n"
        "  h_demold_target_shore: 40\n"
        "  h_24h_target_shore: 55\n",
        encoding="utf-8",
    )
    system = load_material_system(sample)
    assert system.system_id == "TEST_SYSTEM"
    assert system.polyol.water_fraction == 0.01
