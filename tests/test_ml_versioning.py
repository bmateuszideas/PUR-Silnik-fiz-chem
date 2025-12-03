"""
Tests for ML model versioning system (TODO3 Task 22).

Tests cover:
- Manifest creation and loading
- Model metadata generation (with git hash)
- Manifest updates for multiple models
- Compatibility checking between model versions
- Integration with training and inference
"""
import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from pur_mold_twin.ml.versioning import (
    ModelMetadata,
    ModelManifest,
    create_model_metadata,
    save_manifest,
    load_manifest,
    update_manifest_for_model,
    get_model_info,
    validate_model_compatibility,
    get_git_commit_hash,
)


def test_model_metadata_creation():
    """Test creating model metadata with all fields."""
    metadata = create_model_metadata(
        model_type="test_model",
        version="1.0.0",
        metrics={"accuracy": 0.95, "f1": 0.92},
        features_used=["feature1", "feature2", "feature3"],
        framework="sklearn==1.3.0",
        notes="Test model",
    )
    
    assert metadata.model_type == "test_model"
    assert metadata.version == "1.0.0"
    assert metadata.metrics == {"accuracy": 0.95, "f1": 0.92}
    assert metadata.features_used == ["feature1", "feature2", "feature3"]
    assert metadata.framework == "sklearn==1.3.0"
    assert metadata.notes == "Test model"
    assert metadata.trained_at  # Should have timestamp
    
    # Git commit hash may or may not be present depending on environment
    # Just check it's a string or None
    assert metadata.git_commit is None or isinstance(metadata.git_commit, str)


def test_git_commit_hash():
    """Test git commit hash retrieval."""
    commit_hash = get_git_commit_hash()
    
    # In a git repo, should return a 40-char hex string
    # Outside git repo, should return None
    if commit_hash:
        assert isinstance(commit_hash, str)
        assert len(commit_hash) == 40
        assert all(c in "0123456789abcdef" for c in commit_hash)


def test_manifest_save_and_load():
    """Test saving and loading manifest from disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        models_dir = Path(tmpdir)
        
        # Create manifest with test models
        metadata1 = ModelMetadata(
            model_type="model_a",
            version="1.0.0",
            trained_at=datetime.now().isoformat(),
            metrics={"mae": 0.1},
            features_used=["f1", "f2"],
        )
        
        metadata2 = ModelMetadata(
            model_type="model_b",
            version="2.0.0",
            trained_at=datetime.now().isoformat(),
            metrics={"f1": 0.9},
            features_used=["f1", "f2", "f3"],
        )
        
        manifest = ModelManifest(
            models={"model_a": metadata1, "model_b": metadata2},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        
        # Save
        save_manifest(manifest, models_dir)
        
        # Check file exists
        manifest_path = models_dir / "manifest.json"
        assert manifest_path.exists()
        
        # Load
        loaded = load_manifest(models_dir)
        assert loaded is not None
        assert len(loaded.models) == 2
        assert "model_a" in loaded.models
        assert "model_b" in loaded.models
        assert loaded.models["model_a"].version == "1.0.0"
        assert loaded.models["model_b"].version == "2.0.0"


def test_manifest_update_for_model():
    """Test updating manifest with new model metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        models_dir = Path(tmpdir)
        
        # Create first model
        metadata1 = create_model_metadata(
            model_type="model_x",
            version="1.0.0",
            metrics={"accuracy": 0.8},
            features_used=["a", "b"],
        )
        update_manifest_for_model("model_x", metadata1, models_dir)
        
        # Check manifest created
        manifest = load_manifest(models_dir)
        assert manifest is not None
        assert len(manifest.models) == 1
        assert "model_x" in manifest.models
        
        # Add second model
        metadata2 = create_model_metadata(
            model_type="model_y",
            version="1.0.0",
            metrics={"f1": 0.85},
            features_used=["a", "b", "c"],
        )
        update_manifest_for_model("model_y", metadata2, models_dir)
        
        # Check both models present
        manifest = load_manifest(models_dir)
        assert len(manifest.models) == 2
        assert "model_x" in manifest.models
        assert "model_y" in manifest.models


def test_get_model_info():
    """Test retrieving info for a specific model."""
    with tempfile.TemporaryDirectory() as tmpdir:
        models_dir = Path(tmpdir)
        
        metadata = create_model_metadata(
            model_type="test_model",
            version="3.1.4",
            metrics={"loss": 0.05},
            features_used=["x1", "x2"],
        )
        update_manifest_for_model("test_model", metadata, models_dir)
        
        # Get info
        info = get_model_info("test_model", models_dir)
        assert info is not None
        assert info.version == "3.1.4"
        assert info.metrics == {"loss": 0.05}
        
        # Non-existent model
        info_missing = get_model_info("nonexistent", models_dir)
        assert info_missing is None


def test_validate_model_compatibility_exact_match():
    """Test compatibility validation with exact feature match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        models_dir = Path(tmpdir)
        
        features = ["feat_a", "feat_b", "feat_c"]
        metadata = create_model_metadata(
            model_type="compat_model",
            version="1.0.0",
            metrics={},
            features_used=features,
        )
        update_manifest_for_model("compat_model", metadata, models_dir)
        
        # Exact match - should be compatible
        is_compat, msg = validate_model_compatibility("compat_model", features, models_dir)
        assert is_compat
        assert msg == "Compatible"


def test_validate_model_compatibility_missing_features():
    """Test compatibility validation with missing features."""
    with tempfile.TemporaryDirectory() as tmpdir:
        models_dir = Path(tmpdir)
        
        # Model trained with 3 features
        trained_features = ["feat_a", "feat_b", "feat_c"]
        metadata = create_model_metadata(
            model_type="compat_model",
            version="1.0.0",
            metrics={},
            features_used=trained_features,
        )
        update_manifest_for_model("compat_model", metadata, models_dir)
        
        # Current code only has 2 features (missing feat_c)
        current_features = ["feat_a", "feat_b"]
        is_compat, msg = validate_model_compatibility("compat_model", current_features, models_dir)
        
        assert not is_compat
        assert "Missing features" in msg
        assert "feat_c" in msg


def test_validate_model_compatibility_extra_features():
    """Test compatibility validation with extra features."""
    with tempfile.TemporaryDirectory() as tmpdir:
        models_dir = Path(tmpdir)
        
        # Model trained with 2 features
        trained_features = ["feat_a", "feat_b"]
        metadata = create_model_metadata(
            model_type="compat_model",
            version="1.0.0",
            metrics={},
            features_used=trained_features,
        )
        update_manifest_for_model("compat_model", metadata, models_dir)
        
        # Current code has 3 features (added feat_c)
        current_features = ["feat_a", "feat_b", "feat_c"]
        is_compat, msg = validate_model_compatibility("compat_model", current_features, models_dir)
        
        assert not is_compat
        assert "Extra features" in msg
        assert "feat_c" in msg


def test_validate_model_compatibility_nonexistent_model():
    """Test compatibility check for non-existent model."""
    with tempfile.TemporaryDirectory() as tmpdir:
        models_dir = Path(tmpdir)
        
        is_compat, msg = validate_model_compatibility("missing_model", ["f1"], models_dir)
        assert not is_compat
        assert "not found in manifest" in msg


def test_manifest_json_structure():
    """Test that manifest JSON has expected structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        models_dir = Path(tmpdir)
        
        metadata = create_model_metadata(
            model_type="json_test",
            version="1.0.0",
            metrics={"metric1": 0.5},
            features_used=["f1", "f2"],
            notes="Test",
        )
        update_manifest_for_model("json_test", metadata, models_dir)
        
        # Read raw JSON
        manifest_path = models_dir / "manifest.json"
        with open(manifest_path, "r") as f:
            data = json.load(f)
        
        # Check structure
        assert "models" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "json_test" in data["models"]
        
        model_data = data["models"]["json_test"]
        assert model_data["model_type"] == "json_test"
        assert model_data["version"] == "1.0.0"
        assert model_data["metrics"] == {"metric1": 0.5}
        assert model_data["features_used"] == ["f1", "f2"]
        assert model_data["trained_at"]  # Timestamp present


def test_manifest_empty_models():
    """Test creating manifest with no models."""
    with tempfile.TemporaryDirectory() as tmpdir:
        models_dir = Path(tmpdir)
        
        manifest = ModelManifest(
            models={},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        save_manifest(manifest, models_dir)
        
        loaded = load_manifest(models_dir)
        assert loaded is not None
        assert len(loaded.models) == 0


def test_load_manifest_nonexistent():
    """Test loading manifest from directory without manifest file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        models_dir = Path(tmpdir)
        
        manifest = load_manifest(models_dir)
        assert manifest is None
