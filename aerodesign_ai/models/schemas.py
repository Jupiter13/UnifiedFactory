"""Pydantic models for AeroDesign-AI data structures."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class MaterialProps(BaseModel):
    """Material properties for aerospace components."""

    name: str
    density_kg_m3: float = Field(gt=0, description="Density in kg/m³")
    tensile_strength_pa: float = Field(gt=0, description="Tensile strength in Pascals")
    cost_per_kg: float = Field(ge=0, description="Cost per kilogram")
    manufacturability_score: float = Field(ge=0, le=1, description="Manufacturability score 0-1")
    youngs_modulus_pa: Optional[float] = Field(default=None, description="Young's modulus")
    yield_strength_pa: Optional[float] = Field(default=None, description="Yield strength")

    @field_validator("manufacturability_score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError("Manufacturability score must be between 0 and 1")
        return v


class EngineSpecs(BaseModel):
    """Engine performance specifications."""

    name: str
    thrust_newtons: float = Field(gt=0, description="Maximum thrust in Newtons")
    fuel_flow_kg_s: float = Field(ge=0, description="Fuel flow rate in kg/s")
    weight_kg: float = Field(gt=0, description="Engine weight in kg")
    cost_usd: float = Field(ge=0, description="Engine cost in USD")
    specific_fuel_consumption: Optional[float] = Field(default=None, description="SFC")
    max_altitude_m: Optional[float] = Field(default=None, description="Max operating altitude")


class ComplianceReport(BaseModel):
    """Rule engine compliance evaluation report."""

    passed: bool
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checked_rules: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_fully_compliant(self) -> bool:
        """Check if all rules passed without warnings."""
        return self.passed and len(self.warnings) == 0


class BOMItem(BaseModel):
    """Bill of Materials item."""

    part_name: str
    quantity: int = Field(gt=0, description="Number of parts required")
    unit_cost_usd: float = Field(ge=0, description="Cost per unit")
    material: Optional[str] = Field(default=None, description="Material type")
    dimensions: Optional[Dict[str, float]] = Field(default=None, description="Part dimensions")
    weight_kg: Optional[float] = Field(default=None, description="Part weight")
    description: Optional[str] = Field(default=None, description="Part description")

    @property
    def total_cost_usd(self) -> float:
        """Calculate total cost for this BOM item."""
        return self.quantity * self.unit_cost_usd


class GeometryParams(BaseModel):
    """Aircraft geometry parameters."""

    wing_span_m: float = Field(gt=0, description="Wing span in meters")
    wing_area_m2: float = Field(gt=0, description="Wing reference area in m²")
    aspect_ratio: float = Field(gt=0, description="Wing aspect ratio")
    wing_taper_ratio: float = Field(gt=0, le=1, description="Wing taper ratio")
    wing_thickness_ratio: float = Field(gt=0, le=1, description="Airfoil thickness ratio")
    fuselage_length_m: float = Field(gt=0, description="Fuselage length in meters")
    fuselage_diameter_m: float = Field(gt=0, description="Fuselage diameter in meters")
    tail_span_m: float = Field(gt=0, description="Horizontal tail span in meters")
    tail_area_m2: float = Field(gt=0, description="Horizontal tail area in m²")
    engine_pylon_length_m: float = Field(gt=0, description="Engine pylon length in meters")
    max_takeoff_weight_kg: float = Field(gt=0, description="Maximum takeoff weight in kg")
    empty_weight_kg: float = Field(gt=0, description="Empty weight in kg")
    wing_mean_aerodynamic_chord_m: float = Field(gt=0, description="Mean aerodynamic chord in meters")


class OptimizationMetrics(BaseModel):
    """Design optimization metrics."""

    cruise_speed_kt: float = Field(ge=0, description="Cruise speed in knots")
    stall_speed_kt: float = Field(ge=0, description="Stall speed in knots")
    range_nm: float = Field(ge=0, description="Range in nautical miles")
    climb_rate_m_s: float = Field(ge=0, description="Rate of climb in m/s")
    fuel_burn_kg_h: float = Field(ge=0, description="Fuel burn rate in kg/hour")
    lift_to_drag_ratio: float = Field(ge=0, description="L/D ratio")
    wing_loading_kg_m2: float = Field(ge=0, description="Wing loading")
    power_loading_w_kg: float = Field(ge=0, description="Power loading")
    structural_margin: float = Field(description="Safety margin percentage")
    estimated_cost_usd: float = Field(ge=0, description="Estimated total cost")


class DesignState(BaseModel):
    """State model for LangGraph pipeline."""

    # Input
    payload_tons: float = Field(gt=0, description="Payload capacity in tonnes")
    material: str = Field(description="Material type name")
    engine: str = Field(description="Engine type name")
    optional_constraints: Optional[Dict[str, Any]] = Field(default=None)

    # Intermediate
    geometry: Optional[Dict[str, Any]] = None
    optimization_metrics: Optional[Dict[str, float]] = None
    compliance_report: Optional[ComplianceReport] = None
    cad_file_path: Optional[str] = None
    bom: Optional[List[BOMItem]] = None
    version_id: Optional[str] = None
    errors: List[str] = Field(default_factory=list)

    # Metadata
    user_id: str = Field(default="anonymous")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Computed properties
    total_weight_kg: Optional[float] = Field(default=None, description="Total aircraft weight")

    def add_error(self, error: str) -> None:
        """Add an error message to the state."""
        self.errors.append(error)

    def clear_errors(self) -> None:
        """Clear all error messages."""
        self.errors = []


class DesignOutput(BaseModel):
    """Final design output returned to user."""

    design_id: str
    payload_tons: float
    material: str
    engine: str
    geometry: Dict[str, Any]
    optimization_metrics: Dict[str, float]
    compliance_report: ComplianceReport
    cad_file_url: str
    bom: List[BOMItem]
    timestamp: datetime
    total_cost_usd: float


class DesignInput(BaseModel):
    """User input for design request."""

    payload_tons: float = Field(gt=0, le=100, description="Payload capacity in tonnes")
    material: str = Field(min_length=1, description="Material type name")
    engine: str = Field(min_length=1, description="Engine type name")
    optional_constraints: Optional[Dict[str, Any]] = Field(default=None)
    user_id: str = Field(default="anonymous")


class DesignStatus(BaseModel):
    """Design job status response."""

    design_id: str
    status: str  # queued, running, completed, failed
    progress: float = Field(ge=0, le=100, description="Progress percentage")
    message: Optional[str] = None
