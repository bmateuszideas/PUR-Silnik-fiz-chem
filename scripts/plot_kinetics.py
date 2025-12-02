"""
Plot alpha(t) kinetics with optional TDS markers (cream/gel/rise).

Usage:
    python scripts/plot_kinetics.py --sim sim_output.json --cream 15 --gel 60 --rise 110 --out alpha_plot.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot alpha(t) kinetics with TDS markers.")
    parser.add_argument("--sim", required=True, type=Path, help="Simulation JSON (run-sim --save-json).")
    parser.add_argument("--cream", type=float, help="Cream time [s]")
    parser.add_argument("--gel", type=float, help="Gel time [s]")
    parser.add_argument("--rise", type=float, help="Rise time [s]")
    parser.add_argument("--out", type=Path, default=Path("alpha_plot.png"), help="Output PNG file.")
    args = parser.parse_args()

    sim = json.loads(args.sim.read_text(encoding="utf-8"))
    time_s = sim.get("time_s", [])
    alpha = sim.get("alpha", [])

    plt.figure(figsize=(8, 4))
    plt.plot(time_s, alpha, label="alpha(t)")

    def mark(time: Optional[float], label: str) -> None:
        if time is not None:
            plt.axvline(time, color="red", linestyle="--", alpha=0.7)
            plt.text(time, 0.05, label, rotation=90, va="bottom", ha="right")

    mark(args.cream, "cream")
    mark(args.gel, "gel")
    mark(args.rise, "rise")

    plt.ylim(0, 1.05)
    plt.xlabel("time [s]")
    plt.ylabel("alpha [-]")
    plt.title("Kinetics profile")
    plt.legend()
    plt.tight_layout()
    plt.savefig(args.out, dpi=150)
    print(f"Saved plot to {args.out}")


if __name__ == "__main__":
    main()
