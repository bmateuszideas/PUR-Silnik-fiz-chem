PUR-MOLD-TWIN — Service example and quick run
=============================================

This document describes how to run the reference FastAPI service locally.

Prerequisites
-------------
- Python environment with project dependencies. Recommended minimal extras:
  - `fastapi`, `uvicorn[standard]`, `httpx` (for TestClient)

Run locally
-----------
Start the app with uvicorn (from project root):

```powershell
# run development server
python -m uvicorn src.pur_mold_twin.service.app:app --reload --port 8000
```

Configuration
-------------
You can control service settings via environment variables (prefix `PUR_MT_`):

- `PUR_MT_SERVICE_TITLE` — service title shown in OpenAPI UI
- `PUR_MT_SERVICE_VERSION` — service version string
- `PUR_MT_ALLOW_ORIGINS` — comma-separated list of allowed CORS origins (default `*`)
- `PUR_MT_LOG_LEVEL` — logging level (e.g. `INFO`, `DEBUG`)
- `PUR_MT_ENABLE_REQUEST_LOGGING` — `1`/`0` or `true`/`false`

Example (PowerShell):

```powershell
$env:PUR_MT_ALLOW_ORIGINS="http://localhost:3000"
$env:PUR_MT_LOG_LEVEL="DEBUG"
python -m uvicorn src.pur_mold_twin.service.app:app --reload
```

Endpoints
---------
- `GET /health` — health check
- `POST /simulate` — run simulation (JSON payload per API contract)
- `POST /ml/predict` — request ML predictions (JSON payload)

Notes
-----
- The service uses a small env-backed `Settings` fallback if `pydantic-settings` is not present; installing `pydantic-settings` (or pydantic v2 compatible stack) enables typed settings.
- For production deploy, wrap with a process manager (systemd / gunicorn / uvicorn workers) and configure secure CORS and logging.
