# Struktura projektu - PUR-MOLD-TWIN

Szkic katalogow/plikow. Zanim dodasz nowy modul, sprawdz czy pasuje do tej struktury.

```
pur-mold-twin/
├── README.md                # opis produktu + link do agent_instructions
├── README_VERS.md           # checkpointy/wersje
├── todo1.md                 # glowna lista zadan
├── py_lib.md                # stack/biblioteki (Python 3.14)
├── standards.md             # konwencje (root)
├── agent_instructions.md    # obowiazkowe dla AI
├── admin/                   # changelogi TODO1 (PKT1..)
├── docs/
│   ├── MODEL_OVERVIEW.md
│   ├── USE_CASES.md
│   ├── STRUCTURE.md
│   ├── CALIBRATION.md
│   └── ML_LOGGING.md
├── configs/
│   ├── systems/             # parametry Material DB
│   ├── scenarios/           # proces/mold/quality + simulation presets
│   └── quality/             # standalone QualityTargets (np. CLI preset)
├── src/
│   └── pur_mold_twin/
│       ├── __init__.py
│       ├── material_db/
│       │   ├── __init__.py
│       │   ├── models.py        # Pydantic modele
│       │   └── loader.py        # parser YAML/JSON
│       ├── core/
│       │   ├── __init__.py
│       │   └── mvp0d.py        # aktualna implementacja core 0D (docelowo podzial na moduly)
│       ├── optimizer/
│       │   ├── __init__.py
│       │   ├── search.py
│       │   └── constraints.py
│       ├── diagnostics/
│       │   ├── __init__.py
│       │   ├── rules.py
│       │   └── reporter.py
│       ├── cli/
│       │   ├── __init__.py
│       │   └── main.py         # placeholder CLI
│       └── utils/
│           ├── __init__.py
│           └── units.py
├── tests/
│   ├── __init__.py
│   ├── test_core_simulation.py
│   └── test_optimizer.py
└── .github/
    └── workflows/ci.yml
```

### Zaleznosci miedzy katalogami
| Katalog | Uzywa / produkuje | Zakres |
| --- | --- | --- |
| `configs/systems` | czytany przez `material_db.loader` -> `MaterialSystem` | dane stale (TDS/SDS) |
| `configs/scenarios` | czytany przez CLI -> `ProcessConditions`, przekazywany do `core.simulation` | opis partii: masy, temperatury, constraints |
| `src/pur_mold_twin/material_db` | uzywany przez `cli`, `core`, `optimizer` | laduje i waliduje wejscia |
| `src/pur_mold_twin/core` | uzywany przez CLI i Optimizer | rdzen fiz-chem: oblicza profile oraz `SimulationResult` |
| `src/pur_mold_twin/optimizer` | wywoluje `core.simulation` | steruje optymalizacja nastaw |
| `src/pur_mold_twin/diagnostics` | wywolywany z `core.simulation` lub CLI | generuje ostrzezenia i `defect_risk` |
| `src/pur_mold_twin/cli` | korzysta z `configs` -> `material_db` -> `core`/`optimizer` | interfejs uzytkownika |
| `tests/` | zalezy od `src` | weryfikuje moduly |

### Wytyczne dla katalogow
1. **configs/**
   - `configs/README.md`: przewodnik pól wymaganych/opcjonalnych + minimalne i pełne przykłady YAML.
   - `configs/systems/system_M1.yaml`: opis par poliol/izo + parametry docelowe (ładowane przez `material_db.loader` z ruamel.yaml).
   - `configs/scenarios/*.yaml`: kompletne scenariusze (`system_id`, `process`, `mold`, `quality`, opcjonalnie `simulation`), ładowane przez `pur_mold_twin.configs.load_process_scenario`.
   - `configs/quality/*.yaml`: stand-alone `QualityTargets` (preset CLI/testów), ładowane przez `load_quality_preset`.
2. **src/pur_mold_twin/**
   - Produkcyjny kod trafia tutaj; eksperymenty w osobnych branchach/folderach poza `src`.
   - Kazdy modul (material_db/core/optimizer/diagnostics/cli/utils) ma odpowiadajace testy w `tests/`.
   - `core.simulation` skleja backendy solvera (manual/solve_ivp) i korzysta z modulow pomocniczych (`kinetics`, `thermal`, `gases`, `hardness`) – brak bezposrednich importow CLI/optimizer.
3. **docs/**
   - `MODEL_OVERVIEW.md` przechowuje opis rownan/zakresu.
   - `STRUCTURE.md` aktualizujemy przy zmianie layoutu.
   - Kazdy nowy dokument wplywajacy na workflow agenta musi byc podlinkowany w `agent_instructions.md`.
4. **tests/**
   - Organizacja wg modulu (`test_core_simulation.py`, `test_pressure_model.py` itd.).
   - Testy importuja tylko publiczne API (np. `from pur_mold_twin.core.simulation import run_simulation`).
   - Jezeli test wymaga danych, korzysta z malych fixture (dodaj `tests/fixtures/` jezeli potrzebne).
5. **agent_instructions.md / README**
   - Przy kazdej zmianie struktury (nowe katalogi, przenosiny) aktualizujemy oba pliki, aby Copilot/Codex znal aktualny layout.

### Pliki w budowie
- `src/pur_mold_twin/cli/main.py` - CLI placeholder (docelowo Typer/argparse).
- `tests/test_core_simulation.py`, `tests/test_optimizer.py` - podstawowe testy; będą rozszerzane o kolejne przypadki.

### Notatki dla Codex/Copilot
- Przed utworzeniem nowego katalogu upewnij sie, ze pasuje do listy powyzej.
- Nie wrzucaj danych binarnych/Exceli. Jezeli musisz, dodaj `data/` i `.gitignore`, ale tylko po uzgodnieniu.
- Kazdy modul powinien miec krotki docstring i referencje do sekcji TODO, ktora realizuje.
