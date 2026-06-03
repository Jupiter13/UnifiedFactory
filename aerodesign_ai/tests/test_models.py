"""Unit tests for AeroDesign-AI models and tools."""

import pytest
from datetime import datetime

from aerodesign_ai.models.schemas import (
    MaterialProps,
    EngineSpecs,
    ComplianceReport,
    BOMItem,
    DesignState,
    DesignInput,
    GeometryParams,
)


class TestMaterialProps:
    """Tests for MaterialProps model."""

    def test_valid_material_props(self):
        """Test creating valid material properties."""
        props = MaterialProps(
            name="Aluminum 7075-T6",
            density_kg_m3=2810,
            tensile_strength_pa=5.24e8,
            cost_per_kg=12.50,
            manufacturability_score=0.9,
        )
        assert props.name == "Aluminum 7075-T6"
        assert props.density_kg_m3 == 2810
        assert props.manufacturability_score == 0.9

    def test_manufacturability_bounds(self):
        """Test manufacturability score must be 0-1."""
        with pytest.raises(ValueError):
            MaterialProps(
                name="Test Material",
                density_kg_m3=2700,
                tensile_strength_pa=5e8,
                cost_per_kg=10,
                manufacturability_score=1.5,  # Invalid
            )

    def test_negative_manufacturability(self):
        """Test negative manufacturability score is rejected."""
        with pytest.raises(ValueError):
            MaterialProps(
                name="Test Material",
                density_kg_m3=2700,
                tensile_strength_pa=5e8,
                cost_per_kg=10,
                manufacturability_score=-0.1,  # Invalid
            )


class TestEngineSpecs:
    """Tests for EngineSpecs model."""

    def test_valid_engine_specs(self):
        """Test creating valid engine specifications."""
        specs = EngineSpecs(
            name="Lycoming IO-720",
            thrust_newtons=29420,
            fuel_flow_kg_s=0.055,
            weight_kg=240,
            cost_usd=35000,
        )
        assert specs.name == "Lycoming IO-720"
        assert specs.thrust_newtons == 29420
        assert specs.cost_usd == 35000

    def test_zero_thrust_rejected(self):
        """Test zero thrust is rejected."""
        with pytest.raises(ValueError):
            EngineSpecs(
                name="Test Engine",
                thrust_newtons=0,  # Invalid
                fuel_flow_kg_s=0.05,
                weight_kg=200,
                cost_usd=30000,
            )


class TestComplianceReport:
    """Tests for ComplianceReport model."""

    def test_passed_compliance(self):
        """Test passing compliance report."""
        report = ComplianceReport(
            passed=True,
            violations=[],
            warnings=[],
        )
        assert report.passed is True
        assert len(report.violations) == 0
        assert report.is_fully_compliant is True

    def test_failed_compliance(self):
        """Test failing compliance report."""
        report = ComplianceReport(
            passed=False,
            violations=["Stall speed too low"],
            warnings=["Wing loading high"],
        )
        assert report.passed is False
        assert "Stall speed too low" in report.violations
        assert report.is_fully_compliant is False

    def test_compliance_with_warnings(self):
        """Test compliance passed but with warnings."""
        report = ComplianceReport(
            passed=True,
            violations=[],
            warnings=["High wing loading"],
        )
        assert report.is_fully_compliant is False


class TestBOMItem:
    """Tests for BOMItem model."""

    def test_bom_item_calculation(self):
        """Test total cost calculation."""
        item = BOMItem(
            part_name="Wing Assembly",
            quantity=2,
            unit_cost_usd=500,
        )
        assert item.total_cost_usd == 1000

    def test_bom_item_zero_quantity(self):
        """Test zero quantity is rejected."""
        with pytest.raises(ValueError):
            BOMItem(
                part_name="Test Part",
                quantity=0,  # Invalid
                unit_cost_usd=100,
            )


class TestDesignState:
    """Tests for DesignState model."""

    def test_create_design_state(self):
        """Test creating design state."""
        state = DesignState(
            payload_tons=2.0,
            material="al7075_t6",
            engine="lycoming_io720",
            user_id="test_user",
        )
        assert state.payload_tons == 2.0
        assert state.errors == []

    def test_add_error(self):
        """Test adding errors to state."""
        state = DesignState(
            payload_tons=2.0,
            material="al7075_t6",
            engine="lycoming_io720",
        )
        state.add_error("Test error")
        assert len(state.errors) == 1
        assert state.errors[0] == "Test error"

    def test_clear_errors(self):
        """Test clearing errors."""
        state = DesignState(
            payload_tons=2.0,
            material="al7075_t6",
            engine="lycoming_io720",
        )
        state.add_error("Error 1")
        state.add_error("Error 2")
        assert len(state.errors) == 2
        
        state.clear_errors()
        assert len(state.errors) == 0


class TestDesignInput:
    """Tests for DesignInput model."""

    def test_valid_design_input(self):
        """Test valid design input."""
        inp = DesignInput(
            payload_tons=5.0,
            material="al7075_t6",
            engine="lycoming_io720",
        )
        assert inp.payload_tons == 5.0
        assert inp.user_id == "anonymous"  # Default

    def test_max_payload(self):
        """Test payload at maximum value."""
        inp = DesignInput(
            payload_tons=100.0,  # Max allowed
            material="al7075_t6",
            engine="lycoming_io720",
        )
        assert inp.payload_tons == 100.0

    def test_excessive_payload(self):
        """Test payload exceeding maximum is rejected."""
        with pytest.raises(ValueError):
            DesignInput(
                payload_tons=150.0,  # Over max (100)
                material="al7075_t6",
                engine="lycoming_io720",
            )


class TestGeometryParams:
    """Tests for GeometryParams model."""

    def test_valid_geometry(self):
        """Test creating valid geometry parameters."""
        geo = GeometryParams(
            wing_span_m=15.0,
            wing_area_m2=50.0,
            aspect_ratio=10.0,
            wing_taper_ratio=0.4,
            wing_thickness_ratio=0.12,
            fuselage_length_m=12.0,
            fuselage_diameter_m=1.5,
            tail_span_m=3.0,
            tail_area_m2=5.0,
            engine_pylon_length_m=1.0,
            max_takeoff_weight_kg=5000.0,
            empty_weight_kg=2500.0,
            wing_mean_aerodynamic_chord_m=1.5,
        )
        assert geo.wing_span_m == 15.0
        assert geo.aspect_ratio == 10.0

    def test_taper_ratio_bounds(self):
        """Test taper ratio must be <= 1."""
        with pytest.raises(ValueError):
            GeometryParams(
                wing_span_m=15.0,
                wing_area_m2=50.0,
                aspect_ratio=10.0,
                wing_taper_ratio=1.5,  # Invalid
                wing_thickness_ratio=0.12,
                fuselage_length_m=12.0,
                fuselage_diameter_m=1.5,
                tail_span_m=3.0,
                tail_area_m2=5.0,
                engine_pylon_length_m=1.0,
                max_takeoff_weight_kg=5000.0,
                empty_weight_kg=2500.0,
                wing_mean_aerodynamic_chord_m=1.5,
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
