"""
ETL helpers for processing raw process logs into ProcessConditions-like dicts.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd
from ruamel.yaml import YAML

from ..core.types import ProcessConditions


DEFAULT_PROCESS_VALUES: Dict[str, float] = {
    "m_polyol": 1.0,
    "m_iso": 1.0,
    "m_additives": 0.0,
    "T_polyol_in_C": 23.0,
    "T_iso_in_C": 23.0,
    "T_mold_init_C": 40.0,
    "T_ambient_C": 25.0,
    "RH_ambient": 0.5,
    "mixing_eff": 1.0,
}


@dataclass
class LogBundle:
    process: Dict
    measured: pd.DataFrame
    qc: Dict
    metadata: Dict


def _load_yaml(path: Path) -> Dict:
    if not path.exists():
        return {}
    yaml = YAML(typ="safe")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.load(handle) or {}


def _merge_frames_on_time(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()
    merged = reduce(lambda left, right: left.merge(right, on="time_s", how="outer"), frames)
    return merged.sort_values("time_s").reset_index(drop=True)


def load_log_bundle(log_dir: Path) -> LogBundle:
    """
    Load a log directory containing:
    - meta.yaml (mandatory fields: shot_id/system_id optional)
    - process.yaml (optional overrides)
    - sensors_core_temp.csv, sensors_pressure.csv (optional timeseries)
    - qc.yaml (optional QC results)
    """

    meta = _load_yaml(log_dir / "meta.yaml")
    process_yaml = _load_yaml(log_dir / "process.yaml")
    qc = _load_yaml(log_dir / "qc.yaml")

    process = {**DEFAULT_PROCESS_VALUES, **process_yaml, **meta.get("process", {})}
    if "RH_ambient_pct" in process:
        process["RH_ambient"] = float(process["RH_ambient_pct"]) * 0.01

    frames: list[pd.DataFrame] = []
    core_temp = log_dir / "sensors_core_temp.csv"
    pressure = log_dir / "sensors_pressure.csv"
    if core_temp.exists():
        frames.append(pd.read_csv(core_temp))
    if pressure.exists():
        frames.append(pd.read_csv(pressure))

    measured = _merge_frames_on_time(frames) if frames else pd.DataFrame()

    metadata = {k: v for k, v in meta.items() if k != "process"}
    return LogBundle(process=process, measured=measured, qc=qc, metadata=metadata)


def load_measured_csv(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists():
        return None
    return pd.read_csv(path)


def build_process_conditions_from_logs(log_dir: Path) -> ProcessConditions:
    """
    Construct ProcessConditions from a log directory, filling reasonable defaults
    when data is missing (see DEFAULT_PROCESS_VALUES).
    """

    bundle = load_log_bundle(log_dir)
    data = {**DEFAULT_PROCESS_VALUES, **bundle.process}
    return ProcessConditions(**data)


def build_log_bundles_from_source(source, query) -> Iterable[LogBundle]:
    """
    Adapter around ProcessLogSource-like objects.

    The `source` is expected to implement `fetch_shots(query)` and return
    LogBundle instances; this tiny helper exists to keep `etl.py` as the
    central place wiring sources and downstream consumers.
    """

    return source.fetch_shots(query)
