# DEV DASHBOARD TODO3 - PUR-MOLD-TWIN (handover dla kolejnego agenta)

Ten plik jest „home screenem” dla kolejnego agenta/Copilota przejmujacego Faze 3 (TODO3). Zwieza stan, szybkie komendy oraz kolejnosc dzialan. Nie nadpisuje `agent_instructions.md` ani TODO1/2 – jest tylko praktycznym panelem.

## 1. Co juz jest zrobione w TODO3

Przed dalsza praca przeczytaj:
- `agent_instructions.md`, `copilot_update_project_playbook.md`,
- `readme.md`, `README_VERS.md`, `docs/STRUCTURE.md`, `docs/MODEL_OVERVIEW.md`,
- `docs/ML_LOGGING.md`, `docs/CALIBRATION.md`, `docs/API_REST_SPEC.md`,
- `todo3.md`, `docs/ROADMAP_TODO3.md`.

Stan blokow TODO3 (wysoki poziom):
- **Blok 0 – stan produktu i standardy (1–3)**: zrobione
  - `docs/ROADMAP_TODO3.md` opisuje stan produktu i cele TODO3,
  - `README_VERS.md` ma sekcje Faza 3 + Versioning & releases,
  - `standards.md` zawiera zasady backendow ODE, ETL vs konektory, logging.
- **Blok 1 – backend ODE + SUNDIALS + JAX + benchmarki (4–8)**: zrobione w wersji praktycznej
  - `core/ode_backends.py`: backendy `manual`, `solve_ivp`, szkice `sundials` i `jax` (opcjonalne extras),
  - `SimulationConfig.backend` wspiera `"manual"|"solve_ivp"|"sundials"|"jax"`,
  - `docs/PERF_BACKENDS.md` + `scripts/bench_backends.py` – benchmark manual vs solve_ivp (SUNDIALS/JAX aktywne dopiero po instalacji extras),
  - testy porownawcze backendow w `tests/test_core_simulation.py` + dodatkowy test, ze SUNDIALS/JAX wymagaja extras.
- **Blok 2 – pseudo-1D (9–13)**: pierwszy krok zrobiony
  - `docs/MODEL_1D_SPEC.md` – spec pseudo-1D,
  - `SimulationConfig.dimension` (`"0d"|"1d_experimental"`),
  - `core/simulation_1d.py` + routing w `MVP0DSimulator` – dla `layers_count=1` 1D redukuje sie do 0D,
  - test regresyjny w `tests/test_core_simulation.py::test_dimension_1d_equals_0d_for_single_layer`,
  - sekcja „Experimental 1D” w `docs/MODEL_OVERVIEW.md`.
- **Blok 3 – integracja z logami/SQL (14–18)**: zrobione
  - `data/interfaces.py` – `ProcessLogQuery`, `ProcessLogSource`,
  - `data/sql_source.py` – `SQLProcessLogSource` + loader z YAML (SQLite),
  - `etl.py` – adapter `build_log_bundles_from_source`,
  - CLI `import-logs` w `cli/commands.py` (SQL -> lokalne katalogi logow),
  - test E2E `tests/test_data_integration.py` (oznaczony `skip` ze wzgledu na srodowisko).
- **Blok 4 – ML 2.0 (19–24)**: podstawowa wersja zrobiona
  - `ml/baseline.py` + rozbudowany `ml/train_baseline.py` (trening, metryki, zapis modeli, raport Markdown),
  - `ml/inference.py` – lazy-loading modeli i `attach_ml_predictions(...)`,
  - CLI:
    - `train-ml` (przez `ml/train_baseline.py` lub w przyszlosci jako osobna komenda Typer),
    - `run-sim --with-ml` – dokleja predykcje do JSON (best-effort),
  - `docs/ML_LOGGING.md` – zaktualizowany opis pipeline’u ML 2.0,
  - testy: `tests/test_ml_baseline.py`, `tests/test_ml_training.py` (skip gdy brak extras).
- **Blok 5 – API / mikroserwis / tryb operatora (25–29)**: 1. iteracja zrobiona
  - `docs/API_REST_SPEC.md` – spec endpointow `/simulate`, `/optimize`, `/ml/predict`, `/health`, `/version`,
  - `service/api.py` – wrapper `APIService` mapujacy JSON -> modele + wynik symulacji/optymalizacji,
  - `scripts/service_example.py` – referencyjny serwis FastAPI (wymaga extras),
  - CLI: `run-sim --mode operator` – operator-friendly widok KPI (tekstowa tabela) + `--with-ml`,
  - README ma opis trzech trybow uzycia: lib / CLI / API.
- **Blok 6 – Release, CI, smoke (30–33)**: szkic wykonany
  - `pyproject.toml` – realne URL-e (GitHub), extras `ml`, `sundials`, `jax`,
  - `README_VERS.md` – sekcja „Versioning & releases”,
  - `.github/workflows/release.yml` – workflow na tagi `v*.*.*` (build/test, wheel, smoke z wheel),
  - `scripts/smoke_e2e.py` – prosty smoke E2E po instalacji,
  - `tests/test_smoke_e2e.py` – import-check (skip).
- **Blok 7 – drift ML + E2E (34–37)**: podstawy zrobione
  - `ml/drift.py` – mean-based drift metrics + klasyfikacja `OK/WARNING/ALERT`,
  - CLI `check-drift` w `cli/commands.py` – status i kody wyjscia 0/1/2,
  - `tests/test_drift.py` + `tests/test_cli_drift.py` (skip, bo CLI),
  - `docs/CALIBRATION.md` – sekcja „Drift danych i cykliczna re-kalibracja” z przykladowym uzyciem `check-drift`.

## 2. Co zostalo do zrobienia (TODO3 – w praktyce)

Lista z `todo3.md` jest szeroka; po tej iteracji pozostaja przede wszystkim:
- Dopieszczenie pseudo-1D (Blok 2, zadania 11–12):
  - lepszy model przewodnictwa i walidacja profili T/alpha (osobny test `test_core_simulation_1d.py`),
  - ewentualne wlaczenie 1D do benchmarkow backendow.
- Domkniecie pelnego cyklu ML 2.0 (Blok 4):
  - rozbudowa raportow ML (`reports/ml/metrics.md`, docelowo HTML/wykresy),
  - spiecie `train-ml` jako komendy Typer (obecnie jest tylko main() w module),
  - lepsza wersjonizacja modeli (metadane w plikach modeli i raportach).
- API / serwis:
  - dopracowanie `scripts/service_example.py` (OpenAPI, CORS, konfiguracja przez env),
  - ewentualne testy integracyjne API (FastAPI) jesli srodowisko na to pozwala.
- Release/CI:
  - dopelnienie `ci.yml` (w tej chwili jest tylko `release.yml` – TODO3 sugeruje tez osobny workflow CI),
  - opcjonalny upload na TestPyPI (wymaga sekreta w repo).
- Drift/E2E (Blok 7):
  - prawdziwy test pipeline E2E: logi -> `import-logs`/ETL -> `build-features` -> `train-ml` -> `check-drift`,
  - raporty driftu w `reports/ml/` w spieciu z `CALIBRATION.md`.

## 3. Szybkie komendy (lokalnie)

Zakladamy Python 3.14, z repo w CWD.

- Testy core/optimizer/CLI (bez ML extras):
  - `PYTHONPATH=src python -m pytest tests/test_core_simulation.py tests/test_optimizer.py tests/test_cli.py`
- Pelny zestaw (w miare mozliwosci srodowiska):
  - `PYTHONPATH=src python -m pytest`
- Benchmark backendow:
  - `PYTHONPATH=src python scripts/bench_backends.py --scenario configs/scenarios/use_case_1.yaml --backends manual,solve_ivp --repeats 3`
- ETL/feature store:
  - `PYTHONPATH=src python scripts/build_dataset.py` (patrz `docs/ML_LOGGING.md`),
  - CLI: `pur-mold-twin build-features --sim out/run.json --measured logs/sample/ --output data/ml/features.parquet`.
- Trening ML (po `pip install .[ml]`):
  - `PYTHONPATH=src python -m pur_mold_twin.ml.train_baseline --features data/ml/features.parquet`
- Drift:
  - `pur-mold-twin check-drift --baseline data/ml/features_baseline.parquet --current data/ml/features_current.parquet`.
- API (lokalny serwis, gdy masz fastapi/uvicorn):
  - `uvicorn scripts.service_example:app --reload`

## 4. Zasady dla kolejnego agenta

1. **Zawsze najpierw czytaj, potem pisz.**
   - Przed zmiana w danym obszarze przeczytaj odpowiadajace sekcje w `todo3.md`, `docs/ROADMAP_TODO3.md`, `standards.md` i odpowiednich docs (MODEL_OVERVIEW/ML_LOGGING/CALIBRATION/API_REST_SPEC).
2. **Trzymaj sie istniejacej architektury.**
   - Backend ODE: rozszerzaj tylko przez `core/ode_backends.py` + `SimulationConfig`, nie doklejaj ad-hoc backendow w innych miejscach.
   - ML: trzymaj nazwy kolumn zgodne z `logging/features.py` i `data/schema.py` oraz opisem w `docs/ML_LOGGING.md`.
   - ETL/SQL: nie mieszaj logiki konektorow z ETL – nowy backend implementuj jako `ProcessLogSource`.
3. **Nie psuj testow regresyjnych.**
   - `tests/test_core_simulation.py` i golden fixture `use_case_1` sa zrodlem prawdy dla core 0D.
   - Jezeli zmieniasz model/pipeline, dopisz nowe asercje, ale nie „podginaj” testow bez uzasadnienia w docs.
4. **ML i backendy specjalne sa opcjonalne.**
   - Kod musi dzialac z baza dependencji (bez `[ml]`, bez FASTAPI, bez SUNDIALS/JAX); brak extras = czytelny komunikat lub pominiecie funkcjonalnosci, nie crash.
5. **Release / CI.**
   - Zmiany w workflow (`.github/workflows`) traktuj jako osobne, male kroki – nie zmieniaj jednoczesnie wielu rzeczy wokol build/test/release.
6. **Dokumentuj ruchy pod TODO3.**
   - Wieksze zmiany w TODO3 powinny miec odzwierciedlenie w:
     - `README_VERS.md` (sekcja wersjonowania / checkpoint),
     - `docs/ROADMAP_TODO3.md` (stan segmentu),
     - oraz odpowiednim miejscu w `todo3.md` (oznaczenie zadania jako praktycznie zrealizowane lub z notatka, co zostalo).

## 5. Golden path dla reszty TODO3

Sugerowana kolejnosc dla kolejnego agenta:
1. **Pseudo-1D**: dopracowanie `core/simulation_1d.py` + testy regresyjne 1D.
2. **ML 2.0**: spięcie `train-ml` jako komendy Typer i rozbudowa raportow (metrics + wykresy).
3. **API**: dopelnienie `scripts/service_example.py` i ewentualne testy FastAPI (opcjonalne, w zaleznosci od srodowiska).
4. **Release**: dopracowanie CI/`ci.yml` i ewentualny upload na TestPyPI.
5. **Drift E2E**: pelny test pipeline logi -> ETL -> ML -> drift (wykorzystujac istniejace testy jako szablon).

Po zrealizowaniu powyzszych punktow TODO3 bedzie w praktyce gotowe do ogloszenia wersji 1.0.0 zgodnie z kryteriami z `README_VERS.md`.

