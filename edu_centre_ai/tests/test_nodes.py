"""Unit tests for LangGraph nodes."""

import pytest

from edu_centre_ai.nodes.agent_state import (
    AgentStateDict,
    create_initial_state,
    get_last_user_message,
    add_assistant_message,
)
from edu_centre_ai.nodes.agent_nodes import (
    StartNode,
    IdentifyIntentNode,
    BranchIntentNode,
    AskQuestionNode,
    RecommendNode,
    GradeNode,
    FallbackNode,
    FormatAnswerNode,
    FormatRecommendationsNode,
    FormatGradeNode,
    EndNode,
    classify_intent,
)


class TestAgentStateDict:
    """Tests for AgentStateDict and helper functions."""

    def test_create_initial_state(self):
        """Test creating initial state."""
        state = create_initial_state(
            user_id="user_123",
            role="student",
            locale="en",
        )

        assert state["user_id"] == "user_123"
        assert state["role"] == "student"
        assert state["locale"] == "en"
        assert state["messages"] == []
        assert state["intent"] is None

    def test_create_initial_state_with_message(self):
        """Test creating initial state with initial message."""
        state = create_initial_state(
            user_id="user_123",
            role="student",
            initial_message="Hello",
        )

        assert len(state["messages"]) == 1
        assert state["messages"][0]["role"] == "user"
        assert state["messages"][0]["content"] == "Hello"

    def test_get_last_user_message(self):
        """Test getting last user message."""
        state = {
            "messages": [
                {"role": "user", "content": "First"},
                {"role": "assistant", "content": "Response"},
                {"role": "user", "content": "Second"},
            ]
        }
        assert get_last_user_message(state) == "Second"

    def test_get_last_user_message_empty(self):
        """Test getting last user message when none exists."""
        state = {"messages": [{"role": "assistant", "content": "Response"}]}
        assert get_last_user_message(state) is None

    def test_add_assistant_message(self):
        """Test adding assistant message."""
        state = {
            "messages": [
                {"role": "user", "content": "Hello"},
            ]
        }
        new_state = add_assistant_message(state, "Hi there!")

        assert len(new_state["messages"]) == 2
        assert new_state["messages"][1]["role"] == "assistant"
        assert new_state["messages"][1]["content"] == "Hi there!"


class TestClassifyIntent:
    """Tests for intent classification."""

    def test_classify_ask_question(self):
        """Test classifying ask question intent."""
        assert classify_intent("What is Python?") == "ask_question"
        assert classify_intent("How do I learn?") == "ask_question"
        assert classify_intent("Explain this concept") == "ask_question"
        assert classify_intent("Tell me about algorithms") == "ask_question"

    def test_classify_recommendation(self):
        """Test classifying recommendation intent."""
        assert classify_intent("I need course recommendations") == "request_recommendation"
        assert classify_intent("Recommend courses for me") == "request_recommendation"
        assert classify_intent("I want to learn") == "request_recommendation"
        assert classify_intent("Suggest a topic") == "request_recommendation"

    def test_classify_grade_quiz(self):
        """Test classifying grade quiz intent."""
        assert classify_intent("Grade my quiz") == "grade_quiz"
        assert classify_intent("Check my answers") == "grade_quiz"
        assert classify_intent("Submit quiz") == "grade_quiz"

    def test_classify_fallback(self):
        """Test classifying fallback intent."""
        assert classify_intent("Random text") == "fallback"
        assert classify_intent("Hello there") == "fallback"


class TestStartNode:
    """Tests for StartNode."""

    def test_start_node_execute(self):
        """Test start node execution."""
        node = StartNode()
        state = create_initial_state(user_id="user_123")

        result = node(state)

        assert result["last_action"] == "start"


class TestIdentifyIntentNode:
    """Tests for IdentifyIntentNode."""

    def test_identify_question_intent(self):
        """Test identifying question intent."""
        node = IdentifyIntentNode()
        state = create_initial_state(
            user_id="user_123",
            initial_message="What is Python?",
        )

        result = node(state)

        assert result["intent"] == "ask_question"
        assert result["last_action"] == "identify_intent"

    def test_identify_recommendation_intent(self):
        """Test identifying recommendation intent."""
        node = IdentifyIntentNode()
        state = create_initial_state(
            user_id="user_123",
            initial_message="I need a course recommendation",
        )

        result = node(state)

        assert result["intent"] == "request_recommendation"

    def test_identify_empty_messages(self):
        """Test identifying intent with no messages."""
        node = IdentifyIntentNode()
        state = create_initial_state(user_id="user_123")

        result = node(state)

        assert result["intent"] == "fallback"


class TestBranchIntentNode:
    """Tests for BranchIntentNode."""

    def test_branch_ask_question(self):
        """Test branching for ask question intent."""
        node = BranchIntentNode()
        state = {"intent": "ask_question"}

        result = node(state)

        assert result == "ask_question"

    def test_branch_recommendation(self):
        """Test branching for recommendation intent."""
        node = BranchIntentNode()
        state = {"intent": "request_recommendation"}

        result = node(state)

        assert result == "recommend"

    def test_branch_grade(self):
        """Test branching for grade intent."""
        node = BranchIntentNode()
        state = {"intent": "grade_quiz"}

        result = node(state)

        assert result == "grade"

    def test_branch_fallback(self):
        """Test branching for fallback intent."""
        node = BranchIntentNode()
        state = {"intent": "fallback"}

        result = node(state)

        assert result == "fallback"


class TestAskQuestionNode:
    """Tests for AskQuestionNode."""

    def test_ask_question_execute(self):
        """Test ask question node execution."""
        node = AskQuestionNode()
        state = create_initial_state(
            user_id="user_123",
            initial_message="What is Python?",
        )
        state["current_course_id"] = "course_python_101"

        result = node(state)

        assert result["last_action"] == "ask_question"
        assert result["pending_action"] == "format_answer"
        assert "tool_response" in result


class TestRecommendNode:
    """Tests for RecommendNode."""

    def test_recommend_execute(self):
        """Test recommend node execution."""
        node = RecommendNode()
        state = create_initial_state(
            user_id="user_123",
            initial_message="I need recommendations",
        )
        state["intent"] = "request_recommendation"

        result = node(state)

        assert result["last_action"] == "recommend"
        assert result["pending_action"] == "format_recommendations"
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0


class TestGradeNode:
    """Tests for GradeNode."""

    def test_grade_execute(self):
        """Test grade node execution."""
        node = GradeNode()
        state = create_initial_state(
            user_id="user_123",
            initial_message="Grade my quiz",
        )
        state["intent"] = "grade_quiz"
        state["current_quiz_id"] = "quiz_001"

        result = node(state)

        assert result["last_action"] == "grade"
        assert result["pending_action"] == "format_grade"
        assert "grade_result" in result

    def test_grade_no_quiz_id(self):
        """Test grade node without quiz ID."""
        node = GradeNode()
        state = create_initial_state(user_id="user_123")
        state["intent"] = "grade_quiz"

        result = node(state)

        assert result["grade_result"]["score"] == 0
        assert "No quiz ID" in result["grade_result"]["feedback"]


class TestFallbackNode:
    """Tests for FallbackNode."""

    def test_fallback_execute(self):
        """Test fallback node execution."""
        node = FallbackNode()
        state = create_initial_state(
            user_id="user_123",
            initial_message="Random text",
        )
        state["intent"] = "fallback"

        result = node(state)

        assert result["last_action"] == "fallback"
        assert result["pending_action"] == "format_answer"
        assert "tool_response" in result


class TestFormatAnswerNode:
    """Tests for FormatAnswerNode."""

    def test_format_answer_execute(self):
        """Test format answer node execution."""
        node = FormatAnswerNode()
        state = {
            "user_id": "user_123",
            "role": "student",
            "locale": "en",
            "messages": [{"role": "user", "content": "Hello"}],
            "tool_response": {
                "type": "course_content",
                "content": "Here is the answer",
                "success": True,
            },
        }

        result = node(state)

        assert result["last_action"] == "format_answer"
        assert "assistant_message" in result
        assert len(result["messages"]) == 2
        assert result["messages"][1]["role"] == "assistant"


class TestFormatRecommendationsNode:
    """Tests for FormatRecommendationsNode."""

    def test_format_recommendations_execute(self):
        """Test format recommendations node execution."""
        node = FormatRecommendationsNode()
        state = {
            "user_id": "user_123",
            "role": "student",
            "locale": "en",
            "messages": [],
            "recommendations": [
                {
                    "course_id": "course_1",
                    "title": "Python Basics",
                    "description": "Learn Python",
                    "rating": 4.5,
                    "rationale": "For beginners",
                }
            ],
        }

        result = node(state)

        assert result["last_action"] == "format_recommendations"
        assert "assistant_message" in result
        assert "Python Basics" in result["assistant_message"]


class TestFormatGradeNode:
    """Tests for FormatGradeNode."""

    def test_format_grade_execute(self):
        """Test format grade node execution."""
        node = FormatGradeNode()
        state = {
            "user_id": "user_123",
            "role": "student",
            "messages": [],
            "grade_result": {
                "score": 85.0,
                "feedback": "Good job!",
                "correct_answers": {"q1": "A", "q2": "B"},
            },
        }

        result = node(state)

        assert result["last_action"] == "format_grade"
        assert "assistant_message" in result
        assert "85" in result["assistant_message"]


class TestEndNode:
    """Tests for EndNode."""

    def test_end_node_execute(self):
        """Test end node execution."""
        node = EndNode()
        state = {"messages": [], "assistant_message": "Final response"}

        result = node(state)

        assert result["last_action"] == "end"