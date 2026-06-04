"""Agent nodes for the AutoPlane Design Graph.

Each node performs a specific function in the design workflow and
reads/writes to the shared DesignState.
"""

import json
import uuid
import logging
from typing import Literal, Optional

from autoplane.models.state import (
    DesignState,
    MaterialProps,
    EngineProps,
    GeometryJSON,
    AeroResult,
    StructResult,
    PerfResult,
    CostResult,
    RegResult,
    CADFile,
)
from autoplane.tools import (
    generate_geometry,
    run_cfd_surrogate,
    run_fea_surrogate,
    compute_performance,
    estimate_cost,
    check_regulations,
    export_cad,
    generate_report,
    reoptimize_design,
)

logger = logging.getLogger(__name__)


class NodeError(Exception):
    """Exception raised when a node fails."""
    pass


def input_parser(state: DesignState) -> DesignState:
    """Parse and validate user input payload.

    Args:
        state: Current design state

    Returns:
        Updated design state
    """
    logger.info(f"InputParser: Processing payload {state.payload_kg} kg")

    # Validate payload
    if state.payload_kg <= 0:
        state.last_error = "Payload must be positive"
        state.status = "failed"
        return state

    if state.payload_kg > 50000:
        state.last_error = "Payload exceeds maximum (50000 kg)"
        state.status = "failed"
        return state

    # Set default material and engine if not provided
    if not state.material:
        state.material = "Al-6061"
        logger.info("InputParser: Using default material Al-6061")

    if not state.engine:
        state.engine = "Turbofan-1"
        logger.info("InputParser: Using default engine Turbofan-1")

    # Generate job ID if not present
    if not state.job_id:
        state.job_id = str(uuid.uuid4())

    state.status = "running"
    return state


def material_selector(state: DesignState) -> DesignState:
    """Resolve material properties from database.

    Args:
        state: Current design state

    Returns:
        Updated design state with material_props
    """
    logger.info(f"MaterialSelector: Resolving material {state.material}")

    # Material database (would be queried from PostgreSQL in production)
    materials_db = {
        "Al-6061": MaterialProps(
            name="Al-6061",
            density=2700.0,
            tensile_strength=310.0,
            cost_per_kg=5.0,
        ),
        "Carbon Fiber": MaterialProps(
            name="Carbon Fiber",
            density=1600.0,
            tensile_strength=600.0,
            cost_per_kg=50.0,
        ),
        "Titanium": MaterialProps(
            name="Titanium",
            density=4500.0,
            tensile_strength=900.0,
            cost_per_kg=100.0,
        ),
    }

    if state.material not in materials_db:
        state.last_error = f"Unknown material: {state.material}"
        state.status = "failed"
        return state

    state.material_props = materials_db[state.material]
    logger.info(f"MaterialSelector: Resolved to {state.material_props}")
    return state


def engine_selector(state: DesignState) -> DesignState:
    """Resolve engine specifications from database.

    Args:
        state: Current design state

    Returns:
        Updated design state with engine_props
    """
    logger.info(f"EngineSelector: Resolving engine {state.engine}")

    # Engine database (would be queried from PostgreSQL in production)
    engines_db = {
        "Turbofan-1": EngineProps(
            name="Turbofan-1",
            thrust=50.0,
            fuel_flow=500.0,
            weight=800.0,
            cost=50000.0,
        ),
        "Turbofan-2": EngineProps(
            name="Turbofan-2",
            thrust=80.0,
            fuel_flow=800.0,
            weight=1200.0,
            cost=75000.0,
        ),
        "Propeller-1": EngineProps(
            name="Propeller-1",
            thrust=30.0,
            fuel_flow=200.0,
            weight=400.0,
            cost=25000.0,
        ),
    }

    if state.engine not in engines_db:
        state.last_error = f"Unknown engine: {state.engine}"
        state.status = "failed"
        return state

    state.engine_props = engines_db[state.engine]
    logger.info(f"EngineSelector: Resolved to {state.engine_props}")
    return state


def design_generator(state: DesignState) -> DesignState:
    """Generate initial aircraft geometry.

    Args:
        state: Current design state

    Returns:
        Updated design state with geometry_json
    """
    logger.info("DesignGenerator: Generating geometry")

    try:
        geometry_dict = generate_geometry(
            payload=state.payload_kg,
            material=state.material or "Al-6061",
            engine=state.engine or "Turbofan-1",
        )

        state.geometry_json = GeometryJSON(**geometry_dict)
        state.wing_span = state.geometry_json.wing_span
        state.wing_area = state.geometry_json.wing_area
        state.fuselage_length = state.geometry_json.fuselage_length
        state.tail_area = state.geometry_json.tail_area

        logger.info(f"DesignGenerator: Generated geometry with wing_span={state.wing_span}")
    except Exception as e:
        state.last_error = f"Geometry generation failed: {str(e)}"
        state.status = "failed"
        logger.error(state.last_error)

    return state


def should_continue(state: DesignState) -> str:
    """Check if graph should continue or stop due to errors.

    Args:
        state: Current design state

    Returns:
        "continue" to proceed, "stop" to exit
    """
    if state.status == "failed":
        return "stop"
    return "continue"


def aerodynamic_evaluator(state: DesignState) -> DesignState:
    """Run surrogate CFD analysis.

    Args:
        state: Current design state

    Returns:
        Updated design state with aerodynamic results
    """
    logger.info("AerodynamicEvaluator: Running surrogate CFD")

    if not state.geometry_json:
        state.last_error = "No geometry available for CFD analysis"
        state.status = "failed"
        return state

    try:
        geometry_dict = state.geometry_json.model_dump()
        aero_dict = run_cfd_surrogate(geometry_dict)
        state.aerodynamic = AeroResult(**aero_dict)
        logger.info(f"AerodynamicEvaluator: CL={state.aerodynamic.lift_coefficient}, Cd={state.aerodynamic.drag_coefficient}")
    except Exception as e:
        state.last_error = f"CFD surrogate failed: {str(e)}"
        state.status = "failed"
        logger.error(state.last_error)

    return state


def structural_evaluator(state: DesignState) -> DesignState:
    """Run surrogate FEA analysis.

    Args:
        state: Current design state

    Returns:
        Updated design state with structural results
    """
    logger.info("StructuralEvaluator: Running surrogate FEA")

    if not state.geometry_json:
        state.last_error = "No geometry available for FEA analysis"
        state.status = "failed"
        return state

    try:
        geometry_dict = state.geometry_json.model_dump()
        struct_dict = run_fea_surrogate(geometry_dict)
        state.structural = StructResult(**struct_dict)
        logger.info(f"StructuralEvaluator: Weight={state.structural.weight_kg} kg, Max stress={state.structural.max_stress} MPa")
    except Exception as e:
        state.last_error = f"FEA surrogate failed: {str(e)}"
        state.status = "failed"
        logger.error(state.last_error)

    return state


def performance_estimator(state: DesignState) -> DesignState:
    """Compute overall aircraft performance.

    Args:
        state: Current design state

    Returns:
        Updated design state with performance results
    """
    logger.info("PerformanceEstimator: Computing performance")

    if not state.aerodynamic or not state.structural or not state.engine_props:
        state.last_error = "Missing required results for performance estimation"
        state.status = "failed"
        return state

    try:
        aero_dict = state.aerodynamic.model_dump()
        struct_dict = state.structural.model_dump()
        engine_dict = state.engine_props.model_dump()

        perf_dict = compute_performance(aero_dict, struct_dict, engine_dict)
        state.performance = PerfResult(**perf_dict)
        logger.info(f"PerformanceEstimator: Range={state.performance.range_km} km, Cruise={state.performance.cruise_speed_kts} kts")
    except Exception as e:
        state.last_error = f"Performance estimation failed: {str(e)}"
        state.status = "failed"
        logger.error(state.last_error)

    return state


def cost_estimator(state: DesignState) -> DesignState:
    """Estimate manufacturing and material costs.

    Args:
        state: Current design state

    Returns:
        Updated design state with cost results
    """
    logger.info("CostEstimator: Estimating costs")

    if not state.geometry_json or not state.material or not state.engine:
        state.last_error = "Missing required data for cost estimation"
        state.status = "failed"
        return state

    try:
        geometry_dict = state.geometry_json.model_dump()
        cost_dict = estimate_cost(geometry_dict, state.material, state.engine)
        state.cost = CostResult(**cost_dict)
        logger.info(f"CostEstimator: Total cost=${state.cost.total_cost}")
    except Exception as e:
        state.last_error = f"Cost estimation failed: {str(e)}"
        state.status = "failed"
        logger.error(state.last_error)

    return state


def regulatory_checker(state: DesignState) -> DesignState:
    """Check regulatory compliance.

    Args:
        state: Current design state

    Returns:
        Updated design state with regulatory results
    """
    logger.info("RegulatoryChecker: Checking regulations")

    if not state.performance or not state.aerodynamic:
        state.last_error = "Missing required data for regulatory check"
        state.status = "failed"
        return state

    try:
        perf_dict = state.performance.model_dump()
        aero_dict = state.aerodynamic.model_dump()

        reg_dict = check_regulations(perf_dict, aero_dict)
        state.regulatory = RegResult(**reg_dict)

        # Check if re-optimization is needed
        if not state.regulatory.stall_speed_ok or not state.regulatory.noise_limit_ok:
            state.needs_reopt = True
            logger.info("RegulatoryChecker: Re-optimization needed")

        logger.info(f"RegulatoryChecker: Violations={len(state.regulatory.violations)}")
    except Exception as e:
        state.last_error = f"Regulatory check failed: {str(e)}"
        state.status = "failed"
        logger.error(state.last_error)

    return state


def cad_exporter(state: DesignState) -> DesignState:
    """Export geometry to CAD format.

    Args:
        state: Current design state

    Returns:
        Updated design state with CAD file metadata
    """
    logger.info("CADExporter: Exporting to CAD")

    if not state.geometry_json:
        state.last_error = "No geometry available for CAD export"
        state.status = "failed"
        return state

    try:
        geometry_dict = state.geometry_json.model_dump()
        cad_dict = export_cad(geometry_dict, format="STEP")
        state.cad_file = CADFile(**cad_dict)
        logger.info(f"CADExporter: Exported to {state.cad_file.format}, size={state.cad_file.size_bytes} bytes")
    except Exception as e:
        state.last_error = f"CAD export failed: {str(e)}"
        state.status = "failed"
        logger.error(state.last_error)

    return state


def report_generator(state: DesignState) -> DesignState:
    """Generate PDF design report.

    Args:
        state: Current design state

    Returns:
        Updated design state with PDF report
    """
    logger.info("ReportGenerator: Generating PDF report")

    try:
        state_dict = state.model_dump()
        pdf_bytes = generate_report(state_dict)
        state.report_pdf = pdf_bytes
        state.status = "completed"
        logger.info(f"ReportGenerator: Generated {len(pdf_bytes)} byte PDF, status={state.status}")
    except Exception as e:
        state.last_error = f"Report generation failed: {str(e)}"
        state.status = "failed"
        logger.error(state.last_error)

    return state


def feedback_loop(state: DesignState) -> DesignState:
    """Re-optimize design if constraints are not met.

    Args:
        state: Current design state

    Returns:
        Updated design state with re-optimized geometry
    """
    logger.info(f"FeedbackLoop: Iteration {state.iteration + 1}")

    if not state.needs_reopt:
        logger.info("FeedbackLoop: No re-optimization needed")
        return state

    if state.iteration >= state.max_iterations:
        logger.warning("FeedbackLoop: Max iterations reached")
        state.needs_reopt = False
        state.last_error = "Max iterations reached - constraints could not be fully satisfied"
        return state

    try:
        state_dict = state.model_dump()
        new_geometry = reoptimize_design(state_dict)

        state.geometry_json = GeometryJSON(**new_geometry)
        state.wing_span = state.geometry_json.wing_span
        state.wing_area = state.geometry_json.wing_area
        state.fuselage_length = state.geometry_json.fuselage_length
        state.tail_area = state.geometry_json.tail_area

        state.iteration += 1
        state.needs_reopt = False  # Will be re-evaluated after re-running evaluations

        logger.info(f"FeedbackLoop: Re-optimized geometry, iteration={state.iteration}")
    except Exception as e:
        state.last_error = f"Re-optimization failed: {str(e)}"
        state.status = "failed"
        logger.error(state.last_error)

    return state


def should_reoptimize(state: DesignState) -> str:
    """Decide whether to re-optimize or complete.

    Args:
        state: Current design state

    Returns:
        Next node name
    """
    if state.needs_reopt and state.iteration < state.max_iterations:
        return "reoptimize"
    else:
        return "complete"


def should_regenerate(state: DesignState) -> str:
    """Decide whether to regenerate geometry after re-optimization.

    Args:
        state: Current design state

    Returns:
        Next node name
    """
    if state.iteration > 0:
        return "design_generator"
    return "aerodynamic_evaluator"