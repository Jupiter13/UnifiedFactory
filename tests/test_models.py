"""Unit tests for data models."""

import pytest
from datetime import datetime

from afw_d.models import (
    MaterialProperties,
    EngineSpecs,
    DesignParams,
    CADFile,
    CFDSimulationResult,
    FEASimulationResult,
    SimulationResult,
    CostEstimate,
    ComplianceReport,
    Feedback,
    DesignState,
    DesignInput,
    DesignStatus,
    DesignError,
    validate_material_props,
    validate_engine_specs,
)


class TestMaterialProperties:
    """Tests for MaterialProperties model."""

    def test_create_material_properties(self):
        """Test creating material properties."""
        props = MaterialProperties(
            family="Al-Mg-Si",
            density=2700.0,
            modulus=70.0,
            fatigue_limit=150.0,
            cost_per_kg=8.5,
        )
        assert props.family == "Al-Mg-Si"
        assert props.density == 2700.0
        assert props.modulus == 70.0

    def test_validate_positive_density(self):
        """Test that negative density raises error."""
        with pytest.raises(ValueError):
            MaterialProperties(
                family="Test",
                density=-100.0,
                modulus=70.0,
                fatigue_limit=150.0,
                cost_per_kg=8.5,
            )

    def test_validate_positive_modulus(self):
        """Test that negative modulus raises error."""
        with pytest.raises(ValueError):
            MaterialProperties(
                family="Test",
                density=2700.0,
                modulus=-1.0,
                fatigue_limit=150.0,
                cost_per_kg=8.5,
            )


class TestEngineSpecs:
    """Tests for EngineSpecs model."""

    def test_create_engine_specs(self):
        """Test creating engine specs."""
        specs = EngineSpecs(
            family="Turboprop-A",
            thrust=850.0,
            weight=180.0,
            fuel_consumption=120.0,
            cost=85000.0,
        )
        assert specs.family == "Turboprop-A"
        assert specs.thrust == 850.0

    def test_validate_positive_thrust(self):
        """Test that zero thrust raises error."""
        with pytest.raises(ValueError):
            EngineSpecs(
                family="Test",
                thrust=0.0,
                weight=180.0,
                fuel_consumption=120.0,
                cost=85000.0,
            )


class TestDesignParams:
    """Tests for DesignParams model."""

    def test_create_design_params(self):
        """Test creating design parameters."""
        params = DesignParams(
            wing_area=20.0,
            aspect_ratio=8.0,
            sweep=15.0,
            fuselage_length=10.0,
            tail_area=3.0,
            max_takeoff_weight=5000.0,
            empty_weight=3000.0,
            wing_thickness_ratio=0.15,
            taper_ratio=0.6,
        )
        assert params.wing_area == 20.0
        assert params.aspect_ratio == 8.0

    def test_is_invalid_with_valid_params(self):
        """Test is_invalid returns False for valid params."""
        params = DesignParams(
            wing_area=20.0,
            aspect_ratio=8.0,
            sweep=15.0,
            fuselage_length=10.0,
            tail_area=3.0,
            max_takeoff_weight=5000.0,
            empty_weight=3000.0,
            wing_thickness_ratio=0.15,
            taper_ratio=0.6,
        )
        assert params.is_invalid() is False

    def test_is_invalid_with_zero_wing_area(self):
        """Test is_invalid returns True for zero wing area.

        Note: Pydantic validation prevents creating params with wing_area <= 0,
        so this tests that validation raises an error.
        """
        with pytest.raises(Exception):  # ValidationError
            DesignParams(
                wing_area=0.0,
                aspect_ratio=8.0,
                sweep=15.0,
                fuselage_length=10.0,
                tail_area=3.0,
                max_takeoff_weight=5000.0,
                empty_weight=3000.0,
                wing_thickness_ratio=0.15,
                taper_ratio=0.6,
            )

    def test_is_invalid_with_empty_greater_than_max(self):
        """Test is_invalid when empty weight exceeds max takeoff weight."""
        params = DesignParams(
            wing_area=20.0,
            aspect_ratio=8.0,
            sweep=15.0,
            fuselage_length=10.0,
            tail_area=3.0,
            max_takeoff_weight=5000.0,
            empty_weight=6000.0,
            wing_thickness_ratio=0.15,
            taper_ratio=0.6,
        )
        assert params.is_invalid() is True


class TestDesignInput:
    """Tests for DesignInput model."""

    def test_create_design_input_required_only(self):
        """Test creating design input with only required fields."""
        input_data = DesignInput(payload_kg=1000.0)
        assert input_data.payload_kg == 1000.0
        assert input_data.material_family is None
        assert input_data.tags == []

    def test_create_design_input_with_optional(self):
        """Test creating design input with optional fields."""
        input_data = DesignInput(
            payload_kg=1000.0,
            material_family="Al-Mg-Si",
            engine_family="Turboprop-A",
            tags=["test", "demo"],
        )
        assert input_data.material_family == "Al-Mg-Si"
        assert len(input_data.tags) == 2

    def test_validate_payload_positive(self):
        """Test that zero payload raises error."""
        with pytest.raises(ValueError):
            DesignInput(payload_kg=0.0)


class TestComplianceReport:
    """Tests for ComplianceReport model."""

    def test_create_passed_report(self):
        """Test creating a passing compliance report."""
        report = ComplianceReport(passed=True, issues=[])
        assert report.passed is True
        assert report.issues == []

    def test_create_failed_report(self):
        """Test creating a failing compliance report."""
        report = ComplianceReport(
            passed=False,
            issues=["Safety factor too low", "Range insufficient"],
        )
        assert report.passed is False
        assert len(report.issues) == 2


class TestFeedback:
    """Tests for Feedback model."""

    def test_create_feedback(self):
        """Test creating feedback."""
        feedback = Feedback(
            user_id="user123",
            comment="This design needs improvement",
        )
        assert feedback.user_id == "user123"
        assert feedback.timestamp is not None


class TestValidationUtils:
    """Tests for validation utilities."""

    def test_validate_material_props_valid(self):
        """Test validate_material_props with valid input."""
        props = MaterialProperties(
            family="Test",
            density=2700.0,
            modulus=70.0,
            fatigue_limit=150.0,
            cost_per_kg=8.5,
        )
        validate_material_props(props)  # Should not raise

    def test_validate_material_props_invalid(self):
        """Test validate_material_props with invalid input.

        Note: Pydantic validation prevents creating properties with negative values.
        """
        with pytest.raises(Exception):  # ValidationError
            MaterialProperties(
                family="Test",
                density=-1.0,
                modulus=70.0,
                fatigue_limit=150.0,
                cost_per_kg=8.5,
            )

    def test_validate_engine_specs_valid(self):
        """Test validate_engine_specs with valid input."""
        specs = EngineSpecs(
            family="Test",
            thrust=850.0,
            weight=180.0,
            fuel_consumption=120.0,
            cost=85000.0,
        )
        validate_engine_specs(specs)  # Should not raise

    def test_validate_engine_specs_invalid(self):
        """Test validate_engine_specs with invalid input.

        Note: Pydantic validation prevents creating specs with negative thrust.
        """
        with pytest.raises(Exception):  # ValidationError
            EngineSpecs(
                family="Test",
                thrust=-1.0,
                weight=180.0,
                fuel_consumption=120.0,
                cost=85000.0,
            )