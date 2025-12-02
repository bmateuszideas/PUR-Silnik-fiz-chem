# TODO2 - Punkt 5 (Logging runtime i verbose) - Changelog

## 2025-12-06
- Dodano moduł `src/pur_mold_twin/utils/logging.py` (oraz `__init__.py`), zapewniający `configure_logging` i `get_logger`; CLI korzysta teraz z jednolitego loggera zamiast `print`/braku logów.
- `src/pur_mold_twin/cli/main.py` otrzymał flagę globalną `--verbose`, która ustawia poziom logowania na DEBUG zanim uruchomiona zostanie komenda Typer.
- `src/pur_mold_twin/cli/commands.py` loguje kluczowe kroki (`run-sim`, `optimize`, eksport CSV/JSON) i udostępnia przyjazne komunikaty o błędach (scenariusz/system/preset).
- Testy: `pytest tests/test_cli.py tests/test_optimizer.py` – PASS (ostrzeżenia Pydantic legacy). Dodano przypadek CLI z `--verbose`.
- Dokumentacja (`readme.md`, `docs/USE_CASES.md`) uzupełniona o informacje o `--verbose` i nowych flagach CLI; `todo2.md` zaktualizowano, by §5 był odhaczony.
- Status: **OK** (TODO2 §5 zamknięty).
