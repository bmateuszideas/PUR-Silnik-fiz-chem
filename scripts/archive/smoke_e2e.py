"""
Simple end-to-end smoke test for a from-install scenario.

This script assumes that pur-mold-twin is importable (installed into the
current interpreter environment). It is intended to be used in CI or manual
checks after `pip install .`.
"""

from __future__ import annotations

from pathlib import Path

from pur_mold_twin import MVP0DSimulator, ProcessConditions, MoldProperties
from pur_mold_twin.material_db.loader import load_material_catalog


def run_smoke() -> None:
    systems = load_material_catalog(Path("configs/systems/jr_purtec_catalog.yaml"))
    system = systems["SYSTEM_R1"]

    process = ProcessConditions(
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
    total_mass = process.total_mass
    target_rho = system.foam_targets.rho_moulded_target
    cavity_volume = total_mass / max(target_rho, 1e-6)
    mold = MoldProperties(
        cavity_volume_m3=cavity_volume,
        mold_surface_area_m2=0.8,
        mold_mass_kg=120.0,
    )
    simulator = MVP0DSimulator()
    result = simulator.run(system, process, mold)

    assert result.time_s, "Empty time series in smoke test"
    assert result.p_max_Pa > 0.0, "p_max_Pa must be positive in smoke test"
    assert result.rho_moulded > 0.0, "rho_moulded must be positive in smoke test"


if __name__ == "__main__":  # pragma: no cover
    run_smoke()
