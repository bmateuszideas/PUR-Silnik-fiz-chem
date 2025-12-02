"""
Dataset builder combining simulation logs and measured features.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd

from ..data.etl import LogBundle, load_log_bundle, load_measured_csv
from ..logging.features import compute_basic_features


def _load_simulation_payload(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "simulation" in payload:  # SimulationLog format
        return payload["simulation"]
    return payload


def _persist_features(features: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() == ".csv":
        features.to_csv(output_path, index=False)
        return output_path

    try:
        features.to_parquet(output_path, index=False)
        return output_path
    except ImportError:
        csv_path = output_path.with_suffix(".csv")
        features.to_csv(csv_path, index=False)
        return csv_path


def build_dataset(sim_path: Path, log_path: Optional[Path], output_path: Path) -> tuple[pd.DataFrame, Path]:
    """
    Build a feature DataFrame from simulation JSON and either:
    - a log directory (meta/process/qc + CSV sensors), or
    - a standalone measurements CSV (time_s,T_core_C,p_total_bar).
    Returns the dataframe and the path actually written (parquet or csv fallback).
    """

    sim = _load_simulation_payload(sim_path)
    measured = None
    qc = None
    process = None

    if log_path:
        if log_path.is_dir():
            bundle: LogBundle = load_log_bundle(log_path)
            measured = bundle.measured
            qc = bundle.qc
            process = bundle.process
        else:
            measured = load_measured_csv(log_path)

    features = compute_basic_features(sim, measured, qc=qc, process=process)
    saved_path = _persist_features(features, output_path)
    return features, saved_path
