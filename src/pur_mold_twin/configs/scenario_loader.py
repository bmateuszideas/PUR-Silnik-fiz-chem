"""
Scenario/quality configuration loaders (YAML -> Pydantic models).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..core.types import (
    MoldProperties,
    ProcessConditions,
    QualityTargets,
    SimulationConfig,
)
from ..material_db.loader import _ensure_yaml_available  # reuse ruamel gate


@dataclass
class ProcessScenario:
    """Complete set of inputs required by MVP0DSimulator."""

    system_id: str
    process: ProcessConditions
    mold: MoldProperties
    quality: QualityTargets
    simulation: SimulationConfig


def _load_yaml(path: Path) -> dict:
    yaml = _ensure_yaml_available()
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Scenario file {path} must define a YAML mapping at the top level.")
    return data


def load_process_scenario(path: Path | str) -> ProcessScenario:
    """Load scenario describing process/mold/quality/simulation presets."""

    path = Path(path)
    data = _load_yaml(path)
    system_id = data["system_id"]
    process = ProcessConditions(**data["process"])
    mold = MoldProperties(**data["mold"])
    quality = QualityTargets(**data.get("quality", {}))
    simulation = SimulationConfig(**data.get("simulation", {}))
    return ProcessScenario(
        system_id=system_id,
        process=process,
        mold=mold,
        quality=quality,
        simulation=simulation,
    )


def load_quality_preset(path: Path | str) -> QualityTargets:
    """Load standalone QualityTargets preset (configs/quality/*.yaml)."""

    path = Path(path)
    data = _load_yaml(path)
    return QualityTargets(**data)
