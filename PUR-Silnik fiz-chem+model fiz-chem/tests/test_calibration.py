from pathlib import Path

import numpy as np
import pytest

from pur_mold_twin.calibration.cost import CalibrationTargets, aggregate_cost, rmse_core_temperature
from pur_mold_twin.calibration.fit import fit_parameters


def test_rmse_core_temperature():
    sim_time = [0, 10, 20]
    sim_temp = [300.0, 310.0, 320.0]  # K
    ref = [{"time_s": 5.0, "T_core_C": 35.0}]  # 308.15 K
    rmse = rmse_core_temperature(sim_time, sim_temp, ref)
    assert np.isclose(rmse, abs(308.15 - 305.0), atol=0.5)


def test_aggregate_cost_components():
    sim = {"time_s": [0, 10], "T_core_K": [300.0, 310.0], "p_max_Pa": 400000.0, "rho_moulded": 40.0}
    targets = CalibrationTargets(
        T_core_profile=[{"time_s": 5.0, "T_core_C": 35.0}],
        p_max_bar=4.2,
        rho_moulded=41.0,
    )
    total, breakdown = aggregate_cost(sim, targets)
    assert "rmse_T_core_K" in breakdown
    assert "p_max_bar_abs" in breakdown
    assert "rho_moulded_abs" in breakdown
    assert total > 0


def test_fit_parameters_converges_on_linear_model():
    # Simple linear "simulation": y = a * t + b; target is slope=2, intercept=1
    true_params = {"a": 2.0, "b": 1.0}
    times = np.linspace(0, 5, 6)
    ref = [{"time_s": t, "T_core_C": true_params["a"] * t + true_params["b"]} for t in times]

    def simulate(params):
        a, b = params["a"], params["b"]
        temps = [a * t + b for t in times]
        return {"time_s": list(times), "T_core_K": [v + 273.15 for v in temps]}

    targets = CalibrationTargets(T_core_profile=ref)
    init = {"a": 1.0, "b": 0.0}
    result = fit_parameters(init, simulate, targets)
    assert result.cost < 1e-3
    assert abs(result.params["a"] - true_params["a"]) < 0.1
    assert abs(result.params["b"] - true_params["b"]) < 0.1
