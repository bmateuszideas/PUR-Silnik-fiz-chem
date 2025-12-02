# Use cases - PUR-MOLD-TWIN

Scenariusze uzycia zgodne z README/standards. Profile: `p_total(t)`, `p_air`, `p_CO2`, `p_pentane`, `alpha(t)`, `rho(t)`, `T_core/T_mold`, `vent_eff(t)`. Wskazniki jakosci: `alpha_demold`, `H_demold`, `H_24h`, `rho_moulded`, statusy `quality_status`, `pressure_status`, `defect_risk`.

---

## Use case 1 - podstawowa symulacja (Core Engine)

### Cel
- Przyjac dane materialowe i procesowe.
- Policzyc profil procesu: `alpha(t)`, `T(t)`, `rho(t)`, `p_total(t)`, `vent_eff(t)`.
- Wyznaczyc `t_demold_min/max/opt` i statusy jakosci/bezpieczenstwa/ryzyka.

### Wejscie
**Material (SYSTEM_R1, bez pentanu)**
- Poliol: `OH_number=250 mgKOH/g`, `water_pct=1.5%`, `pentane_pct=0%`, `rho_free_rise_target=30 kg/m3`, `rho_moulded_target=40 kg/m3`, `cream_time_ref=15 s`, `gel_time_ref=60 s`, `rise_time_ref=110 s`.
- Izocyjanian: `%NCO=31%`.
- Mechaniczne: `H_24h_target=55 Shore`.

**Proces (referencyjny)**
- `T_polyol_in_C=25`, `T_iso_in_C=25`, `T_mold_init_C=40`, `T_ambient_C=22`.
- `RH_ambient=50%`.
- Receptura: `m_polyol=1.0 kg`, `m_iso=1.05 kg`, `NCO_OH_index=1.05`.
- Forma: `V_cavity=25 l`, standard alu.
- Odpowietrzniki: 3 czyste, drozne.
- `mixing_eff=0.9`.

**Wymagania**
- `alpha_demold_min=0.75`, `H_demold_min=40 Shore`, `H_24h_min=50 Shore`.
- `rho_moulded` w `[38,45] kg/m3`.
- `p_max_allowable_bar=5.0`, `t_cycle_max=600 s`, `defect_risk_max=0.10`.

### Wynik (przyklad)
- Czasy: `t_cream ~ 15 s`, `t_gel ~ 60 s`, `t_rise ~ 110 s`.
- `T_core_max ~ 85 C`.
- `p_max ~ 3.5 bar @ 120 s`, `pressure_status=SAFE`, rozbicie: `p_air ~ 1.0`, `p_CO2 ~ 1.6`, `p_pentane ~ 0.9` bar.
- Dla `t_demold=320 s`: `alpha_demold ~ 0.82`, `H_demold ~ 43 Shore`, `H_24h ~ 56 Shore`, `rho_moulded ~ 41 kg/m3`, `quality_status=OK`, `defect_risk ~ 0.03`.
- Wilgotnosc: `water_from_polyol ~ 0.015 kg`, `water_from_RH_surface ~ 0.001 kg`, `water_eff ~ 0.016 kg`, `water_risk_score ~ 0.05` (SAFE).
- Odpowietrzniki: `vent_eff` startuje z 1.0 i maleje do ~0.35 przy `t ~ 260 s`, `vent_closure_time ~ 265 s` (przy prostym clog-rate).
- Diagnostyka: brak ostrzezen (mixing 0.9, cisnienie SAFE, vent zamyka sie po 260 s).
- Okno demold: `t_demold_min ~ 280 s`, `t_demold_max ~ 420 s`, rekomendacja `t_demold_opt ~ 320 s`.

### Skrot
- Profile: `alpha(t)`, `T_core(t)`, `T_mold(t)`, `rho(t)`, `p_total(t)`, `vent_eff(t)`.
- Kluczowe metryki: `p_max ~ 3.5 bar` (SAFE), `t_demold_opt ~ 320 s`, `alpha_demold ~ 0.82`, `H_demold ~ 43 Shore`, `H_24h ~ 55 Shore`, `rho_moulded ~ 41 kg/m3`, `defect_risk ~ 3%`.
- Dokladnosc po kalibracji (opisowo): `t_demold_opt` +/-60 s, `rho_moulded` +/-10%, `p_max` +/-15%.

- **Konfiguracje YAML**: scenariusz/test dla tego use-case jest dostępny jako `configs/scenarios/use_case_1.yaml`. CLI/ notebook moze go zaladowac:
  ```python
  from pur_mold_twin.configs import load_process_scenario
  from pur_mold_twin.material_db.loader import load_material_catalog

  scenario = load_process_scenario("configs/scenarios/use_case_1.yaml")
  systems = load_material_catalog("configs/systems/jr_purtec_catalog.yaml")
  system = systems[scenario.system_id]
  result = MVP0DSimulator(scenario.simulation).run(system, scenario.process, scenario.mold, scenario.quality)
  ```

### CLI (`run-sim`)
- Parametry:  
  - `--scenario/-s` – ścieżka do pliku YAML z procesem/moldem/symulacją,  
  - `--system/-y` – opcjonalne ID systemu z katalogu (nadpisuje `scenario.system_id`),  
  - `--quality/-q` – opcjonalny preset `QualityTargets` (`configs/quality/*.yaml`),  
  - `--systems/-c` – katalog lub multi-doc YAML z Material DB,  
  - `--output` – format wyjścia na stdout: `json` (domyślnie) lub `table` (skondensowane KPI),  
  - `--save-json` – opcjonalna ścieżka zapisu pełnego wyniku JSON niezależnie od formatu stdout,  
  - `--export-csv` – opcjonalny plik CSV z profilami czasowymi (`time_s`, `alpha`, `T_core`, `p_total`, …),  
  - `--backend` – wymuszenie backendu solvera (`manual` / `solve_ivp`),  
  - `--verbose` – przełącza logowanie na poziom DEBUG.
- Przykład:
  ```bash
  pur-mold-twin run-sim \
      --scenario configs/scenarios/use_case_1.yaml \
      --system SYSTEM_R1 \
      --quality configs/quality/default.yaml \
      --output table \
      --export-csv out/use_case_1_profiles.csv \
      --save-json out/use_case_1.json
  ```

---

## Use case 2 - problematyczne ustawienia + Process Optimizer

### Cel
- Core Engine ocenia suboptymalne nastawy (niskie temperatury, wysoka RH, pentan, oslabione odpowietrzniki).
- Process Optimizer szuka lepszych parametrow przy constraints na `p_max`, `alpha/H/rho`, `t_cycle_max`, `defect_risk_max`.

### Wejscie
**Material (SYSTEM_M1, z pentanem)**
- Poliol: `OH_number=250 mgKOH/g`, `water_pct=2.0%`, `pentane_pct=10%`, `rho_free_rise_target=30 kg/m3`, `rho_moulded_target=40 kg/m3`, `cream_time_ref=18 s`, `gel_time_ref=70 s`, `rise_time_ref=130 s`.
- Izocyjanian: `%NCO=31%`.
- Mechaniczne: `H_24h_target=55 Shore`.

**Proces - suboptymalny**
- `T_polyol_in_C=20`, `T_iso_in_C=20`, `T_mold_init_C=35`, `T_ambient_C=18`.
- `RH_ambient=75%`.
- Receptura: `m_polyol=1.0 kg`, `m_iso=1.10 kg`, `NCO_OH_index=1.05`.
- Forma: `V_cavity=25 l`.
- Odpowietrzniki: 3 kanaly czesciowo zabrudzone.
- `mixing_eff=0.7`.

**Wymagania**
- `alpha_demold_min=0.75`, `H_demold_min=40 Shore`, `H_24h_min=50 Shore`.
- `rho_moulded` w `[38,45] kg/m3`.
- `p_max_allowable_bar=5.0`, `t_cycle_max=600 s`, `defect_risk_max=0.10`.

### Krok 1 - ocena aktualnych nastaw
- Czasy: `t_cream ~ 22 s`, `t_gel ~ 80 s`, `t_rise ~ 140 s`.
- `T_core_max ~ 75 C` (za nisko).
- `p_max ~ 5.8 bar @ 130 s` -> `pressure_status=OVER_LIMIT`.
  - Rozbicie: `p_air ~ 0.9`, `p_CO2 ~ 2.6`, `p_pentane ~ 2.3` bar.
- `vent_eff` spada do ~0.1 przy `t ~ 50-60 s` (przytkane venty).
- Dla `t_demold ~ 300 s`: `alpha_demold ~ 0.68`, `H_demold ~ 35 Shore`, `H_24h ~ 52 Shore`, `rho_moulded ~ 36 kg/m3`, `quality_status=FAIL`, `defect_risk ~ 0.60`.
- Diagnoza: zimne komponenty/forma -> wolna kinetyka; wysoka RH -> wiecej `water_eff` -> nadmiar CO2; pentane 10% przy tych warunkach -> wysokie cisnienie; venty zamulaja sie wczesnie.
- Wilgotnosc: `water_from_polyol ~ 0.020 kg`, `water_from_RH_surface ~ 0.003 kg`, `water_eff ~ 0.023 kg`, `water_risk_score ~ 0.70` (HIGH).
- Odpowietrzniki: `vent_closure_time ~ 58 s`, `vent_eff` < 0.05 -> brak ulatniania, przyczynia sie do wysokiego `p_pentane`.
- Diagnostyka: ostrzezenia dla niskiej twardosci demold, wysokiego cisnienia i wczesnego zamkniecia ventow -> `quality_status=FAIL`, `defect_risk ~ 0.60`.

### Krok 2 - definiowanie optymalizacji
- Zmienne decyzyjne: `T_polyol_in` [20,30] C; `T_iso_in` [20,30] C; `T_mold_init` [35,50] C; `t_demold` [240,600] s; opcjonalnie `pentane_pct` [8,10] %.
- Constraints: `p_max <= 5.0 bar`, `alpha_demold >= 0.75`, `H_demold >= 40`, `H_24h >= 50`, `rho_moulded` w `[38,45]`, `t_demold <= 600 s`, `defect_risk <= 0.10`.
- Cel: minimalizacja `t_demold`; drugorzedne cele: minimalizacja `p_max` oraz wrazliwosci na RH.

### Krok 3 - wynik optymalizacji
- Nowe nastawy: `T_polyol_in=26 C`, `T_iso_in=26 C`, `T_mold_init=42 C`, `t_demold=360 s`, redukcja `pentane_pct` z 10% do 9%.
- Wynik: `p_max ~ 4.3 bar` (`pressure_status=SAFE`); `alpha_demold ~ 0.80`; `H_demold ~ 44 Shore`; `H_24h ~ 56 Shore`; `rho_moulded ~ 41 kg/m3`; `defect_risk ~ 0.05`; `quality_status=OK`.

Przyklad kodu:
```python
from pur_mold_twin import ProcessOptimizer, OptimizerBounds, OptimizationConfig

optimizer = ProcessOptimizer()
config = OptimizationConfig(samples=60, bounds=OptimizerBounds(T_polyol_C=(20, 30)))
result = optimizer.optimize(system, process, mold, quality, config)
best = result.best_candidate
print("Nowe nastawy:", best.T_polyol_in_C, best.T_iso_in_C, best.T_mold_init_C, best.t_demold_s)
```

### Skrot
- Przed optymalizacja: `p_max ~ 5.8 bar` (OVER_LIMIT), `alpha_demold ~ 0.68`, `H_demold ~ 35`, `rho_moulded ~ 36`, `defect_risk ~ 0.60`.
- Po optymalizacji: `p_max ~ 4.3 bar` (SAFE), `alpha_demold ~ 0.80`, `H_demold ~ 44`, `rho_moulded ~ 41`, `defect_risk ~ 0.05`, `t_demold ~ 360 s`.
- `water_risk_score` spada z ok. 0.70 do ~0.20 po podniesieniu temperatur i redukcji pentanu, co ogranicza nadmiar CO2 i stabilizuje gestosc.
- `vent_eff` utrzymuje sie powyzej 0.25 do ~280 s, `vent_closure_time ~ 300 s`, co daje wieksze okno demold przy nizszym cisnieniu.
- Diagnostyka: tylko ostrzezenie informacyjne (cisnienie blisko SAFE); `quality_status=OK`, `defect_risk ~ 0.05`.
- Dokladnosc po kalibracji (opisowo): `p_max` +/-15%, `t_demold_opt` +/-60 s, `rho/H` w tolerancjach po danych z hali.
- **Quality preset**: CLI/optimizer może korzystać z gotowych presetów `QualityTargets` (`configs/quality/default.yaml`) za pomocą `pur_mold_twin.configs.load_quality_preset`.

### CLI (`optimize`)
- Flagi: `--scenario/-s`, `--systems/-c`, `--quality`, `--samples/-n`, `--seed`, `--t-cycle-max`, `--prefer-lower-pressure`, `--output {json|table}`, `--save-json`, `--export-csv`, `--verbose`.
- Przykład:
  ```bash
  pur-mold-twin optimize \
      --scenario configs/scenarios/use_case_1.yaml \
      --quality configs/quality/default.yaml \
      --samples 40 \
      --t-cycle-max 600
  ```

---

## Generowanie raportu z symulacji/optimizacji
- CLI `run-sim` moze zapisac raport Markdown z KPI i wykresami (`--report reports/use_case_1.md`); pliki PNG trafiaja do katalogu raportu.
- Wymagane: `matplotlib` (patrz `py_lib.md`). Przy braku biblioteki CLI wypisze komunikat.
- Przyklad:
  ```bash
  pur-mold-twin run-sim \
      --scenario configs/scenarios/use_case_1.yaml \
      --system SYSTEM_R1 \
      --quality configs/quality/default.yaml \
      --output table \
      --report reports/use_case_1.md
  ```
