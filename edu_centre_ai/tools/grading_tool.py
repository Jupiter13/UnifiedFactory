"""Quiz grading tool."""

from typing import Any, Dict, List, Optional
from edu_centre_ai.tools.base import BaseTool, ToolResponse
from edu_centre_ai.models.schemas import QuizResult


class GradeQuiz(BaseTool):
    """Auto-grade quizzes using stored question bank.

    Compares student answers against correct answers and provides feedback.
    """

    name = "grade_quiz"
    description = "Auto-grade quiz answers and provide feedback"

    def __init__(self, question_bank_url: Optional[str] = None):
        """Initialize the tool.

        Args:
            question_bank_url: URL for the question bank service
        """
        self.question_bank_url = question_bank_url or "http://question-bank:8000"

    def call(
        self,
        quiz_id: str,
        answers: Dict[str, str],
    ) -> ToolResponse:
        """Grade a quiz.

        Args:
            quiz_id: Unique quiz identifier
            answers: Dictionary of question_id to answer

        Returns:
            ToolResponse with QuizResult
        """
        try:
            # In production, this would query the question bank
            result = self._grade_quiz_mock(quiz_id, answers)
            return ToolResponse(success=True, data=result)

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def _grade_quiz_mock(
        self,
        quiz_id: str,
        answers: Dict[str, str],
    ) -> QuizResult:
        """Mock quiz grading for development/testing.

        Args:
            quiz_id: Quiz identifier
            answers: Student answers

        Returns:
            QuizResult with score and feedback
        """
        # Mock correct answers (in production, fetch from question bank)
        correct_answers = {
            "q1": "A",
            "q2": "B",
            "q3": "C",
            "q4": "A",
            "q5": "D",
        }

        # Calculate score
        total_questions = len(correct_answers)
        correct_count = 0
        feedback_items = []

        for q_id, correct_answer in correct_answers.items():
            student_answer = answers.get(q_id, "")
            is_correct = student_answer.upper() == correct_answer.upper()
            if is_correct:
                correct_count += 1
            feedback_items.append({
                "question_id": q_id,
                "correct": is_correct,
                "your_answer": student_answer,
                "correct_answer": correct_answer,
            })

        score = (correct_count / total_questions) * 100 if total_questions > 0 else 0

        # Generate feedback
        if score >= 90:
            feedback = "Excellent work! You have a strong understanding of the material."
        elif score >= 70:
            feedback = "Good job! You have a solid grasp of most concepts."
        elif score >= 50:
            feedback = "You're on the right track. Consider reviewing the material again."
        else:
            feedback = "Keep practicing! Review the lesson content and try again."

        return QuizResult(
            score=score,
            feedback=feedback,
            correct_answers=correct_answers,
        )

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate tool parameters.

        Args:
            params: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if "quiz_id" not in params:
            return False, "quiz_id is required"
        if "answers" not in params:
            return False, "answers is required"
        if not isinstance(params.get("answers"), dict):
            return False, "answers must be a dictionary"
        return True, None