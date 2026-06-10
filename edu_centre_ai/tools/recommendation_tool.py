"""Course recommendation tool."""

from typing import Any, Dict, List, Optional
from edu_centre_ai.tools.base import BaseTool, ToolResponse
from edu_centre_ai.models.schemas import CourseRecommendation


class RecommendCourses(BaseTool):
    """Generate course recommendations based on user history.

    Uses vector store and recommendation model to suggest courses.
    """

    name = "recommend_courses"
    description = "Generate personalized course recommendations for users"

    def __init__(
        self,
        vector_store_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize the tool.

        Args:
            vector_store_url: URL for vector store (Pinecone/Qdrant)
            api_key: API key for vector store
        """
        self.vector_store_url = vector_store_url
        self.api_key = api_key

    def call(
        self,
        user_id: str,
        locale: str = "en",
        max_results: int = 5,
    ) -> ToolResponse:
        """Get course recommendations.

        Args:
            user_id: Unique user identifier
            locale: User's language code
            max_results: Maximum number of recommendations

        Returns:
            ToolResponse with list of CourseRecommendation
        """
        try:
            # In production, this would query vector store + recommendation model
            recommendations = self._get_recommendations_mock(
                user_id, locale, max_results
            )
            return ToolResponse(success=True, data=recommendations)

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def _get_recommendations_mock(
        self,
        user_id: str,
        locale: str,
        max_results: int,
    ) -> List[CourseRecommendation]:
        """Mock recommendations for development/testing.

        Args:
            user_id: User identifier
            locale: Language code
            max_results: Max recommendations

        Returns:
            List of CourseRecommendation
        """
        mock_courses = [
            CourseRecommendation(
                course_id="course_python_101",
                title="Python Programming Fundamentals",
                description="Learn the basics of Python programming",
                rating=4.8,
                rationale="Based on your interest in programming",
            ),
            CourseRecommendation(
                course_id="course_ml_basics",
                title="Machine Learning Basics",
                description="Introduction to machine learning concepts",
                rating=4.6,
                rationale="Matches your learning progression",
            ),
            CourseRecommendation(
                course_id="course_data_science",
                title="Data Science with Python",
                description="Data analysis and visualization",
                rating=4.7,
                rationale="Popular among students with your profile",
            ),
            CourseRecommendation(
                course_id="course_web_dev",
                title="Web Development Fundamentals",
                description="HTML, CSS, and JavaScript basics",
                rating=4.5,
                rationale="Complements your current learning path",
            ),
            CourseRecommendation(
                course_id="course_algorithms",
                title="Algorithms and Data Structures",
                description="Essential computer science concepts",
                rating=4.9,
                rationale="Recommended for advanced learners",
            ),
        ]

        return mock_courses[:max_results]

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate tool parameters.

        Args:
            params: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if "user_id" not in params:
            return False, "user_id is required"
        return True, None