"""Pydantic schemas for EDU_CENTRE AI."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message model."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserProgress(BaseModel):
    """User progress model."""

    completed_lessons: List[str] = Field(default_factory=list)
    progress_pct: float = 0.0
    last_access: datetime = Field(default_factory=datetime.utcnow)


class CourseRecommendation(BaseModel):
    """Course recommendation model."""

    course_id: str
    title: str
    description: str
    rating: float = 0.0
    rationale: str


class QuizResult(BaseModel):
    """Quiz result model."""

    score: float
    feedback: str
    correct_answers: Dict[str, str]


class WebResult(BaseModel):
    """Web search result model."""

    title: str
    snippet: str
    url: str


class IntentType(str):
    """Intent type enumeration."""

    ASK_QUESTION = "ask_question"
    REQUEST_RECOMMENDATION = "request_recommendation"
    GRADE_QUIZ = "grade_quiz"
    FALLBACK = "fallback"
    UNKNOWN = "unknown"


class ToolResult(BaseModel):
    """Tool execution result."""

    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None


class AgentState(BaseModel):
    """Agent state for LangGraph.

    Core context fields:
    - user_id: Unique user identifier
    - role: User role (student, teacher, parent, admin)
    - locale: User language preference (default: en)

    Conversation fields:
    - messages: List of chat messages
    - intent: Detected intent from user input
    - current_course_id: Active course context
    - current_quiz_id: Active quiz context

    Short-term memory:
    - last_action: Previous action taken
    - pending_action: Action to be executed

    Long-term memory:
    - memory_ids: IDs of embeddings relevant to session

    Tool outputs:
    - tool_response: Output from tool execution
    """

    # Core context
    user_id: str = "anonymous"
    role: Literal["student", "teacher", "parent", "admin"] = "student"
    locale: str = "en"

    # Conversation
    messages: List[ChatMessage] = Field(default_factory=list)
    intent: Optional[str] = None
    current_course_id: Optional[str] = None
    current_quiz_id: Optional[str] = None

    # Short-term memory
    last_action: Optional[str] = None
    pending_action: Optional[str] = None

    # Long-term memory (vector store ids)
    memory_ids: List[str] = Field(default_factory=list)

    # Tool outputs
    tool_response: Optional[Dict[str, Any]] = None

    # Recommendations
    recommendations: List[CourseRecommendation] = Field(default_factory=list)

    # Grade result
    grade_result: Optional[QuizResult] = None

    # Final assistant message
    assistant_message: Optional[str] = None

    # Additional context
    course_content: Optional[Dict[str, Any]] = None

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


def create_initial_agent_state(
    user_id: str = "anonymous",
    role: Literal["student", "teacher", "parent", "admin"] = "student",
    locale: str = "en",
) -> AgentState:
    """Create initial agent state.

    Args:
        user_id: User identifier
        role: User role
        locale: Language code

    Returns:
        Initial AgentState instance
    """
    return AgentState(
        user_id=user_id,
        role=role,
        locale=locale,
        messages=[],
        intent=None,
        current_course_id=None,
        current_quiz_id=None,
        last_action=None,
        pending_action=None,
        memory_ids=[],
        tool_response=None,
        recommendations=[],
        grade_result=None,
        assistant_message=None,
        course_content=None,
    )