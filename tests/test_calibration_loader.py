from pathlib import Path

import pytest

from pur_mold_twin.calibration import load_calibration_dataset

SAMPLE_DIR = Path("tests/data/calibration/sample")


def test_load_calibration_dataset_minimal():
    dataset = load_calibration_dataset(SAMPLE_DIR)
    assert dataset.metadata["shot_id"] == "SHOT_001"
    assert dataset.has_core_temperature()
    assert len(dataset.core_temperature) == 3
    assert dataset.density_mechanical["rho_moulded"] == 40.0


def test_missing_meta_raises():
    fake_dataset = Path("tests/tmp_cli/missing_dataset")
    (fake_dataset / "measurements").mkdir(parents=True, exist_ok=True)
    with pytest.raises(FileNotFoundError):
        load_calibration_dataset(fake_dataset)
