# TODO1 - Punkt 12 (ML i logi) - Changelog

## 2025-12-01
- Utworzono `docs/ML_LOGGING.md` opisujacy schemat logow procesu, liste featurów (raw + roznice vs symulacja) oraz plan modeli ML (`defect_risk`, klasyfikacja defektow, diagnozy).
- Zaktualizowano `readme.md` (sekcja 13) i `todo1.md` aby odnotowac wykonanie §12 i wskazac Paczke ML/ETL.

## 2025-05-06
- Dodano testy pokrywajace przypadki brakujacych zaleznosci (pyarrow/scikit-learn) oraz brakow w logach procesowych i raportowaniu ML/ETL (`tests/test_etl.py`, `tests/test_logging_features.py`, `tests/test_ml_baseline.py`, `tests/test_reporting.py`).
