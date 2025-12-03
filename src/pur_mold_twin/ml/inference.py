from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import logging

from .versioning import load_manifest, get_model_info

logger = logging.getLogger(__name__)

try:
    import joblib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    joblib = None


@dataclass
class LoadedModels:
    """Container for loaded ML models with version metadata."""
    defect_risk: Optional[object]
    defect_classifier: Optional[object]
    manifest_data: Optional[Dict[str, Any]] = None


_CACHED_MODELS: Optional[LoadedModels] = None


def _load_models(models_dir: Path = Path("models")) -> LoadedModels:
    """
    Load ML models from disk with manifest metadata.
    
    Implements lazy loading with caching.
    Logs warnings if models exist but manifest is missing.
    """
    global _CACHED_MODELS
    if _CACHED_MODELS is not None:
        return _CACHED_MODELS
    
    if joblib is None:
        raise ImportError("joblib is required for ML inference; install with pur-mold-twin[ml]")
    
    # Load models
    risk_path = models_dir / "defect_risk.pkl"
    cls_path = models_dir / "defect_classifier.pkl"
    
    risk_model = None
    cls_model = None
    
    if risk_path.exists():
        try:
            risk_model = joblib.load(risk_path)
            logger.info(f"Loaded defect risk model from {risk_path}")
        except Exception as e:
            logger.error(f"Failed to load defect risk model: {e}")
    
    if cls_path.exists():
        try:
            cls_model = joblib.load(cls_path)
            logger.info(f"Loaded defect classifier from {cls_path}")
        except Exception as e:
            logger.error(f"Failed to load defect classifier: {e}")
    
    # Load manifest
    manifest = load_manifest(models_dir)
    manifest_data = None
    
    if manifest is not None:
        manifest_data = manifest.to_dict()
        logger.info(f"Loaded model manifest with {len(manifest.models)} entries")
    else:
        if risk_model or cls_model:
            logger.warning(
                f"Models found in {models_dir} but no manifest.json present. "
                "Consider retraining models to generate version metadata."
            )
    
    _CACHED_MODELS = LoadedModels(
        defect_risk=risk_model,
        defect_classifier=cls_model,
        manifest_data=manifest_data,
    )
    return _CACHED_MODELS


def attach_ml_predictions(sim_result: Dict[str, Any], features_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach ML predictions (if models are available) to a SimulationResult-like dict.
    
    Also attaches model version metadata from manifest if available.
    This function never raises if models are missing; in such case it returns the
    original dict unchanged.
    
    Args:
        sim_result: Dictionary representing simulation results
        features_row: Dictionary of features for prediction
    
    Returns:
        Enhanced sim_result with ML predictions and metadata
    """
    try:
        models = _load_models()
    except Exception as e:
        logger.debug(f"Could not load models: {e}")
        return sim_result

    from pandas import DataFrame

    X = DataFrame([features_row]).drop(columns=["defect_risk", "any_defect"], errors="ignore")

    # Attach predictions
    if models.defect_risk is not None:
        try:
            risk_pred = float(models.defect_risk.predict(X)[0])
            sim_result["defect_risk_pred"] = risk_pred
        except Exception as e:
            logger.warning(f"Defect risk prediction failed: {e}")
    
    if models.defect_classifier is not None:
        try:
            cls_pred = models.defect_classifier.predict(X)[0]
            sim_result["defect_class_pred"] = cls_pred
        except Exception as e:
            logger.warning(f"Defect classifier prediction failed: {e}")
    
    # Attach model metadata from manifest
    if models.manifest_data:
        ml_metadata = {}
        
        for model_type in ["defect_risk", "defect_classifier"]:
            if model_type in models.manifest_data.get("models", {}):
                model_info = models.manifest_data["models"][model_type]
                ml_metadata[model_type] = {
                    "version": model_info.get("version"),
                    "trained_at": model_info.get("trained_at"),
                    "git_commit": model_info.get("git_commit"),
                    "metrics": model_info.get("metrics", {}),
                }
        
        if ml_metadata:
            sim_result["ml_model_metadata"] = ml_metadata
            logger.debug(f"Attached metadata for {len(ml_metadata)} models")
    
    return sim_result

