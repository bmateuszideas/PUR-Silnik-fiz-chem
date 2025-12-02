"""
Simulation logging helpers.

Provides a thin, serializable wrapper around `SimulationResult` that can be
stored alongside metadata/inputs for later ETL and feature extraction.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.types import SimulationResult


@dataclass
class SimulationLog:
    """Container for simulation run data."""

    simulation: Dict[str, Any]
    metadata: Dict[str, Any]
    inputs: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {"metadata": self.metadata, "inputs": self.inputs, "simulation": self.simulation}


def build_simulation_log(
    result: SimulationResult,
    metadata: Optional[Dict[str, Any]] = None,
    inputs: Optional[Dict[str, Any]] = None,
) -> SimulationLog:
    """
    Wrap SimulationResult with optional metadata (shot_id, operator, timestamps)
    and inputs (process/mold/quality) so the log is self-contained.
    """

    return SimulationLog(
        simulation=result.to_dict(),
        metadata=metadata or {},
        inputs=inputs or {},
    )


def save_simulation_log(log: SimulationLog, path: Path) -> None:
    """Persist log to JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log.to_dict(), indent=2), encoding="utf-8")
