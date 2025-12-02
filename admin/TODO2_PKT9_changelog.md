# TODO2 - Punkt 9 (Wizualizacja i raporty) - Changelog

## 2025-12-07
- Dodano moduły raportowe: `reporting/plots.py` (wykresy alpha/T/p/rho/vent) i `reporting/report.py` (raport Markdown z KPI + osadzone PNG), eksporty w `reporting/__init__.py`.
- Integracja CLI: `run-sim --report` generuje raport i zapisuje wykresy; obsługa w `src/pur_mold_twin/cli/commands.py`.
- Dokumentacja/stack: `docs/USE_CASES.md` opisuje generowanie raportu, `py_lib.md` dopisuje `matplotlib` do stacku (raporty).
- Testy: `tests/test_reporting.py` (pomija gdy brak matplotlib) korzysta z golden fixture; wymaga zapisu w `tests/tmp_reports/` (gitignored).
- Status: **OK** (TODO2 §9 ukończony).
