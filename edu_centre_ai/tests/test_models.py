"""Unit tests for Pydantic models."""

import pytest
from datetime import datetime

from edu_centre_ai.models.schemas import (
    ChatMessage,
    UserProgress,
    CourseRecommendation,
    QuizResult,
    WebResult,
    AgentState,
    IntentType,
    create_initial_agent_state,
)


class TestChatMessage:
    """Tests for ChatMessage model."""

    def test_create_chat_message(self):
        """Test creating a chat message."""
        message = ChatMessage(
            role="user",
            content="Hello, world!",
        )
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.timestamp is not None

    def test_chat_message_with_custom_timestamp(self):
        """Test chat message with custom timestamp."""
        custom_time = datetime(2024, 1, 15, 10, 0, 0)
        message = ChatMessage(
            role="assistant",
            content="Response",
            timestamp=custom_time,
        )
        assert message.timestamp == custom_time

    def test_chat_message_roles(self):
        """Test valid roles."""
        for role in ["user", "assistant", "system"]:
            message = ChatMessage(role=role, content="Test")
            assert message.role == role


class TestUserProgress:
    """Tests for UserProgress model."""

    def test_create_user_progress(self):
        """Test creating user progress."""
        progress = UserProgress()
        assert progress.completed_lessons == []
        assert progress.progress_pct == 0.0
        assert progress.last_access is not None

    def test_user_progress_with_data(self):
        """Test user progress with data."""
        progress = UserProgress(
            completed_lessons=["lesson_1", "lesson_2"],
            progress_pct=0.5,
        )
        assert len(progress.completed_lessons) == 2
        assert progress.progress_pct == 0.5


class TestCourseRecommendation:
    """Tests for CourseRecommendation model."""

    def test_create_recommendation(self):
        """Test creating a course recommendation."""
        rec = CourseRecommendation(
            course_id="course_123",
            title="Python Basics",
            description="Learn Python",
            rating=4.5,
            rationale="Recommended for beginners",
        )
        assert rec.course_id == "course_123"
        assert rec.title == "Python Basics"
        assert rec.rating == 4.5

    def test_recommendation_defaults(self):
        """Test recommendation default values."""
        rec = CourseRecommendation(
            course_id="course_123",
            title="Test",
            description="Test desc",
            rationale="Test rationale",
        )
        assert rec.rating == 0.0
        assert rec.rationale == "Test rationale"


class TestQuizResult:
    """Tests for QuizResult model."""

    def test_create_quiz_result(self):
        """Test creating a quiz result."""
        result = QuizResult(
            score=85.0,
            feedback="Good job!",
            correct_answers={"q1": "A", "q2": "B"},
        )
        assert result.score == 85.0
        assert result.feedback == "Good job!"
        assert len(result.correct_answers) == 2

    def test_quiz_result_empty_answers(self):
        """Test quiz result with empty answers."""
        result = QuizResult(
            score=0.0,
            feedback="Try again",
            correct_answers={},
        )
        assert result.score == 0.0


class TestWebResult:
    """Tests for WebResult model."""

    def test_create_web_result(self):
        """Test creating a web result."""
        result = WebResult(
            title="Search Result",
            snippet="This is a result",
            url="https://example.com",
        )
        assert result.title == "Search Result"
        assert result.url.startswith("https://")


class TestAgentState:
    """Tests for AgentState model."""

    def test_create_agent_state(self):
        """Test creating agent state."""
        state = AgentState(
            user_id="user_123",
            role="student",
            locale="en",
        )
        assert state.user_id == "user_123"
        assert state.role == "student"
        assert state.locale == "en"
        assert state.messages == []

    def test_agent_state_with_messages(self):
        """Test agent state with messages."""
        messages = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi!"),
        ]
        state = AgentState(
            user_id="user_123",
            role="student",
            messages=messages,
        )
        assert len(state.messages) == 2

    def test_agent_state_roles(self):
        """Test valid agent state roles."""
        for role in ["student", "teacher", "parent", "admin"]:
            state = AgentState(user_id="user", role=role)
            assert state.role == role


class TestIntentType:
    """Tests for IntentType enum."""

    def test_intent_types(self):
        """Test intent type values."""
        assert IntentType.ASK_QUESTION == "ask_question"
        assert IntentType.REQUEST_RECOMMENDATION == "request_recommendation"
        assert IntentType.GRADE_QUIZ == "grade_quiz"
        assert IntentType.FALLBACK == "fallback"


class TestCreateInitialAgentState:
    """Tests for create_initial_agent_state function."""

    def test_create_default_state(self):
        """Test creating default initial state."""
        state = create_initial_agent_state()
        assert state.user_id == "anonymous"
        assert state.role == "student"
        assert state.locale == "en"

    def test_create_custom_state(self):
        """Test creating custom initial state."""
        state = create_initial_agent_state(
            user_id="user_456",
            role="teacher",
            locale="fr",
        )
        assert state.user_id == "user_456"
        assert state.role == "teacher"
        assert state.locale == "fr"

    def test_initial_state_empty_messages(self):
        """Test initial state has empty messages."""
        state = create_initial_agent_state()
        assert state.messages == []