"""Data models for the AutoPlane Design Agent."""

from typing import Optional, List, Any
from pydantic import BaseModel, Field


class MaterialProps(BaseModel):
    """Material properties for aircraft construction."""
    name: str
    density: float = Field(description="Density in kg/m³")
    tensile_strength: float = Field(description="Tensile strength in MPa")
    cost_per_kg: float = Field(description="Cost per kilogram")


class EngineProps(BaseModel):
    """Engine specifications."""
    name: str
    thrust: float = Field(description="Maximum thrust in kN")
    fuel_flow: float = Field(description="Fuel flow rate in kg/h")
    weight: float = Field(description="Engine weight in kg")
    cost: float = Field(description="Engine cost in USD")


class AeroResult(BaseModel):
    """Aerodynamic simulation results from surrogate CFD."""
    lift_coefficient: float = Field(description="Lift coefficient (Cl)")
    drag_coefficient: float = Field(description="Drag coefficient (Cd)")
    stall_speed_kts: float = Field(description="Stall speed in knots")
    max_lift: float = Field(description="Maximum lift coefficient")


class StructResult(BaseModel):
    """Structural analysis results from surrogate FEA."""
    max_bending_moment: float = Field(description="Maximum bending moment in kNm")
    max_stress: float = Field(description="Maximum stress in MPa")
    weight_kg: float = Field(description="Total structural weight in kg")
    fatigue_life_years: float = Field(description="Estimated fatigue life in years")


class PerfResult(BaseModel):
    """Performance estimation results."""
    range_km: float = Field(description="Operational range in kilometers")
    cruise_speed_kts: float = Field(description="Cruise speed in knots")
    fuel_burn_kg: float = Field(description="Fuel burn rate in kg/h")
    endurance_hr: float = Field(description="Endurance in hours")


class CostResult(BaseModel):
    """Cost estimation results."""
    material_cost: float = Field(description="Material cost in USD")
    manufacturing_cost: float = Field(description="Manufacturing cost in USD")
    assembly_cost: float = Field(description="Assembly cost in USD")
    total_cost: float = Field(description="Total cost in USD")


class RegResult(BaseModel):
    """Regulatory compliance check results."""
    stall_speed_ok: bool = Field(description="Stall speed within limits")
    noise_limit_ok: bool = Field(description="Noise levels within limits")
    max_takeoff_weight_ok: bool = Field(description="Takeoff weight within limits")
    violations: List[str] = Field(default_factory=list, description="List of regulatory violations")


class CADFile(BaseModel):
    """CAD file metadata."""
    format: str = Field(description="File format: STEP, IGES, or STL")
    url: str = Field(description="URL to download the CAD file")
    size_bytes: int = Field(description="File size in bytes")


class GeometryJSON(BaseModel):
    """3D geometry representation of the aircraft design."""
    wing_span: float = Field(description="Wing span in meters")
    wing_area: float = Field(description="Wing area in m²")
    fuselage_length: float = Field(description="Fuselage length in meters")
    tail_area: float = Field(description="Tail area in m²")
    aspect_ratio: float = Field(description="Wing aspect ratio")
    mean_aerodynamic_chord: float = Field(description="Mean aerodynamic chord in meters")
    vertices: List[List[float]] = Field(default_factory=list, description="Vertex coordinates")
    faces: List[List[int]] = Field(default_factory=list, description="Face indices")
    metadata: dict = Field(default_factory=dict, description="Additional geometry metadata")


class DesignState(BaseModel):
    """Main state object for the design agent."""
    # User input
    payload_kg: float = Field(description="Required payload capacity in kg")
    payload_cg: Optional[float] = Field(default=None, description="Payload center of gravity offset")
    material: Optional[str] = Field(default=None, description="Selected material")
    engine: Optional[str] = Field(default=None, description="Selected engine")

    # Design variables
    wing_span: Optional[float] = Field(default=None, description="Wing span in meters")
    wing_area: Optional[float] = Field(default=None, description="Wing area in m²")
    fuselage_length: Optional[float] = Field(default=None, description="Fuselage length in meters")
    tail_area: Optional[float] = Field(default=None, description="Tail area in m²")
    geometry_json: Optional[GeometryJSON] = Field(default=None, description="Full geometry specification")

    # Simulation results
    aerodynamic: Optional[AeroResult] = Field(default=None, description="Aerodynamic results")
    structural: Optional[StructResult] = Field(default=None, description="Structural results")
    performance: Optional[PerfResult] = Field(default=None, description="Performance results")
    cost: Optional[CostResult] = Field(default=None, description="Cost estimation results")
    regulatory: Optional[RegResult] = Field(default=None, description="Regulatory check results")

    # Material and engine properties (resolved)
    material_props: Optional[MaterialProps] = Field(default=None, description="Resolved material properties")
    engine_props: Optional[EngineProps] = Field(default=None, description="Resolved engine properties")

    # Artefacts
    cad_file: Optional[CADFile] = Field(default=None, description="Generated CAD file")
    report_pdf: Optional[bytes] = Field(default=None, description="PDF report bytes")

    # Control flags
    needs_reopt: bool = Field(default=False, description="Whether re-optimization is needed")
    last_error: Optional[str] = Field(default=None, description="Last error message if any")
    iteration: int = Field(default=0, description="Current iteration number")
    max_iterations: int = Field(default=5, description="Maximum iterations allowed")

    # Job metadata
    job_id: Optional[str] = Field(default=None, description="Unique job identifier")
    status: str = Field(default="pending", description="Job status: pending, running, completed, failed")

    class Config:
        arbitrary_types_allowed = True


class DesignJob(BaseModel):
    """Design job request model."""
    payload_kg: float = Field(description="Payload requirement in kg")
    material: Optional[str] = Field(default=None, description="Preferred material")
    engine: Optional[str] = Field(default=None, description="Preferred engine")
    payload_cg: Optional[float] = Field(default=None, description="Payload CG offset")


class DesignJobResponse(BaseModel):
    """Response when starting a design job."""
    job_id: str = Field(description="Unique job identifier")


class DesignStatusResponse(BaseModel):
    """Response for design status query."""
    job_id: str
    status: str
    progress: int = Field(description="Progress percentage (0-100)")
    state: Optional[DesignState] = None
    error: Optional[str] = None