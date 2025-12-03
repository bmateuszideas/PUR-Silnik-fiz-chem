"""
Model versioning and manifest management for ML models (TODO3 Task 22).

This module provides:
- Model manifest schema (version, training date, git hash, metrics)
- Manifest creation during training
- Manifest loading and validation during inference
- Compatibility checking between model versions and code versions
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


@dataclass
class ModelMetadata:
    """
    Metadata for a trained ML model.
    
    Attributes:
        model_type: Type of model (e.g., 'defect_risk', 'defect_classifier')
        version: Semantic version (e.g., '1.0.0')
        trained_at: ISO timestamp of training completion
        git_commit: Git commit hash at time of training (if available)
        metrics: Dictionary of training/validation metrics
        features_used: List of feature names used in training
        framework: ML framework (e.g., 'sklearn==1.3.0')
        notes: Optional human-readable notes
    """
    model_type: str
    version: str
    trained_at: str
    git_commit: Optional[str] = None
    metrics: Dict[str, float] = None
    features_used: list[str] = None
    framework: str = "sklearn"
    notes: str = ""
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}
        if self.features_used is None:
            self.features_used = []


@dataclass
class ModelManifest:
    """
    Manifest file for all models in the models/ directory.
    
    Contains metadata for each trained model to enable version tracking
    and compatibility checking.
    """
    models: Dict[str, ModelMetadata]
    created_at: str
    updated_at: str
    
    def to_dict(self) -> dict:
        return {
            "models": {k: asdict(v) for k, v in self.models.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> ModelManifest:
        models = {
            k: ModelMetadata(**v) for k, v in data.get("models", {}).items()
        }
        return cls(
            models=models,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


def get_git_commit_hash() -> Optional[str]:
    """
    Get current git commit hash.
    
    Returns None if not in a git repository or git is not available.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def create_model_metadata(
    model_type: str,
    version: str,
    metrics: Dict[str, float],
    features_used: list[str],
    framework: str = "sklearn",
    notes: str = "",
) -> ModelMetadata:
    """
    Create model metadata for a newly trained model.
    
    Automatically captures training timestamp and git commit hash.
    """
    return ModelMetadata(
        model_type=model_type,
        version=version,
        trained_at=datetime.now().isoformat(),
        git_commit=get_git_commit_hash(),
        metrics=metrics,
        features_used=features_used,
        framework=framework,
        notes=notes,
    )


def save_manifest(manifest: ModelManifest, models_dir: Path = Path("models")) -> None:
    """
    Save model manifest to models/manifest.json.
    
    Updates the 'updated_at' timestamp automatically.
    """
    models_dir.mkdir(parents=True, exist_ok=True)
    manifest.updated_at = datetime.now().isoformat()
    
    manifest_path = models_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest.to_dict(), f, indent=2, ensure_ascii=False)


def load_manifest(models_dir: Path = Path("models")) -> Optional[ModelManifest]:
    """
    Load model manifest from models/manifest.json.
    
    Returns None if manifest doesn't exist.
    """
    manifest_path = models_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return ModelManifest.from_dict(data)


def update_manifest_for_model(
    model_type: str,
    metadata: ModelMetadata,
    models_dir: Path = Path("models"),
) -> None:
    """
    Update manifest with metadata for a specific model.
    
    Creates a new manifest if one doesn't exist.
    """
    manifest = load_manifest(models_dir)
    
    if manifest is None:
        manifest = ModelManifest(
            models={},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
    
    manifest.models[model_type] = metadata
    save_manifest(manifest, models_dir)


def get_model_info(model_type: str, models_dir: Path = Path("models")) -> Optional[ModelMetadata]:
    """
    Get metadata for a specific model from the manifest.
    
    Returns None if model not found in manifest.
    """
    manifest = load_manifest(models_dir)
    if manifest is None:
        return None
    
    return manifest.models.get(model_type)


def validate_model_compatibility(
    model_type: str,
    required_features: list[str],
    models_dir: Path = Path("models"),
) -> tuple[bool, str]:
    """
    Validate that a model is compatible with the current feature set.
    
    Returns:
        (is_compatible, message) tuple
    """
    metadata = get_model_info(model_type, models_dir)
    
    if metadata is None:
        return False, f"Model '{model_type}' not found in manifest"
    
    if not metadata.features_used:
        return True, "No feature validation (legacy model)"
    
    model_features = set(metadata.features_used)
    current_features = set(required_features)
    
    if model_features != current_features:
        missing = model_features - current_features
        extra = current_features - model_features
        
        msg_parts = []
        if missing:
            msg_parts.append(f"Missing features: {sorted(missing)}")
        if extra:
            msg_parts.append(f"Extra features: {sorted(extra)}")
        
        return False, "; ".join(msg_parts)
    
    return True, "Compatible"
