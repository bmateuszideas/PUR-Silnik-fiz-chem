# ML & PROCESS LOGGING - PUR-MOLD-TWIN (TODO1 §12)

Plan rozbudowy logów procesu i modeli ML dla diagnozy/defect risk. Dokument w języku polskim (bez znaków diakrytycznych).

## 1. Cel
- Zebranie spójnych logów produkcyjnych, które można połączyć z wynikami symulacji.
- Definicja featurów i etykiet, umożliwiających pierwsze modele ML (klasyfikacja defektow, regresja `defect_risk`, analiza odchyłek).
- Zapewnienie kompatybilności z procesem kalibracji z `docs/CALIBRATION.md`.

## 2. Schemat logów procesu

### 2.1 Meta (`logs/meta.yaml`)
| Pole | Opis | Przyklad |
| --- | --- | --- |
| `shot_id` | identyfikator cyklu | `2025-01-12-1` |
| `system_id` | referencja do Material DB | `SYSTEM_R1` |
| `operator` | nazwa/ID | `OP123` |
| `timestamp_start` | ISO 8601 | `2025-01-12T09:42:00Z` |
| `line_id` | linia produkcyjna | `LINE_A` |

### 2.2 Parametry wejściowe (`logs/process.yaml`)
Używamy tych samych nazw co w `ProcessConditions` / `MoldProperties`.
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

### 2.4 Wyniki końcowe (`logs/qc.yaml`)
| Pole | Opis |
| --- | --- |
| `rho_moulded`, `rho_free_rise` |
| `H_demold`, `H_24h` |
| `defects`: lista (`voids`, `flash`, `burn`, ...) |
| `defect_risk_operator`: ocena subiektywna 0-1 |

## 3. Feature engineering

### 3.1 Featury bazowe (z logów)
- Statystyki temperatur: `max`, `t_at_max`, `avg(T_core)` 0-120 s, slope w oknie 0-60 s.
- Statystyki cisnienia: `p_max`, `t_p_max`, `p_max_rate`, `vent_open_min`.
- Parametry wejściowe: `T_polyol_in`, `T_iso_in`, `T_mold_init`, `RH_ambient_pct`, `mixing_eff`, `pentane_pct`.
- Parametry QC: `t_demold_actual`, `rho_moulded`, `H_demold`.

### 3.2 Featury z symulacji (róznice vs pomiar)
- `delta_T_core_max = T_core_max_measured - T_core_max_sim`.
- `delta_p_max`, `delta_t_demold_opt`, `delta_H_demold`, `delta_rho`.
- Binary flags: `quality_status != measured_status`, `pressure_status != measured_status`.

### 3.3 Targety ML
- **Klasyfikacja defektów**: wielo-etykietowa (binarna kolumna per defekt) + `any_defect`.
- **Regresja defect_risk**: cel = `max(operator_eval, model_sim.defect_risk)`.
- **Diagnozy**: tags `cold_material`, `high_humidity`, `vent_clog`, `early_demold`.

## 4. Modele i pipeline

1. **ETL**: skrypt (docelowo `scripts/build_dataset.py`) scalający logi i wyniki symulacji.
2. **Feature store**: plik `data/ml/features.parquet` z kolumnami:
   - `features_*` (prefiksy), `targets_*`, `shot_id`, `system_id`.
3. **Modele startowe**:
   - `defect_risk`: `sklearn.ensemble.RandomForestRegressor`.
   - `defect_type`: `RandomForestClassifier` lub `LogisticRegression` dla `voids`/`flash`.
   - `diagnosis`: heurystyki z TODO §8 + `GradientBoostingClassifier` na flagi.
4. **Cross-validation**:
   - Grupowane po `system_id` (k-fold z `GroupKFold`), metryki: `MAE` dla regresji, `F1`/`precision` dla klasyfikacji.

## 5. Integracja z produktem

- CLI (przyszle): `pur-mold-twin ml-train --dataset data/ml/features.parquet`.
- Output modeli: `models/defect_risk.pkl`, `models/defect_classifier.pkl`.
- Raport w `reports/ml/README.md` (accuracy, data drift).

## 6. TODO (dla Paczki §12)
- [ ] Utworzyć katalog `data/ml/` (gitignored) na logi/feature store.
- [ ] Dodać skrypt ETL (po uzgodnieniu) -> generuje `features.parquet`.
- [ ] Zaimplementować baseline w `notebooks/ml_baseline.ipynb`.
- [ ] Dokumentować iteracje w `admin/ML_changelog.md` (po utworzeniu danych).
