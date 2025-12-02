```markdown
# TODO3 - PUR-MOLD-TWIN (Faza 3 – Advanced backends, Integracje i Produkt 1.0)

**Data rozpoczęcia:** 2025-12-02  
**Planowane zakończenie bloku:** 2026-03-31 (realistycznie Q1 2026 – poziom produktu 1.0)  
**Autor:** @bmateuszideas  
**Status ogólny:** 0% – start fazy 3

Trzecia lista zadań po domknięciu TODO2. Skupia się na:
- zaawansowanych backendach ODE (SUNDIALS/JAX), wydajności i skalowaniu na duże batch’e,
- rozszerzonej fizyce (tor w stronę 1D, z wyraźnym modelem przestrzennym),
- integracji z danymi produkcyjnymi (SQL, API, docelowo OPC/SCADA),
- pełnym cyklu ML 2.0 (trenowanie, ewaluacja, inference, drift monitoring),
- przygotowaniu systemu jako dojrzałego produktu (API, serwis, release workflow, obserwowalność). 

Po domknięciu TODO3 → **produkt 1.0 gotowy do pilotażu u klienta**. :contentReference[oaicite:1]{index=1}

---

## Rola tego pliku

- **Ten plik (`TODO3.md`)** = pełna specyfikacja fazy 3 (encyklopedia zadań i kontekstu).
- `DEV_DASHBOARD_TODO3.md` = **panel sterowania / home screen** (szybkie komendy, bloki 0–7, golden path).
- `TODO3_PKT3_changelog.md` (log operacyjny) zostało wchłonięte koncepcyjnie w sekcję **“Tabela zadań TODO3 (operacyjna)”** poniżej – ale można też trzymać go jako osobny plik logu, jeśli wygodniej. 

Numeracja zadań (1–37) jest spójna z:
- tabelą zadań (sekcja “Tabela zadań TODO3”),
- blokami tematycznymi 0–7 w tym pliku,
- panelowym widokiem w `DEV_DASHBOARD_TODO3.md`. :contentReference[oaicite:3]{index=3}

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

**Zakres:** meta-poziom, dokumentacja, standardy, ramy techniczne. :contentReference[oaicite:5]{index=5}

- **(1)** Spisać szczegółowy "state of product" na start TODO3 → `docs/ROADMAP_TODO3.md`  
  - mapa funkcji (core, CLI, optimizer, ML, reporting, configs),  
  - aktualne ograniczenia modeli (0D, brak 1D, brak części integracji),  
  - ryzyka techniczne (wydajność, brak backendów, brak E2E pipeline pod ML + drift),  
  - podział na segmenty: core / integracje / ML / produkt.

- **(2)** Dodać sekcję **"Faza 3 – Advanced backends & Produkt 1.0"** do `README_VERS.md`  
  - cele biznesowe (co to daje klientowi / technologicznemu użytkownikowi),  
  - cele techniczne (backendy, 1D, integracje, ML, API, release),  
  - kryteria DONE dla TODO3 (kiedy mówimy "produkt 1.0").

- **(3)** Zaktualizować `standards.md` o:
  - zasady projektowania backendów ODE (strategy pattern, separacja, testy porównawcze),  
  - wytyczne dot. tolerancji numerycznych i jakości wyników,  
  - granicę odpowiedzialności ETL vs konektory (co jest “źródłem danych”, co jest “transformacją”).

---

## Blok 1 – Backend ODE + SUNDIALS + JAX + benchmarki (zadania 4–8)

**Zakres:** modularne backendy ODE, alternatywne solvery, wydajność. 

  - zdefiniować spójny interfejs np. `integrate_system(ctx, config) -> Trajectory`,  
  - odpiąć bezpośrednią logikę backendów z `core/simulation.py` i przekierować przez `ode_backends`,  
  - udokumentować architekturę backendów w `docs/MODEL_OVERVIEW.md`.

- **(5)** Dodać grupy extras `[sundials]` i `[jax]` w `pyproject.toml` + opis w `py_lib.md`  
- **(11)** Zaimplementować pseudo-1D w `core/simulation_1d.py`  
  - kilka–kilkanaście warstw w grubości formy,  
  - przewodnictwo między warstwami oraz wymiana z formą,  
  - konfiguracja liczby warstw, parametrów materiałowych, warunków brzegowych,  
  - integracja z głównym `simulate()` przez wybór backendu 0D/1D.

- **(12)** Dodać testy regresyjne 1D → `tests/test_core_simulation_1d.py`  
  - case z jedną warstwą → redukcja do 0D (porównanie profili, tolerancje),  
  - case z wieloma warstwami → sanity check profili T/alpha/rho (monotoniczność, zakres, brak artefaktów).

- **(13)** Rozszerzyć `docs/MODEL_OVERVIEW.md` o sekcję  
  **"Experimental 1D – limitations & roadmap"**  
  - co 1D umie, czego jeszcze nie,  
  - w jakich przypadkach można 1D używać, a w jakich nie,  
  - plan dalszego rozwoju (bardziej dokładne 1D / ewentualnie 2D/3D).

---

## Blok 3 – Integracja z logami z hali (SQL, ETL, import-logs) (zadania 14–18)

**Zakres:** zasilanie systemu realnymi danymi, nie tylko lokalnymi plikami. 

- **(14)** Zdefiniować interfejs `ProcessLogSource` → `data/interfaces.py`  
  - metody: `fetch_shots(query)`, filtrowanie po czasie, formie, systemie, statusie jakości,  
  - wsparcie dla paginacji / batchy,  
  - neutralny interfejs, który można podpiąć do różnych backendów (SQL, pliki, API).

- **(15)** Connector SQL (PostgreSQL/MySQL) → `src/pur_mold_twin/data/sql_source.py`  
  - konfiguracja w `configs/datasources/*.yaml`,  
  - bezpieczne połączenia (hasła, connection pooling),  
  - mapowanie tabel/kolumn na struktury `LogBundle` i procesowe parametry wejściowe.

- **(16)** Rozbudować `data/etl.py`  
  - obsługa wielu źródeł (lokalne pliki, SQL, w przyszłości API),  
  - budowa `ProcessConditions` + metadanych bezpośrednio z `ProcessLogSource`,  
  - rozbudowane logowanie błędów i ostrzeżeń (braki, niespójności, dziwne wartości).

- **(17)** Nowa komenda CLI `import-logs`  
  - przyjmuje ID/konfig źródła danych, zakres czasu, filtry,  
  - zapisuje ustandaryzowane logi w `data/raw/...`,  
  - generuje raport podsumowujący (liczba rekordów, zakres dat, formy/systemy).

- **(18)** Test E2E integracji danych → `tests/test_data_integration.py`  
  - sztuczna baza (SQLite),  
  - wgrany sample log,  
  - przebieg: `import-logs` → `build-features`,  
  - asercje na spójność datasetu, poprawność mapowania, brak crashy.

---

## Blok 4 – ML 2.0: train-ml, inference, run-sim --with-ml (zadania 19–24)

**Zakres:** pełen cykl ML – trenowanie, inference, integracja z raportami. 

- **(19)** Formalny kontrakt ML output → `docs/ML_LOGGING.md`  
  - jakie kolumny wejściowe (features),  
  - jakie pola wyjściowe (np. `defect_risk_pred`, `defect_class_pred`, modele czasu/cyklu),  
  - typy danych, standardy nazw,  
  - diagram: ETL → features → train → save model → inference → raport.

- **(20)** Rozbudować `ml/train_baseline.py`  
  - wczytywanie danych (parquet/CSV) + konfiguracja z YAML,  
  - trenowanie kilku modeli (regresja ryzyka, klasyfikacja defektu, ewentualnie czas cyklu),  
  - zapis modeli do `models/*.pkl`,  
  - generowanie raportu metryk (Markdown/HTML, wykresy ROC/PR) do `reports/ml/`.

- **(21)** Komenda CLI `train-ml`  
  - zarządza konfiguracją runów (ścieżki, modele, parametry),  
  - odpala pipeline trenowania,  
  - zapisuje raport z metrykami + metadata (data, wersja, git hash),  
  - spina się z outputem features.

- **(22)** Moduł inference → `src/pur_mold_twin/ml/inference.py`  
  - funkcja `attach_ml_predictions(sim_result, features)`,  
  - lazy-loading modeli (ładowanie przy pierwszym użyciu, cache),  
  - wersjonowanie modeli w metadanych.

- **(23)** `run-sim --with-ml` + integracja z raportami  
  - CLI flaga `--with-ml`,  
  - dołączanie predykcji ML (ryzyko, klasa defektu) do `SimulationResult`,  
  - sekcja “ML predictions” w raportach (opis, confidence, wersja modelu).

- **(24)** Testy regresyjne ML → `tests/test_ml_training.py`  
  - syntetyczny dataset,  
  - pełny run `train-ml`,  
  - asercje: pliki modeli, raport metryk, sensowne wartości.

---

## Blok 5 – API / mikroserwis / tryb operatora (zadania 25–29)

**Zakres:** wystawienie silnika na zewnątrz + lepszy UX CLI. 

- **(25)** Specyfikacja REST API → `docs/API_REST_SPEC.md`  
  - endpointy: `/simulate`, `/optimize`, `/ml/predict`, `/health`, `/version`,  
  - schematy JSON wejścia/wyjścia,  
  - format błędów, wersjonowanie API, przykłady request/response.

- **(26)** Service wrapper + walidacja JSON → `src/pur_mold_twin/service/api.py`  
  - funkcje przyjmujące surowy JSON i zamieniające go na struktury domenowe,  
  - funkcje zwracające JSON spójny z API spec,  
  - pełna walidacja wejść/wyjść.

- **(27)** Referencyjny serwis FastAPI (lub Flask) → `scripts/service_example.py`  
  - implementujący API z `API_REST_SPEC.md`,  
  - z OpenAPI/Swagger, CORS, logowaniem,  
  - z osobnym modułem konfiguracji (port, log level itd.),  
  - z opisem uruchomienia w `docs/API_REST_SPEC.md`.

- **(28)** Tryb operatora w CLI (`--mode operator`)  
  - uproszczony, czytelny widok KPI dla operatora,  
  - mniej parametrów inżynierskich na wierzchu,  
  - standaryzowany zapis raportów w uzgodnionej strukturze katalogów.

- **(29)** Aktualizacja `README.md`  
  - opis trzech trybów użycia systemu:  
    - biblioteka Python,  
    - CLI (dev + operator),  
    - REST API / serwis referencyjny.

---

## Blok 6 – Release, CI, smoke from-install (zadania 30–33)

**Zakres:** produktowość, wersjonowanie, release pipeline. 

- **(30)** Uzupełnić realne URL-e w `pyproject.toml` + sekcja "Versioning & releases" w `README_VERS.md`  
  - `homepage`, `repository`, `documentation`,  
  - polityka wersjonowania (0.3.x = TODO3, 1.0.0 = pierwszy produkcyjny rollout).

- **(31)** CI workflow release + upload na TestPyPI → `.github/workflows/release.yml`  
  - trigger na tag,  
  - build wheel/sdist,  
  - test “from install”,  
  - opcjonalny upload do TestPyPI / internal index,  
  - artefakty: logi testów, benchmarki.

- **(32)** Smoke-test E2E po instalacji → `scripts/smoke_e2e.py` + `tests/test_smoke_e2e.py`  
  - scenariusz: `pip install .` / instalacja z wheel,  
  - odpalenie `pur-mold-twin run-sim` na `use_case_1`,  
  - sprawdzenie raportu i wyników (czy są, czy sensowne).

- **(33)** Posprzątać nazwy loggingów + zasady w `standards.md`  
  - rozwiązać konflikt `logging` vs `utils.logging`,  
  - zaktualizować importy,  
  - dopisać reguły nazewnicze w `standards.md`.

---

## Blok 7 – Drift, observability, full pipeline E2E (zadania 34–37)

**Zakres:** długoterminowa jakość, monitoring, pełny end-to-end. 

- **(34)** Monitoring driftu danych ML → `src/pur_mold_twin/ml/drift.py`  
  - porównanie rozkładów featur (statystyki, testy, wykresy),  
  - generowanie raportów driftu (Markdown/HTML) do `reports/drift/`,  
  - API gotowe do cyklicznego odpalania (np. cron/CI).

- **(35)** Komenda `check-drift`  
  - CLI, które bierze referencyjny i bieżący dataset features,  
  - generuje raport driftu,  
  - wychodzi kodem OK/WARNING/ALERT w zależności od progu.

- **(36)** Sekcja w `CALIBRATION.md` o drifcie i cyklicznej re-kalibracji  
  - jak czytać raporty driftu,  
  - kiedy robić re-kalibrację modelu fiz-chem i ML,  
  - jak to wpisać w harmonogram (np. tygodniowy/miesięczny rytm).

- **(37)** Full pipeline E2E test → `tests/test_full_pipeline_e2e.py`  
  - syntetyczne logi → ETL → features → train-ml → run-sim `--with-ml` → check-drift,  
  - asercje na spójność plików, metryk, struktur danych,  
  - “święty graal” testów – gwarancja, że cały produktowy flow działa od wejścia do raportu.

---

## Tabela zadań TODO3 (operacyjna)

Poniższa tabela jest operacyjnym widokiem TODO3 (1 wiersz = 1 task w jednym cyklu Copilota). To jest logiczne zmergowanie treści z changeloga z pełną specyfikacją powyżej. 

| Lp | Zadanie                                                                                                               | Status           | Priorytet | Szacowany czas   | Uwagi / Linki                                                                                  |
|----|------------------------------------------------------------------------------------------------------------------------|------------------|-----------|------------------|------------------------------------------------------------------------------------------------|
| 1  | Spisać szczegółowy "state of product" na start TODO3 → `docs/ROADMAP_TODO3.md`                                        | ☐ Nie rozpoczęte | Wysoki    | 3–4 h            | mapa funkcji, ograniczenia, ryzyka techniczne, podział core/integracje/ML/produkt             |
| 2  | Dodać sekcję "Faza 3 – Advanced backends & Produkt 1.0" do `README_VERS.md`                                            | ☐ Nie rozpoczęte | Wysoki    | 1–2 h            | cele biznesowe + kryteria DONE                                                                 |
| 3  | Zaktualizować `standards.md` o zasady backendów ODE i odpowiedzialność ETL                                            | ☐ Nie rozpoczęte | Wysoki    | 2 h              | strategy pattern, tolerancje numeryczne, granice ETL vs konektory                              |
| 4  | Wyekstrahować wybór backendu ODE → nowy moduł `src/pur_mold_twin/core/ode_backends.py` + interfejs                    | ☐ Nie rozpoczęte | Wysoki    | 6–8 h            | jasny interfejs `integrate_system(...)`                                                        |
| 5  | Dodać grupy extras `[sundials]` i `[jax]` w `pyproject.toml` + opis w `py_lib.md`                                     | ☐ Nie rozpoczęte | Wysoki    | 2–3 h            | z ograniczeniami i przypadkami użycia                                                          |
| 6  | Zaimplementować pełny backend SUNDIALS (`backend="sundials"`) z tolerancjami i diagnostyką                            | ☐ Nie rozpoczęte | Wysoki    | 12–16 h          | scikits.odes lub scikit-sundae                                                                 |
| 7  | Stworzyć kompleksowy benchmark backendów (manual/solve_ivp/sundials) → `docs/PERF_BACKENDS.md`                        | ☐ Nie rozpoczęte | Wysoki    | 8–10 h           | czas + dokładność + wykresy                                                                    |
| 8  | Przygotować szkielet backendu JAX (API + testy jednostkowe, bez pełnej implementacji)                                 | ☐ Nie rozpoczęte | Średni    | 6–8 h            | zachowujemy miejsce na przyszłość                                                              |
| 9  | Napisać specyfikację modelu 1D → `docs/MODEL_1D_SPEC.md`                                                              | ☐ Nie rozpoczęte | Wysoki    | 4–6 h            | T(x,t), alpha(x,t), rho(x,t), venty, warunki brzegowe                                          |
| 10 | Rozszerzyć `SimulationConfig.dimension` ("0D" / "1D_experimental") + pełna kompatybilność                             | ☐ Nie rozpoczęte | Wysoki    | 4–5 h            | CLI, raporty, API                                                                              |
| 11 | Zaimplementować pseudo-1D (kilka–kilkanaście warstw) w `core/simulation_1d.py`                                        | ☐ Nie rozpoczęte | Wysoki    | 20–30 h          | przewodnictwo między warstwami, konfiguracja liczby warstw                                     |
| 12 | Testy regresyjne 1D (redukcja do 0D + sensowność profili) → `tests/test_core_simulation_1d.py`                        | ☐ Nie rozpoczęte | Wysoki    | 8–10 h           |                                                                                                |
| 13 | Rozszerzyć `MODEL_OVERVIEW.md` o sekcję "Experimental 1D – limitations & roadmap"                                     | ☐ Nie rozpoczęte | Średni    | 2–3 h            |                                                                                                |
| 14 | Zdefiniować interfejs `ProcessLogSource` → `data/interfaces.py`                                                       | ☐ Nie rozpoczęte | Wysoki    | 4–6 h            | batch, filtrowanie, paginacja                                                                  |
| 15 | Connector SQL (PostgreSQL/MySQL) + config w `configs/datasources/`                                                    | ☐ Nie rozpoczęte | Wysoki    | 10–14 h          | bezpieczne połączenie, mapowanie tabel                                                         |
| 16 | Rozbudować `etl.py` o obsługę wielu źródeł + logowanie błędów                                                         | ☐ Nie rozpoczęte | Wysoki    | 8–10 h           |                                                                                                |
| 17 | Nowa komenda CLI `import-logs` + raport podsumowujący                                                                 | ☐ Nie rozpoczęte | Wysoki    | 6–8 h            |                                                                                                |
| 18 | Test E2E integracji danych (SQLite + sample log → features)                                                           | ☐ Nie rozpoczęte | Wysoki    | 6–8 h            |                                                                                                |
| 19 | Formalny kontrakt ML output → `docs/ML_LOGGING.md` + diagram przepływu                                                | ☐ Nie rozpoczęte | Wysoki    | 3–4 h            |                                                                                                |
| 20 | Rozbudować `ml/train_baseline.py` (kilka modeli + raporty metryk)                                                     | ☐ Nie rozpoczęte | Wysoki    | 12–16 h          |                                                                                                |
| 21 | Komenda `train-ml` z pełnym raportem Markdown/HTML + git hash                                                         | ☐ Nie rozpoczęte | Wysoki    | 8–10 h           |                                                                                                |
| 22 | Moduł inference + lazy-loading + wersjonowanie modeli → `ml/inference.py`                                             | ☐ Nie rozpoczęte | Wysoki    | 8–10 h           |                                                                                                |
| 23 | `run-sim --with-ml` + sekcja ML w raportach                                                                           | ☐ Nie rozpoczęte | Wysoki    | 6–8 h            |                                                                                                |
| 24 | Testy regresyjne ML (syntetyczny dataset → train → metryki)                                                           | ☐ Nie rozpoczęte | Wysoki    | 6–8 h            |                                                                                                |
| 25 | Specyfikacja REST API → `docs/API_REST_SPEC.md`                                                                       | ☐ Nie rozpoczęte | Wysoki    | 4–6 h            | /simulate, /optimize, /ml/predict, /health                                                     |
| 26 | Service wrapper + walidacja JSON → `service/api.py`                                                                   | ☐ Nie rozpoczęte | Wysoki    | 8–10 h           |                                                                                                |
| 27 | Referencyjny serwis FastAPI z OpenAPI + CORS                                                                          | ☐ Nie rozpoczęte | Wysoki    | 10–14 h          | `scripts/service_example.py`                                                                   |
| 28 | Tryb operatora w CLI (`--mode operator`) z dedykowanym widokiem                                                       | ☐ Nie rozpoczęte | Średni    | 6–8 h            |                                                                                                |
| 29 | Aktualizacja README – trzy tryby użycia (lib / CLI / API)                                                             | ☐ Nie rozpoczęte | Średni    | 2–3 h            |                                                                                                |
| 30 | Uzupełnić URL-e w `pyproject.toml` + sekcja Versioning w `README_VERS.md`                                             | ☐ Nie rozpoczęte | Wysoki    | 2 h              |                                                                                                |
| 31 | CI workflow release + upload na TestPyPI                                                                              | ☐ Nie rozpoczęte | Wysoki    | 6–8 h            | `.github/workflows/release.yml`                                                                |
| 32 | Smoke-test E2E po instalacji (`pip install .` → działa)                                                               | ☐ Nie rozpoczęte | Wysoki    | 4–6 h            |                                                                                                |
| 33 | Posprzątać nazwy loggingów + zasady w `standards.md`                                                                  | ☐ Nie rozpoczęte | Średni    | 3–4 h            |                                                                                                |
| 34 | Monitoring driftu danych ML → `ml/drift.py` + raporty                                                                 | ☐ Nie rozpoczęte | Średni    | 10–14 h          | testy statystyczne, wykresy                                                                    |
| 35 | Komenda `check-drift` + kody wyjścia OK/WARNING/ALERT                                                                 | ☐ Nie rozpoczęte | Średni    | 6–8 h            |                                                                                                |
| 36 | Sekcja w `CALIBRATION.md` o drifcie i cyklicznej re-kalibracji                                                        | ☐ Nie rozpoczęte | Średni    | 2–3 h            |                                                                                                |
| 37 | Full pipeline E2E test (logi → ETL → ML → symulacja → drift)                                                          | ☐ Nie rozpoczęte | Wysoki    | 10–12 h          | pełny test end-to-end                                                                          |

---

## Podsumowanie punktowe

| Kategoria                        | Punkty możliwe | Punkty zdobyte | Komentarz                    |
|----------------------------------|----------------|----------------|------------------------------|
| Backend ODE + wydajność          | 25             | 0              |                              |
| Fizyka 1D (pseudo)               | 20             | 0              |                              |
| Integracja danych produkcyjnych  | 15             | 0              |                              |
| ML 2.0 + drift                   | 15             | 0              |                              |
| API / mikroserwis / UX operatora | 15             | 0              |                              |
| Product hardening & release      | 10             | 0              |                              |
| **Σ Razem**                      | **100**        | **0**          | Start fazy 3                 | :contentReference[oaicite:14]{index=14}

---

## Status ogólny TODO3

- 0% – faza 3 dopiero startuje.  
- Cel: zamknięcie do końca marca 2026 → **produkt 1.0 gotowy do pilotażu u klienta**. 

## Następne kroki po TODO3

- Wdrożenie pilotażowe u pierwszego klienta.  
- Start TODO4 → pełny model 1D/3D + GUI + OPC UA connector.  
- Publikacja artykułu / prezentacja na konferencji branżowej. 
```
