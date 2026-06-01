"""AFW-D Engine Data Models.

All Pydantic models for the aircraft design agentic system.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class MaterialProperties(BaseModel):
    """Material properties from database query."""

    family: str
    density: float  # kg/m³
    modulus: float  # GPa
    fatigue_limit: float  # MPa
    cost_per_kg: float  # USD/kg

    @field_validator("density", "modulus", "fatigue_limit", "cost_per_kg")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Value must be positive")
        return v


class EngineSpecs(BaseModel):
    """Engine specifications from database query."""

    family: str
    thrust: float  # kN
    weight: float  # kg
    fuel_consumption: float  # kg/h
    cost: float  # USD

    @field_validator("thrust", "weight", "fuel_consumption", "cost")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Value must be positive")
        return v


class DesignParams(BaseModel):
    """Parametric design parameters for aircraft."""

    wing_area: float = Field(gt=0, description="Wing area in m²")
    aspect_ratio: float = Field(gt=0, description="Wing aspect ratio")
    sweep: float = Field(ge=0, le=45, description="Wing sweep angle in degrees")
    fuselage_length: float = Field(gt=0, description="Fuselage length in m")
    tail_area: float = Field(gt=0, description="Tail area in m²")
    max_takeoff_weight: float = Field(gt=0, description="Max takeoff weight in kg")
    empty_weight: float = Field(gt=0, description="Empty weight in kg")
    wing_thickness_ratio: float = Field(gt=0, le=0.5, description="Wing thickness ratio")
    taper_ratio: float = Field(gt=0, le=2, description="Wing taper ratio")

    def is_invalid(self) -> bool:
        """Check if design parameters are invalid."""
        return (
            self.wing_area <= 0
            or self.aspect_ratio <= 0
            or self.fuselage_length <= 0
            or self.empty_weight >= self.max_takeoff_weight
        )


class CADFile(BaseModel):
    """Generated CAD file information."""

    file_id: str
    url: str
    format: Literal["STEP", "IGES", "STL"]


class CFDSimulationResult(BaseModel):
    """CFD simulation results."""

    lift: float  # N
    drag: float  # N
    max_speed: float  # m/s
    range: float  # km
    weight: float  # kg


class FEASimulationResult(BaseModel):
    """FEA simulation results."""

    max_stress: float  # MPa
    safety_factor: float
    weight: float  # kg


class SimulationResult(BaseModel):
    """Combined simulation results."""

    cfd: CFDSimulationResult
    fea: FEASimulationResult


class CostEstimate(BaseModel):
    """Preliminary cost estimate."""

    material_cost: float  # USD
    manufacturing_cost: float  # USD
    total_cost: float  # USD

    @field_validator("material_cost", "manufacturing_cost", "total_cost")
    @classmethod
    def validate_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Cost must be non-negative")
        return v


class ComplianceReport(BaseModel):
    """Compliance check report."""

    passed: bool
    issues: list[str] = Field(default_factory=list)


class Feedback(BaseModel):
    """User or system feedback."""

    user_id: str
    comment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DesignState(BaseModel):
    """Complete design state snapshot."""

    design_params: DesignParams
    cad_file: Optional[CADFile] = None
    simulation: Optional[SimulationResult] = None
    cost_estimate: Optional[CostEstimate] = None
    compliance: Optional[ComplianceReport] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DesignInput(BaseModel):
    """User input for design submission."""

    payload_kg: float = Field(gt=0, description="Payload mass in kg")
    material_family: Optional[str] = Field(None, description="Material family")
    engine_family: Optional[str] = Field(None, description="Engine family")
    tags: list[str] = Field(default_factory=list)


class DesignStatus(BaseModel):
    """Design status response."""

    design_id: str
    state: Literal["queued", "running", "completed", "failed"]
    progress: int = Field(ge=0, le=100)
    error: Optional[str] = None


class FeedbackAck(BaseModel):
    """Feedback acknowledgment response."""

    success: bool
    message: str


# Validation utilities
def validate_material_props(props: MaterialProperties) -> None:
    """Validate material properties."""
    if props.density <= 0:
        raise ValueError("Material density must be positive")


def validate_engine_specs(specs: EngineSpecs) -> None:
    """Validate engine specifications."""
    if specs.thrust <= 0:
        raise ValueError("Engine thrust must be positive")


class DesignError(Exception):
    """Design validation error."""

    pass