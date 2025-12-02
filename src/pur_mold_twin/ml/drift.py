from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


@dataclass
class DriftMetrics:
    column: str
    baseline_mean: Optional[float]
    current_mean: Optional[float]
    abs_delta: Optional[float]


@dataclass
class DriftReport:
    metrics: List[DriftMetrics]
    max_abs_delta: float


def _load_features(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Features file '{path}' not found")
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_parquet(path)


def compute_drift(
    baseline_path: Path,
    current_path: Path,
    columns: Optional[List[str]] = None,
) -> DriftReport:
    """
    Compute simple mean-based drift metrics between two feature datasets.

    For each selected column, the report contains baseline/current means and
    absolute difference. The overall max_abs_delta is used for alerting.
    """

    baseline = _load_features(baseline_path)
    current = _load_features(current_path)

    if columns is None:
        # default: core targets + key process features
        columns = [
            "defect_risk",
            "any_defect",
            "sim_p_max_bar",
            "sim_T_core_max_C",
            "proc_T_mold_init_C",
            "proc_RH_ambient",
        ]

    metrics: List[DriftMetrics] = []
    max_abs_delta = 0.0

    for col in columns:
        if col not in baseline.columns or col not in current.columns:
            metrics.append(DriftMetrics(col, None, None, None))
            continue
        base_series = baseline[col].dropna()
        curr_series = current[col].dropna()
        if base_series.empty or curr_series.empty:
            metrics.append(DriftMetrics(col, None, None, None))
            continue
        base_mean = float(np.mean(base_series))
        curr_mean = float(np.mean(curr_series))
        delta = abs(curr_mean - base_mean)
        max_abs_delta = max(max_abs_delta, delta)
        metrics.append(DriftMetrics(col, base_mean, curr_mean, delta))

    return DriftReport(metrics=metrics, max_abs_delta=max_abs_delta)


def classify_drift(report: DriftReport, warn_threshold: float = 0.1, alert_threshold: float = 0.2) -> str:
    """
    Classify drift severity based on max_abs_delta.

    Thresholds are in "feature units" and should be tuned per deployment;
    here we use generic defaults for initial pilots.
    """

    if report.max_abs_delta >= alert_threshold:
        return "ALERT"
    if report.max_abs_delta >= warn_threshold:
        return "WARNING"
    return "OK"

