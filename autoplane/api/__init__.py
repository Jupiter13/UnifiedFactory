"""FastAPI REST API for the AutoPlane Design Agent.

Provides endpoints for:
- Starting design jobs
- Polling job status
- Downloading reports and CAD files
- Submitting parameter feedback
- Listing design history
"""

import logging
import os
import uuid
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, Field
from jose import jwt, JWTError

from autoplane.models.state import (
    DesignState,
    DesignJob,
    DesignJobResponse,
    DesignStatusResponse,
)
from autoplane.agent import get_agent, AutoPlaneAgent
from autoplane.memory import get_memory, DesignMemory

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.environ.get("JWT_SECRET", "autoplane-secret-key-change-in-production")
ALGORITHM = "HS256"

app = FastAPI(
    title="AutoPlane Designer API",
    description="Autonomous aircraft design agent API",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class FeedbackRequest(BaseModel):
    """Request model for parameter feedback."""
    wing_span: Optional[float] = None
    wing_area: Optional[float] = None
    fuselage_length: Optional[float] = None
    tail_area: Optional[float] = None
    material: Optional[str] = None
    engine: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    job_id: str
    state: DesignState


# Authentication
async def verify_token(authorization: str = Header(None)) -> str:
    """Verify JWT token and return user ID.

    Args:
        authorization: Authorization header

    Returns:
        User ID

    Raises:
        HTTPException: If token is invalid
    """
    if not authorization:
        return "anonymous"  # Allow anonymous for now

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
            )
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub", "anonymous")
    except (ValueError, JWTError) as e:
        logger.warning(f"Token verification failed: {e}")
        return "anonymous"


# Dependencies
def get_agent_instance() -> AutoPlaneAgent:
    """Get the agent instance."""
    return get_agent()


def get_memory_instance() -> DesignMemory:
    """Get the memory instance."""
    return get_memory()


# Endpoints
@app.post("/design/start", response_model=DesignJobResponse)
async def start_design(
    job: DesignJob,
    user_id: str = Depends(verify_token),
    agent: AutoPlaneAgent = Depends(get_agent_instance),
    memory: DesignMemory = Depends(get_memory_instance),
) -> DesignJobResponse:
    """Start a new design job.

    Args:
        job: Design job parameters
        user_id: User identifier (from token)
        agent: AutoPlane agent instance
        memory: Memory instance

    Returns:
        Job ID for tracking
    """
    job_id = str(uuid.uuid4())

    logger.info(f"Starting design job {job_id} for user {user_id}, payload={job.payload_kg}kg")

    # Start the design in background (for now, run synchronously)
    state = agent.start_design(
        payload_kg=job.payload_kg,
        material=job.material,
        engine=job.engine,
        job_id=job_id,
    )

    # Store in memory
    memory.store_design(state, user_id)

    return DesignJobResponse(job_id=job_id)


@app.get("/design/status/{job_id}", response_model=DesignStatusResponse)
async def get_design_status(
    job_id: str,
    user_id: str = Depends(verify_token),
    agent: AutoPlaneAgent = Depends(get_agent_instance),
    memory: DesignMemory = Depends(get_memory_instance),
) -> DesignStatusResponse:
    """Poll design job status.

    Args:
        job_id: Job identifier
        user_id: User identifier
        agent: Agent instance
        memory: Memory instance

    Returns:
        Job status and state
    """
    state = memory.get_design(job_id)

    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    status_response = agent.get_status(state)

    return DesignStatusResponse(
        job_id=job_id,
        status=status_response["status"],
        progress=status_response["progress"],
        state=state,
        error=state.last_error,
    )


@app.get("/design/report/{job_id}")
async def download_report(
    job_id: str,
    user_id: str = Depends(verify_token),
    memory: DesignMemory = Depends(get_memory_instance),
) -> Response:
    """Download PDF design report.

    Args:
        job_id: Job identifier
        user_id: User identifier
        memory: Memory instance

    Returns:
        PDF file
    """
    state = memory.get_design(job_id)

    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    if not state.report_pdf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not available",
        )

    return Response(
        content=state.report_pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=design_{job_id}.pdf"
        },
    )


@app.get("/design/cad/{job_id}")
async def download_cad(
    job_id: str,
    user_id: str = Depends(verify_token),
    memory: DesignMemory = Depends(get_memory_instance),
) -> Response:
    """Download CAD file.

    Args:
        job_id: Job identifier
        user_id: User identifier
        memory: Memory instance

    Returns:
        CAD file
    """
    state = memory.get_design(job_id)

    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    if not state.cad_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CAD file not available",
        )

    # In production, this would stream from S3
    # For now, return placeholder response
    return Response(
        content=b"CAD_FILE_PLACEHOLDER",
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=design_{job_id}.{state.cad_file.format.lower()}"
        },
    )


@app.post("/design/feedback/{job_id}", response_model=FeedbackResponse)
async def submit_feedback(
    job_id: str,
    feedback: FeedbackRequest,
    user_id: str = Depends(verify_token),
    agent: AutoPlaneAgent = Depends(get_agent_instance),
    memory: DesignMemory = Depends(get_memory_instance),
) -> FeedbackResponse:
    """Submit parameter feedback for design adjustment.

    Args:
        job_id: Job identifier
        feedback: Parameter adjustments
        user_id: User identifier
        agent: Agent instance
        memory: Memory instance

    Returns:
        Updated design state
    """
    state = memory.get_design(job_id)

    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    # Apply feedback
    if feedback.wing_span is not None:
        state.wing_span = feedback.wing_span
    if feedback.wing_area is not None:
        state.wing_area = feedback.wing_area
    if feedback.fuselage_length is not None:
        state.fuselage_length = feedback.fuselage_length
    if feedback.tail_area is not None:
        state.tail_area = feedback.tail_area
    if feedback.material is not None:
        state.material = feedback.material
        state.needs_reopt = True
    if feedback.engine is not None:
        state.engine = feedback.engine
        state.needs_reopt = True

    # Continue the design loop
    state = agent.continue_design(state)

    # Update memory
    memory.store_design(state, user_id)

    return FeedbackResponse(job_id=job_id, state=state)


@app.get("/design/history", response_model=List[DesignState])
async def list_designs(
    user_id: str = Depends(verify_token),
    limit: int = 100,
    memory: DesignMemory = Depends(get_memory_instance),
) -> List[DesignState]:
    """List past designs.

    Args:
        user_id: User identifier
        limit: Maximum number of results
        memory: Memory instance

    Returns:
        List of design states
    """
    designs = memory.list_designs(user_id, limit)
    return designs


@app.get("/design/similar/{job_id}")
async def find_similar(
    job_id: str,
    k: int = 5,
    user_id: str = Depends(verify_token),
    memory: DesignMemory = Depends(get_memory_instance),
) -> List[dict]:
    """Find similar designs.

    Args:
        job_id: Reference design job ID
        k: Number of results
        user_id: User identifier
        memory: Memory instance

    Returns:
        List of similar designs
    """
    state = memory.get_design(job_id)

    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    return memory.find_similar(state, k)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": "AutoPlane Designer API",
        "version": "0.1.0",
        "docs": "/docs",
    }


# Application entry point
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)