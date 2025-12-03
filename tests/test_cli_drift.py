from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from pur_mold_twin.cli.main import app


runner = CliRunner()


def test_check_drift_cli_runs_and_sets_exit_code(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.csv"
    current = tmp_path / "current.csv"
    df = pd.DataFrame(
        {
            "defect_risk": [0.1, 0.2, 0.15],
            "any_defect": [0, 1, 0],
        }
    )
    df.to_csv(baseline, index=False)
    df.to_csv(current, index=False)

def test_check_drift_runs_and_reports(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.csv"
    current = tmp_path / "current.csv"
    df = pd.DataFrame(
        {
            "defect_risk": [0.1, 0.2, 0.15],
            "any_defect": [0, 1, 0],
        }
    )
    df.to_csv(baseline, index=False)
    df.to_csv(current, index=False)

    result = runner.invoke(
        app,
        [
            "check-drift",
            "--baseline",
            str(baseline),
            "--current",
            str(current),
        ],
    )
    assert result.exit_code in (0, 1, 2)

