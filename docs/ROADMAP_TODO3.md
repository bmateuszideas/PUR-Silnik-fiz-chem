# ROADMAP TODO3 - PUR-MOLD-TWIN (Faza 3)

Stan produktu na start TODO3 oraz kierunek dojscia do produktu 1.0. Dokument ma byc zbieznym punktem odniesienia dla kodu, README, TODO3 oraz dashboardu developerskiego.

## 1. Stan produktu (koniec TODO2 / start TODO3)

### 1.1 Core Engine (0D MVP)

- Zakres fizyki: stechiometria i bilans gazu (CO2, pentan, powietrze startowe), kinetyka i cieplo (`alpha(t)`, egzoterm, wymiana ciepla pianka-forma-otoczenie), ekspansja i gestosc (`rho_free_rise`, `rho_moulded`), cisnienie i odpowietrzniki (`p_air`, `p_CO2`, `p_pentane`, `vent_eff(t)`), twardosc i demold (`H = f(alpha, rho)`).
- Model jest 0D (single lumped control volume) – brak przestrzennego podzialu na warstwy/sekcje, brak explicit 1D frontu.
- Implementacja: modul `src/pur_mold_twin/core/` (m.in. `mvp0d.py`, `simulation.py`, `kinetics.py`, `thermal.py`, `gases.py`, `hardness.py`, `types.py`) + diagnostyka (`diagnostics/`).
- Backend ODE: reczny schemat krokowy oraz wariant oparty na `scipy.integrate.solve_ivp` (wybor backendu przez konfiguracje).
- Jakosc: golden fixture `use_case_1` (`tests/fixtures/use_case_1_output.json`) oraz testy regresyjne profili (`tests/test_core_simulation.py`); tolerancje zgodne z `docs/MODEL_OVERVIEW.md` i `docs/CALIBRATION.md`.

### 1.2 Process Optimizer

- Pakiet `src/pur_mold_twin/optimizer/` ze strukturami Pydantic (`OptimizerConfig`, bounds/constraints) i losowym przeszukiwaniem opartym o `MVP0DSimulator`.
- Constraints: `p_max`, `alpha_demold`, `H_demold`, `H_24h`, `rho_moulded`, `t_demold` vs `t_cycle_max`, `defect_risk` zgodnie z `docs/MODEL_OVERVIEW.md`.
- Testy regresyjne optymalizatora (stabilnosc wyniku dla `use_case_1`, przypadki skrajne – np. brak ventow).

### 1.3 Configs i Material DB

- Material DB w YAML: `configs/systems/jr_purtec_catalog.yaml` (SYSTEM_R1, SYSTEM_M1 + systemy JR Purtec).
- Mapowanie YAML -> Pydantic `MaterialSystem` w `src/pur_mold_twin/material_db/models.py` + loader w `material_db/loader.py` (ruamel.yaml, walidacja).
- Scenariusze procesu: `configs/scenarios/*.yaml` (m.in. `use_case_1.yaml`) oraz presety jakosci w `configs/quality/*.yaml`.
- Przeplyw: YAML -> Material DB -> core opisany w `docs/STRUCTURE.md` / `docs/MODEL_OVERVIEW.md` i wykorzystywany w CLI/optimizerze.

### 1.4 CLI Typer i raportowanie

- Entry-point `pur-mold-twin` (zdefiniowany w `pyproject.toml`).
- Komendy CLI:
  - `run-sim` – ladowanie scenariusza, uruchomienie symulacji, wypisanie KPI na stdout (`json` / `table`), opcjonalny zapis JSON/CSV (`--save-json`, `--export-csv`), wybor backendu solvera (`--backend`), `--verbose`.
  - `optimize` – random search nad scenariuszem referencyjnym, raport constraints i najlepszych nastaw.
  - `build-features` – ETL i generacja feature store z logow pomiarowych + wynikow symulacji (`data/ml/features.parquet`).
- Raporty: `src/pur_mold_twin/reporting/plots.py` i `reporting/report.py` + flaga `run-sim --report` (raport Markdown z wykresami); opisane w `docs/USE_CASES.md`.

### 1.5 ETL, logging i ML 1.x

- Logowanie procesu i featury zgodne z `docs/ML_LOGGING.md`:
  - ETL z logow produkcyjnych (`data/etl.py`, `data/schema.py`),
  - budowa feature store (`logging/features.py`, CLI `build-features`, `data/ml/features.parquet`),
  - opcjonalne baseline ML (`ml/baseline.py`, `ml/train_baseline.py`) z extras `[ml]` (scikit-learn).
- Integracja z core/CLI: `build-features` laczy wyniki symulacji z danymi z hali; ML jest w pelni opcjonalne (projekt dziala bez zainstalowanego `scikit-learn`).

### 1.6 Packaging, CI, dokumentacja

- Python 3.14 jako wymagany runtime (`py_lib.md`, `pyproject.toml`).
- Packaging: `pyproject.toml` (dependencies + extras `dev`/`ml`), entry-point CLI.
- CI: workflow `.github/workflows/ci.yml` uruchamia `pytest` oraz podstawowe narzedzia QA (zgodnie z TODO2).
- Dokumentacja: `readme.md` (status MVP 0D + optimizer + CLI), `docs/STRUCTURE.md`, `docs/MODEL_OVERVIEW.md`, `docs/USE_CASES.md`, `docs/CALIBRATION.md`, `docs/ML_LOGGING.md`, `README_VERS.md`.

## 2. Ograniczenia na start TODO3

### 2.1 Model i backendy numeryczne

- Model jest 0D – brak explicit 1D (brak przestrzennego frontu, rozkladu temperatury/cisnienia wzdloz glebokosci, brak siatki stref).
- Backend ODE:
  - manualny schemat i `solve_ivp` dzialaja dobrze dla pojedynczych strzalow i malych batchy,
  - brak wsparcia dla zaawansowanych backendow (SUNDIALS, JAX), brak estymacji stiff/DAE use-case,
  - brak zunifikowanego interfejsu backendow (brak strategy pattern z odseparowanymi implementacjami).

### 2.2 ETL, integracje i ML

- ETL/ML dziala na plikach (YAML/CSV/Parquet) – brak produkcyjnych konektorow (SQL, REST API, OPC/SCADA).
- ML 1.x ma zakres proof-of-concept:
  - baseline modele, brak ustalonego cyklu trenowanie -> deploy -> monitoring,
  - brak monitoringu driftu danych/feature (tylko plan w `docs/ML_LOGGING.md`),
  - brak standardu wersjonowania datasetow i modeli (poza prostym zapisem plikow).

### 2.3 Produkt i operacyjny lifecycle

- Brak referencyjnego serwisu API (FastAPI/inna ramka) owijajacego core/optimizer/raporty.
- Brak zdefiniowanego trybu operatora (CLI/API pod konkretnego uzytkownika hali).
- Release workflow ogranicza sie do CI z `pytest`; brak automatycznego publikowania paczek (TestPyPI/PyPI), brak checklisty produktowej 1.0.

## 3. Ryzyka techniczne

- **Wydajnosc i skalowanie**
  - Brak specjalizowanych backendow dla sztywnych/problemowych przypadkow (mozliwy wysokie koszty czasowe dla niestandardowych scenariuszy).
  - Brak benchmarkow backendow (manual/solve_ivp/SUNDIALS/JAX) na reprezentatywnych use-case.
- **Rozszerzona fizyka**
  - Przejscie z 0D do pseudo-1D wymaga ostroznej refaktoryzacji struktur danych i API; ryzyko regresji w istniejacych profilach i diagnostyce.
- **Jakosc danych i ML**
  - Brak E2E pipeline (logi -> ETL -> features -> trening -> deploy -> drift) utrudnia uzycie ML w produkcji.
  - Zaleznosc od jakosci logow z hali (brak formalnych walidatorow i strategii obchodzenia brakow w TODO3 moze prowadzic do niestabilnych modeli).
- **Integracje i produkt**
  - Bez spójnego API/serwisu klient moze miec trudnosc z integracja z wlasnym systemem MES/SCADA/SQL.
  - Brak obserwowalnosci (metryki runtime, logi serwisu) utrudni diagnoze problemow podczas pilota.

## 4. Segmenty TODO3 (target na produkt 1.0)

### 4.1 Core / backendy ODE

- Uporzadkowany interfejs backendow w `core/ode_backends.py` (strategy pattern).
- Implementacja backendu SUNDIALS i przygotowanie interfejsu pod JAX.
- Benchmarki backendow (`docs/PERF_BACKENDS.md`, skrypt `scripts/bench_backends.py`) oraz zasady tolerancji numerycznych (czas, liczba krokow, rozbieznosci vs referencja).
- Przygotowanie modelu do pseudo-1D (struktura danych i API gotowe na rozszerzona fizyke z TODO4).

### 4.2 Integracje danych

- Konektory do zewnetrznych zrodel danych (SQL/API) nad istniejacym ETL-em (`data/etl.py`); jasny podzial: konektor = zrodlo, ETL = transformacja do kontraktow Pydantic.
- Ujednolicone I/O dla logow i wynikow (schema-first w `data/schema.py`).

### 4.3 ML 2.0 i drift

- Rozszerzenie pipeline ML: trening, ewaluacja, serializacja modeli, integracja inference z core/CLI/API.
- Monitoring driftu danych i modeli (`ml/drift.py`, raporty, CLI `check-drift`).
- Dokumentacja cyklu ML 2.0 w `docs/ML_LOGGING.md` / `docs/CALIBRATION.md`.

### 4.4 Produkt (API, serwis, release)

- Warstwa API/serwisu owijajaca core/optimizer/raporty (FastAPI lub podobny framework) z OpenAPI.
- Tryb operatora (CLI/API) z widokiem na najwazniejsze KPI i statusy.
- Release workflow: CI dla packagingu, publikacja na TestPyPI, smoke-test E2E po instalacji, standardy wersjonowania/URL-e w `pyproject.toml` i `README_VERS.md`.

## 5. Kryteria DONE dla TODO3 (produkt 1.0)

- Backend ODE:
  - Istnieje modularny interfejs backendow z co najmniej trzema implementacjami (manual, solve_ivp, SUNDIALS) oraz zdefiniowanym miejscem na JAX.
  - Benchmarki i tolerancje numeryczne sa opisane w `docs/PERF_BACKENDS.md` i pokryte testami porownawczymi.
- Fizyka:
  - Core 0D pozostaje stabilny i zweryfikowany na istniejacych golden fixtures.
  - Architektura i kontrakty sa przygotowane pod pseudo-1D (TODO4) bez lamiania API dla klienta.
- Integracje i ML:
  - Dostepne sa konektory danych (min. SQL/plikowy) nad ETL, z jasnym podzialem odpowiedzialnosci.
  - Pipeline ML obejmuje trenowanie, ewaluacje i inference + podstawowy monitoring driftu (CLI + raport).
- Produkt:
  - Istnieje referencyjny serwis API (np. FastAPI) z udokumentowanym OpenAPI i scenariuszem wdrozenia pilota.
  - CLI/serwis oferuje tryb operatora oraz tryb eksperta (lib/CLI/API sa opisane w README).
  - Release workflow potwierdzony: paczka instaluje sie z TestPyPI, smoke-test E2E przechodzi, a `README_VERS.md` zawiera wpis dla Fazy 3.

