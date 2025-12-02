from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import joblib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    joblib = None


@dataclass
class LoadedModels:
    defect_risk: Optional[object]
    defect_classifier: Optional[object]


_CACHED_MODELS: Optional[LoadedModels] = None


def _load_models(models_dir: Path = Path("models")) -> LoadedModels:
    global _CACHED_MODELS
    if _CACHED_MODELS is not None:
        return _CACHED_MODELS
    if joblib is None:
        raise ImportError("joblib is required for ML inference; install with pur-mold-twin[ml]")
    risk_path = models_dir / "defect_risk.pkl"
    cls_path = models_dir / "defect_classifier.pkl"
    risk_model = joblib.load(risk_path) if risk_path.exists() else None
    cls_model = joblib.load(cls_path) if cls_path.exists() else None
    _CACHED_MODELS = LoadedModels(defect_risk=risk_model, defect_classifier=cls_model)
    return _CACHED_MODELS


def attach_ml_predictions(sim_result: Dict[str, Any], features_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach ML predictions (if models are available) to a SimulationResult-like dict.

    This function never raises if models are missing; in such case it returns the
    original dict unchanged.
    """

    try:
        models = _load_models()
    except Exception:
        return sim_result

    from pandas import DataFrame

    X = DataFrame([features_row]).drop(columns=["defect_risk", "any_defect"], errors="ignore")

    if models.defect_risk is not None:
        try:
            risk_pred = float(models.defect_risk.predict(X)[0])
            sim_result["defect_risk_pred"] = risk_pred
        except Exception:
            pass

    if models.defect_classifier is not None:
        try:
            cls_pred = models.defect_classifier.predict(X)[0]
            sim_result["defect_class_pred"] = cls_pred
        except Exception:
            pass

    return sim_result

