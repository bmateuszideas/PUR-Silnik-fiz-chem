# ODE Backend Contract

This document summarises the expected contract for ODE backends in pur-mold-twin.

Purpose
-------
Define the expected behaviour of `integrate_system` and backend implementations so
that callers can rely on stable outputs and diagnostics.

API
---
Function: `integrate_system(ctx: SimulationContext, backend: Optional[str] = None, **backend_kwargs) -> Trajectory`

- `ctx`: SimulationContext (see `src/pur_mold_twin/core/simulation.py`). Must include a valid
  `config` (SimulationConfig) with `total_time_s` and `time_step_s`.
- `backend`: one of `"manual"`, `"solve_ivp"`, `"sundials"`, `"jax"`. If None, read from `ctx.config.backend`.
- `backend_kwargs`: optional backend-specific kwargs; supported global optional key is `diag_callback`.

Return value
------------
A `Trajectory` object with lists:
- `time_s`: list[float]
- `alpha`: list[float]
- `T_core_K`: list[float]
- `T_mold_K`: list[float]
- `phi`: list[float]

Length: lists should be of equal length > 1. Preferably the returned `time_s` corresponds to
`linspace(0, cfg.total_time_s, cfg.steps())` i.e. the requested evaluation grid. If a solver returns
an internal adaptive grid, backend MAY return that grid but MUST emit diagnostics explaining the
difference.

Diagnostics
-----------
Callers may pass `diag_callback: Callable[[str, dict], None]` in `backend_kwargs`. Backends will call
`diag_callback(event_name, payload)` for notable events, e.g. `("sundials_complete", {"nsteps": 12345})`.
If `diag_callback` is not provided, backends will log diagnostic messages using the module logger.

Errors
------
- Backends MUST raise `RuntimeError` with a clear message when required optional dependencies are missing
  (e.g. scikits.odes for the sundials backend).
- Backends MUST raise `RuntimeError` on solver failure.

Notes on interpolation
----------------------
If a backend returns solver outputs on a grid different from the requested grid and the caller requires
values on the requested grid, consider interpolating solver outputs onto the requested grid before returning.
Document which approach is used for each backend.
