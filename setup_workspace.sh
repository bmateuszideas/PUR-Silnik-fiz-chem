#!/usr/bin/env bash
set -euo pipefail

# setup_workspace.sh
# Tworzy virtualenv w .venv i instaluje zależności projektu.

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

python_bin=""
if command -v python3 >/dev/null 2>&1; then
  python_bin=python3
elif command -v python >/dev/null 2>&1; then
  python_bin=python
else
  echo "Nie znaleziono Pythona w PATH. Zainstaluj Pythona 3.14+ lub ustaw 'python' w PATH." >&2
  exit 1
fi

echo "Używany interpreter: $($python_bin --version 2>&1)"

# Create venv
if [ -d "$VENV_DIR" ]; then
  echo "Wirtualne środowisko .venv już istnieje; używam go." 
else
  echo "Tworzę virtualenv w: $VENV_DIR"
  $python_bin -m venv "$VENV_DIR"
fi

# Activate
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

pip install --upgrade pip setuptools wheel

# Check Python >= 3.14
if python - <<'PY'
import sys
if sys.version_info >= (3,14):
    raise SystemExit(0)
else:
    raise SystemExit(1)
PY
then
  echo "Interpreter spełnia wymaganie Python>=3.14 — instaluję pakiet i zależności deweloperskie."
  pip install -e ".[dev]"
  echo "Instalacja pakietu zakończona."
else
  echo "Uwaga: lokalny Python < 3.14. Pomiń instalację pakietu 'editable'." >&2
  echo "Zainstaluję podstawowe zależności (bez instalacji pakietu jako editable)."
  pip install numpy>=1.26 scipy>=1.11 pydantic>=2.6 pint>=0.22 ruamel.yaml>=0.18 typer>=0.9 pandas>=2.1 matplotlib>=3.8 || true
  echo "Zainstaluję też narzędzia deweloperskie (pytest, mypy, ruff, black)."
  pip install pytest>=7.4 pytest-cov>=4.1 mypy>=1.8 ruff black || true
  echo "Jeśli chcesz zainstalować pakiet 'editable' upewnij się, że używasz Pythona 3.14+ i uruchom:"
  echo "  ./.venv/bin/pip install -e .[dev]"
fi

echo "Gotowe. Aktywuj środowisko: \n  source .venv/bin/activate"

echo "Przykładowe komendy:"
echo "  python -m pytest"
echo "  python -m pur_mold_twin.cli.main --help"

exit 0
