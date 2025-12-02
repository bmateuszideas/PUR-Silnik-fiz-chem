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


def test_build_process_conditions_prefers_meta_overrides(tmp_path: Path) -> None:
    log_dir = tmp_path / "custom_log"
    log_dir.mkdir(parents=True)
    (log_dir / "meta.yaml").write_text(
        """
shot_id: TEST-1
process:
  T_mold_init_C: 55.0
  mixing_eff: 0.7
        """,
        encoding="utf-8",
    )
    (log_dir / "process.yaml").write_text("{}\n", encoding="utf-8")

    process = build_process_conditions_from_logs(log_dir)

    assert process.T_mold_init_C == pytest.approx(55.0)
    assert process.mixing_eff == pytest.approx(0.7)


def test_build_dataset_falls_back_to_csv_when_parquet_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    output = TMP_ML_DIR / "features.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)

    calls = {"parquet": 0, "csv": 0}

    def _raise_import_error(*args, **kwargs):
        calls["parquet"] += 1
        raise ImportError("pyarrow not installed")

    original_to_csv = pd.DataFrame.to_csv

    def _track_csv(self, *args, **kwargs):
        calls["csv"] += 1
        return original_to_csv(self, *args, **kwargs)

    monkeypatch.setattr(pd.DataFrame, "to_parquet", _raise_import_error)
    monkeypatch.setattr(pd.DataFrame, "to_csv", _track_csv)

    df, saved = build_dataset(SAMPLE_SIM, SAMPLE_LOG_DIR, output)

    assert df is not None
    assert saved.suffix == ".csv"
    assert calls["parquet"] == 1
    assert calls["csv"] == 1
