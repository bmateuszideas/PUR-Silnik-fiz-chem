# TODO4 – Faza przygotowania do releasu 1.0.0

Ten dokument jest kontynuacja `todo3.md`. Traktuj go jako scenariusz A→Z dla kolejnego mechanika/ developera, ktory przejmuje gotowy projekt i ma domknac finalne prace przed wersja 1.0.0.

## 0. TL;DR (co trzeba zrobic)

1. **Domkniecie dokumentacji** – README + docs maja zawierac aktualne scenariusze uzycia (CLI/API/ML).
2. **Lekki CI lint/lint** – job `lint` z ruff/black/markdownlint + ograniczona macierz testowa.
3. **Tester scenariuszy ML** – prosty CLI (`scripts/ml_status_tester.py`) uruchamiajacy realne przypadki (brak models, brak extras, OK) i raportujacy `ml_status`.
4. **Mini GUI (opcjonalnie)** – jezeli stakeholderzy potrzebuja przyciskow, mozna oplec tester w Streamlit/FastAPI, ale priorytetem jest CLI.
5. **Release tag 1.0.0** – po przejsciu testow i dokumentacji przygotowujemy changelog, podpisujemy tag.

## 1. Kontekst projektu (stan na 2025-12-03)

- Rdzen symulatora 0D/1D zakonczony (patrz `docs/MODEL_OVERVIEW.md`).
- ML policy wprowadzona (`src/pur_mold_twin/ml/policy.py`) + opis w `docs/ML_LOGGING.md`.
- Skrypty w `scripts/` zawieraja tylko aktywne narzedzia; wersje archiwalne w `scripts/archive/`.
- CI ma workflow `ci.yml` (matrix 5x2) + `release.yml` (tagi `v*.*.*`).
- Wszystkie testy (`pytest -q`) przechodza; brak `skipped`. ML testy maja fallback na brak extras.

## 2. Procedura A→Z

1. **Setup**
   - `python -m venv .venv && .\.venv\Scripts\activate`
   - `pip install -e .[dev,ml]`
2. **Testy bazowe**
   - `PYTHONPATH=src pytest -q`
   - `python scripts/smoke_e2e.py`
3. **Tester ML scenariuszy** (do zaimplementowania w TODO4)
   - `python scripts/ml_status_tester.py --case ok`
   - `python scripts/ml_status_tester.py --case missing-models`
   - `python scripts/ml_status_tester.py --case missing-extras`
4. **CI lint job**
   - Dodac job `lint` (python 3.11) uruchamiajacy: `ruff check .`, `black --check .`, `markdownlint-cli2 "**/*.md"`.
5. **Release checklist**
   - Update `README_VERS.md` (sekcja 1.0.0)
   - `git tag v1.0.0 && git push origin v1.0.0`
   - Monitor `release.yml` workflow.

## 3. Workstreams TODO4

| ID | Obszar | Status | Notatki |
|----|--------|--------|---------|
| 4.1 | Dokumentacja | ✅ Zaktualizowane | README (sekcja „Release prep”) i `docs/ML_LOGGING.md` opisują politykę `ml_status`, tester CLI i checklistę releasu. |
| 4.2 | Tester ML | Do zrobienia | Skrypt CLI + mozliwy interfejs Streamlit (opcjonalny). |
| 4.3 | CI lint | Do zrobienia | Dedykowany job `lint`, mozna zmniejszyc macierz testowa. |
| 4.4 | Release | Do zrobienia | Tag 1.0.0 po akceptacji QA. |

## 4. Guidelines dla kolejnego developera

1. **Nie ruszaj archiwum** – `scripts/archive/` to snapshoty; wszystko co nowe trafia do `scripts/` albo `tests/helpers/`.
2. **ML jest opcjonalny** – kazda integracja (CLI/API) musi dzialac bez `[ml]`. Uzywamy `ml_status` do komunikacji stanu.
3. **Dokumentuj** – zmiany w TODO4 odnotuj w `todo4.md`, `README_VERS.md` i ewentualnie w `DEV_DASHBOARD_TODO3.md` (sekcja „Snapshot CI + skrypty”).
4. **Testy musza byc realne** – brak mockow: generuj pliki tymczasowe w `tmp/`/`tmp_debug_*` (tworz w runtime, nie trzymaj w repo).

## 5. Plan tester CLl

Minimalny zakres `scripts/ml_status_tester.py`:

```text
Usage: python scripts/ml_status_tester.py --case <ok|missing-models|missing-extras>

Case ok:
  - korzysta z prawdziwych modeli (np. generowanych przez tests/helpers/build_ml_models.py)
  - wypisuje JSON z `ml_status = ok`
Case missing-models:
  - ustawia pusty katalog models -> oczekuje statusu `missing-ml-models`
Case missing-extras:
  - uruchamia proces w sub-procesie z `PYTHONPATH=src` i `python -S` bez extras (symulacja)
```

## 6. Załączniki / referencje

- `docs/ML_LOGGING.md` – polityka ML.
- `DEV_DASHBOARD_TODO3.md` – snapshot CI oraz zasady pracy.
- `README_VERS.md` – historia wersji.
- `scripts/service_example.py` – referencja API.
- `tests/test_ml_*` – przyklad realnych testow.

---
Aktualizacja: 2025-12-03, autor: Copilot (mechanik).
