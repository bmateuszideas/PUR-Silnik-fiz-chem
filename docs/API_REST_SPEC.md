# REST API SPEC - PUR-MOLD-TWIN (TODO3)

Specyfikacja referencyjnego REST API dla PUR-MOLD-TWIN. API jest zorientowane na integracje z innymi systemami (MES/SCADA, aplikacje analityczne) i opakowuje istniejace mozliwosci biblioteki/CLI.

## 1. Przeglad

- Baza: `http://host:port/`
- Wersjonowanie: pierwszy pilot moze korzystac z `/api/v1/...`, ale ponizsza specyfikacja opisuje logike niezaleznie od prefiksu.
- Komunikacja: JSON (`Content-Type: application/json`).
- Bledy: standardowy format
  ```json
  { "detail": "opis bledu", "code": "ERROR_CODE" }
  ```

## 2. Endpointy

### 2.1 POST `/simulate`

Uruchamia pojedyncza symulacje 0D (lub 1D experimental) dla zadanych danych materialowych/procesowych.

**Wejscie (body JSON)**:

```json
{
  "system": { /* MaterialSystem zgodny z material_db.models */ },
  "process": { /* pola ProcessConditions */ },
  "mold": { /* pola MoldProperties */ },
  "quality": { /* pola QualityTargets (opcjonalne, fallback do domyslnych) */ },
  "simulation": { /* opcjonalny SimulationConfig (backend, dimension, time_step, itd.) */ }
}
```

Minimalny wariant moze korzystac z `system_id` zamiast pelnego `system`, jezeli serwis ma dostep do `configs/systems/...`:

```json
{
  "system_id": "SYSTEM_R1",
  "process": { ... },
  "mold": { ... },
  "quality": { ... },
  "simulation": { ... }
}
```

**Wyjscie**:

- JSON zgodny z `SimulationResult.to_dict()` (profile czasowe, KPI `t_demold_*`, `p_max_Pa`, `rho_moulded`, `quality_status`, diagnostyka, woda/RH).
- Dodatkowo, jezeli backend ML jest wlaczony po stronie serwisu:
  - `defect_risk_pred`, `defect_class_pred` – pola dodane przez inference.

### 2.2 POST `/optimize`

Uruchamia optymalizator procesu dla jednego scenariusza referencyjnego.

**Wejscie**:

```json
{
  "system": { /* MaterialSystem */ },
  "process": { /* ProcessConditions */ },
  "mold": { /* MoldProperties */ },
  "quality": { /* QualityTargets */ },
  "optimizer_config": { /* pola OptimizationConfig/OptimizerBounds */ }
}
```

Lub wariant z `system_id`:

```json
{
  "system_id": "SYSTEM_R1",
  "process": { ... },
  "mold": { ... },
  "quality": { ... },
  "optimizer_config": { ... }
}
```

**Wyjscie**:

- JSON z polami:
  - `baseline` – metryki dla wejciowych nastaw (jak w CLI optimize),
  - `optimized` – metryki dla najlepszego kandydata,
  - `candidate` – wartosci decyzyjne (temperatury, `t_demold`, itp.),
  - opcjonalnie lista `history` (skrocone informacje o kolejnych probach).

### 2.3 POST `/ml/predict`

Wykonuje inference modeli ML na podstawie feature row (np. po stronie klienta).

**Wejscie**:

```json
{
  "features": { /* pojedynczy wiersz features zgodny z ML_LOGGING (schema data/schema.py) */ }
}
```

**Wyjscie**:

```json
{
  "defect_risk_pred": 0.18,
  "defect_class_pred": 1,
  "model_version": "baseline_v1"
}
```

Jezeli modele sa niedostepne, serwis moze zwrocic kod bledu `503` z `code: "ML_UNAVAILABLE"`.

### 2.4 GET `/health`

Zwraca zdolnosc serwisu do obslugi zapytan.

**Wyjscie**:

```json
{ "status": "ok" }
```

Kod `200` oznacza poprawne dzialanie; w przypadku degradacji serwis moze zwrocic `503` z dodatkowymi informacjami.

### 2.5 GET `/version`

Zwraca informacje wersyjne o pakiecie/serwisie.

**Wyjscie**:

```json
{
  "package": "pur-mold-twin",
  "version": "0.2.0",
  "git_hash": "abc123",
  "build_date": "2025-12-02"
}
```

## 3. Implementacja referencyjna

- Warstwa validacji i mapowania JSON -> modele: `src/pur_mold_twin/service/api.py`.
- Referencyjny serwis FastAPI: `scripts/service_example.py`:
  - rejestruje powyzsze endpointy,
  - korzysta z `MVP0DSimulator`, `ProcessOptimizer` oraz `ml.inference`,
  - udostepnia OpenAPI/Swagger UI.

## 4. Bezpieczenstwo i limity

- Autoryzacja/uwierzytelnianie nie sa czescia TODO3; zaklada sie, ze serwis bedzie za wewnetrznym API gateway/NGINX.
- Serwis powinien:
  - limitowac rozmiar requestu (np. 1-2 MB),
  - wprowadzic proste limity czasowe na /simulate i /optimize,
  - logowac requesty/odpowiedzi w sposob zgodny z polityka danych klienta.
