"""
Pytest configuration for PUR-MOLD-TWIN tests.

- Dodaje `src/` do sys.path (bez PYTHONPATH).
- Loguje szczegóły każdej porażki do `test_failures.log`, aby łatwo zobaczyć,
  co poszło nie tak przy uruchomieniu `python -m pytest`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
LOG_FILE = ROOT / "test_failures.log"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def pytest_configure(config):  # type: ignore
    """Wyczyść plik logów na starcie."""

    LOG_FILE.write_text(f"Pytest run at {datetime.utcnow().isoformat()}Z\n")


def pytest_runtest_logreport(report):  # type: ignore
    """Zapisz do logu pełną treść każdego niepowodzenia."""

    if report.failed and hasattr(report, "longreprtext"):
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write("\n" + "=" * 80 + "\n")
            handle.write(f"FAILED: {report.nodeid}\n")
            handle.write(report.longreprtext)
            handle.write("\n")
