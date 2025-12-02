from __future__ import annotations

from pathlib import Path

import pandas as pd

from pur_mold_twin.ml.drift import classify_drift, compute_drift


def test_compute_and_classify_drift() -> None:
    baseline = Path("tests/tmp_baseline.csv")
    current = Path("tests/tmp_current.csv")

    df_base = pd.DataFrame(
        {
            "defect_risk": [0.1, 0.2, 0.15],
            "any_defect": [0, 1, 0],
            "sim_p_max_bar": [3.5, 3.6, 3.7],
            "sim_T_core_max_C": [80.0, 82.0, 81.0],
            "proc_T_mold_init_C": [40.0, 40.0, 40.0],
            "proc_RH_ambient": [0.5, 0.5, 0.5],
        }
    )
    df_curr = pd.DataFrame(
        {
            "defect_risk": [0.3, 0.35, 0.4],
            "any_defect": [1, 1, 1],
            "sim_p_max_bar": [3.8, 3.9, 4.0],
            "sim_T_core_max_C": [85.0, 86.0, 87.0],
            "proc_T_mold_init_C": [40.0, 40.0, 40.0],
            "proc_RH_ambient": [0.6, 0.6, 0.6],
        }
    )
    df_base.to_csv(baseline, index=False)
    df_curr.to_csv(current, index=False)

    report = compute_drift(baseline, current)
    assert report.metrics
    assert report.max_abs_delta > 0.0

    status_ok = classify_drift(report, warn_threshold=10.0, alert_threshold=20.0)
    assert status_ok == "OK"

    status_alert = classify_drift(report, warn_threshold=0.01, alert_threshold=0.02)
    assert status_alert in {"WARNING", "ALERT"}

