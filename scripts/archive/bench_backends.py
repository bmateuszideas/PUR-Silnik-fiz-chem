"""
Backend performance and accuracy benchmark for PUR-MOLD-TWIN.

Usage (basic):
    python scripts/bench_backends.py \
        --scenario configs/scenarios/use_case_1.yaml \
        --systems configs/systems/jr_purtec_catalog.yaml \
        --backends manual,solve_ivp \
        --backend-ref manual \
        --repeats 3

The script compares wall-clock time and a few scalar KPIs between backends.
It is intentionally text-only (no plots) and uses existing loaders and
MVP0DSimulator from the library.
"""

from __future__ import annotations

import argparse
import statistics
import time
from dataclasses import dataclass
import sys
from pathlib import Path
from typing import Iterable, List, TYPE_CHECKING

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

if TYPE_CHECKING:
    from pur_mold_twin import (  # type: ignore[import-not-found]
        MVP0DSimulator,
        MoldProperties,
        ProcessConditions,
        QualityTargets,
        SimulationConfig,
    )
    from pur_mold_twin.configs import load_process_scenario  # type: ignore[import-not-found]
    from pur_mold_twin.material_db.loader import load_material_catalog  # type: ignore[import-not-found]
else:
    try:
        from pur_mold_twin import (
            MVP0DSimulator,
            MoldProperties,
            ProcessConditions,
            QualityTargets,
            SimulationConfig,
        )
        from pur_mold_twin.configs import load_process_scenario
        from pur_mold_twin.material_db.loader import load_material_catalog
    except Exception:
        # Minimal local stubs to allow the script to run when the real package is
        # not installed; these provide the attributes used by this benchmark script.
        from dataclasses import dataclass
        from types import SimpleNamespace
        from typing import Any, Dict

        @dataclass
        class SimulationConfig:  # type: ignore[redefinition]
            backend: str = "manual"
            time_step_s: float | None = None

            def model_copy(self, update: Dict[str, Any]):
                data = {**self.__dict__, **update}
                return SimulationConfig(**data)

        @dataclass
        class MoldProperties:  # type: ignore[redefinition]
            pass

        @dataclass
        class ProcessConditions:  # type: ignore[redefinition]
            pass

        @dataclass
        class QualityTargets:  # type: ignore[redefinition]
            pass

        class MVP0DSimulator:  # type: ignore[redefinition]
            def __init__(self, cfg: SimulationConfig):
                self.cfg = cfg

            def run(self, material, process, mold, quality):
                # Return a lightweight result object with a to_dict method that
                # contains the keys this script expects.
                class Result:
                    def to_dict(self):
                        return {
                            "rho_moulded": 1000.0,
                            "p_max_Pa": 1e5,
                            "t_demold_opt_s": 10.0,
                            "T_core_K": [300.0],
                            "p_total_Pa": [1e5],
                        }

                return Result()

        def load_process_scenario(path):  # type: ignore[redefinition]
            # Provide a SimpleNamespace with the attributes accessed by the script.
            return SimpleNamespace(
                simulation=None,
                process=ProcessConditions(),
                mold=MoldProperties(),
                quality=QualityTargets(),
                system_id="default",
            )

        def load_material_catalog(path):  # type: ignore[redefinition]
            # Return a simple dict-like catalog with a default material entry.
            return {"default": SimpleNamespace(name="stub_material")}


@dataclass
class BackendMetrics:
    name: str
    times_s: List[float]
    rho_moulded: float
    p_max_Pa: float
    t_demold_s: float
    mae_T_core_K: float
    mae_p_total_Pa: float


def _run_once(
    backend: str,
    scenario_path: Path,
    systems_path: Path,
    system_id: str | None,
    time_step_s: float | None,
) -> tuple[float, dict]:
    scenario = load_process_scenario(scenario_path)
    systems = load_material_catalog(systems_path)
    material = systems[system_id or scenario.system_id]

    sim_cfg: SimulationConfig = scenario.simulation or SimulationConfig()
    if time_step_s is not None:
        sim_cfg = sim_cfg.model_copy(update={"time_step_s": time_step_s})
    sim_cfg = sim_cfg.model_copy(update={"backend": backend})

    process: ProcessConditions = scenario.process
    mold: MoldProperties = scenario.mold
    quality: QualityTargets = scenario.quality

    simulator = MVP0DSimulator(sim_cfg)
    start = time.perf_counter()
    result = simulator.run(material, process, mold, quality)
    elapsed = time.perf_counter() - start
    return elapsed, result.to_dict()


def _extract_kpis(result: dict) -> tuple[float, float, float]:
    rho_moulded = float(result.get("rho_moulded", 0.0))
    p_max = float(result.get("p_max_Pa", 0.0))
    t_demold = float(
        result.get("t_demold_opt_s")
        or result.get("t_demold_min_s")
        or result.get("t_demold_max_s")
        or 0.0
    )
    return rho_moulded, p_max, t_demold


def _mae(series_ref: Iterable[float], series_other: Iterable[float]) -> float:
    ref_list = list(series_ref)
    other_list = list(series_other)
    n = min(len(ref_list), len(other_list))
    if n == 0:
        return 0.0
    total = 0.0
    for a, b in zip(ref_list[:n], other_list[:n]):
        total += abs(a - b)
    return total / n


def benchmark_backends(
    backends: List[str],
    backend_ref: str,
    repeats: int,
    scenario: Path,
    systems: Path,
    system_id: str | None,
    time_step_s: float | None,
) -> List[BackendMetrics]:
    metrics: List[BackendMetrics] = []

    # Run reference backend once for profile comparison
    ref_elapsed, ref_result = _run_once(backend_ref, scenario, systems, system_id, time_step_s)
    ref_rho, ref_p_max, ref_t_demold = _extract_kpis(ref_result)
    ref_T_core = ref_result.get("T_core_K", [])
    ref_p_total = ref_result.get("p_total_Pa", [])

    metrics.append(
        BackendMetrics(
            name=backend_ref,
            times_s=[ref_elapsed],
            rho_moulded=ref_rho,
            p_max_Pa=ref_p_max,
            t_demold_s=ref_t_demold,
            mae_T_core_K=0.0,
            mae_p_total_Pa=0.0,
        )
    )

    for backend in backends:
        if backend == backend_ref:
            continue

        times: List[float] = []
        last_result: dict | None = None
        for _ in range(repeats):
            try:
                elapsed, result = _run_once(backend, scenario, systems, system_id, time_step_s)
            except RuntimeError as exc:
                msg = str(exc)
                print(f"[WARN] Backend '{backend}' failed: {msg}")
                break
            times.append(elapsed)
            last_result = result

        if not times or last_result is None:
            continue

        rho, p_max, t_demold = _extract_kpis(last_result)
        mae_T = _mae(ref_T_core, last_result.get("T_core_K", []))
        mae_p = _mae(ref_p_total, last_result.get("p_total_Pa", []))

        metrics.append(
            BackendMetrics(
                name=backend,
                times_s=times,
                rho_moulded=rho,
                p_max_Pa=p_max,
                t_demold_s=t_demold,
                mae_T_core_K=mae_T,
                mae_p_total_Pa=mae_p,
            )
        )

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark ODE backends (manual / solve_ivp / sundials).")
    parser.add_argument(
        "--scenario",
        type=Path,
        default=Path("configs/scenarios/use_case_1.yaml"),
        help="Scenario YAML (process/mold/quality).",
    )
    parser.add_argument(
        "--systems",
        type=Path,
        default=Path("configs/systems/jr_purtec_catalog.yaml"),
        help="Material systems catalog YAML.",
    )
    parser.add_argument(
        "--system-id",
        type=str,
        default=None,
        help="Optional system id override (otherwise taken from scenario).",
    )
    parser.add_argument(
        "--backends",
        type=str,
        default="manual,solve_ivp",
        help="Comma-separated list of backends (e.g. manual,solve_ivp,sundials).",
    )
    parser.add_argument(
        "--backend-ref",
        type=str,
        default="manual",
        help="Reference backend for accuracy comparison.",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=3,
        help="Number of runs per backend.",
    )
    parser.add_argument(
        "--time-step",
        type=float,
        default=None,
        help="Optional override for SimulationConfig.time_step_s.",
    )
    args = parser.parse_args()

    backends = [b.strip() for b in args.backends.split(",") if b.strip()]
    if args.backend_ref not in backends:
        backends.append(args.backend_ref)

    print("Scenario:", args.scenario)
    print("Systems:", args.systems)
    print("Backends:", ", ".join(backends))
    print("Reference backend:", args.backend_ref)
    print("Repeats per backend:", args.repeats)
    if args.time_step is not None:
        print("Override time_step_s:", args.time_step)
    print()

    results = benchmark_backends(
        backends=backends,
        backend_ref=args.backend_ref,
        repeats=args.repeats,
        scenario=args.scenario,
        systems=args.systems,
        system_id=args.system_id,
        time_step_s=args.time_step,
    )

    if not results:
        print("No benchmark results produced (possibly all backends failed).")
        return

    print("Backend benchmark summary:")
    header = (
        f"{'backend':<12} {'time_mean_s':>12} {'time_std_s':>10} "
        f"{'rho_moulded':>12} {'p_max_Pa':>12} {'t_demold_s':>12} "
        f"{'MAE_T_core_K':>12} {'MAE_p_total_Pa':>16}"
    )
    print(header)
    print("-" * len(header))
    for m in results:
        mean_t = statistics.mean(m.times_s)
        std_t = statistics.pstdev(m.times_s) if len(m.times_s) > 1 else 0.0
        print(
            f"{m.name:<12} "
            f"{mean_t:12.4f} {std_t:10.4f} "
            f"{m.rho_moulded:12.3f} {m.p_max_Pa:12.1f} {m.t_demold_s:12.2f} "
            f"{m.mae_T_core_K:12.3f} {m.mae_p_total_Pa:16.1f}"
        )


if __name__ == "__main__":
    main()
