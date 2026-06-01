"""Tools for the AutoPlane Design Agent.

These tools are exposed as FastAPI endpoints and wrapped in LangChain Tool objects.
They implement the surrogate models and utilities for the design workflow.
"""

import json
import uuid
import random
import hashlib
from typing import Dict, Any, Optional

from autoplane.models.state import (
    GeometryJSON,
    AeroResult,
    StructResult,
    PerfResult,
    CostResult,
    RegResult,
    CADFile,
    DesignState,
)


def generate_geometry(
    payload: float,
    material: str,
    engine: str,
) -> Dict[str, Any]:
    """Generate initial aircraft geometry based on design requirements.

    This is a placeholder implementation that would normally call a VAE+RL model.
    Returns a JSON representation of the 3D geometry.

    Args:
        payload: Payload requirement in kg
        material: Selected material name
        engine: Selected engine name

    Returns:
        Dictionary with geometry parameters
    """
    # Simple heuristic-based geometry generation
    # In production, this would call a trained VAE+RL model

    # Scale factors based on payload
    scale_factor = (payload / 1000.0) ** 0.33

    wing_span = 15.0 * scale_factor
    wing_area = 30.0 * scale_factor
    fuselage_length = 12.0 * scale_factor
    tail_area = 5.0 * scale_factor
    aspect_ratio = wing_span ** 2 / wing_area
    mean_aerodynamic_chord = wing_area / wing_span

    # Generate simplified vertex/face data for a basic aircraft shape
    vertices = [
        [0, 0, 0],
        [wing_span / 2, 0, 0.5],
        [wing_span / 2, 0, -0.5],
        [-wing_span / 2, 0, -0.5],
        [-wing_span / 2, 0, 0.5],
        [fuselage_length / 2, 0, 0],
        [-fuselage_length / 2, 0, 0],
    ]

    faces = [
        [0, 1, 2],
        [0, 2, 3],
        [0, 3, 4],
        [0, 4, 1],
        [5, 1, 2],
        [6, 3, 2],
    ]

    geometry = {
        "wing_span": round(wing_span, 2),
        "wing_area": round(wing_area, 2),
        "fuselage_length": round(fuselage_length, 2),
        "tail_area": round(tail_area, 2),
        "aspect_ratio": round(aspect_ratio, 2),
        "mean_aerodynamic_chord": round(mean_aerodynamic_chord, 2),
        "vertices": vertices,
        "faces": faces,
        "metadata": {
            "material": material,
            "engine": engine,
            "payload": payload,
        },
    }

    return geometry


def run_cfd_surrogate(geometry: Dict[str, Any]) -> Dict[str, Any]:
    """Run surrogate CFD analysis on the geometry.

    This is a placeholder implementation that returns estimated aerodynamic values.
    In production, this would call a trained neural network surrogate model.

    Args:
        geometry: Geometry JSON dictionary

    Returns:
        Dictionary with aerodynamic results
    """
    wing_span = geometry.get("wing_span", 15.0)
    wing_area = geometry.get("wing_area", 30.0)
    aspect_ratio = geometry.get("aspect_ratio", 7.5)

    # Simplified aerodynamic calculations
    # Lift coefficient (Cl_max) - typical values for general aviation
    max_lift = 1.5 + random.uniform(-0.1, 0.1)

    # Lift coefficient at cruise (Cl)
    lift_coefficient = 0.5 + 0.1 * (aspect_ratio / 10.0)

    # Drag coefficient estimation (Oswald efficiency factor ~0.8)
    oswald_efficiency = 0.8
    cd0 = 0.02  # Zero-lift drag coefficient
    cl_cruise = lift_coefficient
    drag_coefficient = cd0 + (cl_cruise ** 2) / (3.14159 * aspect_ratio * oswald_efficiency)

    # Stall speed estimation (in knots)
    # V_stall = sqrt(2 * W / (rho * S * Cl_max))
    weight = geometry.get("metadata", {}).get("payload", 1000) * 9.81
    rho = 1.225  # Air density at sea level
    s = wing_area
    v_stall_ms = (2 * weight / (rho * s * max_lift)) ** 0.5
    stall_speed_kts = v_stall_ms * 1.94384  # Convert to knots

    return {
        "lift_coefficient": round(lift_coefficient, 4),
        "drag_coefficient": round(drag_coefficient, 4),
        "stall_speed_kts": round(stall_speed_kts, 2),
        "max_lift": round(max_lift, 4),
    }


def run_fea_surrogate(geometry: Dict[str, Any]) -> Dict[str, Any]:
    """Run surrogate FEA analysis on the geometry.

    This is a placeholder implementation that returns estimated structural values.
    In production, this would call a trained neural network surrogate model.

    Args:
        geometry: Geometry JSON dictionary

    Returns:
        Dictionary with structural results
    """
    wing_span = geometry.get("wing_span", 15.0)
    wing_area = geometry.get("wing_area", 30.0)
    payload = geometry.get("metadata", {}).get("payload", 1000)

    # Simplified structural calculations
    # Weight estimation based on wing area and material density
    material_density = 2700  # Aluminum 6061 default
    struct_volume = wing_area * 0.1  # Approximate shell thickness
    weight_kg = struct_volume * material_density / 1000 + payload * 0.1 + 500

    # Max bending moment at wing root (simplified)
    max_bending_moment = weight_kg * 9.81 * wing_span / 4

    # Max stress calculation (sigma = M * y / I)
    y = wing_span / 20  # Approximate section modulus factor
    i = wing_area * y ** 2 / 12
    max_stress = (max_bending_moment * 1000 * y) / i if i > 0 else 100

    # Fatigue life estimation (simplified S-N curve approach)
    fatigue_life_years = 20 + random.uniform(-2, 5)

    return {
        "max_bending_moment": round(max_bending_moment / 1000, 2),  # kNm
        "max_stress": round(max_stress / 1e6, 2),  # MPa
        "weight_kg": round(weight_kg, 2),
        "fatigue_life_years": round(fatigue_life_years, 1),
    }


def compute_performance(
    aero: Dict[str, Any],
    structural: Dict[str, Any],
    engine: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute overall aircraft performance metrics.

    Args:
        aero: Aerodynamic results
        structural: Structural results
        engine: Engine properties

    Returns:
        Dictionary with performance results
    """
    cl = aero.get("lift_coefficient", 0.5)
    cd = aero.get("drag_coefficient", 0.03)
    cd0 = 0.02  # Zero-lift drag
    weight = structural.get("weight_kg", 1000) * 9.81

    # L/D ratio
    ld_ratio = cl / cd if cd > 0 else 15

    # Cruise speed (simplified using lift equation)
    rho = 1.225
    s = 30.0  # Default wing area
    v_cruise_ms = ((2 * weight) / (rho * s * cl)) ** 0.5
    cruise_speed_kts = v_cruise_ms * 1.94384

    # Range estimation (Breguet range equation)
    specific_fuel_consumption = 0.0005  # Typical for jet engines
    fuel_fraction = 0.3  # 30% fuel of total weight
    range_km = ld_ratio * 850 / 9.81 * specific_fuel_consumption * (fuel_fraction / (1 - fuel_fraction))
    range_km = min(range_km, 5000)  # Cap at realistic maximum

    # Endurance
    endurance_hr = range_km / (cruise_speed_kts * 1.852) if cruise_speed_kts > 0 else 10

    # Fuel burn
    fuel_flow = engine.get("fuel_flow", 500)  # kg/h
    fuel_burn_kg = fuel_flow * endurance_hr

    return {
        "range_km": round(range_km, 1),
        "cruise_speed_kts": round(cruise_speed_kts, 1),
        "fuel_burn_kg": round(fuel_burn_kg, 1),
        "endurance_hr": round(endurance_hr, 1),
    }


def estimate_cost(
    geometry: Dict[str, Any],
    material: str,
    engine: str,
) -> Dict[str, Any]:
    """Estimate manufacturing and material costs.

    Args:
        geometry: Geometry JSON
        material: Material name
        engine: Engine name

    Returns:
        Dictionary with cost breakdown
    """
    wing_area = geometry.get("wing_area", 30.0)
    fuselage_length = geometry.get("fuselage_length", 12.0)

    # Material costs
    material_costs = {
        "Al-6061": 5.0,
        "Carbon Fiber": 50.0,
        "Titanium": 100.0,
    }
    cost_per_kg = material_costs.get(material, 5.0)
    material_volume = wing_area * 0.1 + fuselage_length * 0.5
    weight_kg = material_volume * 2700 / 1000  # Assuming aluminum density
    material_cost = weight_kg * cost_per_kg

    # Manufacturing cost (labor + machining)
    manufacturing_cost = material_cost * 3.0

    # Assembly cost
    assembly_cost = material_cost * 1.5

    # Engine cost (would be looked up from database)
    engine_costs = {
        "Turbofan-1": 50000,
        "Turbofan-2": 75000,
        "Propeller-1": 25000,
    }
    engine_cost = engine_costs.get(engine, 30000)

    total_cost = material_cost + manufacturing_cost + assembly_cost + engine_cost

    return {
        "material_cost": round(material_cost, 2),
        "manufacturing_cost": round(manufacturing_cost, 2),
        "assembly_cost": round(assembly_cost, 2),
        "total_cost": round(total_cost, 2),
    }


def check_regulations(
    performance: Dict[str, Any],
    aero: Dict[str, Any],
) -> Dict[str, Any]:
    """Check regulatory compliance.

    Args:
        performance: Performance results
        aero: Aerodynamic results

    Returns:
        Dictionary with regulatory compliance results
    """
    violations = []

    # Stall speed check (FAR 23.49)
    stall_speed = aero.get("stall_speed_kts", 60)
    if stall_speed > 61:
        violations.append(f"Stall speed {stall_speed} kts exceeds 61 kts limit (FAR 23.49)")

    # Noise check (FAR 36)
    noise_ok = True
    if stall_speed > 50:
        violations.append("Noise levels may exceed FAR 36 limits")

    # Max takeoff weight check (FAR 23.1)
    # This is simplified - actual check would use structural weight
    max_takeoff_weight_ok = stall_speed > 30  # Placeholder logic

    return {
        "stall_speed_ok": stall_speed <= 61,
        "noise_limit_ok": noise_ok,
        "max_takeoff_weight_ok": max_takeoff_weight_ok,
        "violations": violations,
    }


def export_cad(
    geometry: Dict[str, Any],
    format: str = "STEP",
) -> Dict[str, Any]:
    """Export geometry to CAD format.

    Args:
        geometry: Geometry JSON
        format: Export format (STEP, IGES, STL)

    Returns:
        Dictionary with CAD file metadata
    """
    valid_formats = ["STEP", "IGES", "STL"]
    if format not in valid_formats:
        format = "STEP"

    # Generate a deterministic file ID based on geometry
    geo_str = json.dumps(geometry, sort_keys=True)
    file_hash = hashlib.md5(geo_str.encode()).hexdigest()[:12]

    cad_file = {
        "format": format,
        "url": f"s3://autoplane-cad/{file_hash}.{format.lower()}",
        "size_bytes": random.randint(500000, 2000000),  # Placeholder
    }

    return cad_file


def generate_report(state: Dict[str, Any]) -> bytes:
    """Generate PDF design report.

    Args:
        state: DesignState dictionary

    Returns:
        PDF bytes (placeholder implementation returns empty bytes)
    """
    # In production, this would use Jinja2 templates and a PDF library
    # For now, return placeholder bytes
    report_content = f"AutoPlane Design Report - Job {state.get('job_id', 'unknown')}\n"
    report_content += f"Status: {state.get('status', 'unknown')}\n"
    report_content += f"Iteration: {state.get('iteration', 0)}\n"

    return report_content.encode("utf-8")


def reoptimize_design(state: Dict[str, Any]) -> Dict[str, Any]:
    """Re-optimize design based on constraints.

    This implements an RL policy that adjusts wing span, aspect ratio, etc.
    to satisfy constraints that were violated.

    Args:
        state: Current DesignState dictionary

    Returns:
        Updated geometry JSON
    """
    geometry = state.get("geometry_json", {})
    regulatory = state.get("regulatory")
    performance = state.get("performance", {})

    # Simple re-optimization logic
    wing_span = geometry.get("wing_span", 15.0)
    wing_area = geometry.get("wing_area", 30.0)

    # Adjust based on regulatory violations
    if regulatory and not regulatory.get("stall_speed_ok", True):
        # If stall speed is too high, increase wing area
        wing_area *= 1.1
        wing_span *= 1.05

    if performance and performance.get("range_km", 0) < 1000:
        # If range is insufficient, increase wing span
        wing_span *= 1.15

    # Update geometry
    aspect_ratio = wing_span ** 2 / wing_area
    geometry["wing_span"] = round(wing_span, 2)
    geometry["wing_area"] = round(wing_area, 2)
    geometry["aspect_ratio"] = round(aspect_ratio, 2)
    geometry["mean_aerodynamic_chord"] = round(wing_area / wing_span, 2)

    return geometry


# Tool registry for LangChain
def get_tools() -> list:
    """Get all tools wrapped for LangChain."""
    from langchain_core.tools import tool

    @tool
    def generate_geometry_tool(
        payload: float,
        material: str,
        engine: str,
    ) -> str:
        """Generate initial aircraft geometry.
        
        Args:
            payload: Payload requirement in kg
            material: Selected material name
            engine: Selected engine name
            
        Returns:
            JSON string with geometry parameters
        """
        result = generate_geometry(payload, material, engine)
        return json.dumps(result)

    @tool
    def run_cfd_surrogate_tool(geometry_json: str) -> str:
        """Run surrogate CFD analysis.
        
        Args:
            geometry_json: JSON string of geometry
            
        Returns:
            JSON string with aerodynamic results
        """
        geometry = json.loads(geometry_json)
        result = run_cfd_surrogate(geometry)
        return json.dumps(result)

    @tool
    def run_fea_surrogate_tool(geometry_json: str) -> str:
        """Run surrogate FEA analysis.
        
        Args:
            geometry_json: JSON string of geometry
            
        Returns:
            JSON string with structural results
        """
        geometry = json.loads(geometry_json)
        result = run_fea_surrogate(geometry)
        return json.dumps(result)

    @tool
    def compute_performance_tool(
        aero_json: str,
        structural_json: str,
        engine_props_json: str,
    ) -> str:
        """Compute overall aircraft performance.
        
        Args:
            aero_json: JSON string of aerodynamic results
            structural_json: JSON string of structural results
            engine_props_json: JSON string of engine properties
            
        Returns:
            JSON string with performance results
        """
        aero = json.loads(aero_json)
        structural = json.loads(structural_json)
        engine = json.loads(engine_props_json)
        result = compute_performance(aero, structural, engine)
        return json.dumps(result)

    @tool
    def estimate_cost_tool(
        geometry_json: str,
        material: str,
        engine: str,
    ) -> str:
        """Estimate manufacturing and material costs.
        
        Args:
            geometry_json: JSON string of geometry
            material: Material name
            engine: Engine name
            
        Returns:
            JSON string with cost breakdown
        """
        geometry = json.loads(geometry_json)
        result = estimate_cost(geometry, material, engine)
        return json.dumps(result)

    @tool
    def check_regulations_tool(
        performance_json: str,
        aero_json: str,
    ) -> str:
        """Check regulatory compliance.
        
        Args:
            performance_json: JSON string of performance results
            aero_json: JSON string of aerodynamic results
            
        Returns:
            JSON string with regulatory compliance results
        """
        performance = json.loads(performance_json)
        aero = json.loads(aero_json)
        result = check_regulations(performance, aero)
        return json.dumps(result)

    @tool
    def export_cad_tool(
        geometry_json: str,
        format: str = "STEP",
    ) -> str:
        """Export geometry to CAD format.
        
        Args:
            geometry_json: JSON string of geometry
            format: Export format (STEP, IGES, STL)
            
        Returns:
            JSON string with CAD file metadata
        """
        geometry = json.loads(geometry_json)
        result = export_cad(geometry, format)
        return json.dumps(result)

    @tool
    def generate_report_tool(state_json: str) -> str:
        """Generate PDF design report.
        
        Args:
            state_json: JSON string of DesignState
            
        Returns:
            Base64 encoded PDF bytes (as string)
        """
        import base64
        state = json.loads(state_json)
        result = generate_report(state)
        return base64.b64encode(result).decode("utf-8")

    @tool
    def reoptimize_design_tool(state_json: str) -> str:
        """Re-optimize design based on constraints.
        
        Args:
            state_json: JSON string of DesignState
            
        Returns:
            JSON string with updated geometry
        """
        state = json.loads(state_json)
        result = reoptimize_design(state)
        return json.dumps(result)

    return [
        generate_geometry_tool,
        run_cfd_surrogate_tool,
        run_fea_surrogate_tool,
        compute_performance_tool,
        estimate_cost_tool,
        check_regulations_tool,
        export_cad_tool,
        generate_report_tool,
        reoptimize_design_tool,
    ]