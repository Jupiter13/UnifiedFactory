"""AutoPlane Design Agent - LangGraph implementation.

This module defines the state machine for the autonomous aircraft design agent.
"""

import logging
import uuid
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from autoplane.models.state import DesignState
from autoplane.nodes import (
    input_parser,
    material_selector,
    engine_selector,
    design_generator,
    aerodynamic_evaluator,
    structural_evaluator,
    performance_estimator,
    cost_estimator,
    regulatory_checker,
    cad_exporter,
    report_generator,
    feedback_loop,
    should_reoptimize,
    should_continue,
)

logger = logging.getLogger(__name__)


def create_design_graph() -> StateGraph:
    """Create the AutoPlane design agent graph.

    Returns:
        Compiled StateGraph for the design workflow
    """
    # Define the graph
    graph = StateGraph(DesignState)

    # Add all nodes
    graph.add_node("input_parser", input_parser)
    graph.add_node("material_selector", material_selector)
    graph.add_node("engine_selector", engine_selector)
    graph.add_node("design_generator", design_generator)
    graph.add_node("aerodynamic_evaluator", aerodynamic_evaluator)
    graph.add_node("structural_evaluator", structural_evaluator)
    graph.add_node("performance_estimator", performance_estimator)
    graph.add_node("cost_estimator", cost_estimator)
    graph.add_node("regulatory_checker", regulatory_checker)
    graph.add_node("cad_exporter", cad_exporter)
    graph.add_node("report_generator", report_generator)
    graph.add_node("feedback_loop", feedback_loop)

    # Define edges - sequential execution to avoid concurrent writes
    graph.set_entry_point("input_parser")
    graph.add_edge("input_parser", "material_selector")
    graph.add_edge("material_selector", "engine_selector")
    graph.add_edge("engine_selector", "design_generator")

    # Conditional routing from design_generator - handle both success and failure
    graph.add_conditional_edges(
        "design_generator",
        should_continue,
        {
            "continue": "aerodynamic_evaluator",
            "stop": END,
        },
    )

    # Sequential evaluation
    graph.add_edge("aerodynamic_evaluator", "structural_evaluator")
    graph.add_edge("structural_evaluator", "performance_estimator")

    # Continue with remaining steps
    graph.add_edge("performance_estimator", "cost_estimator")
    graph.add_edge("cost_estimator", "regulatory_checker")

    # Conditional routing for regulatory violations
    graph.add_conditional_edges(
        "regulatory_checker",
        should_reoptimize,
        {
            "reoptimize": "feedback_loop",
            "complete": "cad_exporter",
        },
    )

    # Re-optimization loop
    graph.add_edge("feedback_loop", "design_generator")

    # Final export and reporting
    graph.add_edge("cad_exporter", "report_generator")
    graph.add_edge("report_generator", END)

    return graph


def compile_graph() -> StateGraph:
    """Compile the design graph with memory checkpointing.

    Returns:
        Compiled graph ready for execution
    """
    graph = create_design_graph()

    # Use MemorySaver for checkpointing
    checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)


class AutoPlaneAgent:
    """Autonomous aircraft design agent.

    This agent orchestrates the design generation loop using LangGraph.
    """

    def __init__(self):
        """Initialize the agent."""
        self.graph = compile_graph()
        logger.info("AutoPlaneAgent initialized")

    def _get_config(self, job_id: str = None) -> Dict[str, Any]:
        """Get configuration for graph execution.

        Args:
            job_id: Optional job identifier for checkpointing

        Returns:
            Configuration dictionary
        """
        return {
            "configurable": {
                "thread_id": job_id or str(uuid.uuid4()),
            }
        }

    def start_design(
        self,
        payload_kg: float,
        material: str = None,
        engine: str = None,
        job_id: str = None,
    ) -> DesignState:
        """Start a new design job.

        Args:
            payload_kg: Payload requirement in kg
            material: Preferred material (optional)
            engine: Preferred engine (optional)
            job_id: Optional job identifier

        Returns:
            Final DesignState after graph execution
        """
        # Create initial state
        state = DesignState(
            payload_kg=payload_kg,
            material=material,
            engine=engine,
            job_id=job_id,
        )

        # Ensure we have a job_id for checkpointing
        if not state.job_id:
            state.job_id = str(uuid.uuid4())

        # Run the graph
        logger.info(f"Starting design job for {payload_kg} kg payload")
        config = self._get_config(state.job_id)
        result = self.graph.invoke(state, config=config)

        return result

    def get_status(self, state: DesignState) -> dict:
        """Get the current status of a design job.

        Args:
            state: Current design state

        Returns:
            Status dictionary with progress information
        """
        progress_map = {
            "pending": 0,
            "running": 50,
            "completed": 100,
            "failed": -1,
        }

        return {
            "job_id": state.job_id,
            "status": state.status,
            "progress": progress_map.get(state.status, 0),
            "iteration": state.iteration,
            "error": state.last_error,
        }

    def continue_design(self, state: DesignState) -> DesignState:
        """Continue a design from its current state.

        Args:
            state: Current design state

        Returns:
            Updated DesignState
        """
        config = self._get_config(state.job_id)
        result = self.graph.invoke(state, config=config)
        return result


# Global agent instance
_agent_instance = None


def get_agent() -> "AutoPlaneAgent":
    """Get the global agent instance.

    Returns:
        AutoPlaneAgent singleton
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AutoPlaneAgent()
    return _agent_instance


# System prompt for the agent
SYSTEM_PROMPT = """You are AutoPlane-Designer, an autonomous AI that generates fixed-wing aircraft designs.

You have access to the following tools:
- generate_geometry(payload, material, engine) → geometry_json
- run_cfd_surrogate(geometry_json) → AeroResult
- run_fea_surrogate(geometry_json) → StructResult
- compute_performance(aero, structural, engine) → PerfResult
- estimate_cost(geometry, material, engine) → CostResult
- check_regulations(performance, aero) → RegResult
- export_cad(geometry_json, format) → CADFile
- generate_report(state) → PDF bytes

You must:
1. Keep the design within the weight, balance, and performance constraints.
2. Flag any regulatory violations.
3. Iterate until all constraints are satisfied or a maximum of 5 iterations is reached.
4. Output a final design package: CAD file, performance report, cost estimate, and a short summary.
5. If a constraint cannot be met, explain why and suggest alternatives.

All outputs must be in JSON unless otherwise specified.
When calling a tool, provide the exact JSON input schema defined below.
Do not fabricate data; if a tool fails, set `last_error` and stop the loop."""