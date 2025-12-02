# Raport przeglądu repozytorium (po TODO2)

## 1. Skan struktury i modułów
- **Layout katalogów** zgodny z `docs/STRUCTURE.md`: konfiguracje YAML (`configs/systems`, `configs/scenarios`, `configs/quality`), kod w `src/pur_mold_twin/` z modułami core/material_db/optimizer/cli/logging/ml/reporting oraz testy w `tests/`.【F:docs/STRUCTURE.md†L5-L95】
- **Warstwa core**: `core/mvp0d.py` eksponuje `MVP0DSimulator` i modele Pydantic, delegując obliczenia do `core/simulation.py`.【F:src/pur_mold_twin/core/mvp0d.py†L1-L57】
- **Silnik 0D**: `simulation.py` łączy przygotowanie kontekstu (bilans wody, objętość, parametry reakcji), backendy `integrate_manual`/`solve_ivp` i generowanie profili `SimulationResult`.【F:src/pur_mold_twin/core/simulation.py†L15-L195】
- **CLI**: komendy `run-sim`, `optimize`, `build-features`, raportowanie i eksport CSV są w `cli/commands.py`, reużywalne w testach Typer.【F:src/pur_mold_twin/cli/commands.py†L1-L197】
- **Konfiguracje wysokiego poziomu**: `configs/scenario_loader.py` mapuje YAML scenariuszy/quality na modele Pydantic (ProcessConditions, MoldProperties, QualityTargets, SimulationConfig).【F:src/pur_mold_twin/configs/scenario_loader.py†L1-L65】

## 2. Wykonane prace (stan po TODO2)
- README_VERS dokumentuje domknięcie pakietów TODO2: realne testy core/optimizer, scalony katalog materiałów, refaktory core na moduły pomocnicze, pełne CLI Typer z raportami, pakiety kalibracji oraz ETL/ML, plus workflow CI i packaging PEP621.【F:README_VERS.md†L6-L35】

## 3. Uruchamianie i narzędzia deweloperskie
- Instalacja: `pip install .` dla core lub `pip install .[dev]` (testy) / `.[ml]` (opcjonalne ML); entry-point `pur-mold-twin` rejestruje CLI Typer (Python 3.14).【F:readme.md†L158-L193】
- Komendy CLI: `run-sim` i `optimize` przyjmują scenariusze YAML + katalog systemów, umożliwiają zapis JSON/CSV oraz generowanie raportu Markdown z wykresami (wymaga `matplotlib`).【F:readme.md†L158-L193】【F:src/pur_mold_twin/cli/commands.py†L45-L125】
- Testy: zestaw regresyjny obejmuje symulator (demold, backend parity, golden profile, skrajne przypadki), optymalizator i CLI, a także loader materiałów/scenariuszy, ETL, kalibrację i raporty (skip jeśli brak zależności).【F:tests/test_core_simulation.py†L1-L184】

## 4. Logika domenowa i przepływ danych
- **Przygotowanie symulacji**: `prepare_context` liczy bilans wody (wilgotność + poliol), objętości początkowe, moles CO₂/pentanu, parametry Arrheniusa oraz temperatury wejściowe w K; stan trafia do backendów integracji.【F:src/pur_mold_twin/core/simulation.py†L98-L143】
- **Ewolucja stanu (manual backend)**: pętla czasowa aktualizuje konwersję (`phi`/`alpha`), bilans ciepła między rdzeniem a formą oraz temperatury, co wpływa na dalsze obliczenia gęstości/ciśnień/hardness w dalszej części modułu.【F:src/pur_mold_twin/core/simulation.py†L146-L196】
- **Wejście YAML → modele**: `load_process_scenario` waliduje dane z plików scenariusza do modeli Pydantic; CLI pobiera `system_id` i ładuje `MaterialSystem` z katalogu materiałów, następnie buduje `MVP0DSimulator` i wywołuje `run`.【F:src/pur_mold_twin/configs/scenario_loader.py†L40-L65】【F:src/pur_mold_twin/cli/commands.py†L83-L107】
- **Wyjścia/raporty**: `run_sim` emituje JSON/KPI table, opcjonalnie zapisuje profile CSV i generuje raport Markdown + wykresy profili, przekazując metadane scenariusza do `generate_report`.【F:src/pur_mold_twin/cli/commands.py†L95-L125】

## 5. Ocena jakości inżynierskiej
- **Pokrycie testami**: core zweryfikowany regresyjnie (golden fixtures, tolerancje profili, ekstremalne warunki) i porównanie backendów manual vs `solve_ivp`.【F:tests/test_core_simulation.py†L62-L165】
- **Obsługa błędów CLI**: komenda `run_sim` przechwytuje tylko `ImportError` przy generowaniu raportu; inne wyjątki I/O propagują się jako `Exit(1)` bez szczegółów, co pogarsza DX w przypadku błędnych ścieżek/pozwolenia na zapis.【F:src/pur_mold_twin/cli/commands.py†L110-L125】
- **Ładowanie scenariuszy**: `_load_yaml` wymaga mapy na poziomie root; brak dodatkowej walidacji relacji między sekcjami YAML (np. zgodność `system_id` z katalogiem) poza Pydantic, co może zostawić słabe komunikaty błędów przy literówkach w kluczach.【F:src/pur_mold_twin/configs/scenario_loader.py†L31-L65】

## 6. Dług techniczny i ryzyka
- **Monolityczna pętla integracji**: `integrate_manual` łączy kinetykę i bilans cieplny w jednym bloku, bez osobnych funkcji na krok; utrudnia to testowanie ekstremów (np. dynamiczne h_core/h_mold) i ogranicza możliwość ponownego użycia w innych backendach.【F:src/pur_mold_twin/core/simulation.py†L146-L196】
- **Słabe komunikaty CLI**: brak obsługi wyjątków I/O w sekcji raportowania i przy zapisie CSV/JSON może skutkować mało czytelnymi błędami użytkownika końcowego.【F:src/pur_mold_twin/cli/commands.py†L95-L125】
- **Walidacja wejść YAML**: scenariusze są parsowane bez schematu (wystarczy brakujący klucz, aby Pydantic rzucił generyczny błąd); dodanie walidacji kluczy/top-level mogłoby wcześniej wskazać literówki i brak sekcji.【F:src/pur_mold_twin/configs/scenario_loader.py†L31-L65】

## 7. Propozycje refaktoryzacji i rozwoju
- **Refaktoryzacja backendu manual**: wydzielić funkcje krokowe dla kinetyki, wymiany ciepła i aktualizacji temperatur, tak aby można było niezależnie testować/kalibrować poszczególne części i współdzielić je z backendem `solve_ivp`.【F:src/pur_mold_twin/core/simulation.py†L146-L196】
- **Lepsza obsługa błędów CLI**: opakować sekcje eksportu/raportów w bloki przechwytujące błędy plikowe i walidacyjne, logując przyczynę i sugerując ścieżkę naprawy zamiast gołego `Exit(1)`.【F:src/pur_mold_twin/cli/commands.py†L95-L125】
- **Walidacja konfiguracji**: dodać schemat/explicit check na wymagane pola w scenariuszu oraz przy ładowaniu katalogu materiałów, aby szybciej wykrywać niespójności (np. brak sekcji `simulation`).【F:src/pur_mold_twin/configs/scenario_loader.py†L40-L65】

## 8. Priorytety (MUST/SHOULD/NICE)
- **MUST**: rozbić `integrate_manual` na mniejsze funkcje z dodatkowymi testami brzegowymi; wzmocnić obsługę błędów CLI dla raportów/eksportów, aby uniknąć niejasnych `Exit(1)`.
- **SHOULD**: wprowadzić walidację scenariuszy YAML (schemat lub kontrola kluczy) oraz lepsze komunikaty przy literówkach w nazwach pól; uzupełnić testy CLI o ścieżki błędne dla raportowania/CSV.
- **NICE TO HAVE**: ujednolicić konfigurację logowania (INFO/DEBUG) między CLI a core, dodać sanity-check dla katalogów wyjściowych w CLI oraz rozważyć profilowanie backendu manual/`solve_ivp` dla dłuższych scenariuszy.
