# Configs guide (Material DB + process scenarios)

This guide summarizes required vs optional fields for `configs/systems/` and `configs/scenarios/`, aligning `src/pur_mold_twin/material_db/models.py` with `docs/MODEL_OVERVIEW.md` and `docs/USE_CASES.md`.

## Material systems (`configs/systems/*.yaml`)

### Required fields
- `system_id`, `description`.
- `polyol`: `name`, `oh_number_mgKOH_per_g`, `functionality`, `density_kg_per_m3`, `viscosity_mPa_s`, `water_fraction` (0-1). `pentane_fraction` defaults to 0.0 when the system has no physical blowing agent.
- `isocyanate`: `name`, `nco_percent`, `functionality`, `density_kg_per_m3`, `viscosity_mPa_s`.
- `foam_targets`: `rho_free_rise_target`, `rho_moulded_target`.
- `mechanical_targets`: `h_24h_target_shore` (used for calibration).

### Optional fields
- Reaction times: `cream_time_s`, `gel_time_s`, `rise_time_s`, `tack_free_time_s`.
- Mechanical: `h_demold_target_shore` (demold calibration point).
- Metadata blocks under components or the root (`documents`, `vendor`, `notes`, processing recommendations, URLs).

### Validation notes
- Fractions must stay within `[0,1]` (`water_fraction`, `pentane_fraction`).
- Physical properties and targets should be `> 0` when provided. Use `null` only when data is missing, but fill them before production runs so `MaterialSystem.validate_required_fields()` can enforce completeness.
- Prefer consistent reference temperatures in metadata for viscosity/density values.

### Minimal example (no pentane)
```yaml
---
system_id: SYSTEM_MINIMAL
description: "Baseline two-component foam"
polyol:
  name: "Polyol A"
  oh_number_mgKOH_per_g: 250
  functionality: 3.0
  density_kg_per_m3: 1020
  viscosity_mPa_s: 800
  water_fraction: 0.015
  pentane_fraction: 0.0
  cream_time_s: 15
  gel_time_s: 60
  rise_time_s: 110
isocyanate:
  name: "ISO 31"
  nco_percent: 31.0
  functionality: 2.7
  density_kg_per_m3: 1220
  viscosity_mPa_s: 220
foam_targets:
  rho_free_rise_target: 30
  rho_moulded_target: 40
mechanical_targets:
  h_24h_target_shore: 55
```

### Full example with metadata
```yaml
---
system_id: SYSTEM_FULL
description: "Flexible foam with pentane"
polyol:
  name: "Polyol B"
  oh_number_mgKOH_per_g: 260
  functionality: 3.2
  density_kg_per_m3: 1015
  viscosity_mPa_s: 900
  water_fraction: 0.017
  pentane_fraction: 0.10
  cream_time_s: 18
  gel_time_s: 70
  rise_time_s: 130
  tack_free_time_s: 165
  metadata:
    documents: ["PolyolB_TDS_v2.pdf"]
    reference_temperature_C: 23
    notes:
      - "Cup test times at 23C"
      - "Pentane preblend"
isocyanate:
  name: "ISO 31"
  nco_percent: 31.0
  functionality: 2.7
  density_kg_per_m3: 1220
  viscosity_mPa_s: 220
  metadata:
    documents: ["ISO31_TDS.pdf"]
    reference_temperature_C: 25
foam_targets:
  rho_free_rise_target: 30
  rho_moulded_target: 40
mechanical_targets:
  h_demold_target_shore: 40
  h_24h_target_shore: 55
metadata:
  processing_recommendations:
    component_temp_C: [23, 28]
    mould_temp_C: [40, 50]
  source:
    tds_url: "https://example.com/system_full_tds"
```

## Process scenarios (`configs/scenarios/*.yaml`)

### Required fields
- `system_id`: links to Material DB entry.
- `process`: `m_polyol`, `m_iso`, `nco_oh_index`, `T_polyol_in_C`, `T_iso_in_C`, `T_mold_init_C`, `T_ambient_C`, `RH_ambient`, `mixing_eff`; `m_additives` is optional (default 0.0).
- `mold`: `cavity_volume_m3`, `mold_surface_area_m2`, `mold_mass_kg` (thermal mass); add vent data when available.
- `quality`: `alpha_demold_min`, `H_demold_min_shore`, `H_24h_min_shore`, `rho_moulded_min`, `rho_moulded_max`, `p_max_allowable_bar` (plus `t_cycle_max` if used by optimizers).

### Optional fields
- `simulation`: `total_time_s`, `time_step_s`, `backend` (default solver/backend handled in code when omitted).
- Extended mold data: vent geometry/effectiveness, wall thickness, conductivity.
- Additional quality/constraint knobs: `defect_risk_max`, `t_cycle_max`.

### Minimal scenario example
```yaml
system_id: SYSTEM_MINIMAL
process:
  m_polyol: 1.0
  m_iso: 1.05
  m_additives: 0.0
  nco_oh_index: 1.05
  T_polyol_in_C: 25.0
  T_iso_in_C: 25.0
  T_mold_init_C: 40.0
  T_ambient_C: 22.0
  RH_ambient: 0.5
  mixing_eff: 0.9
mold:
  cavity_volume_m3: 0.025
  mold_surface_area_m2: 0.8
  mold_mass_kg: 120.0
quality:
  alpha_demold_min: 0.75
  H_demold_min_shore: 40.0
  H_24h_min_shore: 55.0
  rho_moulded_min: 35.0
  rho_moulded_max: 45.0
  p_max_allowable_bar: 5.0
```

### Full scenario example with vents and simulation presets
```yaml
system_id: SYSTEM_FULL
process:
  m_polyol: 1.0
  m_iso: 1.08
  m_additives: 0.02
  nco_oh_index: 1.05
  T_polyol_in_C: 26.0
  T_iso_in_C: 26.0
  T_mold_init_C: 42.0
  T_ambient_C: 23.0
  RH_ambient: 0.6
  mixing_eff: 0.85
mold:
  cavity_volume_m3: 0.025
  mold_surface_area_m2: 0.8
  mold_mass_kg: 120.0
  vents:
    count: 3
    diameter_m: 0.001
    length_m: 0.05
    initial_conductance_Pa_s_per_m3: 1.0e6
quality:
  alpha_demold_min: 0.75
  H_demold_min_shore: 40.0
  H_24h_min_shore: 55.0
  rho_moulded_min: 38.0
  rho_moulded_max: 45.0
  p_max_allowable_bar: 5.0
  defect_risk_max: 0.10
  t_cycle_max: 600.0
simulation:
  total_time_s: 600.0
  time_step_s: 0.5
  backend: manual
```

### Commenting missing data
When TDS/SDS values are missing, keep `null` placeholders but add inline comments to document the source gap (e.g., `# OH number not listed in TDS`). This keeps the YAML loadable while signalling fields that must be filled before calibration or production runs.
