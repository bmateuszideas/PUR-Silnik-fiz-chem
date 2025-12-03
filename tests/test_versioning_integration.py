"""
Integration test for ML versioning system with actual training pipeline.

Tests the complete flow:
1. Generate synthetic feature data
2. Train models using train_baseline
3. Verify manifest.json is created with correct metadata
4. Load models via inference and check metadata attachment
"""
from pathlib import Path
import tempfile
import pandas as pd
import numpy as np

import pytest

from pur_mold_twin.ml.inference import _load_models, attach_ml_predictions
from pur_mold_twin.ml.versioning import load_manifest, get_model_info


def test_versioning_integration_with_training(tmp_path):
    """Test full integration: train models → manifest created → inference loads metadata."""
    
    # Import fresh to avoid cached pd=None
    import importlib
    import sys
    
    # Reload the module to ensure fresh imports
    if "pur_mold_twin.ml.train_baseline" in sys.modules:
        importlib.reload(sys.modules["pur_mold_twin.ml.train_baseline"])
    
    from pur_mold_twin.ml.train_baseline import main as train_main_fn
    
    # 1. Create synthetic feature dataset
    np.random.seed(42)
    n_samples = 100
    
    # Create realistic features based on actual model
    df = pd.DataFrame({
        # Basic process params
        "iso_index": np.random.uniform(95, 115, n_samples),
        "t_iso_c": np.random.uniform(15, 35, n_samples),
        "t_poly_c": np.random.uniform(15, 35, n_samples),
        "t_mold_c": np.random.uniform(40, 80, n_samples),
        "shot_size_g": np.random.uniform(180, 220, n_samples),
        "mix_time_s": np.random.uniform(1.0, 3.0, n_samples),
        
        # Reaction kinetics features
        "t_gel_s": np.random.uniform(40, 120, n_samples),
        "t_rise_s": np.random.uniform(100, 300, n_samples),
        "t_cure_s": np.random.uniform(200, 600, n_samples),
        
        # Labels
        "defect_risk": np.random.uniform(0, 0.3, n_samples),
        "has_defect": np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
    })
    
    features_path = tmp_path / "features.parquet"
    df.to_parquet(features_path, index=False)
    
    models_dir = tmp_path / "models"
    models_dir.mkdir(exist_ok=True)
    
    metrics_path = tmp_path / "metrics.md"
    
    # 2. Train models (this should create manifest.json)
    try:
        train_main_fn([
            "--features", str(features_path),
            "--models-dir", str(models_dir),
            "--metrics-path", str(metrics_path),
        ])
    except ImportError:
        pytest.skip("ML extras (sklearn/joblib/pandas) not installed")
    
    # 3. Verify manifest was created
    manifest_path = models_dir / "manifest.json"
    assert manifest_path.exists(), "manifest.json should be created during training"
    
    manifest = load_manifest(models_dir)
    assert manifest is not None
    assert len(manifest.models) == 2  # defect_risk and defect_classifier
    
    # Check defect_risk model metadata
    risk_info = get_model_info("defect_risk", models_dir)
    assert risk_info is not None
    assert risk_info.model_type == "defect_risk"
    assert risk_info.version == "1.0.0"
    assert "mae_defect_risk" in risk_info.metrics or "mae" in risk_info.metrics
    assert len(risk_info.features_used) > 0
    assert risk_info.trained_at  # Timestamp present
    
    # Check defect_classifier metadata
    clf_info = get_model_info("defect_classifier", models_dir)
    assert clf_info is not None
    assert clf_info.model_type == "defect_classifier"
    assert clf_info.version == "1.0.0"
    assert clf_info.metrics is not None  # May be empty dict if no valid metrics
    assert len(clf_info.features_used) > 0
    
    # 4. Load models via inference and check manifest is loaded
    loaded = _load_models(models_dir)
    assert loaded.manifest_data is not None
    assert "defect_risk" in loaded.manifest_data["models"]
    assert "defect_classifier" in loaded.manifest_data["models"]
    
    # 5. Test attach_ml_predictions includes metadata
    # Create dummy simulation result
    sim_result = {
        "simulation_id": "test-123",
        "conditions": {
            "iso_index": 105.0,
            "t_iso_c": 25.0,
            "t_poly_c": 25.0,
            "t_mold_c": 60.0,
            "shot_size_g": 200.0,
            "mix_time_s": 2.0,
        },
        "summary": {
            "t_gel_s": 80.0,
            "t_rise_s": 200.0,
            "t_cure_s": 400.0,
        },
    }
    
    # Attach predictions (which should include metadata)
    result_with_ml = attach_ml_predictions(sim_result, loaded)
    
    # Verify metadata is attached
    assert "ml_model_metadata" in result_with_ml
    metadata = result_with_ml["ml_model_metadata"]
    
    assert "defect_risk" in metadata
    assert metadata["defect_risk"]["version"] == "1.0.0"
    assert "trained_at" in metadata["defect_risk"]
    assert "metrics" in metadata["defect_risk"]
    
    assert "defect_classifier" in metadata
    assert metadata["defect_classifier"]["version"] == "1.0.0"
    assert "trained_at" in metadata["defect_classifier"]
    
    print("\n✅ Integration test passed:")
    print(f"   - Trained models in {models_dir}")
    print(f"   - Created manifest with {len(manifest.models)} models")
    print(f"   - Risk model version: {risk_info.version}, MAE: {risk_info.metrics.get('mae', 'N/A')}")
    print(f"   - Classifier version: {clf_info.version}, Accuracy: {clf_info.metrics.get('accuracy', 'N/A')}")
    print(f"   - Metadata successfully attached to inference results")


def test_versioning_feature_compatibility_check(tmp_path):
    """Test that feature compatibility checking works after training."""
    
    # Create minimal synthetic data
    np.random.seed(123)
    df = pd.DataFrame({
        "iso_index": np.random.uniform(100, 110, 50),
        "t_iso_c": np.random.uniform(20, 30, 50),
        "t_poly_c": np.random.uniform(20, 30, 50),
        "t_mold_c": np.random.uniform(50, 70, 50),
        "shot_size_g": np.random.uniform(190, 210, 50),
        "mix_time_s": np.random.uniform(1.5, 2.5, 50),
        "t_gel_s": np.random.uniform(60, 100, 50),
        "t_rise_s": np.random.uniform(150, 250, 50),
        "t_cure_s": np.random.uniform(300, 500, 50),
        "defect_risk": np.random.uniform(0, 0.2, 50),
        "has_defect": np.random.choice([0, 1], 50, p=[0.85, 0.15]),
    })
    
    features_path = tmp_path / "features.parquet"
    df.to_parquet(features_path, index=False)
    
    models_dir = tmp_path / "models"
    models_dir.mkdir(exist_ok=True)
    
    # Train
    from pur_mold_twin.ml.train_baseline import main as train_main_fn
    try:
        train_main_fn([
            "--features", str(features_path),
            "--models-dir", str(models_dir),
        ])
    except ImportError:
        pytest.skip("ML extras not installed")
    
    # Now check feature compatibility
    from pur_mold_twin.ml.versioning import validate_model_compatibility
    
    # Get features from trained model
    risk_info = get_model_info("defect_risk", models_dir)
    trained_features = risk_info.features_used
    
    # Test 1: Exact match should be compatible
    is_compat, msg = validate_model_compatibility("defect_risk", trained_features, models_dir)
    assert is_compat
    assert msg == "Compatible"
    
    # Test 2: Missing feature should fail
    missing_features = trained_features[:-1]  # Remove last feature
    is_compat, msg = validate_model_compatibility("defect_risk", missing_features, models_dir)
    assert not is_compat
    assert "Missing features" in msg
    
    # Test 3: Extra feature should fail
    extra_features = trained_features + ["new_feature"]
    is_compat, msg = validate_model_compatibility("defect_risk", extra_features, models_dir)
    assert not is_compat
    assert "Extra features" in msg
    
    print("\n✅ Feature compatibility check passed")
