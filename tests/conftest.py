"""Shared pytest fixtures for AutoPlane tests."""

import pytest
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_geometry():
    """Provide sample geometry data."""
    from autoplane.models.state import GeometryJSON
    return GeometryJSON(
        wing_span=15.0,
        wing_area=30.0,
        fuselage_length=12.0,
        tail_area=5.0,
        aspect_ratio=7.5,
        mean_aerodynamic_chord=2.0,
    )


@pytest.fixture
def sample_aero_result():
    """Provide sample aerodynamic results."""
    from autoplane.models.state import AeroResult
    return AeroResult(
        lift_coefficient=0.5,
        drag_coefficient=0.03,
        stall_speed_kts=55.0,
        max_lift=1.5,
    )


@pytest.fixture
def sample_struct_result():
    """Provide sample structural results."""
    from autoplane.models.state import StructResult
    return StructResult(
        max_bending_moment=100.0,
        max_stress=250.0,
        weight_kg=1500.0,
        fatigue_life_years=20.0,
    )


@pytest.fixture
def sample_perf_result():
    """Provide sample performance results."""
    from autoplane.models.state import PerfResult
    return PerfResult(
        range_km=3000.0,
        cruise_speed_kts=250.0,
        fuel_burn_kg=800.0,
        endurance_hr=8.0,
    )


@pytest.fixture
def sample_engine_props():
    """Provide sample engine properties."""
    from autoplane.models.state import EngineProps
    return EngineProps(
        name="Turbofan-1",
        thrust=50.0,
        fuel_flow=500.0,
        weight=800.0,
        cost=50000.0,
    )


@pytest.fixture
def sample_material_props():
    """Provide sample material properties."""
    from autoplane.models.state import MaterialProps
    return MaterialProps(
        name="Al-6061",
        density=2700.0,
        tensile_strength=310.0,
        cost_per_kg=5.0,
    )


@pytest.fixture
def base_design_state():
    """Provide a base DesignState for testing."""
    from autoplane.models.state import DesignState
    return DesignState(
        payload_kg=1000,
        material="Al-6061",
        engine="Turbofan-1",
    )


@pytest.fixture(autouse=True)
def reset_globals():
    """Reset global singletons before each test."""
    import autoplane.agent as agent_module
    import autoplane.memory as memory_module
    
    agent_module._agent_instance = None
    memory_module._memory_instance = None
    
    yield
    
    agent_module._agent_instance = None
    memory_module._memory_instance = None