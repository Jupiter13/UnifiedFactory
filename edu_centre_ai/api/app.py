"""FastAPI application for EDU_CENTRE AI.

Provides REST endpoints for conversational AI and recommendations.
"""

from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from edu_centre_ai.config import get_settings, Settings
from edu_centre_ai.graph.ai_graph import run_chat, run_recommendation, create_agent_graph
from edu_centre_ai.models.schemas import CourseRecommendation


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request model."""

    user_id: str = Field(default="anonymous")
    message: str = Field(..., description="User message content")
    role: str = Field(default="student")
    locale: str = Field(default="en")
    course_id: str = Field(default=None)
    quiz_id: str = Field(default=None)


class ChatResponse(BaseModel):
    """Chat response model."""

    user_id: str
    message: str
    assistant_message: str
    intent: str
    success: bool


class RecommendationRequest(BaseModel):
    """Recommendation request model."""

    user_id: str
    locale: str = Field(default="en")


class RecommendationResponse(BaseModel):
    """Recommendation response model."""

    user_id: str
    recommendations: List[Dict[str, Any]]
    success: bool


class GradeQuizRequest(BaseModel):
    """Quiz grading request model."""

    quiz_id: str
    answers: Dict[str, str]


class GradeQuizResponse(BaseModel):
    """Quiz grading response model."""

    quiz_id: str
    score: float
    feedback: str
    correct_answers: Dict[str, str]
    success: bool


class UserProgressResponse(BaseModel):
    """User progress response model."""

    user_id: str
    completed_lessons: List[str]
    progress_pct: float
    last_access: str
    success: bool


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    settings = get_settings()

    # Startup
    yield

    # Shutdown
    pass


def create_app(settings: Settings = None) -> FastAPI:
    """Create FastAPI application.

    Args:
        settings: Application settings

    Returns:
        FastAPI app instance
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Agentic AI layer for EDU_CENTRE educational platform",
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

    # Register routes
    from edu_centre_ai.api.routes import router
    app.include_router(router, prefix=settings.api_prefix)

    return app


# Default app instance
app = create_app()