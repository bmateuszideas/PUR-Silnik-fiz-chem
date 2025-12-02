from pathlib import Path
import shutil

import pandas as pd
import pytest

from pur_mold_twin.core.types import ProcessConditions
from pur_mold_twin.data.dataset import build_dataset
from pur_mold_twin.data.etl import build_process_conditions_from_logs, load_log_bundle
from pur_mold_twin.data.schema import FEATURE_COLUMNS


SAMPLE_LOG_DIR = Path("tests/data/ml/sample_log")
SAMPLE_SIM = Path("tests/data/ml/sample_sim_result.json")
TMP_ML_DIR = Path("tests/tmp_ml")


def test_load_log_bundle_merges_timeseries() -> None:
    bundle = load_log_bundle(SAMPLE_LOG_DIR)

    assert {"time_s", "T_core_C", "p_total_bar"}.issubset(bundle.measured.columns)
    assert bundle.measured["T_core_C"].max() == pytest.approx(80.0)
    assert bundle.qc["rho_moulded"] == pytest.approx(41.0)
    assert bundle.metadata["shot_id"] == "2025-01-01-1"

    process = build_process_conditions_from_logs(SAMPLE_LOG_DIR)
    assert isinstance(process, ProcessConditions)
    assert process.RH_ambient == pytest.approx(0.55)
    assert process.m_additives == pytest.approx(0.05)
    assert process.m_polyol == pytest.approx(1.0)


def test_build_dataset_from_directory() -> None:
    output = TMP_ML_DIR / "features.csv"
    if output.exists():
        output.unlink()
    output.parent.mkdir(parents=True, exist_ok=True)

    df, saved_path = build_dataset(SAMPLE_SIM, SAMPLE_LOG_DIR, output)

    assert saved_path.exists()
    assert saved_path.suffix in {".csv", ".parquet"}
    assert isinstance(df, pd.DataFrame)
    for col in FEATURE_COLUMNS:
        assert col in df.columns
    row = df.iloc[0]
    assert row["sim_p_max_bar"] == pytest.approx(1.8)
    assert row["meas_p_max_bar"] == pytest.approx(1.8)
    assert row["any_defect"] == 1


def test_log_bundle_handles_missing_files() -> None:
    log_dir = TMP_ML_DIR / "empty_log"
    if log_dir.exists():
        shutil.rmtree(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    bundle = load_log_bundle(log_dir)
    assert bundle.measured.empty

    process = build_process_conditions_from_logs(log_dir)
    assert process.m_polyol == pytest.approx(1.0)
    assert 0.0 <= process.RH_ambient <= 1.0
