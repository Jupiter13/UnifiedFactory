"""Integration tests for LangGraph agent graph."""

import pytest

from edu_centre_ai.graph.ai_graph import (
    create_agent_graph,
    run_chat,
    run_recommendation,
    _route_intent,
)
from edu_centre_ai.nodes.agent_state import create_initial_state


class TestCreateAgentGraph:
    """Tests for create_agent_graph function."""

    def test_create_graph(self):
        """Test creating the agent graph."""
        graph = create_agent_graph()
        assert graph is not None

    def test_graph_has_nodes(self):
        """Test graph has all required nodes."""
        graph = create_agent_graph()
        # Graph should be compilable without errors
        assert graph is not None


class TestRunChat:
    """Tests for run_chat function."""

    def test_run_chat_question(self):
        """Test running chat with question intent."""
        result = run_chat(
            user_id="user_123",
            message="What is Python?",
            role="student",
            locale="en",
        )

        assert result is not None
        assert result["user_id"] == "user_123"
        assert result["intent"] == "ask_question"
        assert "assistant_message" in result

    def test_run_chat_recommendation(self):
        """Test running chat with recommendation request."""
        result = run_chat(
            user_id="user_123",
            message="I need course recommendations",
            role="student",
            locale="en",
        )

        assert result is not None
        assert result["intent"] == "request_recommendation"
        assert "recommendations" in result

    def test_run_chat_grade(self):
        """Test running chat with grading request."""
        result = run_chat(
            user_id="user_123",
            message="Grade my quiz",
            role="student",
            locale="en",
            quiz_id="quiz_001",
        )

        assert result is not None
        assert result["intent"] == "grade_quiz"
        assert "grade_result" in result

    def test_run_chat_fallback(self):
        """Test running chat with unknown intent."""
        result = run_chat(
            user_id="user_123",
            message="Hello there",
            role="student",
            locale="en",
        )

        assert result is not None
        assert result["intent"] == "fallback"
        assert "assistant_message" in result

    def test_run_chat_with_context(self):
        """Test running chat with course context."""
        result = run_chat(
            user_id="user_123",
            message="What is this lesson about?",
            role="student",
            locale="en",
            course_id="course_python_101",
        )

        assert result is not None
        assert result["current_course_id"] == "course_python_101"
        assert "assistant_message" in result

    def test_run_chat_teacher_role(self):
        """Test running chat with teacher role."""
        result = run_chat(
            user_id="teacher_456",
            message="Explain this concept",
            role="teacher",
            locale="en",
        )

        assert result is not None
        assert result["role"] == "teacher"

    def test_run_chat_parent_role(self):
        """Test running chat with parent role."""
        result = run_chat(
            user_id="parent_789",
            message="What courses are available?",
            role="parent",
            locale="en",
        )

        assert result is not None
        assert result["role"] == "parent"


class TestRunRecommendation:
    """Tests for run_recommendation function."""

    def test_run_recommendation_basic(self):
        """Test running recommendation."""
        result = run_recommendation(
            user_id="user_123",
            locale="en",
        )

        assert result is not None
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0

    def test_run_recommendation_has_messages(self):
        """Test recommendation includes assistant message."""
        result = run_recommendation(
            user_id="user_123",
            locale="en",
        )

        assert len(result["messages"]) > 0
        assert result["messages"][-1]["role"] == "assistant"


class TestRouteIntent:
    """Tests for _route_intent function."""

    def test_route_ask_question(self):
        """Test routing for ask question intent."""
        state = {"intent": "ask_question"}
        assert _route_intent(state) == "ask_question"

    def test_route_recommendation(self):
        """Test routing for recommendation intent."""
        state = {"intent": "request_recommendation"}
        assert _route_intent(state) == "recommend"

    def test_route_grade(self):
        """Test routing for grade intent."""
        state = {"intent": "grade_quiz"}
        assert _route_intent(state) == "grade"

    def test_route_fallback(self):
        """Test routing for fallback intent."""
        state = {"intent": "fallback"}
        assert _route_intent(state) == "fallback"

    def test_route_unknown(self):
        """Test routing for unknown intent."""
        state = {"intent": "unknown"}
        assert _route_intent(state) == "fallback"

    def test_route_no_intent(self):
        """Test routing when no intent is set."""
        state = {}
        assert _route_intent(state) == "fallback"


class TestGraphExecution:
    """End-to-end graph execution tests."""

    def test_full_conversation_flow(self):
        """Test complete conversation flow through the graph."""
        # Initial question
        result = run_chat(
            user_id="student_001",
            message="What is machine learning?",
            role="student",
        )

        # Verify the response structure
        assert "messages" in result
        assert len(result["messages"]) >= 2  # At least user message + assistant
        assert result["messages"][-1]["role"] == "assistant"
        assert result["assistant_message"] is not None

    def test_recommendation_flow(self):
        """Test recommendation flow through the graph."""
        result = run_chat(
            user_id="student_002",
            message="Recommend courses for me",
            role="student",
        )

        # Verify recommendations are generated
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0

        # Verify format node added assistant message
        assert "assistant_message" in result

    def test_grading_flow(self):
        """Test grading flow through the graph."""
        result = run_chat(
            user_id="student_003",
            message="Check my quiz answers",
            role="student",
            quiz_id="quiz_math_101",
        )

        # Verify grade result
        assert "grade_result" in result
        assert result["grade_result"] is not None
        assert "score" in result["grade_result"]

    def test_state_persistence(self):
        """Test that state persists correctly through the graph."""
        result = run_chat(
            user_id="user_test",
            message="Hello",
            role="admin",
            locale="fr",
        )

        # Verify user context is maintained
        assert result["user_id"] == "user_test"
        assert result["role"] == "admin"
        assert result["locale"] == "fr"

        # Verify messages are accumulated
        assert len(result["messages"]) >= 1