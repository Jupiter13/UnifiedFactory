"""Unit tests for tools."""

import pytest

from edu_centre_ai.tools.base import BaseTool, ToolResponse
from edu_centre_ai.tools.course_tool import FetchCourseContent
from edu_centre_ai.tools.user_progress_tool import GetUserProgress
from edu_centre_ai.tools.recommendation_tool import RecommendCourses
from edu_centre_ai.tools.grading_tool import GradeQuiz
from edu_centre_ai.tools.messaging_tool import SendMessage
from edu_centre_ai.tools.web_tool import SearchWeb
from edu_centre_ai.tools.code_execution_tool import ExecuteCode


class TestToolResponse:
    """Tests for ToolResponse model."""

    def test_successful_response(self):
        """Test successful tool response."""
        response = ToolResponse(success=True, data={"key": "value"})
        assert response.success is True
        assert response.data == {"key": "value"}
        assert response.error is None

    def test_failed_response(self):
        """Test failed tool response."""
        response = ToolResponse(success=False, error="Something went wrong")
        assert response.success is False
        assert response.data is None
        assert response.error == "Something went wrong"

    def test_response_repr(self):
        """Test response string representation."""
        success_response = ToolResponse(success=True, data="test")
        assert "success=True" in repr(success_response)

        fail_response = ToolResponse(success=False, error="error")
        assert "success=False" in repr(fail_response)


class TestBaseTool:
    """Tests for BaseTool class."""

    def test_base_tool_abstract(self):
        """Test BaseTool is abstract."""
        tool = BaseTool()
        with pytest.raises(NotImplementedError):
            tool.call()


class TestFetchCourseContent:
    """Tests for FetchCourseContent tool."""

    def test_fetch_course_content(self):
        """Test fetching course content."""
        tool = FetchCourseContent()
        result = tool.call(course_id="course_python_101")

        assert result.success is True
        assert result.data is not None
        assert result.data["course_id"] == "course_python_101"

    def test_fetch_course_content_with_module(self):
        """Test fetching course content with module."""
        tool = FetchCourseContent()
        result = tool.call(course_id="course_python_101", module_id="module_1")

        assert result.success is True
        assert result.data["module_id"] == "module_1"

    def test_validate_params(self):
        """Test parameter validation."""
        tool = FetchCourseContent()
        valid, error = tool.validate_params({"course_id": "test"})
        assert valid is True

        valid, error = tool.validate_params({})
        assert valid is False
        assert "course_id" in error


class TestGetUserProgress:
    """Tests for GetUserProgress tool."""

    def test_get_user_progress(self):
        """Test getting user progress."""
        tool = GetUserProgress()
        result = tool.call(user_id="user_123")

        assert result.success is True
        assert result.data is not None
        assert result.data["user_id"] == "user_123"

    def test_get_user_progress_with_course(self):
        """Test getting user progress for specific course."""
        tool = GetUserProgress()
        result = tool.call(user_id="user_123", course_id="course_python_101")

        assert result.success is True
        assert result.data["course_id"] == "course_python_101"

    def test_validate_user_id_required(self):
        """Test user_id is required."""
        tool = GetUserProgress()
        valid, error = tool.validate_params({})
        assert valid is False
        assert "user_id" in error


class TestRecommendCourses:
    """Tests for RecommendCourses tool."""

    def test_recommend_courses(self):
        """Test getting course recommendations."""
        tool = RecommendCourses()
        result = tool.call(user_id="user_123", locale="en")

        assert result.success is True
        assert result.data is not None
        assert len(result.data) > 0

    def test_recommend_courses_max_results(self):
        """Test limiting number of recommendations."""
        tool = RecommendCourses()
        result = tool.call(user_id="user_123", max_results=2)

        assert result.success is True
        assert len(result.data) <= 2

    def test_validate_params(self):
        """Test parameter validation."""
        tool = RecommendCourses()
        valid, error = tool.validate_params({"user_id": "test"})
        assert valid is True


class TestGradeQuiz:
    """Tests for GradeQuiz tool."""

    def test_grade_quiz(self):
        """Test grading a quiz."""
        tool = GradeQuiz()
        result = tool.call(
            quiz_id="quiz_001",
            answers={"q1": "A", "q2": "B", "q3": "C", "q4": "A", "q5": "D"},
        )

        assert result.success is True
        assert result.data is not None
        assert result.data.score >= 0
        assert result.data.feedback is not None

    def test_grade_quiz_partial_answers(self):
        """Test grading with partial answers."""
        tool = GradeQuiz()
        result = tool.call(
            quiz_id="quiz_001",
            answers={"q1": "A"},
        )

        assert result.success is True
        assert result.data.score >= 0

    def test_validate_quiz_id_required(self):
        """Test quiz_id is required."""
        tool = GradeQuiz()
        valid, error = tool.validate_params({"answers": {}})
        assert valid is False
        assert "quiz_id" in error

    def test_validate_answers_required(self):
        """Test answers is required."""
        tool = GradeQuiz()
        valid, error = tool.validate_params({"quiz_id": "test"})
        assert valid is False
        assert "answers" in error


class TestSendMessage:
    """Tests for SendMessage tool."""

    def test_send_message(self):
        """Test sending a message."""
        tool = SendMessage()
        result = tool.call(
            to_user_id="user_123",
            content="Hello, this is a test message!",
        )

        assert result.success is True
        assert result.data["status"] == "sent"
        assert result.data["to_user_id"] == "user_123"

    def test_send_message_with_priority(self):
        """Test sending a message with priority."""
        tool = SendMessage()
        result = tool.call(
            to_user_id="user_123",
            content="Urgent notification",
            priority="high",
        )

        assert result.success is True
        assert result.data["priority"] == "high"

    def test_validate_to_user_id_required(self):
        """Test to_user_id is required."""
        tool = SendMessage()
        valid, error = tool.validate_params({"content": "test"})
        assert valid is False
        assert "to_user_id" in error


class TestSearchWeb:
    """Tests for SearchWeb tool."""

    def test_search_web(self):
        """Test web search."""
        tool = SearchWeb()
        result = tool.call(query="Python programming")

        assert result.success is True
        assert result.data is not None
        assert len(result.data) > 0

    def test_search_web_max_results(self):
        """Test limiting search results."""
        tool = SearchWeb()
        result = tool.call(query="Python", max_results=2)

        assert result.success is True
        assert len(result.data) <= 2

    def test_validate_query_required(self):
        """Test query is required."""
        tool = SearchWeb()
        valid, error = tool.validate_params({})
        assert valid is False
        assert "query" in error


class TestExecuteCode:
    """Tests for ExecuteCode tool."""

    def test_execute_simple_code(self):
        """Test executing simple Python code."""
        tool = ExecuteCode()
        result = tool.call(code="print('Hello, World!')")

        assert result.success is True
        assert "Hello, World!" in result.data["output"]

    def test_execute_code_with_output(self):
        """Test executing code with variable output."""
        tool = ExecuteCode()
        result = tool.call(code="x = 5\nprint(x * 2)")

        assert result.success is True
        assert "10" in result.data["output"]

    def test_execute_code_syntax_error(self):
        """Test executing code with syntax error."""
        tool = ExecuteCode()
        result = tool.call(code="print(")

        assert result.success is False
        assert result.error is not None
        assert "Syntax" in result.error

    def test_execute_code_runtime_error(self):
        """Test executing code with runtime error."""
        tool = ExecuteCode()
        result = tool.call(code="x = 1 / 0")

        assert result.success is False
        assert result.error is not None

    def test_validate_code_required(self):
        """Test code is required."""
        tool = ExecuteCode()
        valid, error = tool.validate_params({})
        assert valid is False
        assert "code" in error