import pandas as pd
import pytest

from pur_mold_twin.logging.features import compute_basic_features


def test_compute_basic_features_handles_missing_measurements() -> None:
    sim = {
        "time_s": [0.0, 1.0, 2.0],
        "T_core_K": [300.0, 310.0, 305.0],
        "p_total_Pa": [101_000.0, 120_000.0, 110_000.0],
        "rho_moulded": 45.0,
        "t_demold_opt_s": 120.0,
    }

    features = compute_basic_features(sim, measured=pd.DataFrame())

    assert features.loc[0, "sim_T_core_max_C"] == pytest.approx(36.85)
    assert "meas_T_core_max_C" not in features.columns
    assert "meas_p_max_bar" not in features.columns


def test_compute_basic_features_merges_qc_and_process() -> None:
    sim = {
        "time_s": [0.0, 10.0],
        "T_core_K": [290.0, 300.0],
        "p_total_Pa": [101_000.0, 130_000.0],
        "rho_moulded": 40.0,
        "t_demold_opt_s": 200.0,
        "defect_risk": 0.2,
    }
    measured = pd.DataFrame(
        {
            "time_s": [0.0, 30.0, 60.0],
            "T_core_C": [25.0, 40.0, 45.0],
            "p_total_bar": [1.0, 1.5, 1.2],
        }
    )
    qc = {"defects": ["voids"], "defect_risk_operator": 0.7}
    process = {"t_demold_actual_s": 220.0, "T_polyol_in_C": 24.0}

    features = compute_basic_features(sim, measured=measured, qc=qc, process=process)

    assert features.loc[0, "meas_p_max_bar"] == 1.5
    assert features.loc[0, "any_defect"] == 1
    assert features.loc[0, "defect_risk"] == 0.7
    assert features.loc[0, "delta_t_demold_s"] == 20.0
