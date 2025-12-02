"""
Typer command implementations for the PUR-MOLD-TWIN CLI.

The functions defined here stay free of Typer decorators so they can be reused
in tests and higher-level wrappers (see `main.py` for registration).
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from pydantic import ValidationError

from ..configs import load_process_scenario, load_quality_preset
from ..core import MVP0DSimulator
from ..material_db.loader import load_material_catalog
from ..material_db.models import MaterialSystem
from ..optimizer import OptimizationConfig, ProcessOptimizer
from ..reporting import generate_report, plot_profiles
from ..utils import get_logger


LOGGER = get_logger(__name__)


def register_commands(app: typer.Typer) -> None:
    """Attach CLI commands to the Typer application."""

    app.command("run-sim")(run_sim)
    app.command("optimize")(optimize)
    app.command("build-features")(build_features_cli)


class OutputFormat(str, Enum):
    JSON = "json"
    TABLE = "table"


def run_sim(
    scenario: Path = typer.Option(..., "--scenario", "-s", help="Path to YAML scenario with process/mold/quality."),
    system: Optional[str] = typer.Option(
        None,
        "--system",
        "-y",
        help="System ID from the material catalog (overrides scenario.system_id).",
    ),
    systems: Path = typer.Option(
        Path("configs/systems/jr_purtec_catalog.yaml"),
        "--systems",
        "-c",
        help="Material DB catalog (multi-doc YAML or folder).",
    ),
    quality: Optional[Path] = typer.Option(
        None, "--quality", "-q", help="Optional QualityTargets preset overriding the scenario definition."
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON,
        "--output",
        case_sensitive=False,
        help="Choose stdout format: 'json' (default) or 'table'.",
    ),
    save_json: Optional[Path] = typer.Option(
        None, "--save-json", help="Optional file to persist full SimulationResult as JSON."
    ),
    export_csv: Optional[Path] = typer.Option(
        None, "--export-csv", help="Optional CSV path for time-series profiles."
    ),
    backend: Optional[str] = typer.Option(None, "--backend", help="Override solver backend (manual/solve_ivp)."),
    report: Optional[Path] = typer.Option(
        None,
        "--report",
        help="Optional path to save a Markdown report (plots saved alongside).",
    ),
) -> None:
    """Run a single 0D simulation."""

    scenario_data = _load_process_scenario(scenario)
    system_id = system or scenario_data.system_id
    material_system = _load_system(system_id, systems)

    quality_targets = scenario_data.quality
    if quality:
        quality_targets = _load_quality_preset(quality)

    sim_config = scenario_data.simulation
    if backend:
        sim_config = sim_config.model_copy(update={"backend": backend})

    LOGGER.info("Running 0D simulation for scenario '%s' (system=%s)", scenario, system_id)
    simulator = MVP0DSimulator(sim_config)
    result = simulator.run(material_system, scenario_data.process, scenario_data.mold, quality_targets)

    payload = result.to_dict()
    _emit_json(payload, save_json, echo=(output_format == OutputFormat.JSON))

    if output_format == OutputFormat.TABLE:
        typer.echo(_format_kpi_table(result))

    if export_csv:
        _export_profiles_csv(result, export_csv)
        LOGGER.info("Saved simulation profiles to %s", export_csv)
        typer.echo(f"Saved time-series CSV to {export_csv}")

    if report:
        try:
            report_path, plot_dir = _prepare_report_paths(report)
        except OSError as exc:
            LOGGER.error("Invalid report path %s: %s", report, exc)
            typer.echo(f"Invalid report path '{report}': {exc}", err=True)
            raise typer.Exit(1)

        try:
            plot_dir.mkdir(parents=True, exist_ok=True)
            plots = plot_profiles(result, plot_dir, prefix=report_path.stem or "report")
            metadata = {
                "scenario": str(scenario),
                "system_id": system_id,
                "backend": sim_config.backend,
            }
            generate_report(result, plots, report_path, metadata=metadata)
            typer.echo(f"Saved report to {report_path}")
        except ImportError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1)
        except OSError as exc:
            LOGGER.exception("Failed to save report to %s: %s", report_path, exc)
            typer.echo(f"Failed to save report to '{report_path}': {exc}", err=True)
            raise typer.Exit(1)


def optimize(
    scenario: Path = typer.Option(..., "--scenario", "-s", help="Scenario file (system + process + mold)."),
    systems: Path = typer.Option(
        Path("configs/systems/jr_purtec_catalog.yaml"),
        "--systems",
        "-c",
        help="Material DB catalog (multi-doc YAML or folder).",
    ),
    quality: Optional[Path] = typer.Option(None, "--quality", help="Optional QualityTargets preset."),
    samples: int = typer.Option(40, "--samples", "-n", help="Number of random samples."),
    seed: Optional[int] = typer.Option(None, "--seed", help="Random generator seed."),
    t_cycle_max: float = typer.Option(600.0, "--t-cycle-max", help="Cycle time limit [s]."),
    prefer_lower_pressure: bool = typer.Option(True, "--prefer-lower-pressure/--no-prefer-lower-pressure"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON,
        "--output",
        case_sensitive=False,
        help="Choose stdout format: 'json' (default) or 'table'.",
    ),
    save_json: Optional[Path] = typer.Option(
        None, "--save-json", help="Optional file to persist optimizer summary as JSON."
    ),
    export_csv: Optional[Path] = typer.Option(
        None, "--export-csv", help="Optional CSV path for optimizer history."
    ),
) -> None:
    """Run the process optimizer (random search)."""

    scenario_data = _load_process_scenario(scenario)
    system = _load_system(scenario_data.system_id, systems)

    quality_targets = scenario_data.quality
    if quality:
        quality_targets = _load_quality_preset(quality)

    LOGGER.info(
        "Starting optimization for scenario '%s' (%d samples, prefer_lower_pressure=%s)",
        scenario,
        samples,
        prefer_lower_pressure,
    )
    simulator = MVP0DSimulator(scenario_data.simulation)
    baseline_result = simulator.run(system, scenario_data.process, scenario_data.mold, quality_targets)

    optimizer_config = OptimizationConfig(
        samples=samples,
        random_seed=seed,
        t_cycle_max_s=t_cycle_max,
        prefer_lower_pressure=prefer_lower_pressure,
    )
    optimizer = ProcessOptimizer(simulator)
    result = optimizer.optimize(system, scenario_data.process, scenario_data.mold, quality_targets, optimizer_config)

    summary = _build_optimizer_summary(
        baseline=baseline_result,
        optimized=result.best_simulation,
        candidate=result.best_candidate,
    )

    if output_format == OutputFormat.JSON:
        _emit_json(summary, None, echo=True)
    else:
        typer.echo(_format_optimizer_table(summary))

    if save_json:
        data = {
            "summary": summary,
            "baseline": baseline_result.to_dict(),
            "best_simulation": result.best_simulation.to_dict(),
            "best_candidate": asdict(result.best_candidate),
            "history": [
                {
                    "candidate": asdict(entry.candidate),
                    "objective": entry.objective,
                    "feasible": entry.feasible,
                    "p_max_bar": entry.p_max_bar,
                    "quality_status": entry.quality_status,
                    "demold_time_s": entry.constraints.demold_time_s,
                    "window_ok": entry.constraints.window_ok,
                }
                for entry in result.evaluations
            ],
        }
        _emit_json(data, save_json, echo=False)

    if export_csv:
        _export_optimizer_history(result, export_csv)
        LOGGER.info("Saved optimizer history to %s", export_csv)
        typer.echo(f"Saved optimizer history CSV to {export_csv}")


def build_features_cli(
    measured: Path = typer.Option(
        ...,
        "--measured",
        "-m",
        help="Path to measured log directory (meta/process/sensors_*.csv) or a CSV with time_s,T_core_C,p_total_bar.",
    ),
    sim: Path = typer.Option(..., "--sim", "-s", help="Simulation JSON exported by run-sim."),
    output: Path = typer.Option("data/ml/features.parquet", "--output", "-o", help="Output Parquet with features."),
) -> None:
    """Build basic feature set combining measurement and simulation outputs."""

    try:
        import pandas as pd  # noqa: F401
    except ModuleNotFoundError:  # pragma: no cover
        typer.echo("pandas is required for build-features; install per py_lib.md", err=True)
        raise typer.Exit(1)

    from ..data.dataset import build_dataset

    features, saved_path = build_dataset(sim, measured, output)
    typer.echo(f"Saved features to {saved_path} (rows={len(features)}); columns={list(features.columns)}")


def _load_process_scenario(path: Path):
    try:
        return load_process_scenario(path)
    except FileNotFoundError:
        typer.echo(f"Scenario file '{path}' not found.", err=True)
        raise typer.Exit(1)
    except (ValidationError, ValueError) as exc:
        typer.echo(f"Invalid scenario '{path}': {exc}", err=True)
        raise typer.Exit(1)


def _load_quality_preset(path: Path):
    try:
        return load_quality_preset(path)
    except FileNotFoundError:
        typer.echo(f"Quality preset '{path}' not found.", err=True)
        raise typer.Exit(1)
    except (ValidationError, ValueError) as exc:
        typer.echo(f"Invalid quality preset '{path}': {exc}", err=True)
        raise typer.Exit(1)


def _load_system(system_id: str, catalog_path: Path) -> MaterialSystem:
    systems = load_material_catalog(catalog_path)
    if system_id not in systems:
        available = ", ".join(sorted(systems)) or "no systems"
        typer.echo(
            f"System '{system_id}' not found in {catalog_path}. Available IDs: {available}.",
            err=True,
        )
        raise typer.Exit(1)
    return systems[system_id]


def _prepare_report_paths(report: Path) -> tuple[Path, Path]:
    """Validate report target and return (report_path, plot_dir)."""

    if report.suffix:
        report_path = report
        plot_dir = report.parent
    else:
        report_path = report / "report.md"
        plot_dir = report

    for directory in {plot_dir, report_path.parent}:
        if directory.exists() and not directory.is_dir():
            raise OSError(f"Path '{directory}' is not a directory.")

    return report_path, plot_dir


def _emit_json(payload: dict, output: Optional[Path], *, echo: bool) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if echo:
        typer.echo(text)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
        typer.echo(f"Saved result to {output}")


def _format_kpi_table(result) -> str:
    def fmt(value: Optional[float], unit: str = "", precision: int = 2) -> str:
        if value is None:
            return "-"
        if isinstance(value, (int, float)):
            return f"{value:.{precision}f}{unit}"
        return str(value)

    rows = [
        ("quality_status", result.quality_status),
        ("pressure_status", result.pressure_status),
        ("t_demold_min_s", fmt(result.t_demold_min_s, " s", 1)),
        ("t_demold_opt_s", fmt(result.t_demold_opt_s, " s", 1)),
        ("t_demold_max_s", fmt(result.t_demold_max_s, " s", 1)),
        ("p_max", fmt(result.p_max_Pa / 100_000.0 if result.p_max_Pa else None, " bar", 2)),
        ("rho_moulded", fmt(result.rho_moulded, " kg/m3", 1)),
        ("H_demold", fmt(result.H_demold_shore, " Sh", 1)),
        ("H_24h", fmt(result.H_24h_shore, " Sh", 1)),
        ("defect_risk", fmt(result.defect_risk, "", 3)),
    ]
    label_width = max(len(label) for label, _ in rows)
    lines = ["KPI Summary"]
    for label, value in rows:
        lines.append(f"{label.ljust(label_width)} : {value}")
    return "\n".join(lines)


def _export_profiles_csv(result, path: Path) -> None:
    headers = [
        "time_s",
        "alpha",
        "T_core_K",
        "T_mold_K",
        "rho_kg_per_m3",
        "p_total_Pa",
        "p_air_Pa",
        "p_CO2_Pa",
        "p_pentane_Pa",
        "vent_eff",
        "hardness_shore",
    ]
    rows = zip(
        result.time_s,
        result.alpha,
        result.T_core_K,
        result.T_mold_K,
        result.rho_kg_per_m3,
        result.p_total_Pa,
        result.p_air_Pa,
        result.p_CO2_Pa,
        result.p_pentane_Pa,
        result.vent_eff,
        result.hardness_shore,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def _build_optimizer_summary(baseline, optimized, candidate) -> dict:
    def metrics(result):
        return {
            "quality_status": result.quality_status,
            "pressure_status": result.pressure_status,
            "t_demold_opt_s": result.t_demold_opt_s,
            "p_max_bar": (result.p_max_Pa / 100_000.0) if result.p_max_Pa else None,
            "rho_moulded": result.rho_moulded,
            "H_demold_shore": result.H_demold_shore,
            "defect_risk": result.defect_risk,
        }

    return {
        "baseline": metrics(baseline),
        "optimized": metrics(optimized),
        "candidate": asdict(candidate),
    }


def _format_optimizer_table(summary: dict) -> str:
    baseline = summary["baseline"]
    optimized = summary["optimized"]
    rows = [
        ("quality_status", baseline["quality_status"], optimized["quality_status"]),
        ("pressure_status", baseline["pressure_status"], optimized["pressure_status"]),
        ("t_demold_opt_s", baseline["t_demold_opt_s"], optimized["t_demold_opt_s"]),
        ("p_max_bar", baseline["p_max_bar"], optimized["p_max_bar"]),
        ("rho_moulded", baseline["rho_moulded"], optimized["rho_moulded"]),
        ("H_demold_shore", baseline["H_demold_shore"], optimized["H_demold_shore"]),
        ("defect_risk", baseline["defect_risk"], optimized["defect_risk"]),
    ]

    def fmt(value):
        if value is None:
            return "-"
        if isinstance(value, float):
            return f"{value:.3f}" if abs(value) < 100 else f"{value:.1f}"
        return str(value)

    label_width = max(len(label) for label, _, _ in rows)
    lines = ["Optimizer Summary"]
    lines.append(f"{'metric'.ljust(label_width)} | baseline | optimized")
    lines.append("-" * (label_width + 24))
    for label, base, opt in rows:
        lines.append(f"{label.ljust(label_width)} | {fmt(base):>9} | {fmt(opt):>9}")
    return "\n".join(lines)


def _export_optimizer_history(result, path: Path) -> None:
    headers = [
        "index",
        "T_polyol_in_C",
        "T_iso_in_C",
        "T_mold_init_C",
        "t_demold_s",
        "objective",
        "feasible",
        "p_max_bar",
        "quality_status",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        for idx, entry in enumerate(result.evaluations, start=1):
            writer.writerow(
                [
                    idx,
                    entry.candidate.T_polyol_in_C,
                    entry.candidate.T_iso_in_C,
                    entry.candidate.T_mold_init_C,
                    entry.candidate.t_demold_s,
                    entry.objective,
                    entry.feasible,
                    entry.p_max_bar,
                    entry.quality_status,
                ]
            )
