"""Tools for EDU_CENTRE AI."""

from edu_centre_ai.tools.base import BaseTool, ToolResponse
from edu_centre_ai.tools.course_tool import FetchCourseContent
from edu_centre_ai.tools.user_progress_tool import GetUserProgress
from edu_centre_ai.tools.recommendation_tool import RecommendCourses
from edu_centre_ai.tools.grading_tool import GradeQuiz
from edu_centre_ai.tools.messaging_tool import SendMessage
from edu_centre_ai.tools.web_tool import SearchWeb
from edu_centre_ai.tools.code_execution_tool import ExecuteCode


__all__ = [
    "BaseTool",
    "ToolResponse",
    "FetchCourseContent",
    "GetUserProgress",
    "RecommendCourses",
    "GradeQuiz",
    "SendMessage",
    "SearchWeb",
    "ExecuteCode",
]