# Struktura projektu - PUR-MOLD-TWIN

Szkic katalogow/plikow. Zanim dodasz nowy modul, sprawdz czy pasuje do tej struktury.

```
pur-mold-twin/
├── README.md                # opis produktu + link do agent_instructions
├── README_VERS.md           # checkpointy/wersje
├── todo1.md                 # glowna lista zadan
├── todo2.md                 # prace produktowe/rozszerzenia
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
│       ├── calibration/         # loader + fit/cost funkcje kalibracyjne
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   ├── cost.py
│       │   └── fit.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── commands.py      # rejestr komend run-sim/optimize/build-features
│       │   └── main.py          # Typer app + logging/version
│       ├── configs/
│       │   ├── __init__.py
│       │   └── scenario_loader.py
│       ├── material_db/
│       │   ├── __init__.py
│       │   ├── models.py        # Pydantic modele
│       │   └── loader.py        # parser YAML/JSON
│       ├── core/
│       │   ├── __init__.py
│       │   ├── mvp0d.py         # implementacja core 0D
│       │   ├── simulation.py    # orchestration + CLI glue
│       │   ├── gases.py/thermal.py/kinetics.py/hardness.py/types.py/utils.py
│       ├── optimizer/
│       │   ├── __init__.py
│       │   ├── search.py
│       │   └── constraints.py
│       ├── diagnostics/
│       │   ├── __init__.py
│       │   ├── rules.py
│       │   └── reporter.py
│       ├── data/
│       │   ├── __init__.py
│       │   ├── dataset.py       # format logow/feature set
│       │   ├── etl.py           # ETL z logow procesowych
│       │   └── schema.py
│       ├── logging/
│       │   ├── features.py      # budowa feature z symulacji/logow
│       │   └── logger.py        # konfiguracja logowania
│       ├── ml/
│       │   ├── __init__.py
│       │   ├── baseline.py      # modele referencyjne (RF)
│       │   └── train_baseline.py
│       ├── reporting/
│       │   ├── __init__.py
│       │   ├── plots.py         # wykresy do raportu CLI
│       │   └── report.py        # generacja raportu Markdown
│       └── utils/
│           ├── __init__.py
│           └── logging.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/                # golden output (np. use_case_1)
│   ├── data/                    # sample inputs dla ETL/logging
│   ├── test_core_simulation.py
│   ├── test_simulation_helpers.py
│   ├── test_optimizer.py
│   ├── test_cli.py
│   ├── test_calibration*.py
│   ├── test_etl.py / test_logging_features.py / test_ml_baseline.py
│   ├── test_reporting.py
│   └── test_material_loader.py / test_scenario_loader.py
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
| `src/pur_mold_twin/cli` | korzysta z `configs` -> `material_db` -> `core`/`optimizer`/`reporting`/`data` | interfejs Typer (run-sim, optimize, build-features, raporty) |
| `src/pur_mold_twin/calibration` | korzysta z danych pomiarowych i `core` | fit parametrow kinetyki/ciepla/pentanu |
| `src/pur_mold_twin/data` | czyta logi procesowe / wyniki symulacji | ETL i schemat danych pod ML |
| `src/pur_mold_twin/logging` | uzywany przez ETL/CLI | budowa featur i logger aplikacyjny |
| `src/pur_mold_twin/ml` | uzywa featur z `data`/`logging` | modele bazowe ML |
| `src/pur_mold_twin/reporting` | uzywany przez CLI | generuje raporty Markdown + wykresy |
| `tests/` | zalezy od `src` | regresje core/optimizer/CLI/ETL/ML/raportowania |

### Wytyczne dla katalogow
1. **configs/**
   - `configs/README.md`: przewodnik pól wymaganych/opcjonalnych + minimalne i pełne przykłady YAML.
   - `configs/systems/system_M1.yaml`: opis par poliol/izo + parametry docelowe (ładowane przez `material_db.loader` z ruamel.yaml).
   - `configs/scenarios/*.yaml`: kompletne scenariusze (`system_id`, `process`, `mold`, `quality`, opcjonalnie `simulation`), ładowane przez `pur_mold_twin.configs.load_process_scenario`.
   - `configs/quality/*.yaml`: stand-alone `QualityTargets` (preset CLI/testów), ładowane przez `load_quality_preset`.
2. **src/pur_mold_twin/**
   - Produkcyjny kod trafia tutaj; eksperymenty w osobnych branchach/folderach poza `src`.
   - Kazdy modul (material_db/core/optimizer/diagnostics/cli/calibration/data/logging/ml/reporting/utils) ma odpowiadajace testy regresyjne w `tests/`.
   - `core.simulation` skleja backendy solvera (manual/solve_ivp) i korzysta z modulow pomocniczych (`kinetics`, `thermal`, `gases`, `hardness`) – brak bezposrednich importow CLI/optimizer.
3. **docs/**
   - `MODEL_OVERVIEW.md` przechowuje opis rownan/zakresu.
   - `STRUCTURE.md` aktualizujemy przy zmianie layoutu.
   - Kazdy nowy dokument wplywajacy na workflow agenta musi byc podlinkowany w `agent_instructions.md`.
4. **tests/**
   - Organizacja wg modulu (`test_core_simulation.py`, `test_optimizer.py`, `test_cli.py`, `test_calibration*.py`, ETL/ML/raporty).
   - Testy importuja publiczne API (np. `from pur_mold_twin.core.simulation import run_simulation`).
   - Fixture regresyjne w `tests/fixtures/` i przykladowe logi w `tests/data/` pozwalaja weryfikowac profile i raporty.
5. **agent_instructions.md / README**
   - Przy kazdej zmianie struktury (nowe katalogi, przenosiny) aktualizujemy oba pliki, aby Copilot/Codex znal aktualny layout.

### Pliki w budowie
- Rozwojowe paczki TODO2 obejmuja kalibracje datasetow, raportowanie i modele ML; struktura powyzej jest aktualna i wykorzystywana przez CLI/testy regresyjne.

### Notatki dla Codex/Copilot
- Przed utworzeniem nowego katalogu upewnij sie, ze pasuje do listy powyzej.
- Nie wrzucaj danych binarnych/Exceli. Jezeli musisz, dodaj `data/` i `.gitignore`, ale tylko po uzgodnieniu.
- Kazdy modul powinien miec krotki docstring i referencje do sekcji TODO, ktora realizuje.
