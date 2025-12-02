"""Simple report generator (Markdown)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from ..core.types import SimulationResult


def _format_kpi(result: SimulationResult) -> str:
    def fmt(value, unit: str = "", precision: int = 2):
        if value is None:
            return "-"
        if isinstance(value, (float, int)):
            return f"{value:.{precision}f}{unit}"
        return str(value)

    lines = [
        "| KPI | Value |",
        "| --- | --- |",
        f"| quality_status | {result.quality_status} |",
        f"| pressure_status | {result.pressure_status} |",
        f"| t_demold_min_s | {fmt(result.t_demold_min_s, ' s', 1)} |",
        f"| t_demold_opt_s | {fmt(result.t_demold_opt_s, ' s', 1)} |",
        f"| t_demold_max_s | {fmt(result.t_demold_max_s, ' s', 1)} |",
        f"| p_max_bar | {fmt((result.p_max_Pa or 0) / 100_000.0, ' bar', 2)} |",
        f"| rho_moulded | {fmt(result.rho_moulded, ' kg/m3', 1)} |",
        f"| H_demold | {fmt(result.H_demold_shore, ' Sh', 1)} |",
        f"| H_24h | {fmt(result.H_24h_shore, ' Sh', 1)} |",
        f"| defect_risk | {fmt(result.defect_risk, '', 3)} |",
    ]
    return "\n".join(lines)


def generate_report(
    result: SimulationResult,
    plot_paths: Dict[str, Path],
    output_path: Path,
    metadata: Optional[Dict[str, str]] = None,
) -> Path:
    """
    Generate a Markdown report with KPI table and plot references.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)
    md_lines = ["# PUR-MOLD-TWIN - Simulation Report", ""]

    if metadata:
        md_lines.append("## Metadata")
        md_lines.append("")
        for key, value in metadata.items():
            md_lines.append(f"- **{key}**: {value}")
        md_lines.append("")

    md_lines.append("## KPI")
    md_lines.append(_format_kpi(result))
    md_lines.append("")

    if plot_paths:
        md_lines.append("## Plots")
        md_lines.append("")
        for label, path in plot_paths.items():
            md_lines.append(f"### {label}")
            md_lines.append(f"![{label}]({path.as_posix()})")
            md_lines.append("")

    output_path.write_text("\n".join(md_lines), encoding="utf-8")
    return output_path
