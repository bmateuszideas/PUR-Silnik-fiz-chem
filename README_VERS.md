# README / Workflow Verification (Checkpoint)

Data: 2025-12-01  
Zakres: kontrola spojnosci repo z `todo1.md` (szczegolnie §13) oraz weryfikacja tresci `readme.md`.

## 2025-12-15
- Release gating TODO4: README i `docs/ML_LOGGING.md` dokumentuja tester `ml_status` oraz checkliste release; `todo4.md` ma status „Ready to tag”.
- CI: workflow `.github/workflows/ci.yml` posiada job `lint` (ruff/black/markdownlint-cli2) oraz zredukowana macierz testowa (Python 3.11/3.12/3.14 z przełącznikiem extras `[ml]`); `release.yml` nadal wykonuje smoke na wheelu.
- Tester scenariuszy ML (`scripts/ml_status_tester.py`) i testy `tests/test_ml_status_tester.py` uznane za wymagane przed tagiem `v1.0.0` (scenariusze `ok`, `missing-models`, `missing-extras`).
- Release checklist (tymczasowa): `pytest -q`, `python scripts/smoke_e2e.py`, `python scripts/ml_status_tester.py --case {ok, missing-models, missing-extras}`, aktualizacja `README_VERS.md` i `todo4.md`, tag `v1.0.0`, obserwacja workflow `release.yml`.

## 2025-12-02
- Dodano realne testy (`test_core_simulation.py`, `test_optimizer.py`) i usunieto placeholdery.
- Standaryzowano strukture dokumentacji (root `standards.md`, `docs/CALIBRATION.md`, `docs/ML_LOGGING.md`).
- Material DB scalona w multi-doc `configs/systems/jr_purtec_catalog.yaml` (zawiera R1/M1 oraz systemy JR Purtec).
- Status README zaktualizowany: MVP 0D + prosty optimizer + testy bazowe.

## 2025-12-07
- Utworzono golden fixture dla `use_case_1` (`tests/fixtures/use_case_1_output.json`) oraz dodano regresje profili w `tests/test_core_simulation.py` (alpha/T_core/p_total/rho) z tolerancjami.
- Test regresyjny optymalizatora (`tests/test_optimizer.py`) wykorzystuje `use_case_1` i weryfikuje brak dryfu; dodano testy skrajne (brak ventów) i podstawowe tolerancje.
- Kalibracja: nowy pakiet `calibration/` (loader/cost/fit) oraz skrypty `calibrate_kinetics.py`, `compare_shot.py`, `calibration_report.py`, `plot_kinetics.py`; dokument `docs/CALIBRATION.md` opisuje automatyzację.
- CLI: rozbudowany Typer (`run-sim`/`optimize`, eksport JSON/CSV, `--verbose`); testy CLI w `tests/test_cli.py` (scenariusze poprawne oraz z blednymi plikami).
- ML/ETL: moduły logowania/featur (`logging/`, `data/`, `ml/`), CLI `build-features`; `docs/ML_LOGGING.md` i `todo2.md` §8 domkniete.
- Raporty: `run-sim --report` generuje raport Markdown + wykresy (matplotlib); dokumentacja w `docs/USE_CASES.md`.
- Packaging/CI: `pyproject.toml` z dependencies/extras i entry-pointem `pur-mold-twin`; workflow `.github/workflows/ci.yml` uruchamia `pytest`.

## 2025-12-12
- Sprawdzono spojnosc sekcji 10–15 `readme.md` z aktualna struktura (`docs/STRUCTURE.md`) oraz plikami CLI/testow i zaktualizowano referencje.
- Status faz: MVP 0D (fazy 1–3: core z cisnieniem/vent, oknem demold i diagnostyka) oraz optimizer + CLI Typer sa dostarczone; dalsze prace (kalibracja danych, rozszerzenia ML/raportow/CI) sa kontynuowane w TODO2.
- Uporzadkowano TODO1: sekcja 13 traktowana jako domknieta; utrzymanie dokumentacji/standardow prowadzone w istniejacych plikach.

## 2025-12-03
- Skonfigurowano polityke `ml_status` (kody + opis) w CLI/API wraz z dokumentacja w README i `docs/ML_LOGGING.md`.
- Dodano tester scenariuszy ML (`scripts/ml_status_tester.py`) oraz testy systemowe `tests/test_ml_status_tester.py` pokrywajace przypadki `ok`/`missing-models`/`missing-extras`.
- Uporzadkowano katalog `scripts/` (usunieto stuby, pozostaly aktywne narzedzia) i przygotowano `todo4.md` z planem releasu 1.0.0.
- Workflow CI uzupelniono o job `lint` (ruff/black/markdownlint); repo zawiera konfiguracje `.markdownlint.jsonc` i instrukcje w dashboardzie.

## 1. Stan TODO1
- §1-13 oznaczone jako ukonczone i potwierdzone w repo (`docs/MODEL_OVERVIEW.md`, `docs/STRUCTURE.md`, `src/pur_mold_twin/core`, `docs/CALIBRATION.md`, `docs/ML_LOGGING.md`).
- Rozbudowa testow/CLI/raportow przechodzi do TODO2 (kalibracja datasetow, ML/ETL, CI/packaging) zgodnie z notatkami w README i dokumentacji.

## 2. Czy README odzwierciedla rzeczywistosc?
**Zgodne**
- Sekcje 1–15 opisuja aktualny kod (core/optimizer/diagnostyka/CLI Typer/raporty/ETL/ML) i odsyłaja do istniejacych modulow oraz `docs/STRUCTURE.md`/`docs/USE_CASES.md`.
- Status w sekcji 10 odpowiada bieżącemu MVP 0D z optimizerem, a sekcje 12–15 pokrywaja komendy CLI, raporty i konfiguracje testowe wykorzystywane w regresjach.

**Rozbiezne**
- Brak nowych rozbiezności; historyczne placeholdery z §13 zostaly zastapione rzeczywistymi modulami (CLI, testy, raporty, ETL/ML).

## 3. Zalecenia dla §13
1. Kolejne iteracje w TODO2: rozszerzyc dataset kalibracyjny i coverage ETL/ML zgodnie z `docs/CALIBRATION.md` i `docs/ML_LOGGING.md`.
2. Przy nowych modulach raportowania/ML/CI aktualizowac `docs/STRUCTURE.md` oraz sekcje 10–15 README.
3. Utrzymywac changelogi TODO1/TODO2 po kazdej zmianie w CLI/testach/regresjach.

## 4. Podsumowanie
Workflow (TODO1 -> README -> docs -> src) jest spójny dla paczek (a–d). Po wprowadzeniu placeholderow i zasad przechowywania danych §13 wymaga juz tylko dopracowania testow i CLI, ale dokumentacja pozostaje zgodna z rzeczywistoscia.
## Faza 3 - Advanced backends & Produkt 1.0 (TODO3)

### Cele biznesowe
- Udostepnienie stabilnego, skalowalnego silnika predykcyjnego klasy Digital Twin PUR, gotowego do pilota u klienta.
- Latwa integracja z istniejacymi systemami klienta (logi procesu, bazy danych, narzedzia analityczne) przez CLI/API/serwis.
- Wsparcie decyzji technologicznych (nastawy, czas w formie, ryzyka cisnienia/defektow) z uzyciem core + optimizer + ML.

### Cele techniczne
- Backend ODE:
  - wyodrebniony interfejs backendow w `core/ode_backends.py` (strategy pattern),
  - implementacja backendu SUNDIALS i przygotowanie interfejsu pod JAX,
  - benchmarki czasu/jakosci backendow na reprezentatywnych scenariuszach (`docs/PERF_BACKENDS.md`).
- Fizyka:
  - utrzymanie stabilnosci i regresji 0D (golden fixtures),
  - przygotowanie struktury danych i API pod pseudo-1D (TODO4) bez lamiania kontraktow klienta.
- Integracje:
  - konektory danych (np. SQL/REST) nad istniejacym ETL (`data/etl.py`),
  - ujednolicone schematy danych w `data/schema.py` dla logow i datasetow ML.
- ML:
  - domkniety pipeline ML 2.0 (trenowanie, ewaluacja, inference),
  - podstawowy monitoring driftu danych i modeli (`ml/drift.py`, CLI `check-drift`).
- Produkt:
  - referencyjny serwis API (np. FastAPI) owijajacy core/optimizer/raporty z OpenAPI,
  - tryb operatora w CLI/API z widokiem na KPI i statusy,
  - release workflow z publikacja na TestPyPI oraz smoke-testem E2E po instalacji.

### Kryteria DONE dla TODO3 (produkt 1.0)
- Backend ODE:
  - co najmniej trzy backendy (manual, `solve_ivp`, SUNDIALS) pod wspolnym interfejsem,
  - benchmarki i tolerancje numeryczne opisane w `docs/PERF_BACKENDS.md` i pokryte testami.
- Core i fizyka:
  - wszystkie istniejace golden fixtures i testy regresyjne przechodza po wprowadzeniu nowych backendow i przygotowaniu pseudo-1D,
  - API core/optimizer/CLI pozostaje kompatybilne z dokumentacja i use-case.
- Integracje i ML:
  - dostepne sa co najmniej dwa zrodla danych (plikowe + SQL/API) spiete z ETL,
  - pipeline ML 2.0 (trening, ewaluacja, inference) dziala na realnym dataset, a drift danych moze byc oceniony przez CLI/report.
- Produkt:
  - istnieje referencyjna implementacja serwisu (np. FastAPI) z udokumentowanym OpenAPI,
  - `pip install pur-mold-twin` z oficjalnego kanalu + smoke-test E2E przechodza,
  - `README_VERS.md` oraz `docs/ROADMAP_TODO3.md` odzwierciedlaja stan produktu 1.0.
