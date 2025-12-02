# TODO2 - Punkt 3 (Material DB i konfiguracje wejścia) - Changelog

## 2025-12-03
- Zastąpiono ręczny parser YAML w `src/pur_mold_twin/material_db/loader.py` ruamel.yaml (parsowanie multi-doc, komunikat o braku biblioteki), a modele `MaterialSystem` otrzymały walidacje `__post_init__`.
- Dodano testy `tests/test_material_loader.py`/`tests/test_scenario_loader.py` (skip gdy brak ruamel) oraz nowe moduły konfiguracyjne (`src/pur_mold_twin/configs/` z `scenario_loader.py`).
- Uzupełniono repo o przykładowe pliki `configs/scenarios/use_case_1.yaml` i `configs/quality/default.yaml`, aktualizując `docs/USE_CASES.md`, `docs/STRUCTURE.md` i `py_lib.md` o przepływ YAML -> Pydantic.
- Status: **OK** (TODO2 §3 zamknięty).
