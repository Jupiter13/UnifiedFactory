"""Integration tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from edu_centre_ai.api.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/ai/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint returns service info."""
        response = client.get("/ai/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "EDU_CENTRE AI"
        assert data["version"] == "1.0.0"


class TestChatEndpoint:
    """Tests for chat endpoint."""

    def test_chat_basic(self, client):
        """Test basic chat request."""
        response = client.post(
            "/ai/chat",
            json={
                "user_id": "user_123",
                "message": "What is Python?",
                "role": "student",
                "locale": "en",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_123"
        assert data["success"] is True
        assert "assistant_message" in data

    def test_chat_with_context(self, client):
        """Test chat with course context."""
        response = client.post(
            "/ai/chat",
            json={
                "user_id": "user_123",
                "message": "Explain this lesson",
                "role": "student",
                "course_id": "course_python_101",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_chat_teacher_role(self, client):
        """Test chat with teacher role."""
        response = client.post(
            "/ai/chat",
            json={
                "user_id": "teacher_456",
                "message": "What teaching resources are available?",
                "role": "teacher",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_chat_default_values(self, client):
        """Test chat with default values."""
        response = client.post(
            "/ai/chat",
            json={
                "message": "Hello",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "anonymous"
        assert data["success"] is True


class TestRecommendEndpoint:
    """Tests for recommendation endpoint."""

    def test_recommend_basic(self, client):
        """Test basic recommendation request."""
        response = client.post(
            "/ai/recommend",
            json={
                "user_id": "user_123",
                "locale": "en",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_123"
        assert data["success"] is True
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0

    def test_recommend_with_locale(self, client):
        """Test recommendation with French locale."""
        response = client.post(
            "/ai/recommend",
            json={
                "user_id": "user_123",
                "locale": "fr",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestGradeEndpoint:
    """Tests for quiz grading endpoint."""

    def test_grade_quiz(self, client):
        """Test quiz grading."""
        response = client.post(
            "/ai/grade",
            json={
                "quiz_id": "quiz_001",
                "answers": {"q1": "A", "q2": "B", "q3": "C", "q4": "A", "q5": "D"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["quiz_id"] == "quiz_001"
        assert data["success"] is True
        assert "score" in data
        assert "feedback" in data

    def test_grade_quiz_partial_answers(self, client):
        """Test grading with partial answers."""
        response = client.post(
            "/ai/grade",
            json={
                "quiz_id": "quiz_001",
                "answers": {"q1": "A"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["score"] >= 0


class TestProgressEndpoint:
    """Tests for user progress endpoint."""

    def test_progress_basic(self, client):
        """Test getting user progress."""
        response = client.get("/ai/progress", params={"user_id": "user_123"})
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_123"
        assert data["success"] is True
        assert "completed_lessons" in data

    def test_progress_with_course(self, client):
        """Test getting progress for specific course."""
        response = client.get(
            "/ai/progress",
            params={
                "user_id": "user_123",
                "course_id": "course_python_101",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestErrorHandling:
    """Tests for error handling."""

    def test_chat_invalid_request(self, client):
        """Test chat with invalid request."""
        response = client.post(
            "/ai/chat",
            json={},
        )
        # Should fail validation (message is required)
        assert response.status_code == 422

    def test_grade_missing_quiz_id(self, client):
        """Test grading with missing quiz_id."""
        response = client.post(
            "/ai/grade",
            json={
                "answers": {"q1": "A"},
            },
        )
        assert response.status_code == 422

    def test_progress_missing_user_id(self, client):
        """Test progress without user_id."""
        response = client.get("/ai/progress")
        assert response.status_code == 422