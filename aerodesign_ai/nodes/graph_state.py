"""Graph state definitions for LangGraph pipeline."""

from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from aerodesign_ai.models.schemas import (
    ComplianceReport,
    BOMItem,
)


class DesignState(TypedDict, total=False):
    """State dictionary for LangGraph design pipeline."""

    # Input
    payload_tons: float
    material: str
    engine: str
    optional_constraints: Optional[Dict[str, Any]]
    
    # Materials and engines
    material_props: Optional[Dict[str, Any]]
    engine_specs: Optional[Dict[str, Any]]
    
    # Intermediate results
    geometry: Optional[Dict[str, Any]]
    optimization_metrics: Optional[Dict[str, float]]
    compliance_report: Optional[Dict[str, Any]]
    cad_file_path: Optional[str]
    bom: Optional[List[Dict[str, Any]]]
    
    # Design tracking
    version_id: Optional[str]
    errors: List[str]
    
    # Metadata
    user_id: str
    timestamp: str
    status: str  # queued, running, completed, failed
    
    # Total cost (computed)
    total_cost_usd: Optional[float]


def create_initial_state(
    payload_tons: float,
    material: str,
    engine: str,
    user_id: str = "anonymous",
    optional_constraints: Optional[Dict[str, Any]] = None,
) -> DesignState:
    """Create initial state for design pipeline.

    Args:
        payload_tons: Payload capacity in tonnes
        material: Material type name
        engine: Engine type name
        user_id: User identifier
        optional_constraints: Optional design constraints

    Returns:
        Initial DesignState dictionary
    """
    return DesignState(
        payload_tons=payload_tons,
        material=material,
        engine=engine,
        optional_constraints=optional_constraints,
        material_props=None,
        engine_specs=None,
        geometry=None,
        optimization_metrics=None,
        compliance_report=None,
        cad_file_path=None,
        bom=None,
        version_id=None,
        errors=[],
        user_id=user_id,
        timestamp=datetime.utcnow().isoformat(),
        status="queued",
        total_cost_usd=None,
    )


def router_node(state: DesignState) -> str:
    """Routing function for conditional edges.

    Args:
        state: Current design state

    Returns:
        Edge name to follow
    """
    # Check if we have errors that cannot be recovered
    if len(state.get("errors", [])) >= 3:
        return "end"
    
    # Check compliance status
    compliance = state.get("compliance_report")
    if compliance is not None:
        if not compliance.get("passed", False):
            # Try optimization again with adjusted parameters
            return "optimize"
    
    # Default routing based on pipeline stage
    if state.get("geometry") is None:
        return "geometry"
    elif state.get("optimization_metrics") is None:
        return "optimize"
    elif state.get("compliance_report") is None:
        return "compliance"
    elif state.get("cad_file_path") is None:
        return "cad"
    elif state.get("bom") is None:
        return "bom"
    elif state.get("version_id") is None:
        return "store"
    else:
        return "end"
