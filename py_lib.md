# py_lib.md – stos bibliotek PUR-MOLD-TWIN (Faza 2 – Productization & Quality)

Docelowy stack Pythona dla TODO2. Core ma dzialac bez egzotycznych zaleznosci; extras instalowane tylko gdy sa potrzebne.

---

## 1. Core produkcyjny – silnik 0D

Twarde zaleznosci runtime (w `pyproject.toml` bez extras).

- **numpy** – algebra numeryczna, wektory/macierze, profile alpha/T/rho/gazy.
- **scipy**
  - `scipy.integrate.solve_ivp` jako domyslny backend ODE (`SimulationConfig.backend="solve_ivp"`), metody stiff `Radau`/`BDF`, eventy cream/gel/rise/demold.
  - `scipy.optimize` do prostych fitow/kosztow (kalibracja, local search).
- **pydantic**
  - Modele danych/config (`SimulationConfig`, `SimulationResult`, `ProcessConditions`, `MaterialSystem`, `OptimizerConfig`...).
  - Walidacja typow i zakresow (`RH 0-1`, masy >0, twardosci >0) + serializacja CLI.
- **pint**
  - Jednostki fizyczne na I/O (C/K, bar/Pa, kg/m3, s); wewnatrz solvera czyste floaty w SI.

---

## 2. Konfiguracje, CLI i I/O

Rowniez produkcyjne – bez nich brak interfejsu.

- **ruamel.yaml**
  - Loader Material DB oraz scenariuszy/presetow jakosci:
    - round-trip (komentarze, kolejnosc kluczy w `configs/systems`),
    - ladowanie + walidacja Pydantic (`MaterialSystem`, `ProcessConditions`, `QualityTargets`, `SimulationConfig`).
- **typer**
  - Framework CLI (`pur-mold-twin`): komendy `run-sim`, `optimize`, `build-features`, `--version`, `--verbose`; testy CLI na `CliRunner`.
- **pandas**
  - ETL/logging/raporty: logi runtime -> DataFrame; pipeline featur (`T_max`, `p_max`, slopes, roznice vs pomiar); builder datasetow (`features.parquet`) dla ML.
- **matplotlib**
  - Wykresy profili symulacji (alpha/T/p/rho/vent) i raporty CLI (`reporting/plots.py`, `run-sim --report`).

---

## 3. ML / analytics – opcjonalne extras

Projekt dziala bez ML. Instalujemy jako `pur-mold-twin[ml]`.

- **scikit-learn**
  - Baseline: klasyfikacja defektow, regresja `defect_risk`, feature importance (RandomForest/GradientBoosting/LogisticRegression).
  - Importy guardowane (`try/except ImportError`), CLI komunikuje brak extras.

---

## 4. Backend ODE – przyszle rozszerzenia (TODO3+)

Architektura backendu pozwala dolaczyc kolejne biblioteki, ale nie instalujemy ich w TODO2.

- **SUNDIALS** (scikits.odes / scikit-SUNDAE) – CVODE/IDA dla duzych stiff systemow/DAE, extras `pur-mold-twin[sundials]`.
- **JAX + Diffrax/probdiffeq** – eksperymentalny backend (auto-diff, GPU, probabilistyczne ODE).

---

## 5. Zaawansowana chemia – integracje specjalne (opcjonalne)

Nie wchodza do core TODO2, zostawiamy miejsce w architekturze.

- **Cantera** – kinetyka/termodynamika/transport (opcjonalny backend).
- **ChemPy** – uklady reakcji + rownowagi.

---

## 6. Dev / QA

Instalowane tylko dla developmentu/CI (`pur-mold-twin[dev]`):

- **pytest**, **pytest-cov** – testy i coverage (cel >80% dla `core`).
- **mypy** – statyczne typowanie (opcjonalnie).
- **ruff**, **black** – lint + format.
- (opcjonalnie) `pre-commit`.

---

## 7. Kontrakt dla TODO2

1. Must-have w podstawowej instalacji: `numpy`, `scipy`, `pydantic`, `pint`, `ruamel.yaml`, `typer`, `pandas`, `matplotlib`.
2. Extras:
   - `[ml]` -> `scikit-learn`,
   - `[sundials]`, `[jax]`, `[chem]` (Cantera/ChemPy) dopiero po akceptacji (TODO3+).
3. Dev -> `[dev]` (`pytest`, `pytest-cov`, `mypy`, `ruff`, `black`).

Core dziala od razu po `pip install pur-mold-twin`; ML/back-endy specjalne sa opt-in.
