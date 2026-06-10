"""API routes for EDU_CENTRE AI."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from edu_centre_ai.graph.ai_graph import run_chat, run_recommendation, create_agent_graph
from edu_centre_ai.tools.grading_tool import GradeQuiz
from edu_centre_ai.tools.user_progress_tool import GetUserProgress


router = APIRouter()


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


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Conversational endpoint for AI chat.

    Args:
        request: Chat request with user message and context

    Returns:
        Chat response with assistant message
    """
    try:
        result = run_chat(
            user_id=request.user_id,
            message=request.message,
            role=request.role,
            locale=request.locale,
            course_id=request.course_id,
            quiz_id=request.quiz_id,
        )

        return ChatResponse(
            user_id=result.get("user_id", request.user_id),
            message=request.message,
            assistant_message=result.get("assistant_message", "No response generated"),
            intent=result.get("intent", "unknown"),
            success=True,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend_endpoint(request: RecommendationRequest) -> RecommendationResponse:
    """Recommendation endpoint for course suggestions.

    Args:
        request: Recommendation request with user ID

    Returns:
        Recommendation response with course list
    """
    try:
        result = run_recommendation(
            user_id=request.user_id,
            locale=request.locale,
        )

        recommendations = result.get("recommendations", [])

        return RecommendationResponse(
            user_id=request.user_id,
            recommendations=recommendations,
            success=True,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/grade", response_model=GradeQuizResponse)
async def grade_quiz_endpoint(request: GradeQuizRequest) -> GradeQuizResponse:
    """Auto-grade quiz endpoint.

    Args:
        request: Quiz grading request with quiz ID and answers

    Returns:
        Grade response with score and feedback
    """
    try:
        grading_tool = GradeQuiz()
        result = grading_tool.call(
            quiz_id=request.quiz_id,
            answers=request.answers,
        )

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)

        quiz_result = result.data

        return GradeQuizResponse(
            quiz_id=request.quiz_id,
            score=quiz_result.score,
            feedback=quiz_result.feedback,
            correct_answers=quiz_result.correct_answers,
            success=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress", response_model=UserProgressResponse)
async def progress_endpoint(
    user_id: str = Query(..., description="User identifier"),
    course_id: str = Query(default=None, description="Optional course ID"),
) -> UserProgressResponse:
    """Get user learning progress endpoint.

    Args:
        user_id: User identifier
        course_id: Optional specific course ID

    Returns:
        Progress response with completed lessons and percentage
    """
    try:
        progress_tool = GetUserProgress()
        result = progress_tool.call(user_id=user_id, course_id=course_id)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)

        progress = result.data

        return UserProgressResponse(
            user_id=user_id,
            completed_lessons=progress.get("completed_lessons", []),
            progress_pct=progress.get("progress_pct", 0.0),
            last_access=progress.get("last_access", ""),
            success=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy", "service": "edu-centre-ai"}


@router.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint.

    Returns:
        Service information
    """
    return {
        "service": "EDU_CENTRE AI",
        "version": "1.0.0",
        "status": "operational",
    }