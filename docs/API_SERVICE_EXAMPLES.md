# FastAPI Service - Usage Examples

Complete guide for using the PUR-MOLD-TWIN REST API service.

## Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn
# Or install from project extras (when available):
# pip install pur-mold-twin[api]
```

### 2. Start the Service

```bash
# Development mode (auto-reload)
uvicorn scripts.service_example:app --reload

# Production mode
export PORT=8080
export HOST=0.0.0.0
export CORS_ORIGINS="https://app.example.com,https://dashboard.example.com"
export LOG_LEVEL=INFO
export MODELS_DIR=models

uvicorn scripts.service_example:app --host $HOST --port $PORT --workers 4
```

### 3. Access API Documentation

- **Interactive Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Environment Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | Server port |
| `HOST` | 127.0.0.1 | Server host (use 0.0.0.0 for external access) |
| `CORS_ORIGINS` | * | Comma-separated list of allowed CORS origins |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `MODELS_DIR` | models | Directory containing ML models |

## API Endpoints

### Health Check

**GET /health**

Check service status and ML models availability.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "PUR-MOLD-TWIN API",
  "version": "0.2.0",
  "configuration": {
    "models_dir": "models",
    "log_level": "INFO",
    "cors_enabled": true
  },
  "ml_models": {
    "defect_risk": {
      "status": "loaded",
      "version": "1.0.0",
      "trained_at": "2025-12-02T23:58:27.567030"
    },
    "defect_classifier": {
      "status": "loaded",
      "version": "1.0.0",
      "trained_at": "2025-12-02T23:58:47.184890"
    }
  }
}
```

### Version Info

**GET /version**

Get API version and build information.

```bash
curl http://localhost:8000/version
```

**Response:**
```json
{
  "api_version": "0.2.0",
  "service": "PUR-MOLD-TWIN",
  "git_commit": "bd147e9abc123...",
  "python_version": "3.12.12"
}
```

### Simulate

**POST /simulate**

Run PUR foam molding simulation.

**Minimal request** (using system_id):
```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
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
      "wall_thickness_mm": 5.0,
      "material": "steel"
    }
  }'
```

**Full request** (with all parameters):
```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "PUR_SYSTEM_A",
    "process": {
      "T_iso_in_C": 25.0,
      "T_polyol_in_C": 25.0,
      "T_mold_init_C": 60.0,
      "iso_index": 105.0,
      "shot_size_g": 200.0,
      "T_ambient_C": 20.0,
      "RH_ambient": 0.5,
      "mixing_eff": 0.95,
      "t_inject_s": 2.0,
      "t_hold_s": 5.0
    },
    "mold": {
      "volume_cm3": 1000.0,
      "wall_thickness_mm": 5.0,
      "material": "steel",
      "T_ambient_C": 20.0,
      "h_ext_W_m2K": 10.0
    },
    "quality": {
      "max_demold_time_s": 300.0,
      "max_cure_time_s": 600.0,
      "target_density_kg_m3": 50.0,
      "max_core_temp_C": 220.0,
      "max_pressure_bar": 5.0
    },
    "simulation": {
      "t_max_s": 1000.0,
      "dt_s": 0.1,
      "backend": "solve_ivp"
    }
  }'
```

**Response structure:**
```json
{
  "simulation_id": "sim-abc123...",
  "timestamp": "2025-12-02T23:58:27.567030",
  "conditions": {
    "T_iso_in_C": 25.0,
    "T_polyol_in_C": 25.0,
    "T_mold_init_C": 60.0,
    "iso_index": 105.0,
    "shot_size_g": 200.0
  },
  "summary": {
    "t_gel_s": 85.3,
    "t_rise_s": 205.7,
    "t_cure_s": 412.8,
    "T_core_max_C": 198.5,
    "p_max_bar": 3.2,
    "rho_final_kg_m3": 48.7,
    "fill_ratio_pct": 97.4
  },
  "time_series": {
    "t_s": [0.0, 0.1, 0.2, ...],
    "T_core_C": [60.0, 61.2, 63.5, ...],
    "T_mold_C": [60.0, 60.1, 60.2, ...],
    "p_bar": [1.0, 1.0, 1.1, ...],
    "alpha": [0.0, 0.001, 0.003, ...],
    "rho_kg_m3": [10.0, 12.3, 15.8, ...]
  },
  "ml_predictions": {
    "defect_risk": 0.15,
    "has_defect": false,
    "confidence": 0.87
  },
  "ml_model_metadata": {
    "defect_risk": {
      "version": "1.0.0",
      "trained_at": "2025-12-02T23:58:27",
      "git_commit": "bd147e9...",
      "metrics": {"mae_defect_risk": 0.025}
    },
    "defect_classifier": {
      "version": "1.0.0",
      "trained_at": "2025-12-02T23:58:47",
      "git_commit": "bd147e9...",
      "metrics": {}
    }
  }
}
```

### Optimize

**POST /optimize**

Find optimal process parameters for quality targets.

**Request:**
```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
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
      "wall_thickness_mm": 5.0,
      "material": "steel"
    },
    "quality": {
      "max_demold_time_s": 300.0,
      "max_cure_time_s": 600.0,
      "target_density_kg_m3": 50.0,
      "max_core_temp_C": 200.0,
      "max_pressure_bar": 4.0
    },
    "optimizer_config": {
      "bounds": {
        "T_iso_range_C": [20.0, 30.0],
        "T_polyol_range_C": [20.0, 30.0],
        "T_mold_range_C": [50.0, 70.0],
        "iso_index_range": [100.0, 110.0]
      },
      "max_iterations": 50,
      "preferred_direction": "minimize_pressure"
    }
  }'
```

**Response structure:**
```json
{
  "optimization_id": "opt-xyz789...",
  "timestamp": "2025-12-02T23:58:27.567030",
  "baseline": {
    "process": {
      "T_iso_in_C": 25.0,
      "T_polyol_in_C": 25.0,
      "T_mold_init_C": 60.0,
      "iso_index": 105.0
    },
    "metrics": {
      "t_demold_s": 320.5,
      "t_cure_s": 412.8,
      "T_core_max_C": 198.5,
      "p_max_bar": 3.2,
      "rho_final_kg_m3": 48.7
    },
    "constraints_violated": ["max_demold_time_s"],
    "is_feasible": false
  },
  "optimized": {
    "process": {
      "T_iso_in_C": 27.3,
      "T_polyol_in_C": 26.8,
      "T_mold_init_C": 65.0,
      "iso_index": 107.2
    },
    "metrics": {
      "t_demold_s": 285.3,
      "t_cure_s": 385.2,
      "T_core_max_C": 195.8,
      "p_max_bar": 2.9,
      "rho_final_kg_m3": 50.2
    },
    "constraints_violated": [],
    "is_feasible": true
  },
  "improvement": {
    "t_demold_s": -35.2,
    "t_cure_s": -27.6,
    "T_core_max_C": -2.7,
    "p_max_bar": -0.3,
    "rho_final_kg_m3": 1.5
  },
  "iterations": 42,
  "convergence": "success"
}
```

## Python Client Example

```python
import requests

API_URL = "http://localhost:8000"

def simulate(system_id: str, process: dict, mold: dict) -> dict:
    """Run simulation."""
    response = requests.post(
        f"{API_URL}/simulate",
        json={
            "system_id": system_id,
            "process": process,
            "mold": mold,
        }
    )
    response.raise_for_status()
    return response.json()

def optimize(system_id: str, process: dict, mold: dict, quality: dict) -> dict:
    """Run optimization."""
    response = requests.post(
        f"{API_URL}/optimize",
        json={
            "system_id": system_id,
            "process": process,
            "mold": mold,
            "quality": quality,
        }
    )
    response.raise_for_status()
    return response.json()

# Example usage
result = simulate(
    system_id="PUR_SYSTEM_A",
    process={
        "T_iso_in_C": 25.0,
        "T_polyol_in_C": 25.0,
        "T_mold_init_C": 60.0,
        "iso_index": 105.0,
        "shot_size_g": 200.0,
    },
    mold={
        "volume_cm3": 1000.0,
        "wall_thickness_mm": 5.0,
        "material": "steel",
    }
)

print(f"Gel time: {result['summary']['t_gel_s']} s")
print(f"Defect risk: {result['ml_predictions']['defect_risk']}")
```

## Error Handling

### 400 Bad Request
Invalid input parameters or missing required fields.

```json
{
  "detail": "Either 'system' or 'system_id' field must be provided."
}
```

### 500 Internal Server Error
Simulation or optimization failed due to internal error.

```json
{
  "detail": "Internal error: Simulation diverged at t=150.0s"
}
```

## Performance Considerations

- **Simulation time**: ~0.1-0.5s per request (depends on t_max_s and backend)
- **Optimization time**: ~5-30s (depends on max_iterations and complexity)
- **Concurrent requests**: Use `--workers N` for parallel processing
- **Rate limiting**: Not implemented by default (add as needed)

## Security Notes

**⚠️ This is a reference implementation without authentication.**

For production:
1. Add API key or JWT authentication
2. Implement rate limiting (e.g., with slowapi)
3. Use HTTPS/TLS
4. Configure CORS for specific domains only
5. Add input validation and sanitization
6. Set up monitoring and alerting

## Monitoring

Structured JSON logs include:
- Request method and path
- Client IP
- Status codes
- Response times
- Error details

Example log entry:
```json
{
  "timestamp": "2025-12-02 23:58:27,567",
  "level": "INFO",
  "logger": "scripts.service_example",
  "message": "Simulation completed successfully",
  "module": "service_example",
  "function": "simulate_endpoint",
  "line": 285,
  "endpoint": "POST /simulate"
}
```

## Deployment

### Docker Example

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install -e .[api]

ENV PORT=8000
ENV HOST=0.0.0.0
ENV LOG_LEVEL=INFO

CMD ["uvicorn", "scripts.service_example:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pur-mold-twin-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pur-mold-twin-api
  template:
    metadata:
      labels:
        app: pur-mold-twin-api
    spec:
      containers:
      - name: api
        image: pur-mold-twin:latest
        ports:
        - containerPort: 8000
        env:
        - name: PORT
          value: "8000"
        - name: HOST
          value: "0.0.0.0"
        - name: LOG_LEVEL
          value: "INFO"
        - name: CORS_ORIGINS
          value: "https://app.example.com"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

## Troubleshooting

### Service won't start
- Check FastAPI/uvicorn installed: `pip list | grep -E "fastapi|uvicorn"`
- Verify Python version: Python 3.8+ required
- Check port availability: `lsof -i :8000`

### ML models not loading
- Verify MODELS_DIR path exists and contains .pkl files
- Check manifest.json exists: `ls $MODELS_DIR/manifest.json`
- Install ML extras: `pip install scikit-learn joblib`

### CORS errors
- Add your domain to CORS_ORIGINS: `export CORS_ORIGINS="https://yourdomain.com"`
- For development, use `CORS_ORIGINS="*"` (not recommended for production)

### Performance issues
- Increase workers: `--workers 4`
- Use production ASGI server: gunicorn with uvicorn workers
- Enable caching for material systems
- Use faster ODE backend (JAX or SUNDIALS)
