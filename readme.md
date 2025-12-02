# PUR-MOLD-TWIN

Predykcyjny silnik / digital twin zamknietej formy pianki PUR. Wirtualny technolog: bierze dane z TDS/SDS, receptury, warunki hali oraz parametry formy, nastepnie symuluje przebieg w zamknietej wnetrzu i zwraca profile procesu, okno demold, ocene jakosci, cisnienie oraz diagnozy/ryzyka.

> **Uwaga dla agentow i Copilota:** przed jakakolwiek praca w repo przeczytaj `agent_instructions.md` oraz `copilot_update_project_playbook.md`. Dokumenty opisujace kolejnosc czytania plikow, wymagania srodowiskowe (Python 3.14) i referencje do `py_lib.md`. AI zaczyna prace dopiero po zapoznaniu sie z tymi plikami.

## 1. Problem
- Co dzieje sie w srodku formy przy zadanych nastawach?
- Czy mozna skrocic czas w formie bez utraty jakosci?
- Jakie sa przyczyny wad (pecherze, flash, zmiana gestosci) wynikajace z wody/RH, pentanu, temperatury formy, mieszania, odpowietrznikow?

## 2. Zakres modelu (pojedyncza zamknieta wneka)
System PUR sklada sie z komponentu poliolowego (opcjonalnie z pentanem), komponentu izocyjanianowego, wody jako reagenta i zrodla CO2, pentanu jako fizycznego blowing agentu oraz aluminiowej formy z odpowietrznikami.

### 2.1 Moduly fizyko-chemiczne
1. Stechiometria i gaz:
   - Index NCO/OH wyznaczany z danych TDS.
   - CO2 z reakcji NCO + H2O.
   - Pentan dostepny jako gaz `n_pentane_total`.
   - Efektywna woda `water_eff = water_from_polyol + water_from_RH_surface`.
2. Kinetyka i cieplo:
   - Stopien utwardzenia `alpha(t)` (0-1).
   - Egzoterm reakcji.
   - Wymiana ciepla: pianka -> forma -> otoczenie.
   - Wplyw temperatury na tempo reakcji (Arrhenius/empiryczny) oraz na odparowanie pentanu.
3. Ekspansja i gestosc:
   - Wzrost objetosci przez CO2 i pentan.
   - `rho_free_rise` vs `rho_moulded`; wplyw temperatury, cisnienia i zamykania odpowietrzen.
4. Cisnienie i odpowietrzniki:
   - `p(t) = p_air + p_CO2 + p_pentane`; suma powietrza startowego, gazu reakcyjnego i pentanu.
   - Odpowietrzniki drozne na starcie, wraz z ruchem frontu i utwardzaniem zamulane; `vent_eff(t)` maleje od 1 do 0.
   - Wyniki: profil `p(t)`, rozbicie skladowych, `p_max` oraz moment zamkniecia odpowietrzen (`vent_eff -> 0`).
5. Wlasciwosci mechaniczne / twardosc:
   - Funkcja `H = f(alpha, rho)`.
   - Rozroznienie stanu demold (`H_demold`, `alpha_demold`) i stanu docelowego (`H_24h`, `alpha_24h`).

## 3. Dane wejsciowe
### 3.1 Material DB (TDS/SDS)
- Poliol/system: `OH_number`, `functionality_polyol`, `density_polyol`, `viscosity_polyol`, `water_pct`, `pentane_pct`, czasy referencyjne `cream/gel/rise/tack_free`, cele `rho_free_rise_target`, `rho_moulded_target`, parametry mechaniczne (np. `H_24h_target`).
- Izocyjanian: `%NCO`, `functionality_iso`, `density_iso`, `viscosity_iso`.
- Gaz i lotne (CO2/pentan): cisnienie pary vs T, cieplo parowania, wlasnosci fizyczne z literatury.
- Material DB zapisujemy jako `configs/systems/*.yaml`. Schemat opisany jest w `docs/MODEL_OVERVIEW.md` i odwzorowany w `src/pur_mold_twin/material_db/models.py`. Dostepne pliki: katalog JR Purtec-style (`jr_purtec_catalog.yaml` zawiera R1/M1 + systemy `elastoflex_*`, `dekolast_*`, `fasipol_*`).

### 3.2 Proces (cykl formy)
- Masy: `m_polyol`, `m_iso`, `m_additives`; ustawiony `NCO_OH_index`.
- Temperatury: `T_polyol_in`, `T_iso_in`, `T_mold_init`, `T_ambient`.
- Wilgotnosc: `RH_ambient` (0-1 lub % na wejsciu) -> `water_from_RH`.
- Mieszanie: czas/obroty/prad -> proxy `mixing_eff` (0-1) dla jednorodnosci.
- Geometria formy: `V_cavity`, `A_mold`, grubosc scian i parametry termiczne.
- Odpowietrzniki: liczba, polozenie, wymiary, przepustowosc startowa, charakterystyka `vent_eff(t)`.

### 3.3 Wymagania jakosci/ograniczenia
- Progi demold: `alpha_demold_min`, `H_demold_min`; progi docelowe: `H_24h_min/target`.
- Zakres gestosci/wymiarow: `[rho_min, rho_max]`.
- Bezpieczenstwo: `p_max_allowable_bar`.
- Czas: `t_cycle_max`.
- Ryzyko: `defect_risk_max`.

## 4. Dane wyjsciowe
- Profile: `alpha(t)`, `T_core(t)`, `T_mold(t)`, `rho(t)`/ekspansja, `p(t)` z rozbiciem `p_air/p_CO2/p_pentane`, `vent_eff(t)`.
- Okno demold: `t_demold_min`, `t_demold_max`, `t_demold_opt`.
- Jakosc: `H_demold`, `H_24h`, `rho_moulded` vs cele; status `quality_status` (OK/MARGINAL/FAIL) oraz `defect_risk`.
- Cisnienie: `p_max`, czas wystapienia, udzial CO2 vs pentan, flagi `pressure_safe/near_limit/over_limit`.
- Odpowietrzniki: `vent_eff(t)`, moment zamkniecia (`vent_closure_time`) i wplyw na odgazowanie pentanu/CO2.
- Wilgotnosc/woda: `water_from_polyol`, `water_from_RH_surface`, `water_eff` oraz heurystyczny `water_risk_score` pokazujacy ryzyko nadmiaru gazu z powodu RH.
- Ryzyko i diagnozy: `diagnostics` (ostrzezenia dot. zimnych komponentow, RH -> water_eff, niska `mixing_eff`, wczesne zamkniecie ventow, demold za wczesnie/pozno).

## 5. Kryteria jakosci i ryzyka
- Demold bezpieczny gdy `alpha >= alpha_min`, `H >= H_min`, `p <= p_limit`, `rho` w zakresie; rekomendacja dodaje margines bezpieczenstwa.
- Defect risk: metryka do ustalenia (np. Monte Carlo na rozrzutach parametrow lub heurystyki QC); cel `<=5-10%`.
- Dokladnosc docelowa (uzgodnic): `p_max +/-10-15%`, `t_demold_opt +/-1 min`, `rho +/-5-10%`.

## 6. Wymiar modelu: 0D vs 1D
- MVP: model 0D/quasi-0D (srednie wartosci w objetosci; opcjonalnie 1D kolumnowy). Szybkie obliczenia oraz poprawne trendy `T(t)`, `p(t)`, `alpha(t)`, okna demold, gestosc/twardosc.
- Docelowo: 1D w grubosci dla gradientow temperatury/alpha/rho i lepszego odwzorowania odpowietrzen/frontu.
- Gaz idealny; bilans energii z cieplem reakcji; kinetyka n-tego rzedu/autokatalityczna z Arrheniusem; parowanie pentanu (rownowaga + tempo przyblizone); odpowietrznik jako zawor o malejacej przepustowosci.

## 7. Kalibracja i dane potrzebne
- Pomiary: `T_core(t)`, `T_surface(t)`, `p(t)` (jesli dostepne), czasy cream/gel/rise/tack-free, `rho_moulded` vs free-rise, `H_demold`, `H_24h`, opis defektow.
- Parametry do fittowania: kinetyka (A, Ea / empiryczne), parametry cieplne (`lambda`, `cp`, `rho` vs `alpha`), model parowania pentanu, krzywa `vent_eff(t)` vs front/cisnienie, mapowanie `alpha + rho -> H`.
- Material DB: uzupelnic co najmniej jeden system jako pierwszy case kalibracyjny.
- Szczegolowy workflow kalibracji/walidacji: patrz `docs/CALIBRATION.md` (Paczka d).

## 8. Roadmap i kryteria MVP
- Faza 0: definicja modelu (fizyka, I/O, wybor bibliotek).
- Faza 1: MVP 0D (`alpha(t)`, `T(t)`, `rho(t)`; CO2 jako gaz; bazowa rekomendacja demold). Kryteria: blad `t_demold_opt +/-1 min`, `rho_moulded +/-10%`, czasy cream/gel/rise zgodne z TDS +/-20%.
- Faza 2: cisnienie i odpowietrzniki (pentan, parowanie vs T/p, `vent_eff(t)`, pelne `p(t)/p_max`). Kryteria: `p_max +/-10-15%` vs pomiary; poprawny trend procentu pentanu i stanu odpowietrzen.
- Faza 3: jakosc i demold (mapowanie `alpha + rho -> H`, okno demold wg progow).
- Faza 4: diagnostyka bledow (reguly inzynierskie).
- Faza 5: dane z hali i ML (logowanie danych, porownanie z symulacja, model ML do predykcji defektow/diagnoz).

## 9. Notatki techniczne
- Jezyk: Python (>=3.10, docelowo 3.14).
- Biblioteki: patrz `py_lib.md` (lekki stack startowy + dodatki po MVP).
- Kodowanie plikow: UTF-8 (bez znakow dziwnych).
- Repo: struktura i katalogi opisane w `docs/STRUCTURE.md`; kod `src/pur_mold_twin/`, testy `tests/`, dokumentacja `README.md`, `TODO.md`, `docs/...` wg standardow.
- Audyt pracy AI: katalog `admin/` zawiera pliki `TODO1_PKT{n}_changelog.md`. Po kazdej zmianie w danym punkcie TODO1 dopisz datowany wpis z lista plikow i krotkim celem; jezeli nie mozesz czegos wykonac, wpisz problem i zaznacz go w `todo1.md` (linia `> Problem: ...`).
- CLI: `src/pur_mold_twin/cli/main.py` + `cli/commands.py` (Typer) dostarcza komendy `run-sim`/`optimize` oraz `build-features` z flagami `--output`, `--save-json`, `--export-csv`, `--verbose`.
- Testy: `tests/test_core_simulation.py`, `tests/test_optimizer.py`, `tests/test_cli.py` (scenariusz `use_case_1`), kolejne przypadki dojda w fazie produktowej.

## 10. Status
- Etap: MVP 0D (`mvp0d.py`) z woda/pentanem, oknem demold oraz optymalizatorem losowym; CLI Typer (run-sim/optimize) z eksportami JSON/CSV i `--verbose`. Testy CLI/optimizer bazuja na `configs/scenarios/use_case_1.yaml`.
- Next (TODO2 §6-§10):
  - kalibracja/walidacja wg `docs/CALIBRATION.md` i przygotowanie datasetów (`docs/CALIBRATION.md`, `docs/USE_CASES.md`),
  - moduły ETL/ML oraz raporty (`docs/ML_LOGGING.md`, `docs/USE_CASES.md`),
  - packaging/CI i dalsze standardy (przeniesienie postępów do README_VERS / standards).

## 11. Core Engine MVP 0D (implementacja robocza)
- Lokalizacja kodu: `src/pur_mold_twin/core/mvp0d.py` + eksporty w `src/pur_mold_twin/__init__.py`.
- Zgloszenia wejsciowe: `MaterialSystem` z Material DB, `ProcessConditions`, `MoldProperties` (z opcjonalnym `VentProperties`), `QualityTargets`, `SimulationConfig`.
- Zakres funkcjonalny:
  1. Kinetyka `alpha(t)` kalibrowana do czasów cream/gel/rise/tack-free zapisanych w TDS.
  2. Sprzezony bilans ciepla pomiedzy rdzeniem pianki a forma (w tym `mixing_eff` jako korektor tempa reakcji).
  3. Ekspansja CO2 z efektywnej wody `water_eff = water_from_polyol + water_from_RH_surface` oraz odparowanie pentanu -> `rho(t)`, fill ratio i ilosc gazu w wnece (RH/pentan > prog -> wiecej gazu).
  4. Okno demold `t_demold_min/max/opt` wyznaczane z progów `alpha`, `rho`, `T_core` i `H_demold`.
  5. Powietrze startowe + modele cisnienia: `p_air/p_CO2/p_pentane`, `vent_eff(t)` (logistyczne zamykanie odpowietrzen), `p_total`, `p_max`, flagi `pressure_status` oraz `vent_closure_time`.
  6. Jakosc + diagnoza: `hardness(t)`, `H_demold`, `H_24h`, `quality_status`, `diagnostics`, `defect_risk` (bazujace na RH, mixing, vent, cisnienie).
- Wyniki: `SimulationResult` zawiera profile (`alpha`, `T_core`, `T_mold`, `rho`, `fill_ratio`, `n_CO2`, `p_air`, `p_CO2`, `p_pentane`, `p_total`, `vent_eff`, `hardness`) oraz zagregowane metryki (`rho_moulded`, `t_demold_*`, `p_max`, `pressure_status`, `vent_closure_time`, `H_demold`, `H_24h`, `quality_status`, `defect_risk`, `diagnostics`, `water_from_polyol`, `water_from_RH_surface`, `water_eff`, `water_risk_score`).
- Przyklad uzycia (pseudo):
  ```python
  from pathlib import Path
  from pur_mold_twin import (
      MVP0DSimulator,
      ProcessConditions,
      MoldProperties,
  )
  from pur_mold_twin.material_db.loader import load_material_system

  system = load_material_system(Path("configs/systems/system_R1.yaml"))
  process = ProcessConditions(m_polyol=1.0, m_iso=1.05, T_mold_init_C=40.0, mixing_eff=0.9)
  mold = MoldProperties(cavity_volume_m3=0.025, mold_surface_area_m2=0.8, mold_mass_kg=120.0)
  result = MVP0DSimulator().run(system, process, mold)
  ```
  Wynik mozna serializowac `result.to_dict()` lub wykreslic profile w CLI/notebooku.

## 12. Process Optimizer (paczka c)
- Lokalizacja kodu: `src/pur_mold_twin/optimizer/` (`search.py`, `constraints.py`, eksporty w `pur_mold_twin/__init__.py`).
- API:
  - `OptimizerBounds` - granice decyzyjne (temperatury komponentow, temperatura formy, docelowy `t_demold`).
  - `OptimizationConfig` - liczba probek, seed RNG, `t_cycle_max`, preferencje cisnienia.
  - `ProcessOptimizer` - random search oparty o `MVP0DSimulator`, zwraca `OptimizationResult` (najlepszy kandydat, raport ograniczen, historia prob).
  - `ConstraintReport` - lista naruszen (`p_max`, `vent`, `H_demold`, `defect_risk`, `t_cycle_max`).
- Przyklad:
  ```python
  from pur_mold_twin import (
      ProcessOptimizer,
      OptimizerBounds,
      OptimizationConfig,
      MVP0DSimulator,
  )

  optimizer = ProcessOptimizer(MVP0DSimulator())
  config = OptimizationConfig(samples=60, bounds=OptimizerBounds())
  opt_result = optimizer.optimize(system, process, mold, quality, config)
  print(opt_result.best_candidate, opt_result.best_constraints)
  ```

## 15. CLI/raporty/packaging
- CLI Typer (`pur-mold-twin`) dostarcza komendy `run-sim`, `optimize`, `build-features`; flaga `--report` zapisuje raport Markdown z wykresami (wymaga `matplotlib`).
- Instalacja lokalna: `pip install .` lub `pip install .[dev]` (testy) / `pip install .[ml]` (opcjonalne ML).
- Entry-point: `pur-mold-twin` (zdefiniowany w `pyproject.toml`).
- CI: `.github/workflows/ci.yml` uruchamia `pytest` (coverage >80% dla `core`); docelowy runtime Python 3.14, w Actions używany kompatybilny runner.

## 13. ML i logi procesu (TODO §12)
- Szczegoly planu ML/logowania: `docs/ML_LOGGING.md` (format logow, featury, modele i pipeline ETL).
- Surowe logi trafiaja do `data/ml/` (gitignore), ETL buduje `data/ml/features.parquet` laczac pomiary i wyniki symulacji.
- CLI `build-features`: `pur-mold-twin build-features --sim out/use_case_1.json --measured logs/sample/ --output data/ml/features.parquet` (przyjmuje katalog logow lub pojedynczy CSV).
- Modele startowe: `RandomForestRegressor` (`defect_risk`) i `RandomForestClassifier` (etykiety defektow); w przyszlosci komenda `pur-mold-twin ml-train` bedzie wykorzystywala te zasoby.
- ML jest opcjonalne; zaleznosci instaluje sie jako extras `pur-mold-twin[ml]`, a CLI komunikuje brak modulow ML.

## 14. CLI Quickstart (`pur-mold-twin`)
- Po instalacji pakietu (patrz `py_lib.md`) dostepna jest aplikacja Typer (`pur-mold-twin`) z komendami `run-sim` i `optimize`.
- `run-sim` (tabela KPI na stdout, JSON/CSV lokalnie):
  ```bash
  pur-mold-twin run-sim \
      --scenario configs/scenarios/use_case_1.yaml \
      --system SYSTEM_R1 \
      --quality configs/quality/default.yaml \
      --output table \
      --save-json out/use_case_1.json \
      --export-csv out/use_case_1_profiles.csv
  ```
  - Kluczowe flagi: `--scenario/-s`, `--system/-y`, `--quality/-q`, `--systems/-c`, `--output {json|table}`, `--save-json`, `--export-csv`, `--backend`, `--verbose`.
- `optimize` (random search na scenariuszu referencyjnym):
  ```bash
  pur-mold-twin optimize \
      --scenario configs/scenarios/use_case_1.yaml \
      --quality configs/quality/default.yaml \
      --samples 40 \
      --t-cycle-max 600
  ```
  - Flagi: `--samples/-n`, `--seed`, `--t-cycle-max`, `--prefer-lower-pressure`, `--systems`, `--quality`, `--output {json|table}`, `--save-json`, `--export-csv`, `--verbose`.
- Szczegoly dot. formatow wyjscia oraz przeplywu YAML -> Material DB -> core opisane sa w `docs/USE_CASES.md`.
