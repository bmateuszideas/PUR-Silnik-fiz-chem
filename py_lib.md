# py_lib.md – stos bibliotek PUR-MOLD-TWIN (Faza 2 – Productization & Quality)

Docelowy stack Pythona dla fazy TODO2. Core musi działać bez „egzotycznych” zależności; extras są włączane tylko wtedy, gdy użytkownik świadomie je doinstaluje.

---

## 1. Core produkcyjny – silnik 0D

Te biblioteki są **twardymi zależnościami runtime** (w `pyproject.toml` bez extras).

- **numpy** – podstawowa algebra numeryczna, macierze, operacje na tablicach (profil `alpha/T/rho`, gazy, raporty).
- **scipy**
  - `scipy.integrate.solve_ivp` stanowi domyślny backend ODE (`SimulationConfig.backend="solve_ivp"`).
  - Stosujemy metody stiff (`Radau`, `BDF`) zgodnie z rekomendacją dokumentacji SciPy oraz eventy do wykrywania cream/gel/rise/demold.
  - `scipy.optimize` pozostaje narzędziem do prostych fitów/kosztów (kalibracja, local search).
- **pydantic**
  - Modele danych i konfiguracji (`SimulationConfig`, `SimulationResult`, `ProcessConditions`, `MaterialSystem`, `OptimizerConfig`…).
  - Walidacja typów i zakresów (`RH ∈ [0,1]`, twardości dodatnie, masy > 0 itd.) + serializacja CLI.
- **pint**
  - Jednostki fizyczne na I/O (°C/K, bar/Pa, kg/m³, s); w solverze pracujemy w SI, na brzegach `Quantity`.
  - Konwencja: pint na wejściu/wyjściu, wewnątrz czyste `float` w SI dla wydajności.

---

## 2. Konfiguracje, CLI i I/O

Również traktujemy jako **produkcyjne** – bez nich nie ma sensownego interfejsu.

- **ruamel.yaml**
  - Loader Material DB oraz scenariuszy/presetów jakości:
    - round-trip (utrzymuje komentarze i kolejność – ważne dla katalogu `configs/systems`),
    - ładowanie → walidacja Pydantic (`MaterialSystem`, `ProcessConditions`, `QualityTargets`, `SimulationConfig`).
- **typer**
  - Framework CLI (`pur-mold-twin`):
    - komendy `run-sim`, `optimize`, `build-features`, `--version`, `--verbose`.
    - testy CLI opierają się na `CliRunner`.
- **pandas**
  - ETL/logging/raporty:
    - logi runtime → DataFrame,
    - pipeline featur (`T_max`, `p_max`, slopes, różnice vs pomiar),
    - builder datasetów (`features.parquet`), zasilanie baseline’ów ML.

---

## 3. ML / analytics – **opcjonalne extras**

Projekt ma działać bez ML. Te biblioteki instalujemy jako `pur-mold-twin[ml]`.

- **scikit-learn**
  - baseline’y: klasyfikacja defektów, regresja `defect_risk`, feature importance.
  - Proste modele (RandomForest, GradientBoosting, LogisticRegression).
  - Importy guardowane (`try/except ImportError`), CLI komunikuje brak extras.

---

## 4. Backend ODE – przyszłe rozszerzenia (TODO3+)

Architektura solvera (abstrakcja backendu) umożliwia dołączanie kolejnych bibliotek, ale **nie instalujemy ich w TODO2**.

- **SUNDIALS (przez scikits.odes / scikit-SUNDAE)**
  - CVODE/IDA do dużych, stiff systemów lub DAE.
  - Planowane jako extras `pur-mold-twin[sundials]`.
- **JAX + Diffrax / probdiffeq**
  - Backend eksperymentalny (auto-diff, GPU, probabilistyczne ODE).

Na etapie TODO2 implementujemy tylko `ScipyBackend` (`solve_ivp`), utrzymując czyste API `ODESolverBackend`, aby kolejne backendy można było dopiąć bez łamania kodu.

---

## 5. Zaawansowana chemia – integracje specjalne (opcjonalne)

Nie wchodzą do core TODO2, ale zostawiamy miejsce w architekturze.

- **Cantera** – pełna kinetyka/termodynamika/transport; potencjalny backend dla rozszerzonego modelu PUR.
- **ChemPy** – układy reakcji chemicznych + równowagi.

Na razie pozostajemy przy własnym modelu Arrhenius/empirycznym (kalibracja vs TDS).

---

## 6. Dev / QA

Zależności instalowane tylko dla developmentu/CI (`pur-mold-twin[dev]`):

- **pytest**, **pytest-cov** – testy jednostkowe/regresyjne + coverage (cel >80% modułu `core`).
- **mypy** – statyczne typowanie (opcjonalnie).
- **ruff** / **black** – lint + format.
- (opcjonalnie) `pre-commit` – spójny workflow developerski.

---

## 7. Kontrakt dla TODO2

1. **Must-have w podstawowej instalacji**: `numpy`, `scipy`, `pydantic`, `pint`, `ruamel.yaml`, `typer`, `pandas`.
2. **Extras**:
   - `[ml]` → `scikit-learn`,
   - `[sundials]`, `[jax]`, `[chem]` (Cantera/ChemPy) – dopiero po akceptacji wewnętrznej (TODO3+).
3. **Dev** → `[dev]` (`pytest`, `pytest-cov`, `mypy`, `ruff`, `black`).

CLI, dokumentacja i configi mają jasno komunikować ten podział – core działa „od razu po `pip install pur-mold-twin`”, a wszystkie cięższe integracje są świadomie opt-in.
