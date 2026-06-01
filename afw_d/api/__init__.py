"""AFW-D Engine API.

FastAPI endpoints for the aircraft design workflow.
"""

import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from afw_d.models import (
    DesignInput,
    DesignStatus,
    Feedback,
    FeedbackAck,
    DesignState,
)
from afw_d.graph import run_design

# Create FastAPI app
app = FastAPI(
    title="AFW-D Design Engine",
    description="Agentic AI Fixed-Wing Aircraft Design API",
    version="0.1.0",
)

# In-memory storage for design status (would use Redis in production)
_designs: dict[str, dict] = {}


class DesignStatusResponse(BaseModel):
    """Response model for design status."""

    design_id: str
    state: str
    progress: int
    error: Optional[str] = None


@app.post("/design/submit", response_model=DesignStatus)
async def submit_design(design_input: DesignInput) -> DesignStatus:
    """Submit a new design request.

    Args:
        design_input: Design input parameters.

    Returns:
        DesignStatus with design ID and initial status.
    """
    design_id = str(uuid.uuid4())

    # Store design in memory
    _designs[design_id] = {
        "state": "queued",
        "progress": 0,
        "input": design_input,
        "result": None,
        "error": None,
    }

    # In production, this would be a background task
    # For now, run synchronously for simplicity
    try:
        _designs[design_id]["state"] = "running"
        _designs[design_id]["progress"] = 10

        # Run the design workflow
        result = run_design(
            payload_kg=design_input.payload_kg,
            material_family=design_input.material_family,
            engine_family=design_input.engine_family,
        )
        _designs[design_id]["progress"] = 90

        # Store result
        _designs[design_id]["result"] = result
        _designs[design_id]["state"] = "completed"
        _designs[design_id]["progress"] = 100

    except Exception as e:
        _designs[design_id]["state"] = "failed"
        _designs[design_id]["error"] = str(e)

    return DesignStatus(
        design_id=design_id,
        state=_designs[design_id]["state"],
        progress=_designs[design_id]["progress"],
        error=_designs[design_id]["error"],
    )


@app.get("/design/status/{design_id}", response_model=DesignStatus)
async def get_design_status(design_id: str) -> DesignStatus:
    """Get the status of a design.

    Args:
        design_id: Design ID.

    Returns:
        DesignStatus with current state.

    Raises:
        HTTPException: If design not found.
    """
    if design_id not in _designs:
        raise HTTPException(status_code=404, detail="Design not found")

    design = _designs[design_id]
    return DesignStatus(
        design_id=design_id,
        state=design["state"],
        progress=design["progress"],
        error=design.get("error"),
    )


@app.get("/design/download/{design_id}")
async def download_design(design_id: str) -> JSONResponse:
    """Download design CAD file.

    Args:
        design_id: Design ID.

    Returns:
        JSON response with download URL.

    Raises:
        HTTPException: If design not found.
    """
    if design_id not in _designs:
        raise HTTPException(status_code=404, detail="Design not found")

    design = _designs[design_id]
    result = design.get("result", {})

    if not result or not result.get("cad_file"):
        raise HTTPException(status_code=404, detail="CAD file not available")

    cad_file = result["cad_file"]
    return JSONResponse({
        "file_id": cad_file["file_id"],
        "url": cad_file["url"],
        "format": cad_file["format"],
    })


@app.post("/design/feedback/{design_id}", response_model=FeedbackAck)
async def submit_feedback(design_id: str, feedback: Feedback) -> FeedbackAck:
    """Submit feedback for a design.

    Args:
        design_id: Design ID.
        feedback: Feedback content.

    Returns:
        FeedbackAck with success status.
    """
    if design_id not in _designs:
        raise HTTPException(status_code=404, detail="Design not found")

    design = _designs[design_id]

    # Store feedback
    feedback_list = design.get("feedback_list", [])
    feedback_list.append(feedback)
    design["feedback_list"] = feedback_list

    return FeedbackAck(
        success=True,
        message=f"Feedback received for design {design_id}",
    )


@app.get("/design/history/{design_id}")
async def get_design_history(design_id: str) -> list[dict]:
    """Get design history.

    Args:
        design_id: Design ID.

    Returns:
        List of design states.

    Raises:
        HTTPException: If design not found.
    """
    if design_id not in _designs:
        raise HTTPException(status_code=404, detail="Design not found")

    design = _designs[design_id]
    result = design.get("result", {})

    history = result.get("history", [])
    return [state.model_dump() if hasattr(state, "model_dump") else state for state in history]


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Health status.
    """
    return {"status": "healthy", "service": "afw-d-engine"}


@app.get("/")
async def root() -> dict:
    """Root endpoint.

    Returns:
        Service information.
    """
    return {
        "service": "AFW-D Design Engine",
        "version": "0.1.0",
        "description": "Agentic AI Fixed-Wing Aircraft Design API",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)