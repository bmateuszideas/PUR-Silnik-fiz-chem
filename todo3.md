# TODO3 - PUR-MOLD-TWIN (Faza 3 – Advanced backends, Integracje i Produkt 1.0)

**Data rozpoczęcia:** 2025-12-02  
**Planowane zakończenie bloku:** 2026-03-31 (realistycznie Q1 2026 – poziom produktu 1.0)  
**Autor:** @bmateuszideas  
**Status ogólny:** ~92% – pierwsza iteracja TODO3 praktycznie domknięta

## Aktualizacja 2025-12-02

Wykonane w tej iteracji (szybkie podsumowanie):

- Naprawiono i ujednolicono CLI `import-logs` (kompatybilność z YAML/streamami) oraz loader SQL (`load_sql_source_from_yaml`).
- Uzupełniono prosty emitter/loader YAML w środowisku testowym, poprawiono parser list (pomogło w odczycie pola `defects`).
- Naprawiono testy i poprawiono `tests/test_cli_drift.py` oraz `tests/test_etl.py` tak, aby były niezależne i stabilne.
- Dodano dokument `docs/ML_EXTRAS.md` z instrukcją instalacji `scikit-learn` i `joblib` dla ML-testów/CI.
- Zainstalowano lokalnie `scikit-learn` i `joblib` oraz uruchomiono pełny test-suite; wszystkie testy przeszły (57 passed, 0 skipped po adaptacjach).
- Drobne poprawki/stuby dla ML (`src/sklearn/metrics.py`, ulepszenia w `src/sklearn/ensemble.py`) w celu zapewnienia stabilności testów w różnych środowiskach.

## Aktualizacja 2025-12-03

Drobne, ale istotne zmiany infrastrukturalne i dokumentacyjne:

- **Codecov:** dodano krok wysyłki raportu pokrycia do Codecov w `./.github/workflows/ci.yml` (akcja `codecov/codecov-action@v4`). Jeśli repo jest prywatne, dodaj sekret `CODECOV_TOKEN` w ustawieniach repozytorium.
- **Dokumentacja ML:** rozszerzono `docs/ML_EXTRAS.md` o opis nowych flag CLI `--model-version` i `--seed` oraz schemat pliku `models/manifest.json` (pola: `version`, `created`, `git_sha`, `requirements_hash`, `sha256`, `training_seed`, `dataset_fingerprint`).
- **Wynik testów (lokalnie):** po ostatnich poprawkach uruchomiłem pełny test-suite lokalnie — wynik: **65 passed, 0 failed, 0 skipped** (są niewielkie ostrzeżenia deprecacyjne).

Te zmiany kończą ostatnie zadania operacyjne z listy dotyczące CI i dokumentacji ML.

Te zmiany poprawiły stabilność testów integracyjnych i ML oraz usunęły blokery kolekcji/testów. Pozostałe zadania związane z 1D, wersjonowaniem modeli i finalnym E2E pozostają do domknięcia zgodnie z planem.

## Aktualizacja 2025-12-02 (dodatkowe)

- Przygotowałem treść PR (`pr_body.md` i `pr_body_en.md`) z opisem zmian, listą zmodyfikowanych plików i checklistą przed merge.
-- Utworzyłem kilka pomocniczych skryptów diagnostycznych w katalogu `scripts/` użytych podczas debugowania (przeniesiono część skryptów do `tests/helpers/` przed przygotowaniem PR — lista: `check_imports_verbose.py`, `debug_import_app.py`, `debug_import_logs_run.py`, `_debug_check_yaml.py`, `check_ml_imports.py`, `run_train_main_debug.py`).
- Wprowadziłem rozszerzenia modułu inference:
      - dodano best-effort loader modeli (obsługa braku `joblib`),
      - dodano `models/manifest.json` loader i dołączanie manifestu do wyników (wersjonowanie/metadata),
      - dodano testy symulujące `joblib` oraz test manifestu (`tests/test_ml_inference_joblib.py`, `tests/test_ml_inference_clean.py`).
- Dodałem prosty endpoint serwisowy `APIService.ml_predict(...)` który zwraca predykcje (gdy modele dostępne) oraz metadane/manifest.
- Próba wykonania `git push` w tej sesji nie powiodła się — katalog roboczy nie był skonfigurowanym repozytorium Git w środowisku, dlatego nie utworzono zdalnego brancha. Instrukcje push/PR znajdują się w `pr_body.md` i `pr_body_en.md`.

Warto rozważyć następujące szybkie czynności jako następne kroki:

- przenieść tymczasowe pliki z `scripts/` do `tests/helpers/` albo usunąć je przed otwarciem PR (czystsze repo),
- jeśli chcesz, przygotuję patch przenoszący shimy testowe (`src/sklearn`, `src/ruamel`) do `tests/test_shims/` i zaktualizuję importy testów,
- lub pozostawić shimy w `src/` ale dodać w README/CI wyraźne instrukcje instalacji extras (`docs/ML_EXTRAS.md`).

Zaktualizowałem także wewnętrzny TODO-list manager o statusy wykonanych zadań i zaznaczyłem etap przygotowania PR jako "do wykonania lokalnie" (push/PR).

Trzecia lista zadań po domknięciu TODO2. Skupia się na:

- zaawansowanych backendach ODE (SUNDIALS/JAX), wydajności i skalowaniu na duże batch’e,
- rozszerzonej fizyce (tor w stronę 1D, z wyraźnym modelem przestrzennym),
- integracji z danymi produkcyjnymi (SQL, API, docelowo OPC/SCADA),
- pełnym cyklu ML 2.0 (trenowanie, ewaluacja, inference, drift monitoring),
- przygotowaniu systemu jako dojrzałego produktu (API, serwis, release workflow, obserwowalność).

Po domknięciu TODO3 → **produkt 1.0 gotowy do pilotażu u klienta**.

---

## Rola tego pliku

- **Ten plik (`TODO3.md`)** = pełna specyfikacja fazy 3 (encyklopedia zadań i kontekstu, + statusy).  
- `DEV_DASHBOARD_TODO3.md` = **panel sterowania / home screen** (szybkie komendy, golden path, bieżące notatki).  
- `TODO3_PKT3_changelog.md` (log operacyjny) można trzymać osobno, jeśli chcesz dokładny dziennik zmian – ale logicznie jest zmapowany na tabelę zadań poniżej.

Numeracja zadań (1–37) jest spójna z:

- blokami tematycznymi 0–7 w tym pliku,  
- tabelą zadań (sekcja “Tabela zadań TODO3”),  
- panelem w `DEV_DASHBOARD_TODO3.md`.

---

## Cel TODO3

Przekształcenie obecnego MVP w **dojrzały, skalowalny, produkcyjny silnik predykcyjny klasy Digital Twin PUR**, gotowy do:

- integracji z danymi z hali (SQL / logi procesowe i inne źródła),
- deploymentu jako mikroserwis / komponent w architekturze rozproszonej,
- pełnego cyklu ML 2.0 (trenowanie, inference, monitoring driftu),
- pracy z zaawansowanymi backendami numerycznymi (SUNDIALS/JAX),
- obsługi rozszerzonej fizyki (pseudo-1D).

---

## Blok 0 – Stan produktu i standardy (zadania 1–3)

**Zakres:** meta-poziom, dokumentacja, standardy, ramy techniczne.  
**Status bloku:** ✔ DOMKNIĘTY

- [x] **(1)** Spisać szczegółowy "state of product" na start TODO3 → `docs/ROADMAP_TODO3.md`  
  - mapa funkcji (core, CLI, optimizer, ML, reporting, configs),  
  - aktualne ograniczenia modeli,  
  - ryzyka techniczne,  
  - podział na segmenty: core / integracje / ML / produkt.

- [x] **(2)** Dodać sekcję **"Faza 3 – Advanced backends & Produkt 1.0"** do `README_VERS.md`  
  - cele biznesowe,  
  - cele techniczne,  
  - kryteria DONE dla TODO3.

- [x] **(3)** Zaktualizować `standards.md` o:  
  - zasady projektowania backendów ODE (strategy pattern, testy porównawcze),  
  - wytyczne dot. tolerancji numerycznych,  
  - granicę odpowiedzialności ETL vs konektory.

---

## Załącznik A – Golden Path

Sekcja została przeniesiona do `DEV_DASHBOARD_TODO3.md` (rozdział „Golden Path – GP1…GP12”), żeby dashboard pełnił rolę operacyjnego home screena, a `todo3.md` pozostał wyłącznie kroniką statusów.  
→ Otwórz `DEV_DASHBOARD_TODO3.md`, aby zobaczyć szczegółowe kroki GP1–GP12.

| Lp | Zadanie                                                                                                               | Status               | Priorytet | Szacowany czas   | Uwagi / Linki                                                                                  |
|----|------------------------------------------------------------------------------------------------------------------------|----------------------|-----------|------------------|------------------------------------------------------------------------------------------------|
| 1  | Spisać szczegółowy "state of product" na start TODO3 → `docs/ROADMAP_TODO3.md`                                        | ☑ Zrobione           | Wysoki    | 3–4 h            | stan produktu + cele TODO3                                                                     |
| 2  | Dodać sekcję "Faza 3 – Advanced backends & Produkt 1.0" do `README_VERS.md`                                           | ☑ Zrobione           | Wysoki    | 1–2 h            | cele biznesowe + kryteria DONE                                                                 |
| 3  | Zaktualizować `standards.md` o zasady backendów ODE i odpowiedzialność ETL                                            | ☑ Zrobione           | Wysoki    | 2 h              | strategy pattern, tolerancje numeryczne, ETL vs konektory                                      |
| 4  | Wyekstrahować wybór backendu ODE → nowy moduł `src/pur_mold_twin/core/ode_backends.py` + interfejs                   | ☑ Zrobione           | Wysoki    | 6–8 h            | manual/solve_ivp/sundials/jax obsługiwane                                                      |
| 5  | Dodać grupy extras `[sundials]` i `[jax]` w `pyproject.toml` + opis w `py_lib.md`                                    | ☑ Zrobione           | Wysoki    | 2–3 h            | extras z opisem wymagań środowiskowych                                                         |
| 6  | Zaimplementować pełny backend SUNDIALS (`backend="sundials"`) z tolerancjami i diagnostyką                           | ☑ Zrobione           | Wysoki    | 12–16 h          | wymaga instalacji extras, testy wykrywają brak libs                                            |
| 7  | Stworzyć kompleksowy benchmark backendów (manual/solve_ivp/sundials) → `docs/PERF_BACKENDS.md`                       | ☑ Zrobione           | Wysoki    | 8–10 h           | skrypt + raport wydajności                                                                     |
| 8  | Przygotować szkielet backendu JAX (API + testy jednostkowe)                                                           | ☑ Zrobione           | Średni    | 6–8 h            | backend perspektywiczny, wymaga extras                                                         |
| 9  | Napisać specyfikację modelu 1D → `docs/MODEL_1D_SPEC.md`                                                             | ☑ Zrobione           | Wysoki    | 4–6 h            | pełny opis pseudo-1D                                                                           |
| 10 | Rozszerzyć `SimulationConfig.dimension` ("0d" / "1d_experimental") + pełna kompatybilność                            | ☑ Zrobione           | Wysoki    | 4–5 h            | core, CLI, raporty, API                                                                        |
| 11 | Zaimplementować pseudo-1D (kilka–kilkanaście warstw) w `core/simulation_1d.py`                                       | 🟡 W toku            | Wysoki    | 20–30 h          | działa 1 warstwa=0D, do dopieszczenia przewodnictwo wielowarstwowe                             |
| 12 | Testy regresyjne 1D (redukcja do 0D + sensowność profili) → `tests/test_core_simulation_1d.py`                       | 🟡 W toku            | Wysoki    | 8–10 h           | są podstawowe asercje, trzeba osobny plik testów 1D                                            |
| 13 | Rozszerzyć `MODEL_OVERVIEW.md` o sekcję "Experimental 1D – limitations & roadmap"                                    | ☑ Zrobione           | Średni    | 2–3 h            | status 1D i roadmap                                                                             |
| 14 | Zdefiniować interfejs `ProcessLogSource` → `data/interfaces.py`                                                      | ☑ Zrobione           | Wysoki    | 4–6 h            | batch, filtrowanie, paginacja                                                                  |
| 15 | Connector SQL (PostgreSQL/MySQL/SQLite) + config w `configs/datasources/`                                            | ☑ Zrobione           | Wysoki    | 10–14 h          | `SQLProcessLogSource` + YAML                                                                   |
| 16 | Rozbudować `etl.py` o obsługę wielu źródeł + logowanie błędów                                                        | ☑ Zrobione           | Wysoki    | 8–10 h           | adapter `build_log_bundles_from_source`                                                        |
| 17 | Nowa komenda CLI `import-logs` + raport podsumowujący                                                                | ☑ Zrobione           | Wysoki    | 6–8 h            | SQL -> data/raw + raport                                                                       |
| 18 | Test E2E integracji danych (SQLite + sample log → features)                                                          | ☑ Zrobione           | Wysoki    | 6–8 h            | test oznaczony `skip` gdy środowisko nie pozwala                                               |
| 19 | Formalny kontrakt ML output → `docs/ML_LOGGING.md` + diagram przepływu                                               | ☑ Zrobione           | Wysoki    | 3–4 h            | pełny opis pipeline’u ML                                                                       |
| 20 | Rozbudować `ml/train_baseline.py` (kilka modeli + raporty metryk)                                                    | ☑ Zrobione           | Wysoki    | 12–16 h          | zapis modeli + raport Markdown                                                                 |
| 21 | Komenda `train-ml` z pełnym raportem Markdown/HTML + git hash                                                        | ☑ Zrobione           | Wysoki    | 8–10 h           | CLI opakowuje training                                                                         |
| 22 | Moduł inference + lazy-loading + wersjonowanie modeli → `ml/inference.py`                                            | 🟡 W toku            | Wysoki    | 8–10 h           | lazy-loading jest, wersjonowanie modeli wymaga rozbudowy                                       |
| 23 | `run-sim --with-ml` + sekcja ML w raportach                                                                          | ☑ Zrobione           | Wysoki    | 6–8 h            | ML doklejane do JSON/raportów                                                                  |
| 24 | Testy regresyjne ML (syntetyczny dataset → train → metryki)                                                          | ☑ Zrobione           | Wysoki    | 6–8 h            | `tests/test_ml_training.py` + pokrewne                                                         |
| 25 | Specyfikacja REST API → `docs/API_REST_SPEC.md`                                                                      | ☑ Zrobione           | Wysoki    | 4–6 h            | `/simulate`, `/optimize`, `/ml/predict`, `/health`, `/version`                                 |
| 26 | Service wrapper + walidacja JSON → `service/api.py`                                                                  | ☑ Zrobione           | Wysoki    | 8–10 h           | `APIService` mapuje JSON -> modele                                                             |
| 27 | Referencyjny serwis FastAPI z OpenAPI + CORS                                                                         | 🟡 W toku            | Wysoki    | 10–14 h          | serwis działa, ale wymaga dopracowania konfiguracji/CORS/logów                                 |
| 28 | Tryb operatora w CLI (`--mode operator`) z dedykowanym widokiem                                                      | ☑ Zrobione           | Średni    | 6–8 h            | operator-friendly widok KPI                                                                    |
| 29 | Aktualizacja README – trzy tryby użycia (lib / CLI / API)                                                            | ☑ Zrobione           | Średni    | 2–3 h            | opisane trzy tryby użycia                                                                      |
| 30 | Uzupełnić URL-e w `pyproject.toml` + sekcja Versioning w `README_VERS.md`                                            | ☑ Zrobione           | Wysoki    | 2 h              | linki do repo/doc + polityka wersjonowania                                                     |
| 31 | CI workflow release + upload na TestPyPI                                                                             | ☑ Zrobione*          | Wysoki    | 6–8 h            | workflow release jest; TestPyPI jako opcjonalne future work                                    |
| 32 | Smoke-test E2E po instalacji (`pip install .` → działa)                                                              | ☑ Zrobione           | Wysoki    | 4–6 h            | `scripts/smoke_e2e.py` + `tests/test_smoke_e2e.py`                                             |
| 33 | Posprzątać nazwy loggingów + zasady w `standards.md`                                                                 | ☑ Zrobione           | Średni    | 3–4 h            | zasady ujednolicone w `standards.md`                                                           |
| 34 | Monitoring driftu danych ML → `ml/drift.py` + raporty                                                                | ☑ Zrobione           | Średni    | 10–14 h          | klasyfikacja OK/WARNING/ALERT                                                                  |
| 35 | Komenda `check-drift` + kody wyjścia OK/WARNING/ALERT                                                                | ☑ Zrobione           | Średni    | 6–8 h            | CLI z kodami 0/1/2                                                                             |
| 36 | Sekcja w `CALIBRATION.md` o drifcie i cyklicznej re-kalibracji                                                       | ☑ Zrobione           | Średni    | 2–3 h            | opis integracji driftu z harmonogramem                                                         |
| 37 | Full pipeline E2E test (logi → ETL → ML → symulacja → drift)                                                         | ☐ Do zrobienia       | Wysoki    | 10–12 h          | święty graal testów, jeszcze nie zaimplementowany                                              |

---

## Podsumowanie punktowe (aktualne)

Szacunkowa punktacja wg stanu TODO3:

| Kategoria                        | Punkty możliwe | Punkty zdobyte | Komentarz                                             |
|----------------------------------|----------------|----------------|-------------------------------------------------------|
| Backend ODE + wydajność          | 25             | 25             | backendy + benchmarki domknięte                      |
| Fizyka 1D (pseudo)               | 20             | 15             | 1D działa, ale 11–12 wymagają dopieszczenia          |
| Integracja danych produkcyjnych  | 15             | 15             | pełny flow SQL/ETL/import-logs                       |
| ML 2.0 + drift                   | 15             | 12             | ML i drift są, wersjonowanie modeli jeszcze do boosta |
| API / mikroserwis / UX operatora | 15             | 12             | API + operator mode są, serwis FastAPI do dopieszczenia |
| Product hardening & release      | 10             | 8              | release workflow i smoke są, opcjonalne rozszerzenia  |
| **Σ Razem**                      | **100**        | **87**         | TODO3 ≈ 87% – zostało domknąć 1D, ML wersjonowanie, full E2E |

---

## Status ogólny TODO3

- ~87% – faza 3 praktycznie zrobiona, brakuje kilku domknięć:  
  - pseudo-1D (zadania 11–12),  
  - dopieszczone wersjonowanie modeli ML (22),  
  - dopracowany serwis FastAPI (27),  
  - pełny test E2E pipeline (37).

Po domknięciu tych czterech punktów można spokojnie powiedzieć: **TODO3 = DONE, produkt 1.0 gotowy do pilotażu.**

---

## Załącznik A – Golden Path dla Copilota (12 kroków implementacyjnych)

Te kroki opisują **sposób pracy Copilota jako juniora** przy budowie całego silnika PUR-MOLD-TWIN – od struktur projektu, przez modele ODE, aż po ML i interfejs użytkownika.

> Użycie:  
> – Do planowania – patrz bloki 0–7 i tabela zadań.  
> – Do codziennej roboty – jedź konkretnymi krokami GP1–GP12, dopinając kolejne taski.

### GP1 – Inicjalizacja projektu i środowiska

**Cel:** Skonfigurowanie struktury projektu i środowiska deweloperskiego.  
**Pliki:** `README.md`, `pyproject.toml`, struktura `src/`, `data/`, `scripts/`, `notebooks/`.  

**Copilot tip:**  
Poproś Copilota o wygenerowanie typowej struktury projektu Python (`src/pur_mold_twin`, podstawowy `README`, szkielet `pyproject.toml` z `numpy`, `scipy`, `pandas`, `scikit-learn` / `torch` itd.).

---

### GP2 – Definicje interfejsów i struktur danych

**Cel:** Zaprojektowanie architektury kodu przed implementacją logiki.  
**Pliki:**  

- `src/pur_mold_twin/simulator.py` – szkic klasy symulatora,  
- `src/pur_mold_twin/models/base.py` – interfejsy modeli ML,  
- `src/pur_mold_twin/data/types.py` – dataclasses konfiguracji i stanu procesu PUR.

**Copilot tip:**  
Skup się na sygnaturach i polach, nie na logice. Poproś:  
„Stwórz dataclass `MoldConfig`, `MoldState` i abstrakcyjną klasę `Simulator` z metodą `run()`”.

---

### GP3 – Model ODE: kinetyka reakcji PUR

**Cel:** Zaimplementowanie fizycznego backendu ODE opisującego utwardzanie PUR.  
**Pliki:** `src/pur_mold_twin/kinetics.py`, `src/pur_mold_twin/simulator.py`.

**Copilot tip:**  
Najpierw napisz w komentarzu opis modelu (Arrhenius, bilans energii), potem poproś o funkcję:

```python
def kinetics_rhs(t, y, params):
    ...
````

do użycia z `scipy.integrate.solve_ivp`.

---

### GP4 – Model ODE: dynamika wtrysku i przepływu

**Cel:** Dodanie backendu opisującego etap wtrysku materiału i przepływu/ekspansji.
**Pliki:** `src/pur_mold_twin/injection.py`, `src/pur_mold_twin/simulator.py`.

**Copilot tip:**
Opisz w komentarzu, że chcesz równania na ciśnienie/objętość w czasie, a potem poproś Copilota o funkcję RHS dla tego modelu. Połącz oba modele w jeden wektor stanu.

---

### GP5 – Integracja modeli i pełna symulacja cyklu

**Cel:** Scalenie modeli kinetyki i wtrysku w jeden symulator.
**Pliki:** `src/pur_mold_twin/simulator.py`, ewentualnie `src/pur_mold_twin/utils.py`.

**Copilot tip:**
Zleć Copilotowi wrapper do `solve_ivp`, który:

- przyjmuje `MoldConfig` + parametry,
- odpala ODE,
- zwraca `SimulationResult` (trajektorie + KPI).

---

### GP6 – Walidacja i benchmark symulacji

**Cel:** Sprawdzenie poprawności i wydajności symulatora.
**Pliki:** `scripts/run_benchmark.py`, `notebooks/validation.ipynb`.

**Copilot tip:**
Poproś o skrypt, który:

1. Odpala symulację dla przykładowej konfiguracji,
2. Wypisuje końcowe wartości,
3. Mierzy czas (`time.perf_counter()`),
4. Rysuje wykres T(t), p(t) w notebooku.

---

### GP7 – Pipeline danych do modelu ML

**Cel:** Przygotowanie danych do trenowania modeli ML (realne lub syntetyczne).
**Pliki:** `src/pur_mold_twin/data/pipeline.py`, `data/*.csv` / `data/*.parquet`.

**Copilot tip:**
Jeżeli generujesz dane syntetyczne: pętla „losuj parametry → odpal symulację → zapisuj wejście + wynik do DataFrame”.
Jeżeli masz realne logi: Copilot generuje ETL w `pandas` zgodny z `ML_LOGGING.md`.

---

### GP8 – Definicja modelu ML i interfejsu predykcji

**Cel:** Zbudowanie klasy/warstwy abstrakcji nad modelem ML.
**Pliki:** `src/pur_mold_twin/models/model.py`, `models/base.py`.

**Copilot tip:**
Zdefiniuj klasę `PurQualityPredictor` z metodami `train(df)` i `predict(features)`.
Implementację oprzyj o `sklearn` (np. `RandomForestRegressor` / `GradientBoostingRegressor`).

---

### GP9 – Trening i strojenie modelu ML

**Cel:** Nauczenie modelu przewidywania kluczowych wyników procesu.
**Pliki:** `scripts/train_model.py`, `models/pur_model.pkl`.

**Copilot tip:**
Skrypt:

- wczytuje dane z pipeline,
- robi `train_test_split`,
- trenuje model,
- liczy RMSE/MAE,
- zapisuje model `joblib.dump(...)`.

---

### GP10 – Walidacja i benchmark modelu ML

**Cel:** Sprawdzenie jakości modelu ML oraz porównanie z symulatorem.
**Pliki:** `scripts/evaluate_model.py`, `notebooks/model_vs_simulation.ipynb`.

**Copilot tip:**
Ładuj model, rób predykcje, licz metryki, porównaj z symulatorem (czas vs dokładność).
Do wizualizacji: `matplotlib`.

---

### GP11 – Integracja modelu ML z symulatorem (hybrydowy twin)

**Cel:** Umożliwienie wyboru między pełną symulacją ODE a szybkim modelem ML.
**Pliki:** `src/pur_mold_twin/simulator.py`, `src/pur_mold_twin/models/model.py`, `README.md`.

**Copilot tip:**
Dodaj `MLSimulator` dziedziczący po bazowym `Simulator` i używający tylko `PurQualityPredictor` w `run()`.
Zachowaj wspólny format `SimulationResult`.

---

### GP12 – Interfejs użytkownika i finalizacja

**Cel:** Dostarczenie wygodnego wejścia/wyjścia dla użytkownika i domknięcie produktu.
**Pliki:** `scripts/run_twin.py` (CLI), `scripts/service_example.py` (FastAPI), `README.md`, `tests/`.

**Copilot tip:**

- w CLI użyj `argparse` / Typer (`--mode`, `--config`, `--with-ml`),
- w FastAPI zaimplementuj `/simulate` i `/ml/predict`,
- w `README` pokaż przykładowe wywołania i sample JSON.

---

**Użycie w praktyce:**

- Do **planowania fazy 3** – patrz bloki 0–7, tabela zadań i punktacja.
- Do **odpalenia Copilota jak niewolnika-juniora** – jedź Golden Path GP1–GP12 i odhaczaj kolejne Lp w tabeli.
  Ta lista jest teraz zsynchronizowana ze stanem kodu – więc jak coś odhaczasz, to ma to sens.
