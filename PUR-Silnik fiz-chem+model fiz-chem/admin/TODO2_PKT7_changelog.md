# TODO2 - Punkt 7 (Testy regresyjne, skrajne i pokrycie) - Changelog

## 2025-12-07
- Przygotowano golden fixture `tests/fixtures/use_case_1_output.json` i dodano regresje profili w `tests/test_core_simulation.py` (alpha, T_core, p_total, rho, p_max) z tolerancjami; dodatkowo scenariusz skrajny (brak ventów, RH=100%, zimna forma) oraz obsługa błędnych danych (ValueError).
- Dodano regresję optymalizatora w `tests/test_optimizer.py` (use_case_1) oraz podstawową konfigurację coverage (`pyproject.toml`) z celem >80% dla core.
- Uaktualniono `README_VERS.md` o informację o golden regression.
- Testy: `pytest tests/test_core_simulation.py tests/test_optimizer.py` – PASS (ostrzeżenia Pydantic legacy/pytest_cache).
- Status: **OK** (bullet’y golden/regresje/skrajne/coverage wykonane; pozostaje ewentualne doprecyzowanie dalszych edge-case w kolejnych iteracjach).
