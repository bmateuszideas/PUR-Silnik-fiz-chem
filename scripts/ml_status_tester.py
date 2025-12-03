"""CLI helper to exercise ML status codes in various scenarios.

Usage:
    python scripts/ml_status_tester.py --case ok
    python scripts/ml_status_tester.py --case missing-models
    python scripts/ml_status_tester.py --case missing-extras
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from contextlib import contextmanager, redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Dict, Iterator

from pur_mold_twin.ml import inference
from pur_mold_twin.ml.inference import attach_ml_predictions
from pur_mold_twin.ml.policy import (
    MLDependencyError,
    MLPolicyError,
    unexpected_error_status,
)

SAMPLE_FEATURES: Dict[str, Any] = {
    "sim_T_core_max_C": 80.0,
    "sim_p_max_bar": 3.6,
    "defect_risk": 0.15,
    "any_defect": 0,
}


@contextmanager
def _temporary_cwd(path: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _emit(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _attach_with_metadata(features: Dict[str, Any], workdir: Path) -> Dict[str, Any]:
    with _temporary_cwd(workdir):
        result = attach_ml_predictions({"tester": True}, dict(features))
    result["tester_workdir"] = str(workdir)
    return result


def _case_ok(_: argparse.Namespace) -> Dict[str, Any]:
    from pur_mold_twin.ml.train_baseline import main as train_main

    try:
        import pandas as pd  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise MLDependencyError(["pandas"], "Tester ML") from exc

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        features_path = tmp_path / "features.csv"
        df = pd.DataFrame(
            {
                "sim_T_core_max_C": [80.0, 85.0],
                "sim_p_max_bar": [3.6, 3.8],
                "defect_risk": [0.15, 0.22],
                "any_defect": [0, 1],
            }
        )
        df.to_csv(features_path, index=False)
        models_dir = tmp_path / "models"
        metrics_path = tmp_path / "reports" / "ml" / "metrics.md"
        args = [
            "--features",
            str(features_path),
            "--models-dir",
            str(models_dir),
            "--metrics-path",
            str(metrics_path),
        ]
        with redirect_stdout(StringIO()):
            train_main(args)
        features_row = df.iloc[0].to_dict()
        output = _attach_with_metadata(features_row, tmp_path)
        return {"case": "ok", "result": output}


def _case_missing_models(_: argparse.Namespace) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "models").mkdir()
        output = _attach_with_metadata(SAMPLE_FEATURES, tmp_path)
        return {"case": "missing-models", "result": output}


def _case_missing_extras(_: argparse.Namespace) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        models_dir = tmp_path / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        original_joblib = inference.joblib
        inference.joblib = None  # simulate environment without extras
        try:
            output = _attach_with_metadata(SAMPLE_FEATURES, tmp_path)
        finally:
            inference.joblib = original_joblib
        return {"case": "missing-extras", "result": output}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run ML status scenarios.")
    parser.add_argument(
        "--case",
        choices=["ok", "missing-models", "missing-extras"],
        default="ok",
        help="Scenario to execute.",
    )
    args = parser.parse_args(argv)

    cases: Dict[str, Callable[[argparse.Namespace], Dict[str, Any]]] = {
        "ok": _case_ok,
        "missing-models": _case_missing_models,
        "missing-extras": _case_missing_extras,
    }

    try:
        payload = cases[args.case](args)
        _emit(payload)
    except MLPolicyError as exc:
        _emit({"case": args.case, "ml_status": exc.to_status().to_dict()})
        raise SystemExit(1) from exc
    except Exception as exc:  # pragma: no cover
        status = unexpected_error_status(exc)
        _emit({"case": args.case, "ml_status": status.to_dict()})
        raise SystemExit(1) from exc


if __name__ == "__main__":  # pragma: no cover
    main()
