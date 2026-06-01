"""LangGraph nodes for AeroDesign-AI design pipeline."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
import math
import uuid

from aerodesign_ai.nodes.graph_state import DesignState
from aerodesign_ai.tools.material_tool import FetchMaterialProps
from aerodesign_ai.tools.engine_tool import FetchEngineSpecs
from aerodesign_ai.tools.compliance_tool import RunComplianceCheck
from aerodesign_ai.tools.optimizer_tool import OptimizeDesign
from aerodesign_ai.tools.cad_tool import GenerateCAD
from aerodesign_ai.tools.bom_tool import GenerateBOM
from aerodesign_ai.tools.storage_tool import StoreDesign, DesignStorage


class DesignGenerationError(Exception):
    """Error in design generation pipeline."""
    pass


class BaseNode:
    """Base class for all pipeline nodes."""

    name: str = "base"

    def execute(self, state: DesignState) -> DesignState:
        """Execute node logic.

        Args:
            state: Current pipeline state

        Returns:
            Updated state dictionary
        """
        raise NotImplementedError

    def _update_state(self, state: DesignState, **updates) -> DesignState:
        """Helper to update state with new values."""
        new_state = {**state}
        for key, value in updates.items():
            if value is not None:
                new_state[key] = value
        return new_state


class StartNode(BaseNode):
    """Entry point node."""

    name = "start"

    def execute(self, state: DesignState) -> DesignState:
        """Initialize pipeline."""
        state["status"] = "running"
        state["timestamp"] = datetime.utcnow().isoformat()
        return state


class ValidateInputNode(BaseNode):
    """Validate input parameters."""

    name = "validate_input"

    VALID_MATERIALS = ["al7075_t6", "al2024_t3", "ti6al4v", "cf_epoxy", "al6061_t6", "steel4130"]
    VALID_ENGINES = ["lycoming_io720", "lycoming_io540", "continental_tsio550", "potez_4e", "potez_6e", "williams_fj33"]

    def execute(self, state: DesignState) -> DesignState:
        """Validate input parameters."""
        errors: List[str] = list(state.get("errors", []))

        # Validate payload
        payload = state.get("payload_tons", 0)
        if payload <= 0:
            errors.append(f"Invalid payload: {payload} tonnes (must be > 0)")
        elif payload > 100:
            errors.append(f"Payload {payload} tonnes exceeds maximum (100 tonnes)")

        # Validate material
        material = state.get("material", "")
        if not material:
            errors.append("Material is required")
        elif material.lower().replace(" ", "_") not in [m.lower() for m in self.VALID_MATERIALS]:
            # Try to match by partial name
            material_lower = material.lower()
            if not any(material_lower in m for m in self.VALID_MATERIALS):
                errors.append(f"Unknown material: {material}")

        # Validate engine
        engine = state.get("engine", "")
        if not engine:
            errors.append("Engine is required")
        elif engine.lower().replace(" ", "_") not in [e.lower() for e in self.VALID_ENGINES]:
            engine_lower = engine.lower()
            if not any(engine_lower in e for e in self.VALID_ENGINES):
                errors.append(f"Unknown engine: {engine}")

        # Update state
        state["errors"] = errors
        if errors:
            state["status"] = "failed"
        else:
            state["status"] = "running"

        return state


class FetchMaterialPropsNode(BaseNode):
    """Fetch material properties from library."""

    name = "fetch_material_props"

    def __init__(self):
        self._tool = FetchMaterialProps()

    def execute(self, state: DesignState) -> DesignState:
        """Fetch material properties."""
        material = state.get("material", "")
        result = self._tool.call(material=material)

        if not result.success:
            state["errors"].append(f"Material fetch error: {result.error}")
            return state

        props = result.data
        if props:
            state["material_props"] = {
                "name": props.name,
                "density_kg_m3": props.density_kg_m3,
                "tensile_strength_pa": props.tensile_strength_pa,
                "cost_per_kg": props.cost_per_kg,
                "manufacturability_score": props.manufacturability_score,
                "youngs_modulus_pa": props.youngs_modulus_pa,
            }

        return state


class FetchEngineSpecsNode(BaseNode):
    """Fetch engine specifications from library."""

    name = "fetch_engine_specs"

    def __init__(self):
        self._tool = FetchEngineSpecs()

    def execute(self, state: DesignState) -> DesignState:
        """Fetch engine specifications."""
        engine = state.get("engine", "")
        result = self._tool.call(engine=engine)

        if not result.success:
            state["errors"].append(f"Engine fetch error: {result.error}")
            return state

        specs = result.data
        if specs:
            state["engine_specs"] = {
                "name": specs.name,
                "thrust_newtons": specs.thrust_newtons,
                "fuel_flow_kg_s": specs.fuel_flow_kg_s,
                "weight_kg": specs.weight_kg,
                "cost_usd": specs.cost_usd,
                "specific_fuel_consumption": specs.specific_fuel_consumption,
            }

        return state


class GenerateInitialGeometryNode(BaseNode):
    """Generate initial parametric geometry."""

    name = "generate_geometry"
    _llm_seed_templates = None

    def execute(self, state: DesignState) -> DesignState:
        """Generate initial aircraft geometry using parametric design."""
        payload_tons = state.get("payload_tons", 1)
        material_props = state.get("material_props", {})
        engine_specs = state.get("engine_specs", {})
        constraints = state.get("optional_constraints", {})

        # Base parameters from payload
        payload_kg = payload_tons * 1000

        # Material-based weight factor
        material_factor = 1.0
        if material_props.get("manuf_", 0) < 0.7:
            material_factor = 0.9  # Stronger materials allow lighter structures
        density = material_props.get("density_kg_m3", 2800)

        # Engine-based sizing
        thrust = engine_specs.get("thrust_newtons", 20000)
        engine_weight = engine_specs.get("weight_kg", 200)

        # Wing sizing based on payload and required lift
        # Simplified: wing_area ∝ payload / wing_loading
        constraints = constraints or {}
        wing_loading_target = constraints.get("wing_loading_kg_m2", 200)  # kg/m²
        estimated_wing_area = payload_kg / wing_loading_target

        # Wing span based on aspect ratio target
        aspect_ratio = constraints.get("aspect_ratio", 10)
        wing_span = math.sqrt(estimated_wing_area * aspect_ratio)
        wing_area = wing_span ** 2 / aspect_ratio

        # Fuselage sizing
        fuselage_length = math.pow(payload_kg / 1000, 0.333) * 4 + 5  # Empirical
        fuselage_diameter = payload_kg / 500 + 1  # Empirical

        # Tail sizing
        tail_span = wing_span * 0.2 + 1
        tail_area = wing_area * 0.15

        # Engine pylon
        pylon_length = fuselage_diameter * 0.8 + 0.5

        # Initial geometry
        geometry = {
            # Geometry parameters
            "wing_span_m": round(wing_span, 2),
            "wing_area_m2": round(wing_area, 2),
            "aspect_ratio": aspect_ratio,
            "taper_ratio": 0.4,
            "wing_thickness_ratio": 0.12,
            "fuselage_length_m": round(fuselage_length, 2),
            "fuselage_diameter_m": round(fuselage_diameter, 2),
            "tail_span_m": round(tail_span, 2),
            "tail_area_m2": round(tail_area, 2),
            "engine_pylon_length_m": round(pylon_length, 2),

            # Derived/computed (will be updated by optimizer)
            "max_takeoff_weight_kg": payload_kg * 2.5,  # Initial estimate
            "empty_weight_kg": payload_kg * 2.5 * 0.5,
            "wing_mean_aerodynamic_chord_m": wing_span / aspect_ratio,

            # Constraints
            "material": state.get("material"),
            "engine": state.get("engine"),
        }

        # Add optional constraint overrides
        for key, value in constraints.items():
            if key in geometry or key in ["stall_speed_kt", "range_nm", "cruise_speed_kt"]:
                geometry[key] = value

        state["geometry"] = geometry
        return state


class OptimizeDesignNode(BaseNode):
    """Run multi-objective optimization."""

    name = "optimize_design"

    def __init__(self):
        self._tool = OptimizeDesign()

    def execute(self, state: DesignState) -> DesignState:
        """Optimize the design."""
        geometry = state.get("geometry", {})
        payload_tons = state.get("payload_tons", 1)
        material_props = state.get("material_props", {})
        engine_specs = state.get("engine_specs", {})

        # Convert props to optimizer format
        # First, ensure we have material props
        if not material_props:
            state["errors"].append("Material properties required for optimization")
            return state

        result = self._tool.call(
            geometry=geometry,
            payload_tons=payload_tons,
            material_density=material_props.get("density_kg_m3", 2800),
            material_cost=material_props.get("cost_per_kg", 10),
            material_strength=material_props.get("tensile_strength_pa", 5e8),
            engine_thrust=engine_specs.get("thrust_newtons", 20000),
            engine_weight=engine_specs.get("weight_kg", 200),
            engine_fuel_flow=engine_specs.get("fuel_flow_kg_s", 0.05),
        )

        if not result.success:
            state["errors"].append(f"Optimization error: {result.error}")
            return state

        result_data = result.data
        if result_data:
            state["geometry"] = result_data.get("geometry", geometry)
            state["optimization_metrics"] = result_data.get("metrics", {})

        return state


class ComplianceCheckNode(BaseNode):
    """Run compliance check against rules."""

    name = "compliance_check"

    def __init__(self):
        self._tool = RunComplianceCheck()

    def execute(self, state: DesignState) -> DesignState:
        """Run compliance validation."""
        geometry = state.get("geometry", {})
        payload_tons = state.get("payload_tons", 1)

        result = self._tool.call(geometry=geometry, payload=payload_tons)

        if result.success and result.data:
            state["compliance_report"] = {
                "passed": result.data.passed,
                "violations": result.data.violations,
                "warnings": result.data.warnings,
                "checked_rules": result.data.checked_rules,
            }

            # If compliance failed with critical errors, add to errors list
            if not result.data.passed:
                state["errors"].extend(result.data.violations)

        return state


class CADExportNode(BaseNode):
    """Export geometry to CAD format."""

    name = "cad_export"

    def __init__(self):
        self._tool = GenerateCAD()

    def execute(self, state: DesignState) -> DesignState:
        """Generate CAD file."""
        geometry = state.get("geometry", {})
        design_id = state.get("version_id") or f"DESIGN-{uuid.uuid4().hex[:8].upper()}"

        result = self._tool.call(geometry=geometry, design_id=design_id)

        if result.success and result.data:
            state["cad_file_path"] = result.data
        else:
            state["errors"].append(f"CAD export error: {result.error}")

        return state


class GenerateBOMNode(BaseNode):
    """Generate bill of materials."""

    name = "generate_bom"

    def __init__(self):
        self._tool = GenerateBOM()

    def execute(self, state: DesignState) -> DesignState:
        """Generate BOM."""
        geometry = state.get("geometry", {})
        material_props = state.get("material_props", {})
        engine_specs = state.get("engine_specs", {})

        result = self._tool.call(
            geometry=geometry,
            material_cost=material_props.get("cost_per_kg", 10),
            material_density=material_props.get("density_kg_m3", 2800),
            engine_cost=engine_specs.get("cost_usd", 30000),
        )

        if result.success and result.data:
            state["bom"] = [
                {
                    "part_name": item.part_name,
                    "quantity": item.quantity,
                    "unit_cost_usd": item.unit_cost_usd,
                    "total_cost_usd": item.total_cost_usd,
                    "material": item.material,
                    "weight_kg": item.weight_kg,
                    "description": item.description,
                }
                for item in result.data
            ]
        else:
            state["errors"].append(f"BOM generation error: {result.error}")

        return state


class StoreDesignNode(BaseNode):
    """Store completed design in database."""

    name = "store_design"

    def __init__(self):
        self._storage = DesignStorage()

    def execute(self, state: DesignState) -> DesignState:
        """Store design."""
        try:
            design_id = state.get("version_id")
            if design_id is None:
                design_id = f"DESIGN-{uuid.uuid4().hex[:8].to_upper()}"

            # Create a proper compliance report dict for storage
            compliance_report = state.get("compliance_report", {})
            if isinstance(compliance_report, dict):
                from aerodesign_ai.models.schemas import ComplianceReport
                from datetime import datetime
                compliance_report = ComplianceReport(
                    passed=compliance_report.get("passed", False),
                    violations=compliance_report.get("violations", []),
                    warnings=compliance_report.get("warnings", []),
                    checked_rules=compliance_report.get("checked_rules", []),
                )

            # Use the storage tool
            storage_tool = StoreDesign()
            result = storage_tool.call(
                payload_tons=state.get("payload_tons", 1),
                material=state.get("material", ""),
                engine=state.get("engine", ""),
                geometry=state.get("geometry", {}),
                optimization_metrics=state.get("optimization_metrics", {}),
                compliance_report=compliance_report,
                bom=[],  # Will be reconstructed from dict
                cad_file_path=state.get("cad_file_path", ""),
                user_id=state.get("user_id", "anonymous"),
                design_id=design_id,
            )

            if result.success and result.data:
                state["version_id"] = result.data
            else:
                state["errors"].append(f"Storage error: {result.error}")

        except Exception as e:
            state["errors"].append(f"Store design error: {str(e)}")

        return state


class EndNode(BaseNode):
    """End node - finalize and return results."""

    name = "end"

    def execute(self, state: DesignState) -> DesignState:
        """Finalize pipeline."""
        if not state.get("errors"):
            state["status"] = "completed"
        else:
            state["status"] = "failed"

        # Calculate total cost
        bom = state.get("bom", [])
        total_cost = sum(item.get("total_cost_usd", 0) for item in bom)
        state["total_cost_usd"] = total_cost

        return state
