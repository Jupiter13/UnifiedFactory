"""AFW-D Engine Graph State Definition.

LangGraph state schema for the aircraft design workflow.
"""

from typing import Optional, List

from langgraph.graph import MessagesState

from ..models import (
    DesignParams,
    CADFile,
    SimulationResult,
    CostEstimate,
    ComplianceReport,
    Feedback,
    DesignState,
    MaterialProperties,
    EngineSpecs,
)


class AFWDesignState(MessagesState):
    """Main state for the AFW-D design workflow."""

    # Input parameters
    payload_kg: float = 0.0
    material_family: Optional[str] = None
    engine_family: Optional[str] = None

    # Design artifacts
    material_props: Optional[MaterialProperties] = None
    engine_specs: Optional[EngineSpecs] = None
    design_params: Optional[DesignParams] = None
    cad_file: Optional[CADFile] = None
    simulation: Optional[SimulationResult] = None
    cost_estimate: Optional[CostEstimate] = None
    compliance: Optional[ComplianceReport] = None

    # Workflow tracking
    iteration: int = 0
    feedback: List[Feedback] = []
    history: List[DesignState] = []

    # Error handling
    error: Optional[str] = None

    # Design ID for tracking
    design_id: Optional[str] = None


def initial_state(payload_kg: float, material_family: str = None, engine_family: str = None) -> dict:
    """Create initial state from user input.

    Args:
        payload_kg: Payload mass in kg.
        material_family: Optional material family.
        engine_family: Optional engine family.

    Returns:
        Initial state dictionary.
    """
    return {
        "payload_kg": payload_kg,
        "material_family": material_family,
        "engine_family": engine_family,
        "iteration": 0,
        "feedback": [],
        "history": [],
    }