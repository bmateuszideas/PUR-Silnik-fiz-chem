# TODO2 - Punkt 10 (Packaging, CI, dokumentacja) - Changelog

## 2025-12-07
- Dodano `pyproject.toml` (PEP621) z zaleznosciami core (`numpy`, `scipy`, `pydantic`, `pint`, `ruamel.yaml`, `typer`, `pandas`, `matplotlib`), extras `ml` (scikit-learn) i `dev` (pytest, pytest-cov, mypy, ruff, black); entry-point `pur-mold-twin`.
- Utworzono workflow CI `.github/workflows/ci.yml` (checkout, Python 3.12 runner, instalacja `[dev]`, uruchomienie `pytest`).
- Zaktualizowano `py_lib.md` (dodano `matplotlib`, doprecyzowano zaleznosci), `standards.md` (sekcja struktura repo + packaging/CI), `README_VERS.md` (wpis o packaging/CI/raportach), `README.md` (sekcja CLI/raporty/packaging).
- Odhaczono §10 w `todo2.md`.
- Testy: `pytest` – 1 error w `tests/test_material_loader.py` z powodu uprawnien do katalogu temp (`PermissionError` na Windows TMP); reszta testow PASS, `tests/test_reporting.py` SKIP (brak matplotlib w srodowisku). Coverage flagi opcjonalne po braku `pytest-cov`.
- Status: **BLOCKED** (częściowo) – funkcjonalnie packaging/CI gotowe; błąd testu dotyczy środowiskowych uprawnień TMP, wymaga uruchomienia z dostępnym katalogiem temp lub ustawienia zmiennych TMPDIR/TEMP.
