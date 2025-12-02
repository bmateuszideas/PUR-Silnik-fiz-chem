# CALIBRATION & VALIDATION - PUR-MOLD-TWIN (Paczka d)

Instrukcja realizacji TODO1 §11: format danych pomiarowych, procedury kalibracyjne i walidacyjne. Wszystko w UTF-8, liczby w SI (wyjątek: temperatury wejsciowe w °C jeśli tak zapisano w logach).

## 1. Format danych pomiarowych

| Plik | Opis | Kluczowe pola |
| --- | --- | --- |
| `measurements/meta.yaml` | Metadane strzału/serii | `system_id`, `shot_id`, `operator`, `m_polyol`, `m_iso`, `T_polyol_in_C`, `T_iso_in_C`, `T_mold_init_C`, `RH_ambient_pct`, `vent_status`, `notes` |
| `measurements/core_temp.csv` | Profil temperatury rdzenia | `time_s`, `T_core_C` (>= 1 Hz) |
| `measurements/mold_temp.csv` | Profil temperatury formy | `time_s`, `T_mold_C` (opcjonalnie `zone_id`) |
| `measurements/pressure.csv` | Profil cisnienia w wnece | `time_s`, `p_total_bar` (opcjonalnie `p_air_bar`, `p_CO2_bar`, `p_pentane_bar`) |
| `measurements/density_mech.yaml` | Wyniki gestosci/twardosci | `rho_moulded`, `rho_free_rise`, `H_demold`, `H_24h`, `demold_time_s`, `defects` (lista) |

Minimalny dataset = `meta.yaml` + `core_temp.csv` + `density_mech.yaml`. Reszta opcjonalnie poprawia kalibracje.

## 2. Procedura kalibracyjna

1. **Kroki wstępne**
   - Znormalizuj wejścia (temperatury -> °C, RH -> %). Dopasuj `ProcessConditions` do logów.
   - Zasymuluj strzał referencyjny (`MVP0DSimulator`) bez zmian parametrów, zapisz błąd `T_core` i `t_demold`.
2. **Korekta kinetyki**
   - Dopasuj `SimulationConfig.reaction_order`, `activation_energy`, `reference_temperature_K` tak, by `alpha(t)` odwzorowywało czasy cream/gel/rise z logu (`np.linalg.lstsq` na parach `time -> alpha_target`).
   - Error metric: `mean(|t_measured - t_pred|) <= 10 s`.
3. **Bilans cieplny**
   - Ustaw `foam_cp_J_per_kgK`, `reaction_enthalpy_J_per_kg`, `h_core_to_mold`, `h_mold_to_ambient` używając krzywych `T_core` i `T_mold` (funkcja kosztu: RMS błędu temperatury).
4. **Ekspansja / gazy**
   - Porównaj `rho_moulded`, `p_total` vs pomiary. Reguluj `surface_moisture_capacity`, `vent_relief_scale`, parametry parowania pentanu (onset, base_rate).
5. **Hardness mapping**
   - Dopasuj `hardness_base_shore`, `hardness_alpha_gain`, `hardness_density_gain`, `hardness_24h_bonus` tak, aby `H_demold` i `H_24h` trafiały w logi (np. solve 2 eq).
6. **Iteracja**
   - Powtarzaj 2-5 aż błędy mieszczą się w celach. Dokumentuj każdy krok w `admin/calibration_log.md` (dowolny format, min. data + opis).
7. **Automatyzacja (skrypty)**
   - `scripts/calibrate_kinetics.py`: dopasowuje parametry kinetyki do czasów cream/gel/rise (`least_squares`).
   - `scripts/compare_shot.py`: porównuje log CSV i wynik symulacji (RMSE T_core, Δp_max, Δt_demold).
   - `scripts/calibration_report.py`: PASS/FAIL względem tolerancji (domyślnie: RMSE T_core ≤5 K, Δp_max ≤0.75 bar, Δt_demold ≤60 s; parametry można dostosować w kodzie).
   - `scripts/plot_kinetics.py`: zapisuje wykres `alpha(t)` z zaznaczonymi punktami TDS (cream/gel/rise) do pliku PNG.

## 3. Walidacja MVP

| Metryka | Cel | Notatki |
| --- | --- | --- |
| `t_demold_opt` | ±60 s | weryfikuj vs faktyczny demold |
| `rho_moulded` | ±10 % | porównanie ze scale-shot |
| `p_max` | ±15 % | wymagany log cisnienia |
| `H_demold`, `H_24h` | ±5 Shore | po kalibracji twardosci |
| `defect_risk` | zgodność trendu | brak ground-truth -> min. potwierdzenie opisowe |

Procedura:
1. Wybierz co najmniej 3 strzały (zimny, nominalny, ekstremalny). Dla każdego:
   - Uruchom symulacje z danymi z `meta`.
   - Zapisz `metrics.yaml` z błędami (pole `validation/<shot_id>.yaml`).
2. Jeśli jakikolwiek błąd > celu, wróć do kalibracji (pkt 2). W `TODO1_PKT11_changelog` dopisz wnioski.
3. Po spełnieniu celów zaznacz w `todo1.md` paragraf 11 jako wykonany i zarchiwizuj zbiory danych w `data/calibration/<shot_id>/`.

## 4. Workflow CLI / Notebook

1. Przygotuj pliki pomiarowe zgodnie z sekcją 1.
2. Stwórz notebook `notebooks/calibration.ipynb` (opcjonalnie) i użyj poniższego szkicu:
   ```python
   from pathlib import Path
   import pandas as pd
   from pur_mold_twin import MVP0DSimulator, ProcessConditions, MoldProperties, QualityTargets, SimulationConfig

   meta = ...  # wczytaj YAML
   process = ProcessConditions(**meta["process"])
   mold = MoldProperties(**meta["mold"])
   sim_cfg = SimulationConfig()
   simulator = MVP0DSimulator(sim_cfg)
   result = simulator.run(system, process, mold, QualityTargets())

   # Oblicz błędy
   df_temp = pd.read_csv("measurements/core_temp.csv")
   err = (df_temp["T_core_C"] - (result.T_core_K - 273.15))**2
   print("RMSE core temp:", err.mean() ** 0.5)
   ```
3. Aktualizuj parametry, aż osiągniesz cele walidacyjne z pkt 3.

## 5. Linki / referencje

- Ten dokument: `docs/CALIBRATION.md`.
- Changelog Paczki (d): `admin/TODO1_PKT11_changelog.md`.
- Wpisy walidacyjne: `data/calibration/` (dodać gdy dostępne dane).
