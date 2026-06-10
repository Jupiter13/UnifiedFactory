"""User progress tracking tool."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from edu_centre_ai.tools.base import BaseTool, ToolResponse


class GetUserProgress(BaseTool):
    """Get user learning progress from PostgreSQL.

    Retrieves completed lessons, progress percentage, and last access time.
    """

    name = "get_user_progress"
    description = "Get student progress including completed lessons and percentage"

    def __init__(self, db_connection_string: Optional[str] = None):
        """Initialize the tool.

        Args:
            db_connection_string: PostgreSQL connection string
        """
        self.db_connection_string = db_connection_string

    def call(
        self,
        user_id: str,
        course_id: Optional[str] = None,
    ) -> ToolResponse:
        """Get user progress.

        Args:
            user_id: Unique user identifier
            course_id: Optional specific course to get progress for

        Returns:
            ToolResponse with user progress data or error
        """
        try:
            # In production, this would query PostgreSQL
            # For now, return mock data
            progress = self._get_progress_mock(user_id, course_id)
            return ToolResponse(success=True, data=progress)

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def _get_progress_mock(
        self,
        user_id: str,
        course_id: Optional[str],
    ) -> Dict[str, Any]:
        """Mock progress data for development/testing.

        Args:
            user_id: User identifier
            course_id: Course identifier

        Returns:
            Mock progress data
        """
        return {
            "user_id": user_id,
            "course_id": course_id,
            "completed_lessons": [
                f"{course_id or 'course'}/lesson_1",
                f"{course_id or 'course'}/lesson_2",
                f"{course_id or 'course'}/lesson_3",
            ],
            "progress_pct": 0.65,
            "last_access": datetime.utcnow().isoformat(),
            "total_lessons": 10,
            "current_lesson": f"{course_id or 'course'}/lesson_4",
        }

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