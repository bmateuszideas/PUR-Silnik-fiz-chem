# TODO2 - Punkt 8 (Logi symulacji, ETL, featury i ML) - Changelog

## 2025-12-07
- Rozbudowano moduły logowania/ETL/ML: `logging/logger.py` (SimulationLog + metadata), `logging/features.py` (featury zgodne z docs/ML_LOGGING), `data/etl.py` (bundle logów + fallbacki), `data/dataset.py` (builder z zapisem Parquet/CSV), `data/schema.py` (lista kolumn), `cli/commands.py` oraz skrypt `scripts/build_dataset.py`.
- Dodano dane testowe (`tests/data/ml/sample_log/*`, `tests/data/ml/sample_sim_result.json`) i testy `tests/test_etl.py` (parsing logów, dataset builder, brakujące pliki). `.gitignore` obejmuje `tests/tmp_ml/`.
- Zaktualizowano dokumentację: `docs/ML_LOGGING.md` (spójne nazwy featur, pipeline, fallback CSV) i `readme.md` (instrukcja `build-features`). `todo2.md` sekcja §8 odhaczona.
- Testy: `TMPDIR=tests/tmp_ml pytest tests/test_etl.py` – PASS, ostrzeżenia Pydantic v1 validators oraz brak zapisu cache Pytest (win perms).
- Status: **OK** (pełny zakres §8 dostarczony, ML extras nadal opcjonalne).
