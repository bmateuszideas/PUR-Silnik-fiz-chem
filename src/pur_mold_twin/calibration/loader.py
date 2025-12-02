"""
Utilities for loading calibration datasets (meta + measurement files).

Datasets follow the structure defined in docs/CALIBRATION.md:
<root>/measurements/meta.yaml, core_temp.csv, mold_temp.csv, pressure.csv,
density_mech.yaml. Only meta.yaml is mandatory; other files are optional.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

try:  # pandas opcjonalne (wspiera odczyt Parquet)
    import pandas as pd  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    pd = None  # type: ignore

from ..material_db.loader import _ensure_yaml_available  # reuse ruamel gate


@dataclass
class CalibrationDataset:
    """Container for calibration metadata and measurement profiles."""

    root: Path
    metadata: dict
    core_temperature: Optional[List[dict]] = None
    mold_temperature: Optional[List[dict]] = None
    pressure: Optional[List[dict]] = None
    density_mechanical: Optional[dict] = None

    def has_core_temperature(self) -> bool:
        return self.core_temperature is not None

    def has_pressure(self) -> bool:
        return self.pressure is not None


def load_calibration_dataset(path: Path | str) -> CalibrationDataset:
    """Load calibration dataset from the given directory."""

    base = Path(path)
    measurements_dir = base / "measurements"
    if not measurements_dir.exists():
        measurements_dir = base

    meta_path = measurements_dir / "meta.yaml"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing meta.yaml in {measurements_dir}")

    metadata = _load_yaml(meta_path)
    core_temp = _load_timeseries(measurements_dir, "core_temp")
    mold_temp = _load_timeseries(measurements_dir, "mold_temp")
    pressure = _load_timeseries(measurements_dir, "pressure")

    density_path = measurements_dir / "density_mech.yaml"
    density = _load_yaml(density_path) if density_path.exists() else None

    return CalibrationDataset(
        root=base,
        metadata=metadata,
        core_temperature=core_temp,
        mold_temperature=mold_temp,
        pressure=pressure,
        density_mechanical=density,
    )


def _load_yaml(path: Path) -> dict:
    yaml = _ensure_yaml_available()
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"File {path} must contain a YAML mapping.")
    return data


def _load_timeseries(directory: Path, stem: str) -> Optional[List[dict]]:
    csv_path = directory / f"{stem}.csv"
    parquet_path = directory / f"{stem}.parquet"
    if csv_path.exists():
        with csv_path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            return [_convert_row(row) for row in reader]
    if parquet_path.exists():
        if pd is None:  # pragma: no cover
            raise RuntimeError(
                f"Unable to read {parquet_path}: install pandas with pyarrow or provide CSV."
            )
        frame = pd.read_parquet(parquet_path)
        return frame.to_dict("records")
    return None


def _convert_row(row: dict) -> dict:
    out: dict[str, Any] = {}
    for key, value in row.items():
        if value is None:
            out[key] = None
            continue
        try:
            out[key] = float(value)
        except (TypeError, ValueError):
            out[key] = value
    return out
