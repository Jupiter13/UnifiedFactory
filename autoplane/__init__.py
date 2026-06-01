"""AutoPlane Designer - Autonomous aircraft design agent.

A LangGraph-based agent that generates fixed-wing aircraft designs
through an iterative design loop with surrogate CFD/FEA simulations.
"""

from autoplane.agent import AutoPlaneAgent, get_agent, SYSTEM_PROMPT
from autoplane.models.state import (
    DesignState,
    DesignJob,
    DesignJobResponse,
    DesignStatusResponse,
    MaterialProps,
    EngineProps,
    AeroResult,
    StructResult,
    PerfResult,
    CostResult,
    RegResult,
    CADFile,
    GeometryJSON,
)
from autoplane.memory import get_memory, DesignMemory
from autoplane.tools import get_tools
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
)

__version__ = "0.1.0"

__all__ = [
    "AutoPlaneAgent",
    "get_agent",
    "SYSTEM_PROMPT",
    "DesignState",
    "DesignJob",
    "DesignJobResponse",
    "DesignStatusResponse",
    "MaterialProps",
    "EngineProps",
    "AeroResult",
    "StructResult",
    "PerfResult",
    "CostResult",
    "RegResult",
    "CADFile",
    "GeometryJSON",
    "get_memory",
    "DesignMemory",
    "get_tools",
    "input_parser",
    "material_selector",
    "engine_selector",
    "design_generator",
    "aerodynamic_evaluator",
    "structural_evaluator",
    "performance_estimator",
    "cost_estimator",
    "regulatory_checker",
    "cad_exporter",
    "report_generator",
    "feedback_loop",
]