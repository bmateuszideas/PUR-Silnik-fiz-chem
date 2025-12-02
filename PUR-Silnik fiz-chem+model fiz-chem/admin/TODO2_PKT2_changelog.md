# TODO2 - Punkt 2 (Modele danych, walidacja i jednostki) - Changelog

## 2025-12-02
- Zaktualizowano `py_lib.md`, aby opisać docelowy stos bibliotek dla fazy Productization & Quality: sekcje core/CLI/ML/extras/dev wraz z wymaganiami dla `scipy.solve_ivp`, `ruamel.yaml`, `typer`, `pandas`, extras ML i przyszłych backendów ODE.
- Doprecyzowano kontrakt instalacyjny (podstawowe zależności vs extras `ml`/`sundials`/`jax`/`chem` oraz `[dev]`).
- Status: **OK** (dokumentacja stacku odzwierciedla aktualne założenia TODO2 §2).

## 2025-12-03
- Przeniesiono dataclasses z `mvp0d.py` do nowych modeli Pydantic w `src/pur_mold_twin/core/types.py` (ProcessConditions, MoldProperties, VentProperties, QualityTargets, SimulationConfig, SimulationResult, WaterBalance); `mvp0d.py` teraz re-eksportuje te klasy i deleguje wykonanie do `simulation.py`.
- Zaktualizowano moduły zależne (`simulation.py`, `thermal.py`, `gases.py`, `tests/test_core_simulation.py`, `docs/STRUCTURE.md`) tak, aby korzystały z nowych modeli; dodano brakujące helpery (`utils.py`) i poinformowano o nowych plikach w strukturze.
- Dodano walidacje zakresów w modelach Pydantic (masy > 0, RH clamp 0–1 z obsługą %, mixing_eff ∈ [0,1], parametry ventów/formy dodatnie, zależności `rho_moulded_min/max`, ograniczenia `SimulationConfig`), co spełnia punkt „Dodac walidacje…”.
- Zintegrowano opcjonalny `pint` na wejściu/wyjściu (`types.py` akceptuje `Quantity` dla temperatur, ciśnień, gęstości) oraz dopisano wzmiankę w `docs/MODEL_OVERVIEW.md`; walidacje `MaterialSystem` teraz pilnują zakresów TDS, a `optimizer/search.py` korzysta z Pydantic `OptimizerBounds`/`OptimizationConfig`.
- Status: **OK** (TODO2 §2 – pierwszy bullet ukończony, baza pod walidacje gotowa).
