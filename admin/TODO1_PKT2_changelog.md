# TODO1 - Punkt 2 (Material DB) - Changelog

Historia zmian wykonanych przez Copylota w ramach sekcji 2 `todo1.md`.

## 2025-01-12
- Utworzenie katalogu `src/pur_mold_twin/material_db/` oraz plikow:
  - `models.py` - modele Pydantic dla komponentow poliolowych/izo, celow gestosciowych i twardosci oraz helper `has_pentane`.
  - `loader.py` - funkcje `load_material_system` i `load_material_systems` wykorzystujace `ruamel.yaml`.
  - `__init__.py` w pakiecie glownym i w `material_db`.
- Dodanie systemow TDS: `configs/systems/system_R1.yaml` (bez pentanu) i `configs/systems/system_M1.yaml` (z pentanem) wraz z metadanymi.
- Aktualizacja README (sekcja 3.1) o wskazanie katalogu `configs/systems` i powiazanie z modelami Material DB.
- Odnotowanie wykonania sekcji 2 w `todo1.md` (checkboxy + referencje do plikow).

## 2025-12-02
- Dodano metodę `MaterialSystem.validate_required_fields()` do sygnalizowania brakujących pól wejściowych.
- Dopisano komentarze w `configs/systems/jr_purtec_catalog.yaml` oraz wskazówki w `configs/scenarios/use_case_1.yaml` o wymaganych danych i jednostkach.
- Utworzono `configs/README.md` z listą pól wymaganych/opcjonalnych oraz minimalnymi i pełnymi przykładami konfiguracji; link w `docs/STRUCTURE.md`.

## 2025-12-03
- Ujednolicono komentarze jednostek i placeholderów w `configs/systems/jr_purtec_catalog.yaml`, zaznaczając brakujące dane TDS i konieczność pomiarów.
- Dodano krótkie opisy jednostek w `configs/scenarios/use_case_1.yaml` oraz progach jakości w `configs/quality/default.yaml` dla spójności konfiguracji.
- Uporządkowano format pliku testowego `tests/fixtures/use_case_1_output.json` (znacznik końca pliku).
