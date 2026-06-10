"""Agent state for LangGraph pipeline.

This module defines the state dictionary used by LangGraph to pass
data between nodes in the agent pipeline.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, TypedDict


class AgentStateDict(TypedDict, total=False):
    """State dictionary for LangGraph agent pipeline.

    Core context:
    - user_id: Unique user identifier
    - role: User role (student, teacher, parent, admin)
    - locale: User language preference

    Conversation:
    - messages: List of chat messages (dicts with role, content, timestamp)
    - intent: Detected intent from user input
    - current_course_id: Active course context
    - current_quiz_id: Active quiz context

    Short-term memory:
    - last_action: Previous action taken
    - pending_action: Action to be executed

    Long-term memory:
    - memory_ids: IDs of embeddings relevant to session

    Tool outputs:
    - tool_response: Output from tool execution

    Recommendations:
    - recommendations: List of course recommendations

    Grade result:
    - grade_result: Quiz grading result

    Final output:
    - assistant_message: Final assistant response
    """

    # Core context
    user_id: str
    role: Literal["student", "teacher", "parent", "admin"]
    locale: str

    # Conversation
    messages: List[Dict[str, Any]]  # [{"role": str, "content": str, "timestamp": str}]
    intent: Optional[str]
    current_course_id: Optional[str]
    current_quiz_id: Optional[str]

    # Short-term memory
    last_action: Optional[str]
    pending_action: Optional[str]

    # Long-term memory (vector store ids)
    memory_ids: List[str]

    # Tool outputs
    tool_response: Optional[Dict[str, Any]]

    # Recommendations
    recommendations: List[Dict[str, Any]]

    # Grade result
    grade_result: Optional[Dict[str, Any]]

    # Course content
    course_content: Optional[Dict[str, Any]]

    # Final assistant message
    assistant_message: Optional[str]


def create_initial_state(
    user_id: str = "anonymous",
    role: Literal["student", "teacher", "parent", "admin"] = "student",
    locale: str = "en",
    initial_message: Optional[str] = None,
) -> AgentStateDict:
    """Create initial state for agent pipeline.

    Args:
        user_id: User identifier
        role: User role
        locale: Language code
        initial_message: Optional initial user message

    Returns:
        Initial AgentStateDict
    """
    messages = []
    if initial_message:
        messages.append({
            "role": "user",
            "content": initial_message,
            "timestamp": datetime.utcnow().isoformat(),
        })

    return AgentStateDict(
        user_id=user_id,
        role=role,
        locale=locale,
        messages=messages,
        intent=None,
        current_course_id=None,
        current_quiz_id=None,
        last_action=None,
        pending_action=None,
        memory_ids=[],
        tool_response=None,
        recommendations=[],
        grade_result=None,
        course_content=None,
        assistant_message=None,
    )


def get_last_user_message(state: AgentStateDict) -> Optional[str]:
    """Extract the last user message from the conversation.

    Args:
        state: Current agent state

    Returns:
        Content of last user message or None
    """
    messages = state.get("messages", [])
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content")
    return None


def add_assistant_message(state: AgentStateDict, content: str) -> AgentStateDict:
    """Add an assistant message to the conversation.

    Args:
        state: Current agent state
        content: Message content

    Returns:
        Updated state
    """
    messages = list(state.get("messages", []))
    messages.append({
        "role": "assistant",
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
    })
    return {**state, "messages": messages}