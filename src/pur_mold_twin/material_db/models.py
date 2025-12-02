"""
Data models for material systems stored in configs/systems.

The fields mirror TODO1 requirements and the tables described in docs/MODEL_OVERVIEW.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


def _require_positive(value: float | None, name: str) -> None:
    if value is None:
        return
    if value <= 0:
        raise ValueError(f"{name} must be > 0 (got {value}).")


def _require_fraction(value: float | None, name: str) -> None:
    if value is None:
        return
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1 (got {value}).")


@dataclass
class MaterialMetadata:
    """Optional metadata that helps trace the origin of the TDS/SDS."""

    vendor: Optional[str] = None
    documents: List[str] = field(default_factory=list)
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["MaterialMetadata"]:
        if not data:
            return None
        return cls(
            vendor=data.get("vendor"),
            documents=list(data.get("documents", [])),
            notes=data.get("notes"),
        )


@dataclass
class PolyolComponent:
    """Polyol/system component with blowing additives."""

    name: str
    oh_number_mgKOH_per_g: float
    functionality: float
    density_kg_per_m3: float
    viscosity_mPa_s: float
    water_fraction: float
    pentane_fraction: float = 0.0
    cream_time_s: Optional[float] = None
    gel_time_s: Optional[float] = None
    rise_time_s: Optional[float] = None
    tack_free_time_s: Optional[float] = None
    metadata: Optional[dict] = None

    def __post_init__(self) -> None:
        _require_positive(self.oh_number_mgKOH_per_g, "oh_number_mgKOH_per_g")
        _require_positive(self.functionality, "functionality")
        _require_positive(self.density_kg_per_m3, "density_kg_per_m3")
        _require_positive(self.viscosity_mPa_s, "viscosity_mPa_s")
        _require_fraction(self.water_fraction, "water_fraction")
        _require_fraction(self.pentane_fraction, "pentane_fraction")

    @classmethod
    def from_dict(cls, data: dict) -> "PolyolComponent":
        meta = data.pop("metadata", None)
        obj = cls(**data)
        obj.metadata = meta
        return obj


@dataclass
class IsoComponent:
    """Isocyanate component."""

    name: str
    nco_percent: float
    functionality: float
    density_kg_per_m3: float
    viscosity_mPa_s: float
    metadata: Optional[dict] = None

    def __post_init__(self) -> None:
        _require_positive(self.nco_percent, "nco_percent")
        _require_positive(self.functionality, "functionality")
        _require_positive(self.density_kg_per_m3, "density_kg_per_m3")
        _require_positive(self.viscosity_mPa_s, "viscosity_mPa_s")

    @classmethod
    def from_dict(cls, data: dict) -> "IsoComponent":
        meta = data.pop("metadata", None)
        obj = cls(**data)
        obj.metadata = meta
        return obj


@dataclass
class FoamTargets:
    """Free-rise and molded density targets."""

    rho_free_rise_target: float
    rho_moulded_target: float

    @classmethod
    def from_dict(cls, data: dict) -> "FoamTargets":
        return cls(**data)

    def __post_init__(self) -> None:
        _require_positive(self.rho_free_rise_target, "rho_free_rise_target")
        _require_positive(self.rho_moulded_target, "rho_moulded_target")



@dataclass
class MechanicalTargets:
    """Hardness targets used during calibration."""

    h_demold_target_shore: Optional[float]
    h_24h_target_shore: float

    @classmethod
    def from_dict(cls, data: dict) -> "MechanicalTargets":
        return cls(
            h_demold_target_shore=data.get("h_demold_target_shore"),
            h_24h_target_shore=data["h_24h_target_shore"],
        )

    def __post_init__(self) -> None:
        if self.h_demold_target_shore is not None and self.h_demold_target_shore <= 0:
            raise ValueError("h_demold_target_shore must be > 0 when provided.")
        _require_positive(self.h_24h_target_shore, "h_24h_target_shore")


@dataclass
class MaterialSystem:
    """Complete material system definition."""

    system_id: str
    description: str
    polyol: PolyolComponent
    isocyanate: IsoComponent
    foam_targets: FoamTargets
    mechanical_targets: MechanicalTargets
    metadata: Optional[MaterialMetadata] = None

    @property
    def has_pentane(self) -> bool:
        """Quick helper flag for logic that depends on physical blowing agents."""

        return self.polyol.pentane_fraction > 0

    def validate_required_fields(self) -> None:
        """Raise an error when critical fields required by the solver are missing."""

        missing: list[str] = []

        if self.polyol.oh_number_mgKOH_per_g is None:
            missing.append("polyol.oh_number_mgKOH_per_g")
        if self.polyol.functionality is None:
            missing.append("polyol.functionality")
        if self.polyol.density_kg_per_m3 is None:
            missing.append("polyol.density_kg_per_m3")
        if self.polyol.viscosity_mPa_s is None:
            missing.append("polyol.viscosity_mPa_s")
        if self.polyol.water_fraction is None:
            missing.append("polyol.water_fraction")
        if self.polyol.pentane_fraction is None:
            missing.append("polyol.pentane_fraction")

        if self.isocyanate.nco_percent is None:
            missing.append("isocyanate.nco_percent")
        if self.isocyanate.functionality is None:
            missing.append("isocyanate.functionality")
        if self.isocyanate.density_kg_per_m3 is None:
            missing.append("isocyanate.density_kg_per_m3")
        if self.isocyanate.viscosity_mPa_s is None:
            missing.append("isocyanate.viscosity_mPa_s")

        if self.foam_targets.rho_free_rise_target is None:
            missing.append("foam_targets.rho_free_rise_target")
        if self.foam_targets.rho_moulded_target is None:
            missing.append("foam_targets.rho_moulded_target")
        if self.mechanical_targets.h_24h_target_shore is None:
            missing.append("mechanical_targets.h_24h_target_shore")

        if missing:
            raise ValueError(
                f"MaterialSystem '{self.system_id}' is missing required fields: {', '.join(missing)}"
            )

    @classmethod
    def from_dict(cls, data: dict) -> "MaterialSystem":
        return cls(
            system_id=data["system_id"],
            description=data["description"],
            polyol=PolyolComponent.from_dict(data["polyol"]),
            isocyanate=IsoComponent.from_dict(data["isocyanate"]),
            foam_targets=FoamTargets.from_dict(data["foam_targets"]),
            mechanical_targets=MechanicalTargets.from_dict(data["mechanical_targets"]),
            metadata=MaterialMetadata.from_dict(data.get("metadata")),
        )
