# TODO2 - Punkt 4 (CLI fundamenty, run-sim i optimize) - Changelog

## 2025-12-03
- Utworzono modul `src/pur_mold_twin/cli/commands.py`, ktory kapsuluje logike komend `run-sim` i `optimize`, wspolne helpery (ladowanie systemow, zapis JSON) oraz przyjazne komunikaty o bledach.
- Przebudowano `src/pur_mold_twin/cli/main.py`, aby tworzylo aplikacje Typer z flaga `--version`, dedykowanym helpem oraz rejestracja komend przez nowy modul; CLI posiada teraz punkt wejscia `main()` i gotowy `app`.
- Uruchomiono `pytest tests/test_cli.py` w celu potwierdzenia, ze nowa struktura komend dziala poprawnie.
- Status: **OK** (pierwszy bullet TODO2 §4 zrealizowany).

## 2025-12-04
- Rozszerzono komendę `run-sim` o parametry `--system` (nadpisuje `system_id`) oraz `--quality` (preset `QualityTargets`), dzięki czemu użytkownik może łączyć scenariusze z katalogiem DB i niezależnymi presetami jakości.
- Zaktualizowano `tests/test_cli.py` (`test_run_sim_cli_with_overrides`) oraz dokument `docs/USE_CASES.md` o sekcję opisującą flagi `run-sim`, tak aby dokumentacja odzwierciedlała nowe wejścia.
- Uruchomiono `pytest tests/test_cli.py` – wszystkie testy CLI przechodzą.
- Status: **OK** (drugi bullet TODO2 §4 wykonany).

## 2025-12-05
- Dodano obsługę `--output json/table`, `--save-json` i `--export-csv` w `run-sim`, wraz z generowaniem tabeli KPI oraz eksportem profili do CSV (zmiany w `src/pur_mold_twin/cli/commands.py`).
- Rozszerzono `docs/USE_CASES.md` o opis nowych flag i przykład użycia, a `tests/test_cli.py` o test `test_run_sim_cli_table_and_csv`.
- `pytest tests/test_cli.py` – PASS (ostrzeżenia Pydantic legacy).
- Status: **OK** (trzeci bullet TODO2 §4 zrealizowany).

## 2025-12-05 (cz.2)
- Dodano sekcję „CLI Quickstart” w `readme.md` oraz rozszerzono `docs/USE_CASES.md` o opis komendy `optimize`, zamykając punkt TODO dot. dokumentacji CLI (§4).
- `todo2.md` – zaktualizowano status bulletu (README + USE_CASES).
- Status: **OK** (czwarty bullet TODO2 §4).

## 2025-12-06
- Rozbudowano `run-sim` i `optimize` w `src/pur_mold_twin/cli/commands.py`: tryb JSON/tabela, eksport CSV, zapisywanie JSON, raport „Przed vs Po” oraz przyjazna obsługa błędów (scenariusz, system, preset).
- `tests/test_cli.py` otrzymał dodatkowe scenariusze (błędny plik, tryb tabeli) gwarantujące happy-path i czytelne komunikaty; `tests/test_optimizer.py` wykorzystuje teraz realny `use_case_1`.
- Dokumentacja CLI (`readme.md`, `docs/USE_CASES.md`) opisuje nowe flagi, a `todo2.md` oznacza kolejne bullet pointy jako wykonane.
- `pytest tests/test_cli.py tests/test_optimizer.py` – PASS (ostrzeżenia Pydantic legacy / brak dostępu do `.pytest_cache`).
- Status: **OK** (kolejne bullet'y TODO2 §4 zamknięte).
