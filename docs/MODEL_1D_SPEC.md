# MODEL 1D SPEC (EXPERIMENTAL) - PUR-MOLD-TWIN (TODO3)

Specification for the pseudo-1D thermal/kinetic extension planned in TODO3 Block 2.
This document complements `docs/MODEL_OVERVIEW.md` and focuses on additional assumptions,
state variables and solver requirements for a layered, quasi-1D representation of the mold cavity.

## 1. Purpose & scope

- Capture spatial gradients along the thickness of the foam layer inside the mold (normal to the mold wall).
- Preserve compatibility with the existing 0D solver:
  - same external API (`MVP0DSimulator` + dataclasses),
  - ability to collapse to 0D when `dimension = "0d"` or when only one layer is used.
- Provide an experimental mode (`dimension = "1d_experimental"`) for R&D teams to study:
  - thermal lag between mold wall and core,
  - cures rates in early/late sections of the part,
  - effect of vents or trapped gas near the surface.

The 1D extension does **not** target CFD-level fidelity; it uses a lumped set of layers (5-15) with simplified conduction and reaction coupling.

## 2. Domain discretisation

- Geometry: slab from mold wall (layer index `0`) to inner core (layer index `N-1`).
- Each layer stores:
  - `alpha_i(t)` – local degree of cure,
  - `T_i(t)` – local core temperature,
  - `rho_i(t)` – local apparent density (derived from expansion state),
  - optional `p_i(t)` – local gas pressure contribution (for future vent modelling).
- Thickness per layer: `thickness = foam_thickness / N_layers`.
- `N_layers` is configurable (default 5), with `N=1` equivalent to the current 0D formulation.
- Boundary conditions:
  - layer `0` exchanges heat with the mold wall via `h_core_to_mold`,
  - layer `N-1` exchanges with "bulk/core" or ambient (depending on vent openness).

## 3. Governing equations (sketch)

1. **Kinetics per layer**:
   - Arrhenius-based kinetics reused from 0D but applied per-layer with local temperature `T_i`.
   - `phi_i` / `alpha_i` integration remains uncoupled between layers except through temperature coupling.
2. **Heat conduction**:
   - Finite-difference style conduction between adjacent layers:
     ```
     dT_i/dt = (heat_release_i - conduction_to_neighbors_i - conduction_to_mold_or_ambient) / (m_layer * cp)
     ```
   - Conduction coefficient derived from effective thermal conductivity of foam (parameterised).
3. **Gas / expansion**:
   - Base version shares the same global gas balance as 0D (CO2, pentane) but distributes density per layer using `rho_i`.
   - Future work may include local vent sealing or permeability.
4. **Pressure & vent effects**:
   - For the experimental stage, pressure remains a global metric (0D) while vent closure can optionally depend on surface layers (e.g., when `alpha_0` exceeds a threshold).
   - Later iterations may incorporate per-layer vent effectiveness.

## 4. Solver approach

- Maintain the existing `SimulationContext` concept but extend it with 1D-specific fields (number of layers, thermal conductivity, etc.).
- Backends:
  - manual/explicit scheme extended to handle per-layer states,
  - `solve_ivp` backend may not be immediately extended (manual backend suffices for prototype),
  - selection controlled via `SimulationConfig.dimension`.
- Integration loop:
  1. Evaluate kinetics for each layer (Arrhenius step).
  2. Compute heat conduction between layers.
  3. Update temperature and alpha.
  4. Update gas/pressure via aggregated densities (for compatibility with existing outputs).
- Output profiles:
  - For compatibility, we still provide single `T_core(t)` etc. by aggregating (e.g., mean temperature of all layers or of the deepest layer).
  - Additionally expose per-layer profiles in the result dictionary (e.g., `T_layer_K` as list of lists) for analysis.

## 5. Configuration & API

- `SimulationConfig.dimension` (Literal `"0d"` or `"1d_experimental"`) selects solver path.
  - Default `"0d"` (fully backward compatible).
  - When `"1d_experimental"`, `MVP0DSimulator.run()` will route to the 1D solver module.
- Additional config fields (to be introduced later in TODO3):
  - `layers_count`: int (default 5),
  - `foam_conductivity_W_per_mK`,
  - `interlayer_contact_resistance`,
  - optional toggles for per-layer vent closure heuristics.
- CLI / config files:
  - YAML scenarios may specify `simulation.dimension: 1d_experimental`.
  - CLI should surface a `--dimension` override for experimentation (later task).
- Result serialisation:
  - Keep existing keys for compatibility.
  - Extend `SimulationResult` with optional `layer_profiles` dict to store per-layer series.

## 6. Validation & roadmap

- Validation strategy:
  - `N_layers = 1` -> results should match 0D baseline within regression tolerances.
  - Multi-layer cases compared against either lab data or expected qualitative behaviour (e.g., hotter core, colder surface).
- Performance expectations:
  - O(N_layers) compared to 0D; number of spatial nodes remains low (<20) to keep runtime acceptable.
- Roadmap:
  1. Implement 1D solver skeleton (`core/simulation_1d.py`) with conduction + kinetics.
  2. Extend CLI/tests to toggle between 0D and 1D.
  3. Add documentation to `docs/MODEL_OVERVIEW.md` (experimental section) summarising limitations and recommended use cases.
  4. Future iterations may integrate per-layer vent sealing, localized pressure, or coupling with 1D vent network models.

