"""Plot helpers for SimulationResult."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from ..core.types import SimulationResult


def _require_matplotlib():
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise ImportError("matplotlib is required for reporting; install per py_lib.md") from exc
    return plt


def plot_profiles(result: SimulationResult, output_dir: Path, prefix: str = "simulation") -> Dict[str, Path]:
    """
    Generate basic plots for key profiles and save to PNG files.

    Returns a dict with plot names -> file paths.
    """

    plt = _require_matplotlib()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, Path] = {}

    time = result.time_s

    # Temperature profiles
    fig, ax = plt.subplots()
    ax.plot(time, [t - 273.15 for t in result.T_core_K], label="T_core [C]")
    ax.plot(time, [t - 273.15 for t in result.T_mold_K], label="T_mold [C]", linestyle="--")
    ax.set_xlabel("time [s]")
    ax.set_ylabel("Temperature [C]")
    ax.legend()
    temp_path = output_dir / f"{prefix}_temperature.png"
    fig.tight_layout()
    fig.savefig(temp_path)
    plt.close(fig)
    paths["temperature"] = temp_path

    # Pressure profiles
    fig, ax = plt.subplots()
    ax.plot(time, [p / 100_000.0 for p in result.p_total_Pa], label="p_total [bar]")
    ax.plot(time, [p / 100_000.0 for p in result.p_CO2_Pa], label="p_CO2 [bar]", linestyle="--")
    ax.plot(time, [p / 100_000.0 for p in result.p_pentane_Pa], label="p_pentane [bar]", linestyle=":")
    ax.set_xlabel("time [s]")
    ax.set_ylabel("Pressure [bar]")
    ax.legend()
    pressure_path = output_dir / f"{prefix}_pressure.png"
    fig.tight_layout()
    fig.savefig(pressure_path)
    plt.close(fig)
    paths["pressure"] = pressure_path

    # Cure/hardness profiles
    fig, ax = plt.subplots()
    ax.plot(time, result.alpha, label="alpha [-]")
    if result.hardness_shore:
        ax2 = ax.twinx()
        ax2.plot(time, result.hardness_shore, color="tab:orange", label="hardness [Shore]")
        ax2.set_ylabel("Hardness [Shore]")
    ax.set_xlabel("time [s]")
    ax.set_ylabel("Alpha [-]")
    ax.legend(loc="upper left")
    cure_path = output_dir / f"{prefix}_cure.png"
    fig.tight_layout()
    fig.savefig(cure_path)
    plt.close(fig)
    paths["cure"] = cure_path

    # Density and vent efficiency
    fig, ax = plt.subplots()
    ax.plot(time, result.rho_kg_per_m3, label="rho [kg/m3]")
    ax.set_xlabel("time [s]")
    ax.set_ylabel("Density [kg/m3]")
    if result.vent_eff:
        ax2 = ax.twinx()
        ax2.plot(time, result.vent_eff, color="tab:green", linestyle="--", label="vent_eff")
        ax2.set_ylabel("Vent efficiency [-]")
    ax.legend(loc="upper left")
    density_path = output_dir / f"{prefix}_density.png"
    fig.tight_layout()
    fig.savefig(density_path)
    plt.close(fig)
    paths["density"] = density_path

    return paths
