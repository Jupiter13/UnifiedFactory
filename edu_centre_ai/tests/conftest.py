"""Pytest configuration and fixtures for EDU_CENTRE AI tests."""

import pytest
from typing import Generator

from edu_centre_ai.nodes.agent_state import AgentStateDict, create_initial_state
from edu_centre_ai.models.schemas import AgentState, ChatMessage, CourseRecommendation


@pytest.fixture
def sample_user_id() -> str:
    """Sample user ID for tests."""
    return "user_123"


@pytest.fixture
def sample_role() -> str:
    """Sample role for tests."""
    return "student"


@pytest.fixture
def sample_locale() -> str:
    """Sample locale for tests."""
    return "en"


@pytest.fixture
def sample_messages() -> list:
    """Sample messages for tests."""
    return [
        {"role": "user", "content": "Hello, I need help with Python", "timestamp": "2024-01-15T10:00:00Z"},
        {"role": "assistant", "content": "Hi! I'd be happy to help.", "timestamp": "2024-01-15T10:00:05Z"},
    ]


@pytest.fixture
def initial_state(sample_user_id, sample_role, sample_locale) -> AgentStateDict:
    """Create initial state for tests."""
    return create_initial_state(
        user_id=sample_user_id,
        role=sample_role,
        locale=sample_locale,
    )


@pytest.fixture
def agent_state_model(sample_user_id, sample_role, sample_locale) -> AgentState:
    """Create AgentState Pydantic model for tests."""
    return AgentState(
        user_id=sample_user_id,
        role=sample_role,
        locale=sample_locale,
        messages=[
            ChatMessage(role="user", content="Test message"),
        ],
    )


@pytest.fixture
def course_recommendations() -> list:
    """Sample course recommendations for tests."""
    return [
        {
            "course_id": "course_python_101",
            "title": "Python Programming Fundamentals",
            "description": "Learn the basics of Python",
            "rating": 4.8,
            "rationale": "Based on your interests",
        },
        {
            "course_id": "course_ml_basics",
            "title": "Machine Learning Basics",
            "description": "Introduction to ML",
            "rating": 4.6,
            "rationale": "Matches your progression",
        },
    ]