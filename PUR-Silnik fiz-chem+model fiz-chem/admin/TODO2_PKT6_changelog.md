# TODO2 - Punkt 6 (Kalibracja i walidacja) - Changelog

## 2025-12-06
- Stworzono pakiet `src/pur_mold_twin/calibration/` z loaderem datasetów (`loader.py`) zgodnym z `docs/CALIBRATION.md` (meta YAML + pomiary CSV/Parquet).
- Dodano przykładowy zestaw testowy (`tests/data/calibration/sample/...`) oraz testy `tests/test_calibration_loader.py` weryfikujące happy-path i błąd przy braku `meta.yaml`.
- `todo2.md` – pierwszy bullet §6 oznaczony jako wykonany; dokumentacja/stack nie wymagają dodatkowych zmian.
- Test: `pytest tests/test_calibration_loader.py` – PASS (ostrzeżenia Pydantic legacy / uprawnienia tmpdir). 
- Status: **OK** (loader datasetów gotowy).

## 2025-12-06 (cz.2)
- Dodano moduły `calibration/cost.py` (koszt: czasy TDS, RMSE T_core, p_max, rho) oraz `calibration/fit.py` (least_squares nad callbackiem symulacji).
- Testy kalibracji: `tests/test_calibration.py` (RMSE, agregacja kosztów, syntetyczne dopasowanie parametrów) – PASS; uzupełniono `todo2.md` o kolejne odhaczone bullet’y §6.
- Status: **OK** (funkcje kosztu, kalibracja i testy regresyjne gotowe).

## 2025-12-07
- Dodano skrypty CLI wspierające kalibrację: `scripts/calibrate_kinetics.py` (dopasowanie czasów cream/gel/rise), `scripts/compare_shot.py` (RMSE T_core, Δp_max, Δt_demold), `scripts/calibration_report.py` (PASS/FAIL vs tolerancje) oraz `scripts/plot_kinetics.py` (wykres alpha(t) z markerami TDS).
- Zaktualizowano `docs/CALIBRATION.md` o sekcję „Automatyzacja (skrypty)” i odhaczono pozostałe bullet’y TODO2 §6; `todo2.md` zaktualizowane.
- Testy: `pytest tests/test_calibration_loader.py tests/test_calibration.py` – PASS (ostrzeżenia Pydantic legacy).
- Status: **OK** (TODO2 §6 ukończony).
