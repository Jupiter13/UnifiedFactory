"""FastAPI API implementation for AeroDesign-AI."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextcontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response

from aerodesign_ai.models.schemas import DesignInput, DesignOutput, DesignStatus, BOMItem
from aerodesign_ai.graph import run_design_pipeline
from aerodesign_ai.tools.storage_tool import DesignStorage, RetrieveDesign


# Metrics
design_requests_total = Counter(
    "aerodesign_requests_total", "Total design requests", ["status"]
)
design_duration_seconds = Histogram(
    "aerodesign_duration_seconds", "Design request duration", ["stage"]
)
compliance_pass_rate = Counter(
    "aerodesign_compliance_pass_total", "Compliance check pass count"
)
compliance_fail_rate = Counter(
    "aerodesign_compliance_fail_total", "Compliance check fail count"
)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


def get_storage() -> DesignStorage:
    """Get design storage instance."""
    return DesignStorage()


@asynccontextcontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="AeroDesign-AI API",
    description="Agentic aircraft design engine powered by LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


@app.post("/designs/submit", response_model=Dict[str, str], status_code=status.HTTP_202_ACCEPTED)
async def submit_design(design_input: DesignInput) -> Dict[str, str]:
    """Submit a new aircraft design request.

    Args:
        design_input: Design parameters

    Returns:
        Dictionary with design_id
    """
    try:
        # Run the design pipeline
        import uuid
        design_id = f"DESIGN-{uuid.uuid4().hex[:8].upper()}"
        
        result = run_design_pipeline(
            payload_tons=design_input.payload_tons,
            material=design_input.material,
            engine=design_input.engine,
            user_id=design_input.user_id,
            optional_constraints=design_input.optional_constraints,
        )

        # Extract design_id from result
        design_id = result.get("version_id", design_id)
        
        design_requests_total.labels(status="submitted").inc()
        
        return {"design_id": design_id, "status": result.get("status", "running")}

    except Exception as e:
        design_requests_total.labels(status="error").inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Design submission failed: {str(e)}"
        )


@app.get("/designs/{design_id}/status", response_model=DesignStatus)
async def get_design_status(design_id: str, storage: DesignStorage = Depends(get_storage)) -> DesignStatus:
    """Poll design status.

    Args:
        design_id: Design identifier
        storage: Storage dependency

    Returns:
        Design status
    """
    design = storage.retrieve(design_id)
    if design is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Design {design_id} not found"
        )

    return DesignStatus(
        design_id=design_id,
        status=design.status,
        progress=100 if design.status == "completed" else 50,
        message=None
    )


@app.get("/designs/{design_id}/metadata", response_model=DesignOutput)
async def get_design_metadata(design_id: str, storage: DesignStorage = Depends(get_storage)) -> DesignOutput:
    """Retrieve complete design metadata.

    Args:
        design_id: Design identifier
        storage: Storage dependency

    Returns:
        Complete design output
    """
    design = storage.retrieve(design_id)
    if design is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Design {design_id} not found"
        )

    return DesignOutput(
        design_id=design_id,
        payload_tons=design.payload_tons,
        material=design.material,
        engine=design.engine,
        geometry=design.geometry or {},
        optimization_metrics=design.optimization_metrics or {},
        compliance_report=design.compliance_report or {"passed": False, "violations": [], "warnings": []},
        cad_file_url=design.cad_file_path or "",
        bom=[BOMItem(**item) for item in design.bom] if design.bom else [],
        timestamp=design.timestamp,
        total_cost_usd=design.total_weight_kg or 0
    )


@app.get("/designs/{design_id}/report")
async def get_compliance_report(design_id: str, storage: DesignStorage = Depends(get_storage)) -> Dict[str, Any]:
    """Retrieve compliance report.

    Args:
        design_id: Design identifier
        storage: Storage dependency

    Returns:
        Compliance report
    """
    design = storage.retrieve(design_id)
    if design is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Design {design_id} not found"
        )

    compliance = design.compliance_report
    if compliance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance report for {design_id} not found"
        )

    is_passed = compliance.get("passed", False)
    if is_passed:
        compliance_pass_rate.inc()
    else:
        compliance_fail_rate.inc()

    return compliance


@app.get("/designs/{design_id}/bom")
async def get_bom(design_id: str, storage: DesignStorage = Depends(get_storage)) -> List[Dict[str, Any]]:
    """Retrieve Bill of Materials.

    Args:
        design_id: Design identifier
        storage: Storage dependency

    Returns:
        List of BOM items
    """
    design = storage.retrieve(design_id)
    if design is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Design {design_id} not found"
        )

    return design.bom or []


@app.get("/designs/{design_id}/download")
async def download_cad(design_id: str, storage: DesignStorage = Depends(get_storage)) -> Response:
    """Download CAD STEP file.

    Args:
        design_id: Design identifier
        storage: Storage dependency

    Returns:
        STEP file stream
    """
    design = storage.retrieve(design_id)
    if design is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Design {design_id} not found"
        )

    cad_path = design.cad_file_path
    if not cad_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CAD file for {design_id} not found"
        )

    from pathlib import Path
    file_path = Path(cad_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CAD file not found on disk"
        )

    return Response(
        content=file_path.read_bytes(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{design_id}.step"'}
    )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return ErrorResponse(
        error=str(exc.detail),
        detail=exc.headers.get("detail")
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    design_requests_total.labels(status="error").inc()
    return ErrorResponse(
        error="Internal server error",
        detail=str(exc)
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=12000)
