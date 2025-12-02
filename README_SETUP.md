# Setup środowiska — PUR-Silnik-fiz-chem

Instrukcja szybkiego uruchomienia repozytorium lokalnie w systemie Linux/WSL/macOS.

Wymagania:
- Python (preferowane 3.14+, patrz `pyproject.toml`)
- Git
- (opcjonalnie) Docker/Dev Container

Kroki:

1. Sklonuj repo i przejdź do katalogu projektu

```bash
git clone <repo-url>
cd PUR-Silnik-fiz-chem
```

2. Uruchom skrypt setup (tworzy `.venv` i instaluje zależności)

```bash
# nadaj prawa wykonywania (tylko raz)
chmod +x setup_workspace.sh
# uruchom
./setup_workspace.sh
```

3. Aktywuj środowisko

```bash
source .venv/bin/activate
```

4. Uruchom testy (opcjonalnie)

```bash
python -m pytest
```

Uwagi:
- `pyproject.toml` deklaruje `requires-python = ">=3.14"`. Jeśli lokalny interpreter jest starszy, skrypt zainstaluje podstawowe zależności (bez instalacji pakietu w trybie editable).
- Aby w pełni zainstalować pakiet w editable mode uruchom, mając Python 3.14+:

```bash
pip install -e .[dev]
```

- Dalsze kroki: uruchom `python -m pur_mold_twin.cli.main --help` lub sprawdź `docs/`.
