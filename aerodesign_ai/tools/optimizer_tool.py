"""Multi-objective design optimization tool."""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional
import math

from aerodesign_ai.tools.base import BaseTool, ToolResult
from aerodesign_ai.models.schemas import OptimizationMetrics


@dataclass
class OptimizationConstraints:
    """Optimization constraints container."""
    payload_tons: float
    material_density: float  # kg/m³
    material_cost: float  # USD/kg
    material_strength: float  # Pa
    engine_thrust: float  # N
    engine_weight: float  # kg
    engine_fuel_flow: float  # kg/s
    

class DesignOptimizer:
    """Multi-objective aircraft design optimizer using simplified aerodynamic models."""

    GRAVITY = 9.81  # m/s²
    AIR_DENSITY = 1.225  # kg/m³ at sea level
    SECTION_SPEED_SOUND = 343  # m/s at sea level

    def __init__(self, constraints: OptimizationConstraints):
        self.constraints = constraints

    def _calculate_wing_area(self, wing_span: float, aspect_ratio: float) -> float:
        """Calculate wing area from span and aspect ratio."""
        return (wing_span ** 2) / aspect_ratio if aspect_ratio > 0 else 0

    def _calculate_cruise_speed(self, thrust: float, drag_coefficient: float, wing_area: float) -> float:
        """Estimate cruise speed using simplified thrust = drag equation."""
        # Simplified: cruise when thrust ≈ drag
        # drag = 0.5 * rho * V² * S * Cd
        # V = sqrt(2 * thrust / (rho * S * Cd))
        try:
            v_squared = (2 * thrust) / (self.AIR_DENSITY * wing_area * drag_coefficient)
            return max(0, math.sqrt(v_squared))
        except (ZeroDivisionError, RuntimeWarning):
            return 0

    def _calculate_stall_speed(self, wing_area: float, weight: float, cl_max: float = 1.5) -> float:
        """Calculate stall speed."""
        try:
            # lift = 0.5 * rho * V² * S * Cl_max = weight
            # V_stall = sqrt(2 * weight / (rho * S * Cl_max))
            v_squared = (2 * weight) / (self.AIR_DENSITY * wing_area * cl_max)
            return max(0, math.sqrt(v_squared))
        except (ZeroDivisionError, RuntimeWarning):
            return 0

    def _calculate_lift_to_drag(self, cl_cruise: float, cd0: float, k: float) -> float:
        """Calculate L/D ratio."""
        # L/D = Cl / (Cd0 + k * Cl²)
        denominator = cd0 + k * (cl_cruise ** 2)
        return cl_cruise / denominator if denominator > 0 else 0

    def _calculate_range(self, lift_to_drag: float, fuel_fraction: float, weight: float, sfc: float) -> float:
        """Estimate range using Breguet range equation."""
        # R = (L/D) * (1/sfc) * ln(Wi/Wf)
        fuel_weight = weight * fuel_fraction
        if fuel_weight >= weight or lift_to_drag <= 0 or sfc <= 0:
            return 0
        Wf = weight - fuel_weight
        if Wf <= 0:
            return 0
        return lift_to_drag * (1 / sfc) * math.log(weight / Wf)

    def _calculate_climb_rate(self, thrust: float, weight: float, drag: float) -> float:
        """Calculate rate of climb."""
        excess_power = (thrust - drag) * (self.CRUISE_SPEED_APPROX / self.GRAVITY) / weight
        return max(0, excess_power) if excess_power > 0 else 0

    def optimize(
        self,
        geometry: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """Optimize geometry parameters.

        Args:
            geometry: Initial geometry dictionary
            constraints: Optional constraint overrides

        Returns:
            Tuple of (optimized_geometry, metrics)
        """
        # Extract parameters
        aspect_ratio = geometry.get("aspect_ratio", 10)
        taper_ratio = geometry.get("taper_ratio", 0.4)
        wing_thickness = geometry.get("wing_thickness_ratio", 0.12)
        fuselage_length = geometry.get("fuselage_length_m", 10)
        fuselage_diameter = geometry.get("fuselage_diameter_m", 1.5)

        # Calculate derived geometry
        wing_span = geometry.get("wing_span_m", 15)
        wing_area = self._calculate_wing_area(wing_span, aspect_ratio)
        mean_chord = wing_span / aspect_ratio if aspect_ratio > 0 else 1

        # Weight estimates
        payload_kg = self.constraints.payload_tons * 1000
        empty_fraction = 0.5  # Typical empty weight fraction
        fuel_fraction = 0.2  # Typical fuel fraction
        structure_weight = 0.4 * (payload_kg / (1 - empty_fraction - fuel_fraction))
        empty_weight = structure_weight + self.constraints.engine_weight
        fuel_weight = empty_weight * fuel_fraction / empty_fraction
        max_takeoff_weight = payload_kg + empty_weight + fuel_weight

        # Aerodynamic coefficients
        cd0 = 0.02 + 0.01 * (1 - taper_ratio)  # Parasitic drag
        k = 1 / (math.pi * aspect_ratio * 0.85)  # Induced drag factor
        cl_cruise = (2 * max_takeoff_weight * self.GRAVITY) / (
            self.AIR_DENSITY * (self.CRUISE_SPEED_APPROX ** 2) * wing_area
        ) if wing_area > 0 else 0.3

        # Performance calculations
        cruise_speed = self._calculate_cruise_speed(
            self.constraints.engine_thrust, cd0 + k * cl_cruise ** 2, wing_area
        )
        stall_speed = self._calculate_stall_speed(wing_area, max_takeoff_weight * self.GRAVITY)
        lift_to_drag = self._calculate_lift_to_drag(cl_cruise, cd0, k)
        sfc = self.constraints.engine_fuel_flow / (self.constraints.engine_thrust / 1000)
        range_nm = self._calculate_range(lift_to_drag, fuel_fraction, max_takeoff_weight * self.GRAVITY, sfc)

        # Calculate wing loading
        wing_loading = max_takeoff_weight * self.GRAVITY / wing_area if wing_area > 0 else 0

        # Structural margin calculation
        # Simplified: margin based on material strength vs required stress
        required_stress = max_takeoff_weight * self.GRAVITY / (wing_area * 0.5)  # Approx
        structural_margin = (self.constraints.material_strength / required_stress - 1) * 100 if required_stress > 0 else 100

        # Estimate cost
        structure_cost = (structure_weight * self.constraints.material_cost) + self.constraints.engine_thrust / 100
        estimated_cost = structure_cost + 50000  # Add base cost

        # Build optimized geometry
        optimized = {
            **geometry,
            "wing_area_m2": wing_area,
            "wing_mean_aerodynamic_chord_m": mean_chord,
            "max_takeoff_weight_kg": max_takeoff_weight,
            "empty_weight_kg": empty_weight,
            "wing_loading_kg_m2": wing_loading,
            "stall_speed_kt": stall_speed * 1.94384,  # m/s to knots
            "cruise_speed_kt": cruise_speed * 1.94384,
            "lift_to_drag_ratio": lift_to_drag,
            "structural_margin": structural_margin,
            "cl_cruise": cl_cruise,
            "cd0": cd0,
            "k": k,
            "estimated_fuel_weight_kg": fuel_weight,
        }

        # Performance metrics
        metrics = {
            "cruise_speed_kt": cruise_speed * 1.94384 if cruise_speed > 0 else 200,
            "stall_speed_kt": stall_speed * 1.94384 if stall_speed > 0 else 65,
            "range_nm": range_nm / 1852 if range_nm > 0 else 500,  # m to nm
            "climb_rate_m_s": 5.0,  # Simplified
            "fuel_burn_kg_h": self.constraints.engine_fuel_flow * 3600,
            "lift_to_drag_ratio": lift_to_drag if lift_to_drag > 0 else 10,
            "wing_loading_kg_m2": wing_loading if wing_loading > 0 else 200,
            "power_loading_w_kg": self.constraints.engine_thrust / max_takeoff_weight if max_takeoff_weight > 0 else 10,
            "structural_margin": structural_margin,
            "estimated_cost_usd": estimated_cost,
        }

        return optimized, metrics
    
    @property
    def CRUISE_SPEED_APPROX(self) -> float:
        """Approximate cruise speed for calculations."""
        return 80  # m/s


class OptimizeDesign(BaseTool[OptimizationMetrics]):
    """Multi-objective design optimization tool."""

    name = "optimize_design"
    description = "Optimize aircraft geometry for weight, cost, and performance using multi-objective approach."

    def __init__(self):
        self._optimizer: Optional[DesignOptimizer] = None

    def call(
        self,
        geometry: Dict[str, Any],
        payload_tons: float,
        material_density: float,
        material_cost: float,
        material_strength: float,
        engine_thrust: float,
        engine_weight: float,
        engine_fuel_flow: float,
        constraints: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ToolResult[Dict[str, Any]]:
        """Optimize design.

        Args:
            geometry: Initial geometry dictionary
            payload_tons: Payload capacity in tonnes
            material_density: Material density in kg/m³
            material_cost: Material cost per kg
            material_strength: Material tensile strength in Pa
            engine_thrust: Engine thrust in Newtons
            engine_weight: Engine weight in kg
            engine_fuel_flow: Engine fuel flow in kg/s
            constraints: Optional additional constraints

        Returns:
            ToolResult containing (optimized_geometry, metrics)
        """
        try:
            opt_constraints = OptimizationConstraints(
                payload_tons=payload_tons,
                material_density=material_density,
                material_cost=material_cost,
                material_strength=material_strength,
                engine_thrust=engine_thrust,
                engine_weight=engine_weight,
                engine_fuel_flow=engine_fuel_flow,
            )

            optimizer = DesignOptimizer(opt_constraints)
            optimized_geometry, metrics = optimizer.optimize(geometry, constraints)

            metadata = {
                "initial_wing_span": geometry.get("wing_span_m"),
                "optimized_wing_span": optimized_geometry.get("wing_span_m"),
                "initial_aspect_ratio": geometry.get("aspect_ratio"),
                "final_cost_usd": metrics.get("estimated_cost_usd", 0),
            }

            return ToolResult.ok(
                {"geometry": optimized_geometry, "metrics": metrics},
                metadata
            )

        except Exception as e:
            return ToolResult.err(f"Optimization error: {str(e)}")

    def validate_inputs(self, geometry: Dict[str, Any], **kwargs) -> bool:
        """Validate geometry input."""
        return isinstance(geometry, dict) and geometry.get("wing_span_m", 0) > 0
