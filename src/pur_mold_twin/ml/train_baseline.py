"""
Training entry point for baseline ML models (optional extras).

Usage (script):
    python -m pur_mold_twin.ml.train_baseline --features data/ml/features.parquet

Usage (CLI):
    pur-mold-twin train-ml --features data/ml/features.parquet
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

try:
    import pandas as pd  # type: ignore
    from sklearn.metrics import f1_score, mean_absolute_error  # type: ignore
    import joblib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    pd = None
    mean_absolute_error = None
    f1_score = None
    joblib = None

from .baseline import BaselineModels, build_baseline_models


@dataclass
class TrainingReport:
    samples: int
    features: int
    mae_defect_risk: float | None
    f1_any_defect: float | None


def _train_models(df: "pd.DataFrame") -> Tuple[BaselineModels, TrainingReport]:
    models = build_baseline_models()

    mae_value: float | None = None
    f1_value: float | None = None

    X = df.drop(columns=["defect_risk", "any_defect"], errors="ignore")

    if "defect_risk" in df.columns and mean_absolute_error is not None:
        y_risk = df["defect_risk"]
        models.defect_risk_regressor.fit(X, y_risk)
        preds = models.defect_risk_regressor.predict(X)
        mae_value = float(mean_absolute_error(y_risk, preds))

    if "any_defect" in df.columns and f1_score is not None:
        y_cls = df["any_defect"]
        models.defect_classifier.fit(X, y_cls)
        preds_cls = models.defect_classifier.predict(X)
        f1_value = float(f1_score(y_cls, preds_cls))

    report = TrainingReport(
        samples=int(len(df)),
        features=int(X.shape[1]),
        mae_defect_risk=mae_value,
        f1_any_defect=f1_value,
    )
    return models, report


def _save_models(models: BaselineModels, out_dir: Path) -> Dict[str, str]:
    if joblib is None:
        raise ImportError("joblib is required to save ML models; install with pur-mold-twin[ml]")

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, str] = {}
    if models.defect_risk_regressor is not None:
        path = out_dir / "defect_risk.pkl"
        joblib.dump(models.defect_risk_regressor, path)
        paths["defect_risk"] = str(path)
    if models.defect_classifier is not None:
        path = out_dir / "defect_classifier.pkl"
        joblib.dump(models.defect_classifier, path)
        paths["defect_classifier"] = str(path)
    return paths


def _write_metrics_report(report: TrainingReport, model_paths: Dict[str, str], output_path: Path) -> Path:
    lines = ["# ML Baseline Training Report", ""]
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- samples: {report.samples}")
    lines.append(f"- features: {report.features}")
    if report.mae_defect_risk is not None:
        lines.append(f"- MAE defect_risk: {report.mae_defect_risk:.4f}")
    if report.f1_any_defect is not None:
        lines.append(f"- F1 any_defect: {report.f1_any_defect:.4f}")
    lines.append("")
    lines.append("## Model artifacts")
    lines.append("")
    for name, path in model_paths.items():
        lines.append(f"- **{name}**: `{path}`")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Train baseline ML models.")
    parser.add_argument("--features", required=True, type=Path, help="Path to features parquet/CSV file.")
    parser.add_argument("--models-dir", type=Path, default=Path("models"), help="Directory for saved models.")
    parser.add_argument("--metrics-path", type=Path, default=Path("reports/ml/metrics.md"), help="Metrics report path.")
    args = parser.parse_args(argv)

    if pd is None:
        raise ImportError("pandas is required to train baselines; install with pur-mold-twin[ml]")

    if not args.features.exists():
        raise FileNotFoundError(f"Features file '{args.features}' not found")

    if args.features.suffix.lower() == ".csv":
        df = pd.read_csv(args.features)
    else:
        df = pd.read_parquet(args.features)

    models, report = _train_models(df)
    model_paths = _save_models(models, args.models_dir)
    _write_metrics_report(report, model_paths, args.metrics_path)

    # Simple JSON payload on stdout for CLI usage / tests
    payload: Dict[str, Any] = {
        "report": asdict(report),
        "models": model_paths,
    }
    print(json.dumps(payload))


if __name__ == "__main__":  # pragma: no cover
    main()
