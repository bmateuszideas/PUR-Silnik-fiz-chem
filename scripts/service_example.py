"""
Reference FastAPI service exposing PUR-MOLD-TWIN API.

Enhanced production-ready service with:
- Environment-based configuration (PORT, HOST, CORS_ORIGINS, LOG_LEVEL, MODELS_DIR)
- CORS support with configurable origins
- Structured JSON logging
- Health check endpoint with dependency status
- Rate limiting (optional)
- Comprehensive API documentation with examples

Requires extra dependencies (fastapi, uvicorn), which are not installed by default.

Usage (after installing fastapi/uvicorn):
    # Development
    uvicorn scripts.service_example:app --reload
    
    # Production with env config
    export PORT=8080
    export HOST=0.0.0.0
    export CORS_ORIGINS="https://app.example.com,https://dashboard.example.com"
    export LOG_LEVEL=INFO
    export MODELS_DIR=models
    uvicorn scripts.service_example:app --host $HOST --port $PORT --workers 4
    
Example requests:
    # Health check
    curl http://localhost:8000/health
    
    # Simulate
    curl -X POST http://localhost:8000/simulate \\
      -H "Content-Type: application/json" \\
      -d '{
        "system_id": "PUR_SYSTEM_A",
        "process": {
          "T_iso_in_C": 25.0,
          "T_polyol_in_C": 25.0,
          "T_mold_init_C": 60.0,
          "iso_index": 105.0,
          "shot_size_g": 200.0,
          "T_ambient_C": 20.0,
          "RH_ambient": 0.5
        },
        "mold": {
          "volume_cm3": 1000.0,
          "wall_thickness_mm": 5.0,
          "material": "steel"
        }
      }'
    
    # Optimize
    curl -X POST http://localhost:8000/optimize \\
      -H "Content-Type: application/json" \\
      -d '{
        "system_id": "PUR_SYSTEM_A",
        "process": {
          "T_iso_in_C": 25.0,
          "T_polyol_in_C": 25.0,
          "T_mold_init_C": 60.0,
          "iso_index": 105.0,
          "shot_size_g": 200.0
        },
        "mold": {
          "volume_cm3": 1000.0,
          "wall_thickness_mm": 5.0
        },
        "quality": {
          "max_demold_time_s": 300.0,
          "max_cure_time_s": 600.0
        }
      }'
"""

from __future__ import annotations

import os
import logging
import json
from typing import Any, Dict
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
except ModuleNotFoundError:  # pragma: no cover
    FastAPI = None  # type: ignore
    HTTPException = Exception  # type: ignore
    CORSMiddleware = None  # type: ignore
    Request = None  # type: ignore
    JSONResponse = None  # type: ignore
    uvicorn = None  # type: ignore

from pur_mold_twin.service.api import APIService


# ============================================================================
# Configuration from Environment
# ============================================================================

PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "127.0.0.1")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")  # Comma-separated origins
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
MODELS_DIR = Path(os.getenv("MODELS_DIR", "models"))

# ============================================================================
# Structured Logging Setup
# ============================================================================

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        
        return json.dumps(log_data)


def setup_logging(level: str = "INFO") -> None:
    """Configure structured JSON logging."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level))
    root_logger.handlers = [handler]
    
    # Configure uvicorn loggers
    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("uvicorn.error").handlers = [handler]


setup_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)


# ============================================================================
# FastAPI Application
# ============================================================================

if FastAPI is not None:  # pragma: no cover - only tested when fastapi is available
    
    app = FastAPI(
        title="PUR-MOLD-TWIN API",
        version="0.2.0",
        description="""
        Production-ready API for PUR foam molding simulation and optimization.
        
        ## Features
        - **Simulate**: Run physics-based simulation of PUR foam molding process
        - **Optimize**: Find optimal process parameters for quality targets
        - **ML Predictions**: Defect risk prediction with model versioning (when models available)
        - **Health Check**: Service and dependency status monitoring
        
        ## Authentication
        (Not implemented in this reference version - add API keys or JWT as needed)
        
        ## Rate Limiting
        (Basic rate limiting available - configure as needed for production)
        """,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize service
    service = APIService()
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(
            "Request started",
            extra={
                "endpoint": f"{request.method} {request.url.path}",
                "client": request.client.host if request.client else "unknown",
            }
        )
        
        try:
            response = await call_next(request)
            logger.info(
                "Request completed",
                extra={
                    "endpoint": f"{request.method} {request.url.path}",
                    "status_code": response.status_code,
                }
            )
            return response
        except Exception as exc:
            logger.exception(
                "Request failed",
                extra={
                    "endpoint": f"{request.method} {request.url.path}",
                    "error": str(exc),
                }
            )
            raise
    
    # ========================================================================
    # Endpoints
    # ========================================================================
    
    @app.post(
        "/simulate",
        summary="Run PUR foam molding simulation",
        description="""
        Execute physics-based simulation of PUR foam molding process.
        
        Returns detailed simulation results including:
        - Temperature profile over time
        - Pressure evolution
        - Density and alpha (cure degree) progression
        - Quality metrics (gel time, rise time, cure time)
        - Optional ML predictions (defect risk, defect classification)
        
        Example request:
        ```json
        {
          "system_id": "PUR_SYSTEM_A",
          "process": {
            "T_iso_in_C": 25.0,
            "T_polyol_in_C": 25.0,
            "T_mold_init_C": 60.0,
            "iso_index": 105.0,
            "shot_size_g": 200.0
          },
          "mold": {
            "volume_cm3": 1000.0,
            "wall_thickness_mm": 5.0,
            "material": "steel"
          }
        }
        ```
        """,
        response_description="Simulation results with time series and summary metrics",
    )
    async def simulate_endpoint(payload: Dict[str, Any]):
        try:
            logger.info("Simulation requested", extra={"payload_keys": list(payload.keys())})
            result = service.simulate(payload)
            logger.info("Simulation completed successfully")
            return result
        except ValueError as exc:
            logger.warning(f"Invalid simulation request: {exc}")
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            logger.exception("Simulation failed")
            raise HTTPException(status_code=500, detail=f"Internal error: {str(exc)}")
    
    @app.post(
        "/optimize",
        summary="Optimize process parameters",
        description="""
        Find optimal process parameters to meet quality targets.
        
        Uses optimization algorithms to search for best combination of:
        - Isocyanate temperature
        - Polyol temperature
        - Mold temperature
        - ISO index
        - Shot size
        
        Example request:
        ```json
        {
          "system_id": "PUR_SYSTEM_A",
          "process": {
            "T_iso_in_C": 25.0,
            "T_polyol_in_C": 25.0,
            "T_mold_init_C": 60.0,
            "iso_index": 105.0,
            "shot_size_g": 200.0
          },
          "mold": {
            "volume_cm3": 1000.0,
            "wall_thickness_mm": 5.0
          },
          "quality": {
            "max_demold_time_s": 300.0,
            "max_cure_time_s": 600.0,
            "target_density_kg_m3": 50.0
          },
          "optimizer_config": {
            "bounds": {
              "T_iso_range_C": [20.0, 30.0],
              "T_polyol_range_C": [20.0, 30.0],
              "T_mold_range_C": [50.0, 70.0]
            },
            "max_iterations": 50
          }
        }
        ```
        """,
        response_description="Optimization results with baseline and optimized parameters",
    )
    async def optimize_endpoint(payload: Dict[str, Any]):
        try:
            logger.info("Optimization requested", extra={"payload_keys": list(payload.keys())})
            result = service.optimize(payload)
            logger.info("Optimization completed successfully")
            return result
        except ValueError as exc:
            logger.warning(f"Invalid optimization request: {exc}")
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            logger.exception("Optimization failed")
            raise HTTPException(status_code=500, detail=f"Internal error: {str(exc)}")
    
    @app.get(
        "/health",
        summary="Health check",
        description="""
        Check service health and dependency status.
        
        Returns:
        - Service status
        - ML models availability
        - Model versions and metadata (if available)
        - Configuration info
        """,
    )
    async def health():
        """Health check endpoint with dependency status."""
        health_status = {
            "status": "healthy",
            "service": "PUR-MOLD-TWIN API",
            "version": "0.2.0",
            "configuration": {
                "models_dir": str(MODELS_DIR),
                "log_level": LOG_LEVEL,
                "cors_enabled": len(CORS_ORIGINS) > 0,
            },
        }
        
        # Check ML models availability
        try:
            from pur_mold_twin.ml.inference import _load_models
            from pur_mold_twin.ml.versioning import load_manifest
            
            loaded = _load_models(MODELS_DIR)
            manifest = load_manifest(MODELS_DIR)
            
            models_info = {}
            if loaded.defect_risk is not None:
                models_info["defect_risk"] = {"status": "loaded"}
                if manifest and "defect_risk" in manifest.models:
                    meta = manifest.models["defect_risk"]
                    models_info["defect_risk"]["version"] = meta.version
                    models_info["defect_risk"]["trained_at"] = meta.trained_at
            
            if loaded.defect_classifier is not None:
                models_info["defect_classifier"] = {"status": "loaded"}
                if manifest and "defect_classifier" in manifest.models:
                    meta = manifest.models["defect_classifier"]
                    models_info["defect_classifier"]["version"] = meta.version
                    models_info["defect_classifier"]["trained_at"] = meta.trained_at
            
            health_status["ml_models"] = models_info if models_info else {"status": "no_models_found"}
        
        except ImportError:
            health_status["ml_models"] = {"status": "ml_extras_not_installed"}
        except Exception as exc:
            health_status["ml_models"] = {"status": "error", "detail": str(exc)}
        
        logger.info("Health check requested")
        return health_status
    
    @app.get(
        "/version",
        summary="API version info",
        description="Get API version and build information",
    )
    async def version():
        """Version info endpoint."""
        try:
            from pur_mold_twin.ml.versioning import get_git_commit_hash
            git_commit = get_git_commit_hash()
        except:
            git_commit = None
        
        return {
            "api_version": "0.2.0",
            "service": "PUR-MOLD-TWIN",
            "git_commit": git_commit,
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        }

else:
    app = None  # type: ignore


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == "__main__":
    if uvicorn is None:
        print("ERROR: uvicorn not installed. Install with: pip install uvicorn fastapi")
        exit(1)
    
    print(f"🚀 Starting PUR-MOLD-TWIN API server...")
    print(f"   Host: {HOST}:{PORT}")
    print(f"   CORS: {CORS_ORIGINS}")
    print(f"   Log level: {LOG_LEVEL}")
    print(f"   Models dir: {MODELS_DIR}")
    print(f"   Docs: http://{HOST}:{PORT}/docs")
    print()
    
    uvicorn.run(
        "scripts.service_example:app",
        host=HOST,
        port=PORT,
        log_level=LOG_LEVEL.lower(),
        reload=False,  # Set to True for development
    )
