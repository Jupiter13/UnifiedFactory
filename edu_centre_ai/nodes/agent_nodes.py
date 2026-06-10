"""LangGraph nodes for EDU_CENTRE AI agent.

Each node is a function that takes the current state and returns an updated state.
These functions are compatible with LangGraph's StateGraph.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from edu_centre_ai.nodes.agent_state import AgentStateDict, add_assistant_message
from edu_centre_ai.tools import (
    FetchCourseContent,
    GetUserProgress,
    RecommendCourses,
    GradeQuiz,
    SendMessage,
)


# Intent patterns for classification
INTENT_PATTERNS = {
    "ask_question": [
        "what is", "how do", "explain", "tell me about", "can you",
        "why does", "what's", "how does", "describe", "define",
        "help me understand", "clarify", "show me", "teach me",
    ],
    "request_recommendation": [
        "recommend", "suggest", "what should I", "what course",
        "what class", "what lesson", "what topic", "next course",
        "what do you recommend", "i want to learn", "help me learn",
    ],
    "grade_quiz": [
        "grade", "check my", "submit quiz", "submit answers",
        "how did I do", "my score", "my result", "quiz result",
        "check answers", "evaluate my",
    ],
}


def classify_intent(message: str) -> str:
    """Classify user intent from message content.

    Args:
        message: User message content

    Returns:
        Intent type string
    """
    message_lower = message.lower()

    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if pattern in message_lower:
                return intent

    return "fallback"


class StartNode:
    """Entry point node - initializes the pipeline."""

    name = "start"

    def __call__(self, state: AgentStateDict) -> AgentStateDict:
        """Execute start node.

        Args:
            state: Current agent state

        Returns:
            Updated state
        """
        return {
            **state,
            "last_action": "start",
        }


class IdentifyIntentNode:
    """Identify user intent from conversation messages."""

    name = "identify_intent"

    def __call__(self, state: AgentStateDict) -> AgentStateDict:
        """Execute intent identification.

        Args:
            state: Current agent state

        Returns:
            Updated state with intent
        """
        messages = state.get("messages", [])

        # Get last user message
        last_message = None
        for message in reversed(messages):
            if message.get("role") == "user":
                last_message = message.get("content", "")
                break

        if not last_message:
            return {
                **state,
                "intent": "fallback",
                "last_action": "identify_intent",
            }

        # Classify intent
        intent = classify_intent(last_message)

        return {
            **state,
            "intent": intent,
            "last_action": "identify_intent",
        }


class BranchIntentNode:
    """Branch based on detected intent.

    This is a routing function, not a processing node.
    Returns the name of the next node.
    """

    name = "branch_intent"

    def __call__(self, state: AgentStateDict) -> str:
        """Route to appropriate node based on intent.

        Args:
            state: Current agent state

        Returns:
            Next node name
        """
        intent = state.get("intent", "fallback")

        intent_to_node = {
            "ask_question": "ask_question",
            "request_recommendation": "recommend",
            "grade_quiz": "grade",
            "fallback": "fallback",
        }

        return intent_to_node.get(intent, "fallback")


class AskQuestionNode:
    """Handle general questions using course content and tools."""

    name = "ask_question"

    def __init__(self):
        self._course_tool = FetchCourseContent()
        self._progress_tool = GetUserProgress()

    def __call__(self, state: AgentStateDict) -> AgentStateDict:
        """Execute question handling.

        Args:
            state: Current agent state

        Returns:
            Updated state with tool response
        """
        messages = state.get("messages", [])
        current_course_id = state.get("current_course_id")
        user_id = state.get("user_id", "anonymous")

        # Get last user message
        last_message = None
        for message in reversed(messages):
            if message.get("role") == "user":
                last_message = message.get("content", "")
                break

        # Try to fetch course content if course_id is available
        tool_response = None
        course_content = None

        if current_course_id:
            result = self._course_tool.call(course_id=current_course_id)
            if result.success:
                course_content = result.data
                tool_response = {
                    "type": "course_content",
                    "content": result.data,
                    "success": True,
                }

        # Also get user progress
        progress_result = self._progress_tool.call(user_id=user_id)
        progress_data = progress_result.data if progress_result.success else None

        # Build response based on available data
        response_content = self._build_question_response(
            last_message, course_content, progress_data
        )

        return {
            **state,
            "tool_response": tool_response,
            "course_content": course_content,
            "pending_action": "format_answer",
            "last_action": "ask_question",
        }

    def _build_question_response(
        self,
        question: Optional[str],
        course_content: Optional[Dict],
        progress_data: Optional[Dict],
    ) -> str:
        """Build response for user question.

        Args:
            question: User's question
            course_content: Course content data
            progress_data: User progress data

        Returns:
            Response content
        """
        if course_content:
            return f"Based on the course material: {course_content.get('title', 'Course')}. {course_content.get('text', '')}"
        return "I can help you with your questions about courses. Please specify which course or topic you'd like to learn about."


class RecommendNode:
    """Generate course recommendations."""

    name = "recommend"

    def __init__(self):
        self._recommend_tool = RecommendCourses()

    def __call__(self, state: AgentStateDict) -> AgentStateDict:
        """Execute recommendation generation.

        Args:
            state: Current agent state

        Returns:
            Updated state with recommendations
        """
        user_id = state.get("user_id", "anonymous")
        locale = state.get("locale", "en")

        # Get recommendations
        result = self._recommend_tool.call(user_id=user_id, locale=locale)

        recommendations = []
        if result.success and result.data:
            recommendations = [
                {
                    "course_id": rec.course_id,
                    "title": rec.title,
                    "description": rec.description,
                    "rating": rec.rating,
                    "rationale": rec.rationale,
                }
                for rec in result.data
            ]

        return {
            **state,
            "recommendations": recommendations,
            "pending_action": "format_recommendations",
            "last_action": "recommend",
        }


class GradeNode:
    """Auto-grade quiz submissions."""

    name = "grade"

    def __init__(self):
        self._grade_tool = GradeQuiz()

    def __call__(self, state: AgentStateDict) -> AgentStateDict:
        """Execute quiz grading.

        Args:
            state: Current agent state

        Returns:
            Updated state with grade result
        """
        current_quiz_id = state.get("current_quiz_id")
        messages = state.get("messages", [])

        # Try to extract answers from messages
        answers = self._extract_answers_from_messages(messages)

        if not current_quiz_id:
            return {
                **state,
                "grade_result": {
                    "score": 0,
                    "feedback": "No quiz ID provided. Please provide a quiz ID to grade.",
                    "correct_answers": {},
                },
                "pending_action": "format_grade",
                "last_action": "grade",
            }

        # Grade the quiz
        result = self._grade_tool.call(quiz_id=current_quiz_id, answers=answers)

        grade_result = None
        if result.success and result.data:
            grade_result = {
                "score": result.data.score,
                "feedback": result.data.feedback,
                "correct_answers": result.data.correct_answers,
            }

        return {
            **state,
            "grade_result": grade_result,
            "pending_action": "format_grade",
            "last_action": "grade",
        }

    def _extract_answers_from_messages(self, messages: List[Dict]) -> Dict[str, str]:
        """Extract quiz answers from conversation messages.

        Args:
            messages: List of chat messages

        Returns:
            Dictionary of question_id to answer
        """
        # In production, this would parse structured answer submissions
        # For now, return empty dict (quiz must be submitted with answers)
        return {}


class FallbackNode:
    """Handle unknown or unsupported intents."""

    name = "fallback"

    def __call__(self, state: AgentStateDict) -> AgentStateDict:
        """Execute fallback handling.

        Args:
            state: Current agent state

        Returns:
            Updated state with fallback response
        """
        messages = state.get("messages", [])
        user_id = state.get("user_id", "anonymous")
        role = state.get("role", "student")

        # Get last user message
        last_message = None
        for message in reversed(messages):
            if message.get("role") == "user":
                last_message = message.get("content", "")
                break

        # Generate helpful fallback response
        fallback_response = self._generate_fallback_response(role, last_message)

        return {
            **state,
            "tool_response": {
                "type": "fallback",
                "content": fallback_response,
                "success": True,
            },
            "pending_action": "format_answer",
            "last_action": "fallback",
        }

    def _generate_fallback_response(self, role: str, message: Optional[str]) -> str:
        """Generate a helpful fallback response.

        Args:
            role: User role
            message: User message

        Returns:
            Fallback response content
        """
        if not message:
            return "Hello! I'm EduTutor, your AI learning assistant. How can I help you today?"

        return (
            "I'm not sure I understand your request. Here are some things I can help you with:\n"
            "- Ask questions about course content\n"
            "- Get personalized course recommendations\n"
            "- Grade your quiz submissions\n"
            "- Check your learning progress\n\n"
            "Please try rephrasing your request or ask for help with a specific topic."
        )


class FormatAnswerNode:
    """Format the final assistant response for question intents."""

    name = "format_answer"

    def __call__(self, state: AgentStateDict) -> AgentStateDict:
        """Format answer response.

        Args:
            state: Current agent state

        Returns:
            Updated state with assistant_message
        """
        tool_response = state.get("tool_response", {})
        role = state.get("role", "student")
        locale = state.get("locale", "en")

        # Build the response
        response_content = self._format_response(tool_response, role, locale)

        # Add assistant message to state
        new_state = add_assistant_message(state, response_content)
        new_state["assistant_message"] = response_content

        return {
            **new_state,
            "last_action": "format_answer",
        }

    def _format_response(
        self,
        tool_response: Optional[Dict],
        role: str,
        locale: str,
    ) -> str:
        """Format the final response.

        Args:
            tool_response: Tool output data (can be None)
            role: User role
            locale: Language code

        Returns:
            Formatted response string
        """
        if tool_response is None:
            return "I wasn't able to process your request. Please try again or rephrase your question."

        content = tool_response.get("content", "")

        if not content:
            return "I wasn't able to find specific information for your question. Please try asking about a specific course or topic."

        # Tailor response based on role
        if role == "student":
            return f"As a student, here's what I found: {content}"
        elif role == "teacher":
            return f"For teaching purposes: {content}"
        elif role == "parent":
            return f"Here's information that may help: {content}"
        return content


class FormatRecommendationsNode:
    """Format the final assistant response for recommendation intents."""

    name = "format_recommendations"

    def __call__(self, state: AgentStateDict) -> AgentStateDict:
        """Format recommendations response.

        Args:
            state: Current agent state

        Returns:
            Updated state with assistant_message
        """
        recommendations = state.get("recommendations", [])
        role = state.get("role", "student")

        # Build the response
        response_content = self._format_recommendations(recommendations, role)

        # Add assistant message to state
        new_state = add_assistant_message(state, response_content)
        new_state["assistant_message"] = response_content

        return {
            **new_state,
            "last_action": "format_recommendations",
        }

    def _format_recommendations(
        self,
        recommendations: List[Dict],
        role: str,
    ) -> str:
        """Format recommendations into a readable response.

        Args:
            recommendations: List of recommendation dicts
            role: User role

        Returns:
            Formatted recommendations string
        """
        if not recommendations:
            return "I couldn't find any suitable recommendations at this time. Please check back later or try a different topic."

        response = "Here are some courses I recommend for you:\n\n"
        for i, rec in enumerate(recommendations, 1):
            response += f"{i}. **{rec.get('title', 'Untitled Course')}**\n"
            response += f"   {rec.get('description', '')}\n"
            response += f"   Rating: {rec.get('rating', 0):.1f}/5.0\n"
            response += f"   Why: {rec.get('rationale', 'Matches your interests')}\n\n"

        return response


class FormatGradeNode:
    """Format the final assistant response for quiz grading intents."""

    name = "format_grade"

    def __call__(self, state: AgentStateDict) -> AgentStateDict:
        """Format grade response.

        Args:
            state: Current agent state

        Returns:
            Updated state with assistant_message
        """
        grade_result = state.get("grade_result", {})
        role = state.get("role", "student")

        # Build the response
        response_content = self._format_grade_result(grade_result, role)

        # Add assistant message to state
        new_state = add_assistant_message(state, response_content)
        new_state["assistant_message"] = response_content

        return {
            **new_state,
            "last_action": "format_grade",
        }

    def _format_grade_result(
        self,
        grade_result: Dict,
        role: str,
    ) -> str:
        """Format grade result into a readable response.

        Args:
            grade_result: Quiz result dict
            role: User role

        Returns:
            Formatted grade response string
        """
        if not grade_result:
            return "I couldn't process your quiz submission. Please try again with a valid quiz ID and answers."

        score = grade_result.get("score", 0)
        feedback = grade_result.get("feedback", "")
        correct_answers = grade_result.get("correct_answers", {})

        response = f"**Quiz Results**\n\n"
        response += f"Score: {score:.1f}%\n\n"
        response += f"{feedback}\n\n"

        if correct_answers:
            response += "Correct Answers:\n"
            for q_id, answer in correct_answers.items():
                response += f"- {q_id}: {answer}\n"

        return response


class EndNode:
    """End node - finalize and return results."""

    name = "end"

    def __call__(self, state: AgentStateDict) -> AgentStateDict:
        """Execute end node.

        Args:
            state: Current agent state

        Returns:
            Final state
        """
        return {
            **state,
            "last_action": "end",
        }