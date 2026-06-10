"""LangGraph agent pipeline for EDU_CENTRE AI.

This module defines the complete agent graph with nodes, edges,
and conditional routing based on intent classification.
"""

from typing import Callable, Dict, Optional

from langgraph.graph import StateGraph, END

from edu_centre_ai.nodes.agent_state import AgentStateDict, create_initial_state
from edu_centre_ai.nodes.agent_nodes import (
    StartNode,
    IdentifyIntentNode,
    BranchIntentNode,
    AskQuestionNode,
    RecommendNode,
    GradeNode,
    FallbackNode,
    FormatAnswerNode,
    FormatRecommendationsNode,
    FormatGradeNode,
    EndNode,
)


def create_agent_graph() -> StateGraph:
    """Create the EDU_CENTRE AI agent graph.

    The graph follows this structure:
    ```
    Start
      └─> Identify Intent
            ├─> Ask Question
            │     └─> Format Answer
            ├─> Recommend
            │     └─> Format Recommendations
            ├─> Grade
            │     └─> Format Grade
            └─> Fallback
                  └─> Format Answer
    ```

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the state graph
    graph = StateGraph(AgentStateDict)

    # Instantiate nodes
    start_node = StartNode()
    identify_intent_node = IdentifyIntentNode()
    ask_question_node = AskQuestionNode()
    recommend_node = RecommendNode()
    grade_node = GradeNode()
    fallback_node = FallbackNode()
    format_answer_node = FormatAnswerNode()
    format_recommendations_node = FormatRecommendationsNode()
    format_grade_node = FormatGradeNode()
    end_node = EndNode()

    # Add nodes to graph
    graph.add_node("start", start_node)
    graph.add_node("identify_intent", identify_intent_node)
    graph.add_node("ask_question", ask_question_node)
    graph.add_node("recommend", recommend_node)
    graph.add_node("grade", grade_node)
    graph.add_node("fallback", fallback_node)
    graph.add_node("format_answer", format_answer_node)
    graph.add_node("format_recommendations", format_recommendations_node)
    graph.add_node("format_grade", format_grade_node)
    graph.add_node("end", end_node)

    # Define edges
    # Start -> Identify Intent
    graph.add_edge("start", "identify_intent")

    # Branch Intent routes to specific nodes based on intent
    graph.add_conditional_edges(
        "identify_intent",
        _route_intent,
        {
            "ask_question": "ask_question",
            "recommend": "recommend",
            "grade": "grade",
            "fallback": "fallback",
        },
    )

    # Processing nodes -> Format nodes -> End
    graph.add_edge("ask_question", "format_answer")
    graph.add_edge("recommend", "format_recommendations")
    graph.add_edge("fallback", "format_answer")
    graph.add_edge("format_answer", "end")
    graph.add_edge("format_recommendations", "end")
    graph.add_edge("format_grade", "end")

    # Grade node goes to format_grade
    graph.add_edge("grade", "format_grade")

    # Set entry point
    graph.set_entry_point("start")

    # Compile the graph
    return graph.compile()


def _route_intent(state: AgentStateDict) -> str:
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


def run_chat(
    user_id: str,
    message: str,
    role: str = "student",
    locale: str = "en",
    course_id: Optional[str] = None,
    quiz_id: Optional[str] = None,
) -> AgentStateDict:
    """Run a chat interaction through the agent graph.

    Args:
        user_id: User identifier
        message: User message
        role: User role (student, teacher, parent, admin)
        locale: Language code
        course_id: Optional current course context
        quiz_id: Optional current quiz context

    Returns:
        Final agent state with assistant_message
    """
    # Create initial state
    initial_state = create_initial_state(
        user_id=user_id,
        role=role,
        locale=locale,
        initial_message=message,
    )

    # Add context
    if course_id:
        initial_state["current_course_id"] = course_id
    if quiz_id:
        initial_state["current_quiz_id"] = quiz_id

    # Create and run graph
    graph = create_agent_graph()
    result = graph.invoke(initial_state)

    return result


def run_recommendation(
    user_id: str,
    locale: str = "en",
) -> AgentStateDict:
    """Run a recommendation request through the agent graph.

    Args:
        user_id: User identifier
        locale: Language code

    Returns:
        Final agent state with recommendations
    """
    # Create initial state with recommendation intent
    initial_state = create_initial_state(
        user_id=user_id,
        locale=locale,
        initial_message="I need course recommendations",
    )
    initial_state["intent"] = "request_recommendation"

    # Create and run graph
    graph = create_agent_graph()
    result = graph.invoke(initial_state)

    return result


# Export compiled graph for direct use
agent_graph = create_agent_graph()