from pathlib import Path
import json

import pytest

from pur_mold_twin.core.types import SimulationResult


def _load_sample_result() -> SimulationResult:
    data = json.loads(Path("tests/fixtures/use_case_1_output.json").read_text(encoding="utf-8"))
    return SimulationResult.model_validate(data)


def test_generate_report_and_plots() -> None:
    pytest.importorskip("matplotlib")

    from pur_mold_twin.reporting import generate_report, plot_profiles

    result = _load_sample_result()
    out_dir = Path("tests/tmp_reports")
    out_dir.mkdir(parents=True, exist_ok=True)

    plots = plot_profiles(result, out_dir, prefix="sample")
    for path in plots.values():
        assert path.exists()

    report_path = out_dir / "report.md"
    generate_report(result, plots, report_path, metadata={"system_id": "SYSTEM_R1"})
    content = report_path.read_text(encoding="utf-8")
    assert "quality_status" in content
    assert "SYSTEM_R1" in content


def test_generate_report_without_plots_or_metadata(tmp_path: Path) -> None:
    from pur_mold_twin.reporting import generate_report

    result = SimulationResult()
    report_path = tmp_path / "report.md"

    generated = generate_report(result, {}, report_path)

    content = generated.read_text(encoding="utf-8")
    assert generated.exists()
    assert "PUR-MOLD-TWIN - Simulation Report" in content
    assert "quality_status" in content
