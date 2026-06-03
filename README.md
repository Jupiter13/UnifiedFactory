# AeroDesign-AI

Agentic aircraft design engine powered by LangGraph.

## Overview

AeroDesign-AI is an autonomous fixed-wing aircraft design assistant that generates complete, manufacturable aircraft designs based on payload capacity, material selection, and engine specifications. It uses a LangGraph-based agentic pipeline to orchestrate multi-objective optimization, compliance checking, CAD export, and bill of materials generation.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    UI / API Gateway                         │
│              (FastAPI REST Endpoints)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Graph                              │
│       (LangGraph State Machine Pipeline)                    │
│         Start → Validate → Fetch → Generate                 │
│         → Optimize → Compliance → CAD → BOM → Store          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Tools Layer                              │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │ Material  │ │  Engine   │ │Compliance │ │Optimizer  │  │
│  │  Props    │ │  Specs    │ │  Check    │ │           │  │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘  │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │    CAD    │ │   BOM     │ │  Storage  │ │ Retrieval │  │
│  │  Export   │ │ Generator │ │           │ │           │  │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
pip install -r aerodesign_ai/requirements.txt
```

## Quick Start

```python
from aerodesign_ai.graph import run_design_pipeline

# Run a complete design pipeline
result = run_design_pipeline(
    payload_tons=2.0,
    material="al7075_t6",
    engine="lycoming_io720",
)

print(f"Design ID: {result['version_id']}")
print(f"Status: {result['status']}")
print(f"Wing Span: {result['geometry']['wing_span_m']} m")
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/designs/submit` | POST | Submit new design request |
| `/designs/{id}/status` | GET | Poll design status |
| `/designs/{id}/metadata` | GET | Retrieve design metadata |
| `/designs/{id}/report` | GET | Get compliance report |
| `/designs/{id}/bom` | GET | Get bill of materials |
| `/designs/{id}/download` | GET | Download CAD file |

## Testing

```bash
python -m pytest aerodesign_ai/tests/ -v
```