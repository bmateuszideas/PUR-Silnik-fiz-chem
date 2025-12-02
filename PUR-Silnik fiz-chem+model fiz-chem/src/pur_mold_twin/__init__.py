"""
PUR-MOLD-TWIN package root.

Exports key data structures so downstream modules and CLI can rely on a single entry point.
"""

from .core.mvp0d import MVP0DSimulator  # noqa: F401
from .core.types import (  # noqa: F401
    MoldProperties,
    ProcessConditions,
    QualityTargets,
    SimulationConfig,
    SimulationResult,
    VentProperties,
    WaterBalance,
)
from .material_db.models import MaterialSystem  # noqa: F401
from .optimizer import (  # noqa: F401
    CandidateEvaluation,
    ConstraintReport,
    OptimizationCandidate,
    OptimizationConfig,
    OptimizationResult,
    OptimizerBounds,
    ProcessOptimizer,
)

__all__ = [
    "MaterialSystem",
    "ProcessConditions",
    "MoldProperties",
    "VentProperties",
    "QualityTargets",
    "SimulationConfig",
    "SimulationResult",
    "WaterBalance",
    "MVP0DSimulator",
    "ProcessOptimizer",
    "OptimizerBounds",
    "OptimizationConfig",
    "OptimizationCandidate",
    "OptimizationResult",
    "CandidateEvaluation",
    "ConstraintReport",
]
