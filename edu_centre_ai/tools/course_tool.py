"""Course content fetching tool."""

from typing import Any, Dict, Optional
from edu_centre_ai.tools.base import BaseTool, ToolResponse


class FetchCourseContent(BaseTool):
    """Fetch course content from the platform.

    Retrieves lesson or quiz data from the Course Service REST API.
    """

    name = "fetch_course_content"
    description = "Retrieve lesson or quiz data for a specific course"

    def __init__(self, api_base_url: Optional[str] = None):
        """Initialize the tool.

        Args:
            api_base_url: Base URL for the Course Service API
        """
        self.api_base_url = api_base_url or "http://course-service:8000"

    def call(
        self,
        course_id: str,
        module_id: Optional[str] = None,
        lesson_id: Optional[str] = None,
    ) -> ToolResponse:
        """Fetch course content.

        Args:
            course_id: Unique course identifier
            module_id: Optional module identifier
            lesson_id: Optional lesson identifier

        Returns:
            ToolResponse with course content or error
        """
        try:
            # Build the request parameters
            params: Dict[str, Any] = {"course_id": course_id}
            if module_id:
                params["module_id"] = module_id
            if lesson_id:
                params["lesson_id"] = lesson_id

            # For now, return mock data since we're not connecting to a real API
            # In production, this would call the actual Course Service
            content = self._fetch_content_mock(course_id, module_id, lesson_id)
            return ToolResponse(success=True, data=content)

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def _fetch_content_mock(
        self,
        course_id: str,
        module_id: Optional[str],
        lesson_id: Optional[str],
    ) -> Dict[str, Any]:
        """Mock content fetching for development/testing.

        Args:
            course_id: Course identifier
            module_id: Module identifier
            lesson_id: Lesson identifier

        Returns:
            Mock content data
        """
        return {
            "course_id": course_id,
            "module_id": module_id,
            "lesson_id": lesson_id,
            "title": f"Course {course_id} - {module_id or 'Overview'}",
            "media_url": f"https://cdn.example.com/courses/{course_id}/media.mp4",
            "text": f"This is the lesson content for course {course_id}. "
            f"Module: {module_id or 'Introduction'}, "
            f"Lesson: {lesson_id or 'Overview'}",
            "duration": 1800,  # 30 minutes in seconds
            "created_at": "2024-01-15T10:00:00Z",
        }

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate tool parameters.

        Args:
            params: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if "course_id" not in params:
            return False, "course_id is required"
        return True, None