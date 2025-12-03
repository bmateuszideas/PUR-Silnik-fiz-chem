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
| `rho_moulded`, `rho_free_rise` | Gestosci formowane i free-rise |
| `H_demold`, `H_24h` | Twardosci w chwili demold i po 24h |
| `defects` | Lista defektow (`voids`, `flash`, `burn`, ...) |
| `defect_risk_operator` | Ocena operatora 0-1 |

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
3. **Skrypt pomocniczy**: historyczne wersje znajduja sie w `scripts/archive/`; kanoniczny sposob lokalny to CLI `build-features` (lub helpery w `tests/helpers/`).
4. **Modele startowe** (opcjonalne extras `[ml]`): `ml/baseline.py` (RandomForest), trening w `ml/train_baseline.py` przy `features.parquet`.
5. **Cross-validation**: planowane `GroupKFold` po `system_id`, metryki: `MAE` (regresja), `F1/precision` (klasyfikacja).

## 5. Integracja z produktem

- CLI: `pur-mold-twin build-features --sim out/run.json --measured logs/sample/ --output data/ml/features.parquet`.
- Modele ML sa **opcjonalne** (`pip install pur-mold-twin[ml]`), brak scikit-learn skutkuje czytelnym komunikatem.
- Output modeli: `models/defect_risk.pkl`, `models/defect_classifier.pkl` (gdy beda trenowane).
- Raport w `reports/ml/README.md` (accuracy, data drift) po zbudowaniu datasetu.

## 6. Polityka bledow ML

- Kazda komenda/API, ktora probuje wlaczyc ML, dokleja do payloadu pole `ml_status` z kodem (`code`) i opcjonalnym opisem (`detail`).
- Obecne kody:
  - `ok` – predykcje dolaczone poprawnie.
  - `missing-ml-extras` – brakuje optionalnych zaleznosci (`pip install .[ml]`).
  - `missing-ml-models` – brak artefaktow `models/*.pkl`; uruchom `train-ml` albo podmien katalog.
  - `invalid-ml-input` – plik cech jest pusty/uszkodzony albo CLI/API otrzymalo bledne pola.
  - `ml-error` – inne awarie (szczegoly w `detail`).
- CLI `run-sim --with-ml`, `service_example.py` oraz `APIService.ml_predict` zawsze zwracaja `ml_status` – jezeli predykcje sa niedostepne, status informuje dlaczego.
- Skrypt treningowy `pur_mold_twin.ml.train_baseline` podnosi kontrolowane wyjatki (`MLDependencyError`, `MLInputError`), a w trybie `python -m ...` wypisuje przyjazny komunikat na stderr.

### 6.1 Tester scenariuszy ML

- Komenda referencyjna: `python scripts/ml_status_tester.py --case ok`.
- Dostepne przypadki: `ok`, `missing-models`, `missing-extras`.
- `ok` generuje mini dataset, trenuje baseline i wywoluje `attach_ml_predictions` (wymaga extras `[ml]`).
- `missing-models` odpala attach na pustym katalogu `models/` (spodziewany kod `missing-ml-models`).
- `missing-extras` tymczasowo symuluje brak `joblib` i pokazuje kod `missing-ml-extras`.
- Tester wypisuje jeden JSON z polem `result.ml_status.code`; w testach jednostkowych (`tests/test_ml_status_tester.py`) kazdy scenariusz jest uruchamiany w subprocessie.

### 6.2 Release gating (TODO4)

- `todo4.md` traktujemy jako checklist dla releasu 1.0.0: dokumentacja (`readme.md`, `docs/ML_LOGGING.md`) musi opisac polityke ML, a tester z §6.1 jest obowiazkowym krokiem smoke.
- Przed tagiem `v1.0.0` uruchom: `pytest -q`, `scripts/smoke_e2e.py`, `python scripts/ml_status_tester.py --case ok`, `--case missing-models`, `--case missing-extras`. Kazdy wynik musi zwrocic odpowiedni `ml_status.code`.
- CI `.github/workflows/ci.yml` posiada job `lint` (ruff/black/markdownlint) i macierz testowa Pythona 3.10–3.14; release jest dopuszczany dopiero, gdy lint/test przejda oraz `README_VERS.md` zawiera wpis przygotowujacy release.
- Raport z tego kroku zapisujemy w `README_VERS.md` (sekcja 1.0.0) oraz w `todo4.md` wiersz 4.1 (dokumentacja) / 4.2 (tester ML).

## 7. TODO (dla Paczki §12)

- [x] Utworzyc katalog `data/ml/` (gitignored) na logi/feature store.
- [x] Dodac CLI/ETL build-features (`pur-mold-twin build-features`, helper w `tests/helpers/`).
- [ ] Zaimplementowac baseline w `notebooks/ml_baseline.ipynb`.
- [ ] Dokumentowac iteracje w `admin/ML_changelog.md` (po utworzeniu danych).
