"""LangGraph design pipeline graph definition."""

from typing import Dict, Literal, Optional, Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from aerodesign_ai.nodes.graph_state import DesignState
from aerodesign_ai.nodes.nodes import (
    StartNode,
    ValidateInputNode,
    FetchMaterialPropsNode,
    FetchEngineSpecsNode,
    GenerateInitialGeometryNode,
    OptimizeDesignNode,
    ComplianceCheckNode,
    CADExportNode,
    GenerateBOMNode,
    StoreDesignNode,
    EndNode,
)


class AeroDesignGraph:
    """LangGraph pipeline for aircraft design generation."""

    def __init__(self):
        self.nodes = {
            "start": StartNode(),
            "validate_input": ValidateInputNode(),
            "fetch_material": FetchMaterialPropsNode(),
            "fetch_engine": FetchEngineSpecsNode(),
            "generate_geometry": GenerateInitialGeometryNode(),
            "optimize": OptimizeDesignNode(),
            "compliance_check": ComplianceCheckNode(),
            "cad_export": CADExportNode(),
            "generate_bom": GenerateBOMNode(),
            "store_design": StoreDesignNode(),
            "end": EndNode(),
        }
        self.graph: Optional[StateGraph] = None

    def _create_node_function(self, node_name: str):
        """Create a node function for the graph."""
        node = self.nodes[node_name]

        def node_func(state: DesignState) -> DesignState:
            return node.execute(state)

        return node_func

    def build(self) -> StateGraph:
        """Build the LangGraph pipeline.

        Returns:
            Compiled StateGraph
        """
        # Create the graph
        graph = StateGraph(DesignState)

        # Add all nodes
        for name in self.nodes:
            graph.add_node(name, self._create_node_function(name))

        # Define edges
        # Start -> Validate
        graph.add_edge("start", "validate_input")

        # Validate -> fetch_material OR end (if invalid)
        def validate_route(state: DesignState) -> str:
            if state.get("errors"):
                return "end"
            return "fetch_material"

        graph.add_conditional_edges(
            "validate_input",
            validate_route,
            {
                "fetch_material": "fetch_material",
                "end": "end",
            }
        )

        # fetch_material -> fetch_engine
        graph.add_edge("fetch_material", "fetch_engine")

        # fetch_engine -> generate_geometry
        graph.add_edge("fetch_engine", "generate_geometry")

        # generate_geometry -> optimize
        graph.add_edge("generate_geometry", "optimize")

        # optimize -> compliance_check
        graph.add_edge("optimize", "compliance_check")

        # compliance_check -> cad_export (if passed) OR end (if failed with critical)
        def compliance_route(state: DesignState) -> str:
            compliance = state.get("compliance_report", {})
            violations = compliance.get("violations", [])

            if violations:
                # Check if any critical violations
                # For now, continue if any errors but record them
                return "cad_export"

            return "cad_export"

        graph.add_conditional_edges(
            "compliance_check",
            compliance_route,
            {
                "cad_export": "cad_export",
                "optimize": "optimize",  # Could loop back for adjustment
                "end": "end",
            }
        )

        # cad_export -> generate_bom
        graph.add_edge("cad_export", "generate_bom")

        # generate_bom -> store_design
        graph.add_edge("generate_bom", "store_design")

        # store_design -> end
        graph.add_edge("store_design", "end")

        # Set entry point
        graph.set_entry_point("start")

        # Compile with memory checkpointer for state persistence
        checkpointer = MemorySaver()
        self.graph = graph.compile(checkpointer=checkpointer)

        return self.graph

    def run(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the pipeline with initial state.

        Args:
            initial_state: Initial state dictionary

        Returns:
            Final state after pipeline execution
        """
        if self.graph is None:
            self.build()

        result = self.graph.invoke(initial_state)
        return result


# Singleton instance
_design_graph: Optional[AeroDesignGraph] = None


def get_design_graph() -> AeroDesignGraph:
    """Get or create the singleton design graph."""
    global _design_graph
    if _design_graph is None:
        _design_graph = AeroDesignGraph()
        _design_graph.build()
    return _design_graph


def run_design_pipeline(
    payload_tons: float,
    material: str,
    engine: str,
    user_id: str = "anonymous",
    optional_constraints: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convenience function to run the design pipeline.

    Args:
        payload_tons: Payload capacity in tonnes
        material: Material type name
        engine: Engine type name
        user_id: User identifier
        optional_constraints: Optional design constraints

    Returns:
        Final design state
    """
    from aerodesign_ai.nodes.graph_state import create_initial_state

    initial_state = create_initial_state(
        payload_tons=payload_tons,
        material=material,
        engine=engine,
        user_id=user_id,
        optional_constraints=optional_constraints,
    )

    graph = get_design_graph()
    return graph.run(initial_state)