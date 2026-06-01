"""AFW-D Engine Graph Definition.

LangGraph workflow definition for the aircraft design process.
"""

from typing import Literal

from langgraph.graph import StateGraph, END

from .state import AFWDesignState, initial_state
from .nodes import (
    input_collector,
    material_selector,
    engine_selector,
    design_generator,
    simulation_runner,
    cost_estimator,
    compliance_checker,
    optimization_loop,
    exporter,
    feedback_handler,
)


def create_graph() -> StateGraph:
    """Create and configure the AFW-D design graph.

    Returns:
        Compiled StateGraph ready for execution.
    """
    # Create the state graph
    graph = StateGraph(AFWDesignState)

    # Add all nodes
    graph.add_node("input_collector", input_collector)
    graph.add_node("material_selector", material_selector)
    graph.add_node("engine_selector", engine_selector)
    graph.add_node("design_generator", design_generator)
    graph.add_node("simulation_runner", simulation_runner)
    graph.add_node("cost_estimator", cost_estimator)
    graph.add_node("compliance_checker", compliance_checker)
    graph.add_node("optimization_loop", optimization_loop)
    graph.add_node("exporter", exporter)
    graph.add_node("feedback_handler", feedback_handler)

    # Set entry point
    graph.set_entry_point("input_collector")

    # Add edges
    graph.add_edge("input_collector", "material_selector")
    graph.add_edge("material_selector", "engine_selector")
    graph.add_edge("engine_selector", "design_generator")
    graph.add_edge("design_generator", "simulation_runner")
    graph.add_edge("simulation_runner", "cost_estimator")
    graph.add_edge("cost_estimator", "compliance_checker")
    graph.add_edge("compliance_checker", "optimization_loop")
    graph.add_edge("optimization_loop", "exporter")
    graph.add_edge("exporter", "feedback_handler")
    graph.add_edge("feedback_handler", END)

    return graph


def create_conditional_graph() -> StateGraph:
    """Create graph with conditional routing.

    Returns:
        Compiled StateGraph with conditional branches.
    """
    # Create the state graph
    graph = StateGraph(AFWDesignState)

    # Add all nodes
    graph.add_node("input_collector", input_collector)
    graph.add_node("material_selector", material_selector)
    graph.add_node("engine_selector", engine_selector)
    graph.add_node("design_generator", design_generator)
    graph.add_node("simulation_runner", simulation_runner)
    graph.add_node("cost_estimator", cost_estimator)
    graph.add_node("compliance_checker", compliance_checker)
    graph.add_node("optimization_loop", optimization_loop)
    graph.add_node("exporter", exporter)
    graph.add_node("feedback_handler", feedback_handler)

    # Set entry point
    graph.set_entry_point("input_collector")

    # Add edges with routing
    graph.add_edge("input_collector", "material_selector")
    graph.add_edge("material_selector", "engine_selector")
    graph.add_edge("engine_selector", "design_generator")
    graph.add_edge("design_generator", "simulation_runner")
    graph.add_edge("simulation_runner", "cost_estimator")
    graph.add_edge("cost_estimator", "compliance_checker")
    graph.add_edge("compliance_checker", "optimization_loop")

    # Conditional routing from optimization loop
    def route_after_optimization(state: AFWDesignState) -> Literal["design_generator", "exporter"]:
        """Route based on whether re-run is needed."""
        if state.get("needs_rerun", False):
            return "design_generator"
        return "exporter"

    graph.add_conditional_edges(
        "optimization_loop",
        route_after_optimization,
        {
            "design_generator": "design_generator",
            "exporter": "exporter",
        }
    )

    graph.add_edge("exporter", "feedback_handler")
    graph.add_edge("feedback_handler", END)

    return graph


# Pre-built compiled graph
_app = None


def get_app():
    """Get the compiled graph application.

    Returns:
        Compiled LangGraph application.
    """
    global _app
    if _app is None:
        graph = create_conditional_graph()
        _app = graph.compile()
    return _app


def run_design(payload_kg: float, material_family: str = None, engine_family: str = None) -> dict:
    """Run the design workflow.

    Args:
        payload_kg: Payload mass in kg.
        material_family: Optional material family.
        engine_family: Optional engine family.

    Returns:
        Final state dictionary.
    """
    app = get_app()
    initial = initial_state(payload_kg, material_family, engine_family)
    return app.invoke(initial)