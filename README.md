# AFW-D Engine

Agentic AI Fixed-Wing Aircraft Design Engine built with LangGraph.

## Overview

AFW-D is an autonomous aircraft design assistant that uses LangGraph to orchestrate a multi-step workflow for fixed-wing aircraft design. It takes user constraints (payload, materials, engines) and generates optimized aircraft designs with CFD/FEA simulations, cost estimates, and regulatory compliance checks.

## Features

- **Parametric Design Generation**: Create aircraft designs from payload and constraint specifications
- **Multi-Objective Optimization**: Evolutionary optimization for design refinement
- **CFD/FEA Simulation**: Reduced-order aerodynamic and structural analysis
- **Regulatory Compliance**: FAA/ICAO compliance checking
- **CAD Export**: Generate STEP/IGES/STL files
- **Version Control**: Store and retrieve design history

## Architecture

The system uses a state machine workflow with the following nodes:
- InputCollector → MaterialSelector → EngineSelector → DesignGenerator → SimulationRunner → CostEstimator → ComplianceChecker → OptimizationLoop → Exporter → FeedbackHandler

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Python API

```python
from afw_d.graph import run_design

# Run design workflow
result = run_design(
    payload_kg=1000.0,
    material_family="Al-Mg-Si",
    engine_family="Turboprop-A"
)
```

### API Server

```bash
uvicorn afw_d.api:app --host 0.0.0.0 --port 8000
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/design/submit` | POST | Submit a new design request |
| `/design/status/{id}` | GET | Get design status |
| `/design/download/{id}` | GET | Download CAD file |
| `/design/feedback/{id}` | POST | Submit feedback |
| `/design/history/{id}` | GET | Get design history |
| `/health` | GET | Health check |

## Testing

```bash
pytest tests/ -v
```

## Docker

```bash
docker build -t afwd-engine:latest .
docker run -p 8000:8000 afwd-engine:latest
```

## Deployment

### Helm

```bash
helm install afwd-engine ./helm
```

### Kubernetes

```bash
kubectl apply -f helm/templates/deployment.yaml
```

## Configuration

Environment variables:
- `LOG_LEVEL`: Logging level (default: INFO)
- `REDIS_URL`: Redis connection URL
- `DATABASE_URL`: PostgreSQL connection URL
- `LANGSMITH_API_KEY`: LangSmith API key for tracing
- `OPENAI_API_KEY`: OpenAI API key (if using OpenAI models)

## License

MIT License