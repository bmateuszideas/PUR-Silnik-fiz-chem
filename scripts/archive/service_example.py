"""
Reference FastAPI service exposing PUR-MOLD-TWIN API.

Requires extra dependencies (fastapi, uvicorn), which are not installed by default.

Usage (after installing fastapi/uvicorn):
    uvicorn scripts.service_example:app --reload
"""

from __future__ import annotations

from typing import Any, Dict

try:
    from fastapi import FastAPI, HTTPException
except ModuleNotFoundError:  # pragma: no cover
    FastAPI = None  # type: ignore
    HTTPException = Exception  # type: ignore

from pur_mold_twin.service.api import APIService


if FastAPI is not None:  # pragma: no cover - only tested when fastapi is available
    app = FastAPI(title="PUR-MOLD-TWIN API", version="0.2.0")
    service = APIService()

    @app.post("/simulate")
    async def simulate_endpoint(payload: Dict[str, Any]):
        try:
            return service.simulate(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    @app.post("/optimize")
    async def optimize_endpoint(payload: Dict[str, Any]):
        try:
            return service.optimize(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    @app.get("/health")
    async def health():
        return {"status": "ok"}

else:
    app = None  # type: ignore
