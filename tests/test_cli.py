import json
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

sys.path.append(str(Path(".") / "src"))

try:
    import pydantic  # noqa: F401
    import ruamel.yaml  # noqa: F401
    import matplotlib  # noqa: F401

    CLI_DEPS_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover
    CLI_DEPS_AVAILABLE = False

from pur_mold_twin.cli.main import app

runner = CliRunner()


@pytest.mark.skipif(not CLI_DEPS_AVAILABLE, reason="CLI deps (pydantic/ruamel) not installed")
def test_run_sim_cli_outputs_json():
    result = runner.invoke(app, ["run-sim", "--scenario", "configs/scenarios/use_case_1.yaml"])
    assert result.exit_code == 0
    data = json.loads(result.stdout.strip())
    assert "time_s" in data
    assert isinstance(data["alpha"], list)


@pytest.mark.skipif(not CLI_DEPS_AVAILABLE, reason="CLI deps (pydantic/ruamel) not installed")
def test_run_sim_cli_missing_scenario():
    result = runner.invoke(app, ["run-sim", "--scenario", "configs/scenarios/missing.yaml"])
    assert result.exit_code == 1
    assert "Scenario file" in result.stderr


@pytest.mark.skipif(not CLI_DEPS_AVAILABLE, reason="CLI deps (pydantic/ruamel) not installed")
def test_run_sim_cli_with_overrides():
    tmp_dir = Path("tests") / "tmp_cli"
    tmp_dir.mkdir(exist_ok=True)
    output_path = tmp_dir / "result.json"
    result = runner.invoke(
        app,
        [
            "run-sim",
            "--scenario",
            "configs/scenarios/use_case_1.yaml",
            "--system",
            "SYSTEM_R1",
            "--quality",
            "configs/quality/default.yaml",
            "--save-json",
            str(output_path),
        ],
    )
    assert result.exit_code == 0
    assert output_path.exists()
    stored = json.loads(output_path.read_text())
    assert stored.get("quality_status")


@pytest.mark.skipif(not CLI_DEPS_AVAILABLE, reason="CLI deps (pydantic/ruamel) not installed")
def test_run_sim_cli_table_and_csv():
    tmp_dir = Path("tests") / "tmp_cli"
    tmp_dir.mkdir(exist_ok=True)
    csv_path = tmp_dir / "profiles.csv"
    result = runner.invoke(
        app,
        [
            "run-sim",
            "--scenario",
            "configs/scenarios/use_case_1.yaml",
            "--output",
            "table",
            "--export-csv",
            str(csv_path),
        ],
    )
    assert result.exit_code == 0
    assert "KPI Summary" in result.stdout
    assert csv_path.exists()
    content = csv_path.read_text().splitlines()
    assert content[0].startswith("time_s")
    assert len(content) > 2


@pytest.mark.skipif(not CLI_DEPS_AVAILABLE, reason="CLI deps (pydantic/ruamel) not installed")
def test_run_sim_cli_invalid_report_path(tmp_path):
    invalid_parent = tmp_path / "report_target"
    invalid_parent.write_text("blocking file")
    report_path = invalid_parent / "report.md"

    result = runner.invoke(
        app,
        [
            "run-sim",
            "--scenario",
            "configs/scenarios/use_case_1.yaml",
            "--report",
            str(report_path),
        ],
    )

    assert result.exit_code == 1
    assert "Invalid report path" in result.stderr


@pytest.mark.skipif(not CLI_DEPS_AVAILABLE, reason="CLI deps (pydantic/ruamel/matplotlib) not installed")
def test_run_sim_cli_generates_report(tmp_path):
    report_path = tmp_path / "reports" / "use_case.md"
    result = runner.invoke(
        app,
        [
            "run-sim",
            "--scenario",
            "configs/scenarios/use_case_1.yaml",
            "--report",
            str(report_path),
        ],
    )

    assert result.exit_code == 0
    assert report_path.exists()
    plots = list(report_path.parent.glob("*.png"))
    assert plots
    assert "Saved report" in result.stdout


@pytest.mark.skipif(not CLI_DEPS_AVAILABLE, reason="CLI deps (pydantic/ruamel) not installed")
def test_run_sim_cli_with_verbose_flag():
    result = runner.invoke(
        app,
        [
            "--verbose",
            "run-sim",
            "--scenario",
            "configs/scenarios/use_case_1.yaml",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout.strip())
    assert "time_s" in data


@pytest.mark.skipif(not CLI_DEPS_AVAILABLE, reason="CLI deps (pydantic/ruamel) not installed")
def test_run_sim_cli_operator_mode_table():
    result = runner.invoke(
        app,
        [
            "run-sim",
            "--scenario",
            "configs/scenarios/use_case_1.yaml",
            "--mode",
            "operator",
        ],
    )
    assert result.exit_code == 0
    assert "KPI Summary" in result.stdout


@pytest.mark.skipif(not CLI_DEPS_AVAILABLE, reason="CLI deps (pydantic/ruamel) not installed")
def test_optimize_cli_runs_with_few_samples():
    result = runner.invoke(
        app,
        [
            "optimize",
            "--scenario",
            "configs/scenarios/use_case_1.yaml",
            "--samples",
            "1",
            "--t-cycle-max",
            "400",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout.strip())
    assert "candidate" in payload
    assert "optimized" in payload and "p_max_bar" in payload["optimized"]
