# ML & PROCESS LOGGING - PUR-MOLD-TWIN (TODO1 §12)

Plan logowania procesu i startowego pipeline ML. Dokument w języku polskim (bez znaków diakrytycznych w nazwach pól), UTF-8.

## 1. Cel
- Zebrać spójne logi produkcyjne, które można połączyć z wynikami symulacji.
- Zdefiniować featury i etykiety dla pierwszych modeli ML (klasyfikacja defektów, regresja `defect_risk`).
- Zapewnić kompatybilność z procesem kalibracji z `docs/CALIBRATION.md`.

## 2. Schemat logów procesu

### 2.1 Meta (`logs/meta.yaml`)
| Pole | Opis | Przyklad |
| --- | --- | --- |
| `shot_id` | identyfikator cyklu | `2025-01-12-1` |
| `system_id` | referencja do Material DB | `SYSTEM_R1` |
| `operator` | nazwa/ID | `OP123` |
| `timestamp_start` | ISO 8601 | `2025-01-12T09:42:00Z` |
| `line_id` | linia produkcyjna | `LINE_A` |

### 2.2 Parametry wejsciowe (`logs/process.yaml`)
Uzywamy tych samych nazw co w `ProcessConditions` / `MoldProperties`.
- `m_polyol`, `m_iso`, `m_additives`
- `T_polyol_in_C`, `T_iso_in_C`, `T_mold_init_C`, `T_ambient_C`
- `RH_ambient_pct`, `mixing_eff`
- `vent_status` (np. `clean`, `partial`, `clogged`)
- `t_demold_actual_s`, `pentane_pct`

### 2.3 Czasowe logi CSV
| Plik | Kolumny | Uwagi |
| --- | --- | --- |
| `logs/sensors_core_temp.csv` | `time_s`, `T_core_C` | 2-10 Hz |
| `logs/sensors_pressure.csv` | `time_s`, `p_total_bar`, opcjonalnie `vent_open_fraction` | |
| `logs/sensors_power_mix.csv` | `time_s`, `power_W`, `rpm` | optional |

### 2.4 Wyniki koncowe (`logs/qc.yaml`)
| Pole | Opis |
| --- | --- |
| `rho_moulded`, `rho_free_rise` |
| `H_demold`, `H_24h` |
| `defects`: lista (`voids`, `flash`, `burn`, ...) |
| `defect_risk_operator`: ocena subiektywna 0-1 |

## 3. Feature engineering

Nazwy kolumn pokrywaja sie z `src/pur_mold_twin/logging/features.py` i `src/pur_mold_twin/data/schema.py`.

### 3.1 Featury bazowe (z logow)
- Temperatury: `meas_T_core_max_C`, `meas_T_core_t_at_max_s`, `meas_T_core_avg_0_120_C`, `meas_T_core_slope_0_60_C_per_s`.
- Cisnienie: `meas_p_max_bar`, `meas_p_t_at_max_s`, `meas_p_slope_0_60_bar_per_s`.
- Wejscia procesu: `proc_T_polyol_in_C`, `proc_T_iso_in_C`, `proc_T_mold_init_C`, `proc_RH_ambient`, `proc_mixing_eff`, `t_demold_actual_s` (opcjonalnie z meta/process.yaml).
- QC: `qc_rho_moulded`, `qc_H_demold`, `qc_H_24h`, `any_defect`, `defect_risk` (operator lub model).

### 3.2 Featury z symulacji + roznice
- Symulacja: `sim_T_core_max_C`, `sim_T_core_t_at_max_s`, `sim_p_max_bar`, `sim_p_t_at_max_s`, `sim_rho_moulded`, `sim_t_demold_opt_s`, `sim_defect_risk`.
- Roznice: `delta_T_core_max_C`, `delta_p_max_bar`, `delta_t_demold_s`.

### 3.3 Targety ML
- **Klasyfikacja defektow**: `any_defect` (oraz ewentualne per-defect po rozszerzeniu logow).
- **Regresja defect_risk**: pole `defect_risk` (preferowana ocena operatora, fallback = wynik symulacji).

## 4. Modele i pipeline

1. **ETL**: `src/pur_mold_twin/data/etl.py` laczy logi (`meta/process/qc` + `sensors_core_temp.csv`, `sensors_pressure.csv`).
2. **Feature store**: `src/pur_mold_twin/logging/features.py` + CLI `build-features` (`pur-mold-twin build-features --sim ... --measured logs/...`) zapisuje `data/ml/features.parquet` (fallback do CSV, jeżeli brak `pyarrow`/`fastparquet`).
3. **Skrypt pomocniczy**: `scripts/build_dataset.py` realizuje to samo poza CLI.
4. **Modele startowe** (opcjonalne extras `[ml]`): `ml/baseline.py` (RandomForest), trening w `ml/train_baseline.py` przy `features.parquet`.
5. **Cross-validation**: planowane `GroupKFold` po `system_id`, metryki: `MAE` (regresja), `F1/precision` (klasyfikacja).

## 5. Integracja z produktem

- CLI: `pur-mold-twin build-features --sim out/run.json --measured logs/sample/ --output data/ml/features.parquet`.
- Modele ML sa **opcjonalne** (`pip install pur-mold-twin[ml]`), brak scikit-learn skutkuje czytelnym komunikatem.
- Output modeli: `models/defect_risk.pkl`, `models/defect_classifier.pkl` (gdy beda trenowane).
- Raport w `reports/ml/README.md` (accuracy, data drift) po zbudowaniu datasetu.

## 6. TODO (dla Paczki §12)
- [x] Utworzyc katalog `data/ml/` (gitignored) na logi/feature store.
- [x] Dodac skrypt ETL/feature builder (`scripts/build_dataset.py`, CLI `build-features`).
- [ ] Zaimplementowac baseline w `notebooks/ml_baseline.ipynb`.
- [ ] Dokumentowac iteracje w `admin/ML_changelog.md` (po utworzeniu danych).
