# PERFORMANCE & BACKEND COMPARISON - PUR-MOLD-TWIN (TODO3)

Benchmark and comparison methodology for ODE backends in PUR-MOLD-TWIN.

This document supports TODO3 Blok 1 (zadania 4-7): modular backends, optional SUNDIALS/JAX integration and performance validation.

## 1. Goals

- Provide a reproducible way to compare solver backends (`manual`, `solve_ivp`, and future `sundials`/`jax`) on representative scenarios.
- Track:
  - wall-clock time per simulation,
  - number of time steps / solver steps (if available),
  - numerical deviation from a reference backend (profiles and key KPIs).
- Offer a lightweight workflow suitable for local experiments and CI sanity checks (without heavy plotting requirements).

## 2. Backends under test

- `manual`:
  - explicit time-marching scheme implemented in `core/ode_backends.py`,
  - fixed time step based on `SimulationConfig.time_step_s`.
- `solve_ivp`:
  - SciPy-based backend (`scipy.integrate.solve_ivp`),
  - typically using stiff methods (`Radau`/`BDF`) with tolerances from `SimulationConfig`.
- `sundials` (future):
  - backend based on SUNDIALS through `scikits.odes` or `scikit-sundae`,
  - exposed as backend `"sundials"` in `core/ode_backends.py`, guarded by optional extra `pur-mold-twin[sundials]`.
- `jax` (future):
  - experimental backend using JAX + Diffrax or a similar library,
  - intended for batch / GPU use cases and advanced research, not required for baseline product 1.0.

Current implementation provides `manual` and `solve_ivp` as working backends; `sundials` and `jax` are placeholders guarded by extras and should fail with descriptive messages if the required libraries are missing.

## 3. Benchmark scenarios

Benchmarks use existing configuration files and golden paths to keep results comparable with regression tests.

Suggested scenarios:

1. **Short / nominal shot**:
   - `configs/scenarios/use_case_1.yaml` (SYSTEM_R1, no pentane, moderate RH),
   - total time ~600 s, default time step (0D reference case).
2. **Long / cold shot**:
   - variant of use_case_1 with reduced temperatures and higher RH (configured via CLI or scenario override),
   - stresses convergence and stiffness behaviour.
3. **High-pressure / no-vent shot**:
   - mold with disabled vents (`vent=None`), mimicking clogged vent edge-case from tests.

The initial implementation of `scripts/bench_backends.py` focuses on a single scenario (use_case_1) and can be extended with additional variants as TODO3 progresses.

## 4. Metrics

For each backend and scenario, benchmarks should report at minimum:

- **Performance metrics**:
  - wall-clock time for a single simulation (s),
  - number of time points in the result (`len(time_s)`),
  - optionally: internal solver stats if available (e.g. SciPy `nfev`, `njev`).
- **Accuracy metrics vs reference**:
  - reference backend: `manual` (baseline) or `solve_ivp` (if chosen as reference),
  - scalar KPIs:
    - `rho_moulded` difference,
    - `p_max_Pa` difference,
    - `t_demold_opt_s` (or `t_demold_min_s` as fallback) difference.
  - simple profile error:
    - mean absolute difference for `T_core_K` and `p_total_Pa` sampled on the common time grid.

All tolerances and expectations should be aligned with those used in regression tests (`tests/test_core_simulation.py`).

## 5. Tooling: scripts/bench_backends.py

The script `scripts/bench_backends.py` provides a simple CLI to run benchmarks:

- Inputs:
  - `--scenario` (Path, default `configs/scenarios/use_case_1.yaml`),
  - `--systems` (Path, default `configs/systems/jr_purtec_catalog.yaml`),
  - `--system-id` (str, default scenario.system_id),
  - `--backends` (comma-separated list, default `manual,solve_ivp`),
  - `--repeats` (int, default 3 runs per backend),
  - `--backend-ref` (str, default `manual`),
  - `--time-step` (float, optional override for `SimulationConfig.time_step_s`).
- Behaviour:
  - loads scenario and material system via existing loaders,
  - constructs `MVP0DSimulator` for each backend,
  - measures wall-clock time using `time.perf_counter()` over N repeats,
  - collects KPIs and profile-based errors vs reference backend,
  - prints a human-readable summary table.

The script is intentionally text-only (no plots) to keep dependencies minimal and to be suitable for command-line use or CI runs.

## 6. Usage examples

Basic benchmark on the reference scenario using manual vs solve_ivp:

```bash
python scripts/bench_backends.py \
    --scenario configs/scenarios/use_case_1.yaml \
    --systems configs/systems/jr_purtec_catalog.yaml \
    --backends manual,solve_ivp \
    --backend-ref manual \
    --repeats 3
```

Attempt to include SUNDIALS backend (will report a clear error if extras are missing):

```bash
python scripts/bench_backends.py \
    --scenario configs/scenarios/use_case_1.yaml \
    --backends manual,solve_ivp,sundials
```

On environments with `pur-mold-twin[sundials]` installed, this can be used to compare SUNDIALS vs the reference backend.

## 7. Reporting and evolution

- For day-to-day development, text output from `bench_backends.py` is sufficient.
- For deeper analysis, results can be redirected to a CSV/JSON file and plotted externally or in a notebook.
- As TODO3 progresses:
  - add additional scenarios to cover cold/high-RH and high-pressure cases,
  - extend metrics with solver-specific statistics where available,
  - integrate with CI to detect regressions in backend performance or accuracy.

