"""
Utilities for loading material systems defined as YAML.

System files reside under configs/systems/NAME.yaml (see docs/STRUCTURE.md).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

try:  # ruamel.yaml zapewnia pelne wsparcie YAML (multi-doc, komentarze)
    from ruamel.yaml import YAML  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    YAML = None

from .models import MaterialSystem


def _ensure_yaml_available() -> "YAML":
    if YAML is None:  # pragma: no cover
        raise RuntimeError(
            "ruamel.yaml is required to load YAML files. "
            "Install it via pip (see py_lib.md) before using material/scenario loaders."
        )
    return YAML(typ="safe")


def _load_yaml_documents(path: Path) -> List[dict]:
    yaml = _ensure_yaml_available()
    with path.open("r", encoding="utf-8") as handle:
        data = list(yaml.load_all(handle))
    return [doc for doc in data if doc]


def load_material_system(path: Path | str) -> MaterialSystem:
    """Load a single material system from YAML."""

    path = Path(path)
    docs = _load_yaml_documents(path)
    if len(docs) > 1:
        raise ValueError(
            f"File {path} contains multiple documents. Use load_material_catalog or split into separate files."
        )
    data = docs[0]
    return MaterialSystem.from_dict(data)


def load_material_catalog(path: Path | str) -> Dict[str, MaterialSystem]:
    """Load multiple systems from a single multi-document YAML."""

    path = Path(path)
    docs = _load_yaml_documents(path)
    systems: Dict[str, MaterialSystem] = {}
    for doc in docs:
        system = MaterialSystem.from_dict(doc)
        if system.system_id in systems:
            raise ValueError(f"Duplicate system_id '{system.system_id}' in catalog {path}")
        systems[system.system_id] = system
    return systems


def load_material_systems(
    directory: Path | str, pattern: str = "*.yaml"
) -> Dict[str, MaterialSystem]:
    """Load all systems in a directory and return them keyed by system_id.

    Files containing multiple documents (catalog) are expanded inline.
    """

    directory = Path(directory)
    systems: Dict[str, MaterialSystem] = {}
    for file in sorted(directory.glob(pattern)):
        docs = _load_yaml_documents(file)
        for doc in docs:
            system = MaterialSystem.from_dict(doc)
            if system.system_id in systems:
                # Skip duplicates when a catalog and a single file both exist.
                # Prefer the first occurrence to avoid overwriting user-provided files.
                continue
            systems[system.system_id] = system
    return systems
