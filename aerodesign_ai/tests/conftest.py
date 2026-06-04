"""Pytest configuration for AeroDesign-AI tests."""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_payload():
    """Sample payload data."""
    return {
        "payload_tons": 2.0,
        "material": "al7075_t6",
        "engine": "lycoming_io720",
        "user_id": "test_user",
    }


@pytest.fixture
def sample_geometry():
    """Sample geometry data."""
    return {
        "wing_span_m": 12.0,
        "aspect_ratio": 10.0,
        "taper_ratio": 0.4,
        "wing_thickness_ratio": 0.12,
        "fuselage_length_m": 10.0,
        "fuselage_diameter_m": 1.3,
        "tail_span_m": 2.5,
        "tail_area_m2": 3.0,
        "engine_pylon_length_m": 1.0,
    }


@pytest.fixture
def sample_material_props():
    """Sample material properties."""
    return {
        "name": "Aluminum 7075-T6",
        "density_kg_m3": 2810,
        "tensile_strength_pa": 5.24e8,
        "cost_per_kg": 12.50,
        "manufacturability_score": 0.9,
        "youngs_modulus_pa": 7.2e10,
    }


@pytest.fixture
def sample_engine_specs():
    """Sample engine specifications."""
    return {
        "name": "Lycoming IO-720",
        "thrust_newtons": 29420,
        "fuel_flow_kg_s": 0.055,
        "weight_kg": 240,
        "cost_usd": 35000,
        "specific_fuel_consumption": 0.22,
    }


@pytest.fixture
def sample_compliance_geometry():
    """Sample compliant geometry for testing."""
    return {
        "stall_speed_kt": 70,
        "takeoff_field_length_m": 1000,
        "landing_field_length_m": 800,
        "max_takeoff_weight_kg": 5000,
        "aspect_ratio": 10,
        "structural_margin": 15,
        "engine_clearance_m": 0.5,
        "tail_clearance_m": 0.3,
        "climb_gradient_percent": 3.5,
        "wing_loading_kg_m2": 300,
        "lift_to_drag_ratio": 12,
    }
