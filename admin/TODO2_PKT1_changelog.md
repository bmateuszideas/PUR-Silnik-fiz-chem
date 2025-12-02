# TODO2 - Punkt 1 (Core 0D i modularizacja) - Changelog

## 2025-12-02
- Dopisano sekcje „0. Obserwacje z analizy” w `todo2.md`, odnotowujac problemy z testami, CLI i loaderem YAML.
- Dodano `src/pur_mold_twin/core/kinetics.py` (funkcje Arrheniusa i kalibracji krzywej reakcji) i podlaczono je w `mvp0d.py` jako pierwszy etap modularizacji.
- Rozszerzono `SimulationConfig` o pole `backend` i logike wyboru backendu w `MVP0DSimulator.run`; przygotowano stub `_run_solve_ivp` oraz zachowano istniejacy backend reczny.
- Uruchomiono `pytest tests/test_optimizer.py` (ostrzezenie z cache Pytest, testy zielone) aby potwierdzic, ze zmiany nie psuja obecnego API.
