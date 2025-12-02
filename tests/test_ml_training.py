from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from pur_mold_twin.ml.train_baseline import main as train_main


def test_train_baseline_produces_models_and_report(tmp_path: Path) -> None:
    features_path = tmp_path / "features.csv"
    df = pd.DataFrame(
        {
            "sim_T_core_max_C": [80.0, 85.0],
            "sim_p_max_bar": [3.5, 3.8],
            "defect_risk": [0.1, 0.2],
            "any_defect": [0, 1],
        }
    )
    df.to_csv(features_path, index=False)

    models_dir = tmp_path / "models"
    metrics_path = tmp_path / "reports" / "ml" / "metrics.md"

    # If sklearn/joblib are missing, the function will raise; we treat this as optional
    try:
        train_main(
            [
                "--features",
                str(features_path),
                "--models-dir",
                str(models_dir),
                "--metrics-path",
                str(metrics_path),
            ]
        )
    except ImportError:
        pytest.skip("ML extras (sklearn/joblib) not installed")

    assert models_dir.exists()
    model_files = list(models_dir.glob("*.pkl"))
    assert model_files
    assert metrics_path.exists()
    text = metrics_path.read_text(encoding="utf-8")
    assert "ML Baseline Training Report" in text

