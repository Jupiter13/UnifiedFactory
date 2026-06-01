"""AFW-D Engine Graph Nodes.

LangGraph node implementations for the aircraft design workflow.
"""

import uuid
from typing import Optional

from .state import AFWDesignState

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
    CFDSimulationResult,
    FEASimulationResult,
)

# Import tools first
from ..tools import (
    MaterialDBQueryTool,
    EngineDBQueryTool,
    CADGeneratorTool,
    CFDSolverTool,
    FEASolverTool,
    CostEstimatorTool,
    ComplianceCheckerTool,
    OptimizationTool,
    VersionControlTool,
    ExportTool,
)

# Tool instances (would be injected in production)
_material_tool = MaterialDBQueryTool()
_engine_tool = EngineDBQueryTool()
_cad_tool = CADGeneratorTool()
_cfd_tool = CFDSolverTool()
_fea_tool = FEASolverTool()
_cost_tool = CostEstimatorTool()
_compliance_tool = ComplianceCheckerTool()
_optimization_tool = OptimizationTool()
_version_tool = VersionControlTool()
_export_tool = ExportTool()

MAX_ITERATIONS = 10


def _to_design_params(params) -> DesignParams:
    """Convert dict or DesignParams to DesignParams."""
    if isinstance(params, dict):
        return DesignParams(**params)
    return params


def _to_material_props(props) -> Optional[MaterialProperties]:
    """Convert dict or MaterialProperties to MaterialProperties."""
    if props is None:
        return None
    if isinstance(props, dict):
        return MaterialProperties(**props)
    return props


def _to_engine_specs(specs) -> Optional[EngineSpecs]:
    """Convert dict or EngineSpecs to EngineSpecs."""
    if specs is None:
        return None
    if isinstance(specs, dict):
        return EngineSpecs(**specs)
    return specs


def input_collector(state: AFWDesignState) -> dict:
    """Collect and validate user input.

    Args:
        state: Current design state.

    Returns:
        Updated state dictionary.
    """
    design_id = str(uuid.uuid4())

    # Validate payload
    if state.get("payload_kg", 0) <= 0:
        return {
            "error": "Payload must be greater than 0 kg",
            "design_id": design_id,
        }

    return {
        "design_id": design_id,
        "iteration": 0,
        "feedback": [],
        "history": [],
        "error": None,
    }


def material_selector(state: AFWDesignState) -> dict:
    """Select and validate material based on constraints.

    Args:
        state: Current design state.

    Returns:
        Updated state dictionary.
    """
    material_family = state.get("material_family")

    if not material_family:
        # Default material selection
        material_family = "Al-Mg-Si"

    try:
        material_props = _material_tool.invoke(material_family)
        return {
            "material_family": material_family,
            "material_props": material_props,
            "error": None,
        }
    except ValueError as e:
        return {
            "material_family": material_family,
            "error": f"Material selection failed: {str(e)}",
        }


def engine_selector(state: AFWDesignState) -> dict:
    """Select and validate engine based on constraints.

    Args:
        state: Current design state.

    Returns:
        Updated state dictionary.
    """
    engine_family = state.get("engine_family")

    if not engine_family:
        # Default engine selection based on payload
        payload = state.get("payload_kg", 0)
        if payload > 5000:
            engine_family = "Turboprop-B"
        else:
            engine_family = "Turboprop-A"

    try:
        engine_specs = _engine_tool.invoke(engine_family)
        return {
            "engine_family": engine_family,
            "engine_specs": engine_specs,
            "error": None,
        }
    except ValueError as e:
        return {
            "engine_family": engine_family,
            "error": f"Engine selection failed: {str(e)}",
        }


def design_generator(state: AFWDesignState) -> dict:
    """Generate initial design parameters.

    Args:
        state: Current design state.

    Returns:
        Updated state dictionary.
    """
    payload_kg = state.get("payload_kg", 1000)
    material_props = state.get("material_props")
    engine_specs = state.get("engine_specs")

    # Estimate empty weight based on payload
    empty_weight = payload_kg * 3.0  # Rough estimation
    max_takeoff_weight = empty_weight + payload_kg

    # Generate design parameters based on constraints
    wing_area = max(10.0, payload_kg / 50.0)
    aspect_ratio = 8.0 if payload_kg < 2000 else 6.0

    design_params = {
        "wing_area": wing_area,
        "aspect_ratio": aspect_ratio,
        "sweep": 15.0,
        "fuselage_length": max(5.0, wing_area * 1.5),
        "tail_area": wing_area * 0.15,
        "max_takeoff_weight": max_takeoff_weight,
        "empty_weight": empty_weight,
        "wing_thickness_ratio": 0.15,
        "taper_ratio": 0.6,
    }

    return {
        "design_params": design_params,
        "error": None,
    }


def simulation_runner(state: AFWDesignState) -> dict:
    """Run CFD and FEA simulations.

    Args:
        state: Current design state.

    Returns:
        Updated state dictionary.
    """
    design_params_raw = state.get("design_params")
    engine_specs_raw = state.get("engine_specs")
    material_props_raw = state.get("material_props")

    if not design_params_raw:
        return {"error": "No design parameters to simulate"}

    # Convert to proper types
    design_params = _to_design_params(design_params_raw)
    engine_specs = _to_engine_specs(engine_specs_raw)
    material_props = _to_material_props(material_props_raw)

    # Run CFD simulation
    cfd_result = _cfd_tool.invoke(design_params, engine_specs)

    # Run FEA simulation
    fea_result = _fea_tool.invoke(design_params, material_props)

    simulation = {
        "cfd": cfd_result,
        "fea": fea_result,
    }

    return {
        "simulation": simulation,
        "error": None,
    }


def cost_estimator(state: AFWDesignState) -> dict:
    """Estimate design cost.

    Args:
        state: Current design state.

    Returns:
        Updated state dictionary.
    """
    design_params_raw = state.get("design_params")
    material_props_raw = state.get("material_props")
    engine_specs_raw = state.get("engine_specs")

    if not design_params_raw:
        return {"error": "No design parameters to cost"}

    # Convert to proper types
    design_params = _to_design_params(design_params_raw)
    material_props = _to_material_props(material_props_raw)
    engine_specs = _to_engine_specs(engine_specs_raw)

    cost_estimate = _cost_tool.invoke(design_params, material_props, engine_specs)

    return {
        "cost_estimate": cost_estimate,
        "error": None,
    }


def compliance_checker(state: AFWDesignState) -> dict:
    """Check regulatory compliance.

    Args:
        state: Current design state.

    Returns:
        Updated state dictionary.
    """
    design_params_raw = state.get("design_params")
    simulation_raw = state.get("simulation")
    cost_estimate_raw = state.get("cost_estimate")

    if not design_params_raw:
        return {"error": "No design parameters to check"}

    # Convert to proper types
    design_params = _to_design_params(design_params_raw)

    compliance = _compliance_tool.invoke(design_params, simulation_raw, cost_estimate_raw)

    return {
        "compliance": compliance,
        "error": None,
    }


def optimization_loop(state: AFWDesignState) -> dict:
    """Run optimization loop based on compliance results.

    Args:
        state: Current design state.

    Returns:
        Updated state dictionary with routing decision.
    """
    compliance_raw = state.get("compliance")
    design_params_raw = state.get("design_params")
    simulation_raw = state.get("simulation")
    cost_estimate_raw = state.get("cost_estimate")
    iteration = state.get("iteration", 0)

    # Increment iteration
    new_iteration = iteration + 1

    if compliance_raw and not compliance_raw.passed and new_iteration < MAX_ITERATIONS:
        # Convert to proper types
        design_params = _to_design_params(design_params_raw)

        # Run optimization to fix issues
        optimized_params = _optimization_tool.invoke(
            design_params, simulation_raw, cost_estimate_raw
        )

        return {
            "design_params": optimized_params,
            "iteration": new_iteration,
            "error": None,
            "needs_rerun": True,
        }

    # Either passed or max iterations reached
    return {
        "iteration": new_iteration,
        "needs_rerun": False,
        "error": None,
    }


def exporter(state: AFWDesignState) -> dict:
    """Export final design to CAD file.

    Args:
        state: Current design state.

    Returns:
        Updated state dictionary.
    """
    design_params_raw = state.get("design_params")

    if not design_params_raw:
        return {"error": "No design parameters to export"}

    # Convert to proper types
    design_params = _to_design_params(design_params_raw)

    cad_file = _cad_tool.invoke(design_params)

    # Store design state in history
    design_state = DesignState(
        design_params=design_params,
        cad_file=cad_file,
        simulation=state.get("simulation"),
        cost_estimate=state.get("cost_estimate"),
        compliance=state.get("compliance"),
    )
    _version_tool.invoke(design_state)

    return {
        "cad_file": cad_file,
        "error": None,
    }


def feedback_handler(state: AFWDesignState) -> dict:
    """Handle user feedback and prepare final report.

    Args:
        state: Current design state.

    Returns:
        Updated state dictionary.
    """
    design_id = state.get("design_id")
    compliance = state.get("compliance")
    design_params = state.get("design_params")
    simulation = state.get("simulation")
    cost_estimate = state.get("cost_estimate")

    # Prepare final report
    report = {
        "design_id": design_id,
        "status": "completed" if compliance and compliance.passed else "failed",
        "compliance_passed": compliance.passed if compliance else False,
        "issues": compliance.issues if compliance else [],
        "iteration": state.get("iteration", 0),
    }

    return {
        "feedback": state.get("feedback", []) + [report],
        "error": None,
    }