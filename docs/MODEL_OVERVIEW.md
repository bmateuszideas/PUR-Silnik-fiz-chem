# MODEL OVERVIEW - PUR-MOLD-TWIN

Definition of Task 1 deliverables: physics scope, I/O specification, quality gates, constraints, accuracy targets, and runtime stack. English only, UTF-8.

## 1. Phenomena covered in MVP

| Area | Phenomena included | Notes |
| --- | --- | --- |
| Stoichiometry and gas balance | NCO/OH index from TDS, CO2 from NCO + H2O, pentane inventory (if used), effective water `water_eff = water_from_polyol + water_from_RH_surface` | Drives molar balances and available gas; RH component uses mold area, RH threshold (45% default) and a capped condensation mass to estimate extra H2O |
| Kinetics and heat | Degree of cure `alpha(t)` (0-1), Arrhenius or empirical kinetics vs temperature, reaction exotherm, heat exchange foam-mold-ambient, temperature influence on pentane evaporation | Coupled ODEs for `alpha` and `T` |
| Expansion and density | Volume gain from CO2 + pentane, mapping to `rho_free_rise` and `rho_moulded`, influence of temperature/pressure/vent sealing | Provides molded density trend and fill ratio |
| Pressure and vents | Partial pressures `p_air`, `p_CO2`, `p_pentane`, vent effectiveness `vent_eff(t)` decreasing 1 to 0, total pressure `p(t)`, `pressure_status`, `vent_closure_time` | Supports `p_max`/safety diagnostics |
| Mechanical response | Hardness function `H = f(alpha, rho)` with demold vs 24 h states | Feeds demold status |
| Diagnostics | Rules for cold components, RH driven `water_eff`, `mixing_eff`, early vent closure, demold timing | Produces warnings and `defect_risk` |

## 2. I/O specification (names, units, ranges)

### 2.1 Material and system inputs

| Field | Description | Units internal | Typical range | Source |
| --- | --- | --- | --- | --- |
| `OH_number` | Hydroxyl number of polyol/system | mgKOH/g -> SI | 200-500 | TDS |
| `functionality_polyol` | Average OH functionality | dimensionless | 2.0-4.5 | TDS |
| `density_polyol` | Density at reference temperature | kg/m3 | 900-1100 | TDS |
| `viscosity_polyol` | Kinematic viscosity at reference temperature | mPa*s -> Pa*s | 300-3000 | TDS |
| `water_pct` | Water mass fraction in polyol | 0-1 | 0.005-0.03 | TDS |
| `pentane_pct` | Pentane wt. fraction (if system uses physical blowing) | 0-1 | 0-0.12 | TDS |
| `cream_time_ref`, `gel_time_ref`, `rise_time_ref`, `tack_free_time_ref` | Reference times from TDS | s | 10-200 | TDS |
| `rho_free_rise_target`, `rho_moulded_target` | Density targets | kg/m3 | 20-80 | TDS / customer spec |
| `%NCO` | NCO wt.% of iso component | percent -> fraction | 25-33 | TDS |
| `functionality_iso` | Iso functionality | dimensionless | 2.0-3.0 | TDS |
| `density_iso`, `viscosity_iso` | Iso physical properties | kg/m3, Pa*s | 1100-1300 kg/m3; 150-1500 mPa*s | TDS |
| Mechanical targets (`H_24h_target`, etc.) | Reference hardness for calibration | Shore | 35-70 Shore A equivalent | QA data |

### 2.2 Process and cycle inputs

| Field | Description | Units internal | Typical range | Source |
| --- | --- | --- | --- | --- |
| `m_polyol`, `m_iso`, `m_additives` | Component masses | kg | 0.5-5 per shot | Recipe |
| `NCO_OH_index` | Stoichiometric index | dimensionless | 0.90-1.15 | Recipe |
| `T_polyol_in_C`, `T_iso_in_C`, `T_mold_init_C`, `T_ambient_C` (koncepcyjnie: `T_polyol_in`, `T_iso_in`, `T_mold_init`, `T_ambient`) | Temperatures converted to K internally | C on input | 15-60 C | Process log |
| `RH_ambient` | Relative humidity (input can be %, drives `water_from_RH_surface`) | 0-1 | 0.30-0.85 | Process log |
| `mixing_eff` | Proxy for mixing quality | 0-1 | 0.6-1.0 | Operator |
| `V_cavity` | Mold cavity volume | m3 | 0.01-0.20 | Tooling |
| `A_mold`, wall thickness, thermal properties | Mold area and conduction data | m2, m, W/m*K | project dependent | Tooling |
| `VentConfig` | Number, size, location, initial conductance | mm, Pa*s/m3 eq. | project dependent | Tooling |

### 2.3 Quality and constraint inputs

| Field | Description | Units | Default/initial value |
| --- | --- | --- | --- |
| `alpha_demold_min` | Minimum degree of cure at demold | 0-1 | 0.75 |
| `H_demold_min` | Minimum hardness at demold | Shore | 40 Shore |
| `H_24h_min` | Minimum hardness after 24 h | Shore | 50 Shore |
| `rho_moulded_min` / `rho_moulded_max` | Acceptable density band | kg/m3 | 38 / 45 in reference case |
| `defect_risk_max` | Maximum acceptable risk metric | 0-1 | 0.10 |
| `p_max_allowable_bar` | Maximum in-cavity pressure (safety limit) | bar | 5.0 bar default |
| `t_cycle_max` | Maximum cycle time | s | 600 s default |

### 2.4 Simulation outputs

| Field | Description | Units |
| --- | --- | --- |
| Profiles `alpha(t)`, `T_core(t)`, `T_mold(t)`, `rho(t)`, `p_total(t)`, partials `p_air/p_CO2/p_pentane`, `vent_eff(t)` | Time series from solver | alpha 0-1, K, kg/m3, Pa |
| Demold window `t_demold_min`, `t_demold_max`, `t_demold_opt` | Times where constraints are met | s |
| Hardness predictions `hardness(t)`, `H_demold`, `H_24h` | Shore |  |
| Density prediction `rho_moulded` | kg/m3 |  |
| Pressure metrics `p_air`, `p_CO2`, `p_pentane`, `p_total`, `p_max`, time of occurrence, `pressure_status` | Pa/bar, categorical |  |
| Vent diagnostics `vent_eff(t)`, `vent_closure_time` | fraction, s | |
| Water diagnostics `water_from_polyol`, `water_from_RH_surface`, `water_eff`, `water_eff_fraction`, `water_risk_score` | kg, kg, kg, fraction, 0-1 | |
| Quality status `quality_status`, `defect_risk`, diagnostics list | categorical, 0-1, text |  |

> **Validation & units**: Wszystkie wejścia/wyjścia procesu korzystają z modeli Pydantic (`src/pur_mold_twin/core/types.py`). Pola temperatury i ciśnienia akceptują zarówno wartości numeryczne (°C/bar/Pa) jak i `pint.Quantity`; na etapie walidacji konwertujemy je do SI (K / Pa), więc jeden kontrakt obowiązuje w całym solverze.

## 3. Quality gates and process constraints

- Demold readiness requires `alpha >= alpha_demold_min`, `H >= H_demold_min`, `p <= p_max_allowable_bar`, and `rho_moulded` within `[rho_moulded_min, rho_moulded_max]`.
- Safety classification: `p_max` flagged SAFE, NEAR_LIMIT, or OVER_LIMIT relative to `p_max_allowable_bar`; `quality_status` uses te same plus `H_24h` i `defect_risk`.
- Cycle planning: optimizer must deliver `t_demold <= t_cycle_max`.
- Diagnostics assign `defect_risk`; viable plans hold `defect_risk <= defect_risk_max`.

## 4. MVP accuracy targets

| Metric | Target accuracy |
| --- | --- |
| `t_demold_opt` | +/- 60 s (approx. +/- 1 min) |
| `rho_moulded` | +/- 5-10 percent vs measured data |
| `p_max` | +/- 10-15 percent vs measured data |
| Cream / gel / rise times | +/- 20 percent vs TDS |
| `H_demold`, `H_24h` | +/- 5 Shore once calibrated |

## 5. Runtime stack confirmation (Python 3.14)

- Runtime: `numpy`, `scipy`, `pandas`, `pydantic`, `pint`, `matplotlib`.
- Config and CLI: `ruamel.yaml`, `typer` (or fallback `argparse`).
- Dev and QA: `pytest`.
- Deferred extras (post-MVP or when justified): `thermo`, `CoolProp`, `Cantera`, `scikit-learn`, `pyomo`, `numba`, `pint-pandas`.
