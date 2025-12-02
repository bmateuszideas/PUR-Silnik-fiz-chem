# TODO2 - PUR-MOLD-TWIN (faza implementacji i produktowienia / Productization & Quality)

Druga lista zadan po domknieciu TODO1. Skupia sie na modularizacji core, docelowym stacku (`numpy` / `scipy` / `pydantic` / `pint`), CLI, kalibracji, logach/ML i packagingu. Wszystko w UTF-8.

> Zasada: jeden bullet = jeden skonczony task w jednym cyklu pracy Copilota.  
> Notatka: po kazdej pracy nad konkretnym punktem TODO2 dopisz wpis do odpowiadajacego `admin/TODO2_PKT{n}_changelog.md` (data, pliki, krotki opis); gdy krok jest zablokowany, odnotuj problem w tym changelogu.

## 0. Obserwacje z analizy (2025-12-02)

- `tests/test_core_simulation.py` zawiera martwy kod (brak `FIXTURE_DIR`, niezaimportowane `load_material_system`, zla sygnatura `_build_mold`); uruchomienie `pytest` pada zanim dotrzemy do sensu testu. Trzeba poprawic fixture lub przerobic test na przypadek oparty o `load_material_catalog`.
- CLI pozostaje placeholderem (`src/pur_mold_twin/cli/main.py` tylko drukuje komunikat), mimo ze README/TODO opisuje komendy `run-sim`/`optimize`; sekcja 4 ponizej powinna ten brak pokryc.
- Loader Material DB wciaz korzysta z recznego parsera YAML; zanim wprowadzimy `ruamel.yaml` + walidacje Pydantic (TODO2 §2-3) musimy liczyc sie z kruchem formatem i brakiem jasnych bledow.
- W katalogu systemow (`configs/systems/jr_purtec_catalog.yaml`) wiele pol ma `null`, brak tez walidacji jednostek (`pint`/Pydantic). Dopoki nie zrealizujemy §2, kazdy nowy system moze niespodziewanie przerwac solver.

## 1. Core 0D i modularizacja

- [x] Zweryfikowac aktualny sposob integracji ODE w `mvp0d.py` (petla vs. integrator). -> `src/pur_mold_twin/core/mvp0d.py`
- [x] Zaprojektowac interfejs ODE pod `scipy.integrate.solve_ivp` (stan = alpha, T_core, T_mold, n_CO2, n_pentane, itp.). -> `src/pur_mold_twin/core/mvp0d.py`, `py_lib.md`
- [x] Zaimplementowac wariant solvera oparty o `solve_ivp` z tym samym I/O co obecny MVP (flagi do wyboru backendu: reczny vs. `scipy`). -> `src/pur_mold_twin/core/mvp0d.py`
- [x] Porownac wyniki reczny vs. `solve_ivp` na istniejacych testach (roznice w alpha/T/p/rho w dopuszczalnych granicach). -> `tests/test_core_simulation.py`
- [x] Wyekstrahowac logike kinetyki do `kinetics.py` (alpha(t), arrhenius, kalibracja do cream/gel/rise). -> `src/pur_mold_twin/core/kinetics.py`
- [x] Wyekstrahowac bilans ciepla do `thermal.py` (pianka + forma, wymiana z otoczeniem). -> `src/pur_mold_twin/core/thermal.py`
- [x] Wyekstrahowac gaz/ekspansje/cisnienia do `gases.py` / `pressure.py` (CO2, pentan, powietrze, p_total). -> `src/pur_mold_twin/core/gases.py`, `src/pur_mold_twin/core/pressure.py`
- [x] Wyekstrahowac model twardosci do `hardness.py` (H = f(alpha, rho)). -> `src/pur_mold_twin/core/hardness.py`
- [x] Zbudowac cienki `simulation.py`, ktory skleja wszystkie powyzsze moduly w jeden interfejs `run_0d_simulation(...)`. -> `src/pur_mold_twin/core/simulation.py`, `docs/STRUCTURE.md`

## 2. Modele danych, walidacja i jednostki

- [x] Przeniesc dataclasses z `mvp0d.py` do `types.py` jako modele Pydantic (`ProcessConditions`, `MoldProperties`, `VentProperties`, `QualityTargets`, `SimulationConfig`, `SimulationResult`). -> `src/pur_mold_twin/core/types.py`, `py_lib.md`
- [x] Dodac walidacje zakresow (np. RH 0–1, temperatury w °C, masy > 0, mixing_eff w [0,1]) w modelach Pydantic. -> `src/pur_mold_twin/core/types.py`
- [x] Zintegrowac `pint` na wejsciu/wyjsciu (Temp °C/K, cisnienia bar/Pa, gestosc kg/m3) zgodnie z zaleceniami z `py_lib.md`. -> `src/pur_mold_twin/core/types.py`, `py_lib.md`
- [x] Walidacja `MaterialSystem`: sprawdzanie spojnosci danych TDS (np. czy `%NCO` w realnym zakresie). -> `src/pur_mold_twin/material_db/models.py`
- [x] Uaktualnic `docs/MODEL_OVERVIEW.md` o info, ze I/O sa realizowane przez modele Pydantic + jednostki z `pint`. -> `docs/MODEL_OVERVIEW.md`
- [x] Zdefiniowac `OptimizerConfig` (zmienne decyzyjne, bounds, cele, constrainty) jako model Pydantic. -> `src/pur_mold_twin/optimizer/constraints.py`, `src/pur_mold_twin/optimizer/search.py`

## 3. Material DB i konfiguracje wejscia

- [x] Dopiac mapowanie YAML -> `MaterialSystem` (w tym pola: woda, pentan, czasy reakcji, docelowa rho/H). -> `src/pur_mold_twin/material_db/models.py`, `configs/systems/*`
- [x] Zaimplementowac loader z `ruamel.yaml` (`load_system(name)`) z walidacja Pydantic i bezpieczna obsluga bledow formatowania. -> `src/pur_mold_twin/material_db/loader.py`, `py_lib.md`
- [x] Zapewnienie, ze core (`simulation.py`) przyjmuje `MaterialSystem` jako pierwszy argument (zamiast „recznych” parametrow). -> `src/pur_mold_twin/core/simulation.py`
- [x] Upewnic sie, ze `configs/systems/jr_purtec_catalog.yaml` i inne systemy laduja sie poprawnie po refaktorze; dodac test loadera. -> `tests/test_material_loader.py`
- [x] Uaktualnic `docs/STRUCTURE.md` i `docs/MODEL_OVERVIEW.md` o przeplyw: YAML -> Material DB -> core. -> `docs/STRUCTURE.md`, `docs/MODEL_OVERVIEW.md`
- [x] Uporzadkowac `configs/systems/*.yaml` pod wspolny schemat (slepy vs zmapowany na `MaterialSystem`). -> `configs/systems/*`, `src/pur_mold_twin/material_db/models.py`
- [x] Zdefiniowac format `configs/scenarios/*.yaml` (warunki procesu: masy, T, RH, formy, vent). -> `configs/scenarios/*`, `docs/USE_CASES.md`
- [x] Zdefiniowac format `configs/quality/*.yaml` dla presetow `QualityTargets`. -> `configs/quality/*`, `docs/MODEL_OVERVIEW.md`
- [x] Dodac do `py_lib.md` info, ze konfiguracje sa ladowane przez `ruamel.yaml` i walidowane Pydantic. -> `py_lib.md`

## 4. CLI fundamenty, `run-sim` i `optimize`

 - [x] Zastapic placeholder w `src/pur_mold_twin/cli/main.py` pelnoprawna aplikacja `Typer` z entry pointem, `--version` i helpem; zdefiniowac strukture komend w `src/pur_mold_twin/cli/commands.py` (lub submodulach). -> `src/pur_mold_twin/cli/main.py`, `src/pur_mold_twin/cli/commands.py`
- [x] Zaprojektowac parametry CLI `run-sim` (system, scenario, quality, output path). -> `src/pur_mold_twin/cli/main.py`, `docs/USE_CASES.md`
- [x] Zaimplementowac `run-sim`: ladowanie YAML, odpalenie `run_0d_simulation(...)`, obsluga flag `--output json/table`, `--export-csv`, prezentacja KPI w tabeli. -> `src/pur_mold_twin/cli/commands.py`, `src/pur_mold_twin/cli/utils.py`
- [x] Dodac przyklad wywolania do `readme.md` (sekcja „Przyklady uzycia”) i opis flag w `docs/USE_CASES.md`. -> `readme.md`, `docs/USE_CASES.md`
- [x] Dopisac testy CLI (`pytest` + `CliRunner`) dla `run-sim`: scenariusz happy-path (`exit_code == 0`) oraz bledny plik (czytelny komunikat). -> `tests/test_cli.py`
- [x] Dodac walidacje i ladne komunikaty CLI dla bledow Pydantic/loader (zamiast tracebacka). -> `src/pur_mold_twin/cli/main.py`
- [x] Komenda `optimize`: wczytuje scenariusz + `OptimizerConfig` z YAML, spina `ProcessOptimizer`, raportuje „Przed vs Po” (czas demold, cisnienie) i zapisuje wyniki (JSON/CSV). -> `src/pur_mold_twin/cli/commands.py`, `src/pur_mold_twin/cli/utils.py`
- [x] Uaktualnic `docs/USE_CASES.md` o referencyjny use-case optymalizacji (wejscia, cele, ograniczenia). -> `docs/USE_CASES.md`
- [x] Dodac testy optymalizera w `tests/test_optimizer.py` dla case z `USE_CASES`. -> `tests/test_optimizer.py`

## 5. Logging runtime i verbose

- [x] Zastapic `print()` w silniku/CLI modułem `logging`. -> `src/pur_mold_twin/utils/logging.py`
- [x] Konfiguracja poziomow: INFO dla uzytkownika (postep), DEBUG dla dewelopera (szczegoly solvera). -> `src/pur_mold_twin/utils/logging.py`
- [x] Integracja z CLI: flaga `--verbose` sterujaca poziomem logowania. -> `src/pur_mold_twin/cli/main.py`

## 6. Kalibracja i walidacja

- [x] Zaimplementowac loader datasetu kalibracyjnego wg `docs/CALIBRATION.md` (CSV/Parquet + meta). -> `src/pur_mold_twin/calibration/loader.py`
- [x] Zbudowac funkcje kosztu (bledy t_cream/gel/rise, T_core(t), p_max, rho_moulded). -> `src/pur_mold_twin/calibration/cost.py`
- [x] Uzyc `scipy.optimize` (np. `least_squares`/`minimize`) do kalibracji wybranych parametrow `SimulationConfig` dla 1–2 referencyjnych case’ow. -> `src/pur_mold_twin/calibration/fit.py`, `py_lib.md`
- [x] Dodac testy regresyjne kalibracji (sprawdzajace, ze bledy <= zalozone progi). -> `tests/test_calibration.py`, `docs/CALIBRATION.md`
 - [x] Skrypt `scripts/calibrate_kinetics.py`: wczytanie czasow TDS (cream/gel/rise) i optymalizacja parametrów Arrheniusa. -> `scripts/`
 - [x] Wizualizacja kinetyki: generowanie prostego wykresu `alpha(t)` z zaznaczonymi punktami TDS. -> `scripts/`
 - [x] Zgodnosc z `docs/CALIBRATION.md`: format wejscia/wyjscia dla narzedzi kalibracyjnych. -> `docs/CALIBRATION.md`
 - [x] Skrypt `scripts/compare_shot.py`: wczytanie logu CSV (temperatura/cisnienie) i pliku wynikowego symulacji. -> `scripts/`
 - [x] Obliczenie metryk bledu: RMSE dla temperatury, delta p_max, delta t_demold. -> `scripts/`
 - [x] Raportowanie: wypisanie czy strzal miesci sie w tolerancjach zdefiniowanych w `docs/CALIBRATION.md`. -> `scripts/`

## 7. Testy regresyjne, skrajne i pokrycie

 - [x] Wyznaczyc „golden” zestaw wejsciowy (system + scenario + quality) dla podstawowego case i zapisac jako fixture. -> `tests/fixtures/*`, `docs/USE_CASES.md`
 - [x] Rozszerzyc `test_core_simulation.py` o asercje na dokladne profile (t/alpha/T_core/p_total/rho) vs. golden outputs (z tolerancja). -> `tests/test_core_simulation.py`
 - [x] Dodac test regresyjny dla optymalizera, upewniajacy sie, ze wynik nie „dryfuje” po zmianach w core. -> `tests/test_optimizer.py`
 - [x] Uaktualnic `README_VERS.md` o info, ze golden data sa uzywane jako regresja. -> `README_VERS.md`
 - [x] Testy skrajne: zatkanie ventow w pierwszych sekundach, `RH=100%`, bardzo zimna forma. -> `tests/test_core_simulation.py`
 - [x] Weryfikacja stabilnosci solvera: czy `MVP0DSimulator` rzuca zrozumialym bledem zamiast zawieszac sie przy nierealnych danych. -> `tests/test_core_simulation.py`
 - [x] Coverage: konfiguracja `pytest-cov`, cel >80% pokrycia dla modułu `core`. -> `pyproject.toml`

## 8. Logi symulacji, ETL, featury i ML

- [ ] Zaimplementowac modul logowania symulacji (profile + meta) zgodnie z `docs/ML_LOGGING.md`. -> `src/pur_mold_twin/logging/logger.py`, `py_lib.md`
- [ ] Zbudowac pipeline `build_features` (skrypt/CLI), ktory z logow wyciagnie featury opisane w ML_LOGGING (T_max, p_max, slopes, roznice vs pomiar). -> `src/pur_mold_twin/logging/features.py`
- [ ] Dodac komende CLI `build-features` i opis w `readme.md`. -> `src/pur_mold_twin/cli/main.py`, `readme.md`
- [ ] Sprawdzic spojnosc nazw featur miedzy ML_LOGGING a kodem. -> `docs/ML_LOGGING.md`
- [ ] Modul ETL: parsowanie surowych logow (format z `docs/ML_LOGGING.md`) do obiektow `ProcessConditions`. -> `src/pur_mold_twin/data/etl.py`
- [ ] Obsluga brakujacych danych: strategie uzupelniania (np. domyslne RH jesli brak czujnika). -> `src/pur_mold_twin/data/etl.py`
- [ ] Testy ETL: parsowanie przykladowego pliku logow. -> `tests/test_etl.py`
- [ ] Dataset builder: laczenie wynikow symulacji z danymi z ETL w `features.parquet`. -> `src/pur_mold_twin/data/dataset.py`
- [ ] Struktura katalogow: utworzenie `data/ml/` (gitignored) i skryptow pomocniczych. -> `scripts/build_dataset.py`
- [ ] Weryfikacja schematu danych: zgodnosc kolumn z `docs/ML_LOGGING.md`. -> `src/pur_mold_twin/data/schema.py`
- [ ] Utworzyc modul `ml/baseline.py` (sklearn) z modelami klasyfikacji defektow i regresji `defect_risk`. -> `src/pur_mold_twin/ml/baseline.py`, `py_lib.md`
- [ ] Przygotowac minimalny skrypt treningowy (train/test split, zapis modelu). -> `src/pur_mold_twin/ml/train_baseline.py`
- [ ] Dodac sekcje „ML (opcjonalnie)” w `docs/ML_LOGGING.md` i `readme.md`, opisujaca te baseline’y. -> `docs/ML_LOGGING.md`, `readme.md`
- [ ] Upewnic sie, ze ML jest oznaczone jako **opcjonalne** (projekt dziala bez zainstalowanego `scikit-learn`). -> `py_lib.md`, `readme.md`

## 9. Wizualizacja i raporty

- [ ] Dodac modul `reporting/plots.py` z funkcjami do rysowania profili (alpha/T/p/rho) przy uzyciu `matplotlib`. -> `src/pur_mold_twin/reporting/plots.py`, `py_lib.md`
- [ ] Dodac prosty raport HTML/Markdown (np. generator na podstawie szablonu) z wykresami i KPI dla jednego strzalu. -> `src/pur_mold_twin/reporting/report.py`
- [ ] Zintegrowac generowanie raportu jako opcje CLI (`run-sim --report`). -> `src/pur_mold_twin/cli/main.py`
- [ ] Uaktualnic `docs/USE_CASES.md` o use-case „wygeneruj raport z symulacji/optimizacji”. -> `docs/USE_CASES.md`

## 10. Packaging, CI, dokumentacja

- [ ] Uporzadkowac `pyproject.toml` / konfiguracje dependency (`numpy`, `scipy`, `pydantic`, `pint`, `ruamel.yaml`, `typer`, `pytest`, opcjonalne ML); odnotowac to w `py_lib.md`. -> `pyproject.toml`, `py_lib.md`
- [ ] Dodac entry-point dla CLI (`pur-mold-twin`) w packagingu. -> `pyproject.toml`, `src/pur_mold_twin/cli/main.py`
- [ ] Skonfigurowac proste CI (np. GitHub Actions) odpalajace `pytest` + ewentualnie mypy/ruff/black. -> `.github/workflows/*`
- [ ] Zaktualizowac `standards.md` o zasady dot. CLI, packagingu, CI (wersjonowanie, naming) oraz sprawdzic zgodnosc nowych modulow (CLI, ETL). -> `standards.md`, `README_VERS.md`
- [ ] Aktualizacja `README.md`: instrukcja CLI (`run-sim`, `optimize`, flagi, konfiguracje) oraz finalny przeglad spojnosci `docs/` po zakonczeniu Fazy 2. -> `README.md`, `docs/*`
- [ ] Aktualizacja `py_lib.md`: dodanie `typer`, `ruamel.yaml`, `pandas` (ETL) jako zaleznosci produkcyjnych. -> `py_lib.md`

