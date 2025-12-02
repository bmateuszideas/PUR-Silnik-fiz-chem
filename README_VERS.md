# README / Workflow Verification (Checkpoint)

Data: 2025-12-01  
Zakres: kontrola spojnosci repo z `todo1.md` (szczegolnie §13) oraz weryfikacja tresci `readme.md`.

## 2025-12-02
- Dodano realne testy (`test_core_simulation.py`, `test_optimizer.py`) i usunieto placeholdery.
- Standaryzowano strukture dokumentacji (root `standards.md`, `docs/CALIBRATION.md`, `docs/ML_LOGGING.md`).
- Material DB scalona w multi-doc `configs/systems/jr_purtec_catalog.yaml` (zawiera R1/M1 oraz systemy JR Purtec).
- Status README zaktualizowany: MVP 0D + prosty optimizer + testy bazowe.

## 2025-12-07
- Utworzono golden fixture dla `use_case_1` (`tests/fixtures/use_case_1_output.json`) oraz dodano regresje profili w `tests/test_core_simulation.py` (alpha/T_core/p_total/rho) z tolerancjami.
- Test regresyjny optymalizatora (`tests/test_optimizer.py`) wykorzystuje `use_case_1` i weryfikuje brak dryfu; dodano testy skrajne (brak ventów) i podstawowe tolerancje.
- Kalibracja: nowy pakiet `calibration/` (loader/cost/fit) oraz skrypty `calibrate_kinetics.py`, `compare_shot.py`, `calibration_report.py`, `plot_kinetics.py`; dokument `docs/CALIBRATION.md` opisuje automatyzację.
- CLI: rozbudowany Typer (`run-sim`/`optimize`, eksport JSON/CSV, `--verbose`); testy CLI w `tests/test_cli.py` (happy-path, błędne pliki).

## 1. Stan TODO1
- §1-12 oznaczone jako ukonczone i faktycznie posiadaja odpowiadajace pliki/kod (`docs/MODEL_OVERVIEW.md`, `src/pur_mold_twin/core`, `docs/CALIBRATION.md`, `docs/ML_LOGGING.md`).
- §13 (`Dokumentacja i standardy`) pozostaje otwarty: README/standards aktualne, ale testy i CLI istnieja w wersji startowej (trzeba je rozwinac funkcjonalnie).

## 2. Czy README odzwierciedla rzeczywistosc?
**Zgodne**
- Sekcje 1–13 opisujace problem, dane, core, optimizer, kalibracje i ML odsyłaja do realnego kodu/dokumentow.
- README zawiera notatki o CLI/testach jako paczce w budowie.

**Rozbiezne (naprawione w tym FIXie)**
1. Brak katalogu `tests/` -> dodano `tests/test_placeholder.py` (opisany w README/STRUCTURE jako krok przejsciowy).
2. Brak `src/pur_mold_twin/cli/` -> dodano `cli/main.py` z komunikatem "CLI in progress".
3. `.gitignore` nie mial wpisow dla `data/calibration/`, `data/ml/`, `reports/ml/` -> dodano.
4. `standards.md` i README nie wspominaly o `docs/CALIBRATION.md` i `docs/ML_LOGGING.md` -> dopisano referencje oraz zasady danych.

## 3. Zalecenia dla §13
1. Rozszerzyc placeholder tests -> docelowe `test_core_simulation.py`, `test_optimizer.py` (np. w kolejnej paczce).
2. Rozwinac CLI w `src/pur_mold_twin/cli/main.py` (komendy `run-sim`, `optimize`).
3. Utrzymywac `.gitignore` dla katalogow danych; realne logi przechowywac tylko lokalnie.

## 4. Podsumowanie
Workflow (TODO1 -> README -> docs -> src) jest spójny dla paczek (a–d). Po wprowadzeniu placeholderow i zasad przechowywania danych §13 wymaga juz tylko dopracowania testow i CLI, ale dokumentacja pozostaje zgodna z rzeczywistoscia.
