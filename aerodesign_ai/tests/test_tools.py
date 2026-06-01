"""Unit tests for AeroDesign-AI tools."""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from aerodesign_ai.tools.base import BaseTool, ToolResult, ToolError
from aerodesign_ai.tools.material_tool import FetchMaterialProps, MaterialDatabase
from aerodesign_ai.tools.engine_tool import FetchEngineSpecs, EngineDatabase
from aerodesign_ai.tools.compliance_tool import RunComplianceCheck, RuleEvaluator
from aerodesign_ai.tools.optimizer_tool import OptimizeDesign, DesignOptimizer, OptimizationConstraints
from aerodesign_ai.tools.cad_tool import GenerateCAD, CADExporter
from aerodesign_ai.tools.bom_tool import GenerateBOM, BOMGenerator
from aerodesign_ai.tools.storage_tool import StoreDesign, RetrieveDesign, DesignStorage
from aerodesign_ai.models.schemas import MaterialProps, EngineSpecs, ComplianceReport, BOMItem, DesignState


class TestToolResult:
    """Tests for ToolResult."""
    
    def test_successful_result(self):
        """Test creating successful result."""
        data = MaterialProps(
            name="Test Material",
            density_kg_m3=2700,
            tensile_strength_pa=5e8,
            cost_per_kg=10,
            manufacturability_score=0.9,
        )
        result = ToolResult.ok(data)
        assert result.success is True
        assert result.data == data
        assert result.error is None

    def test_error_result(self):
        """Test creating error result."""
        result = ToolResult.err("Test error message")
        assert result.success is False
        assert result.error == "Test error message"
        assert result.data is None


class TestMaterialDatabase:
    """Tests for MaterialDatabase."""
    
    def test_get_material_by_id(self):
        """Test getting material by ID."""
        db = MaterialDatabase()
        mat = db.get("al7075_t6")
        assert mat is not None
        assert mat["name"] == "Aluminum 7075-T6"

    def test_get_material_by_name(self):
        """Test getting material by name (case-insensitive)."""
        db = MaterialDatabase()
        mat = db.get_by_name("Aluminum 7075-T6")
        assert mat is not None
        assert mat["density_kg_m3"] == 2810

    def test_list_all_materials(self):
        """Test listing all materials."""
        db = MaterialDatabase()
        materials = db.list_all()
        assert len(materials) > 0


class TestFetchMaterialProps:
    """Tests for FetchMaterialProps tool."""

    def test_fetch_existing_material(self):
        """Test fetching existing material."""
        tool = FetchMaterialProps()
        result = tool.call(material="al7075_t6")
        assert result.success is True
        assert result.data is not None
        assert "7075" in result.data.name

    def test_fetch_nonexistent_material(self):
        """Test fetching non-existent material."""
        tool = FetchMaterialProps()
        result = tool.call(material="nonexistent_material")
        assert result.success is False
        assert result.error is not None

    def test_validate_material_input(self):
        """Test input validation."""
        tool = FetchMaterialProps()
        assert tool.validate_inputs(material="al7075_t6") is True
        assert tool.validate_inputs(material="") is False


class TestEngineDatabase:
    """Tests for EngineDatabase."""
    
    def test_get_engine_by_id(self):
        """Test getting engine by ID."""
        db = EngineDatabase()
        eng = db.get("lycoming_io720")
        assert eng is not None
        assert eng["name"] == "Lycoming IO-720"

    def test_list_all_engines(self):
        """Test listing all engines."""
        db = EngineDatabase()
        engines = db.list_all()
        assert len(engines) > 0


class TestFetchEngineSpecs:
    """Tests for FetchEngineSpecs tool."""

    def test_fetch_existing_engine(self):
        """Test fetching existing engine."""
        tool = FetchEngineSpecs()
        result = tool.call(engine="lycoming_io720")
        assert result.success is True
        assert result.data is not None

    def test_validate_engine_input(self):
        """Test input validation."""
        tool = FetchEngineSpecs()
        assert tool.validate_inputs(engine="lycoming_io720") is True
        assert tool.validate_inputs(engine="") is False


class TestRuleEvaluator:
    """Tests for RuleEvaluator."""

    def test_evaluate_simple_condition_pass(self):
        """Test evaluating simple condition that passes."""
        config = {
            "rules": [
                {
                    "id": "stall_speed",
                    "condition": "geometry.stall_speed_kt >= 60",
                    "severity": "critical",
                    "message": "Stall speed too low"
                }
            ]
        }
        evaluator = RuleEvaluator(config)
        
        # Passing case
        geometry = {"stall_speed_kt": 70, "aspect_ratio": 10}
        report = evaluator.evaluate(geometry)
        assert len(report.violations) == 0
        assert len(report.checked_rules) == 1

    def test_evaluate_simple_condition_fail(self):
        """Test evaluating simple condition that fails."""
        config = {
            "rules": [
                {
                    "id": "stall_speed",
                    "condition": "geometry.stall_speed_kt >= 60",
                    "severity": "critical",
                    "message": "Stall speed too low"
                }
            ]
        }
        evaluator = RuleEvaluator(config)
        
        # Failing case - stall speed < 60
        geometry = {"stall_speed_kt": 50, "aspect_ratio": 10}
        report = evaluator.evaluate(geometry)
        assert len(report.violations) == 1

    def test_chained_comparison_pass(self):
        """Test chained comparison that passes."""
        config = {
            "rules": [
                {
                    "id": "aspect_ratio",
                    "condition": "5 <= geometry.aspect_ratio <= 15",
                    "severity": "warning",
                    "message": "Aspect ratio out of range"
                }
            ]
        }
        evaluator = RuleEvaluator(config)
        
        # In range
        geometry = {"aspect_ratio": 10, "stall_speed_kt": 70}
        report = evaluator.evaluate(geometry)
        assert len(report.warnings) == 0


class TestRunComplianceCheck:
    """Tests for RunComplianceCheck tool."""

    def test_compliance_check_with_all_required_fields(self):
        """Test compliance check with all required geometry fields."""
        tool = RunComplianceCheck()
        geometry = {
            "stall_speed_kt": 70,
            "takeoff_field_length_m": 1000,
            "max_takeoff_weight_kg": 5000,
            "aspect_ratio": 10,
            "structural_margin": 10,
            "engine_clearance_m": 0.5,
            "tail_clearance_m": 0.3,
            "climb_gradient_percent": 3.0,
            "landing_field_length_m": 800,
            "wing_loading_kg_m2": 300,
            "lift_to_drag_ratio": 12,
        }
        result = tool.call(geometry=geometry)
        assert result.success is True
        assert result.data is not None
        # Should pass the stall speed critical rule
        assert all(v != "Stall speed must be at least 60 knots" for v in result.data.violations)

    def test_compliance_check_fails_stall_speed(self):
        """Test compliance check catches low stall speed."""
        tool = RunComplianceCheck()
        geometry = {
            "stall_speed_kt": 50,  # Too low - should fail
            "takeoff_field_length_m": 1000,
            "max_takeoff_weight_kg": 5000,
            "aspect_ratio": 10,
            "structural_margin": 10,
            "engine_clearance_m": 0.5,
            "tail_clearance_m": 0.3,
            "climb_gradient_percent": 3.0,
            "landing_field_length_m": 800,
            "wing_loading_kg_m2": 300,
            "lift_to_drag_ratio": 12,
        }
        result = tool.call(geometry=geometry)
        assert result.success is True
        assert result.data is not None
        assert not result.data.passed


class TestDesignOptimizer:
    """Tests for DesignOptimizer."""

    def test_optimization_constraints(self):
        """Test optimization with constraints."""
        constraints = OptimizationConstraints(
            payload_tons=2.0,
            material_density=2810,
            material_cost=12.50,
            material_strength=5.24e8,
            engine_thrust=29420,
            engine_weight=240,
            engine_fuel_flow=0.055,
        )
        optimizer = DesignOptimizer(constraints)
        
        geometry = {
            "wing_span_m": 12,
            "aspect_ratio": 10,
            "taper_ratio": 0.4,
            "wing_thickness_ratio": 0.12,
            "fuselage_length_m": 10,
            "fuselage_diameter_m": 1.3,
        }
        
        optimized, metrics = optimizer.optimize(geometry)
        assert optimized is not None
        assert "wing_area_m2" in optimized
        assert metrics is not None


class TestOptimizeDesign:
    """Tests for OptimizeDesign tool."""

    def test_optimize_design(self):
        """Test design optimization."""
        tool = OptimizeDesign()
        result = tool.call(
            geometry={"wing_span_m": 12, "aspect_ratio": 10},
            payload_tons=2.0,
            material_density=2810,
            material_cost=12.50,
            material_strength=5.24e8,
            engine_thrust=29420,
            engine_weight=240,
            engine_fuel_flow=0.055,
        )
        assert result.success is True
        assert "geometry" in result.data


class TestCADExporter:
    """Tests for CADExporter."""

    def test_export_to_step(self, tmp_path):
        """Test STEP file export."""
        exporter = CADExporter(output_dir=tmp_path)
        geometry = {
            "wing_span_m": 12,
            "aspect_ratio": 10,
        }
        file_path = exporter.export_to_step(geometry, "TEST-001")
        assert Path(file_path).exists()


class TestGenerateCAD:
    """Tests for GenerateCAD tool."""

    def test_generate_cad(self, tmp_path):
        """Test CAD generation."""
        tool = GenerateCAD(output_dir=tmp_path)
        result = tool.call(
            geometry={"wing_span_m": 12},
            design_id="TEST-001"
        )
        assert result.success is True
        assert result.data is not None


class TestBOMGenerator:
    """Tests for BOMGenerator."""

    def test_generate_bom(self):
        """Test BOM generation."""
        generator = BOMGenerator()
        geometry = {
            "wing_span_m": 12,
            "aspect_ratio": 10,
            "wing_area_m2": 50,
            "fuselage_length_m": 10,
            "fuselage_diameter_m": 1.3,
            "tail_span_m": 2.5,
            "tail_area_m2": 3,
            "material": "Aluminum",
            "estimated_fuel_weight_kg": 500,
        }
        
        items = generator.generate(
            geometry=geometry,
            material_cost=12.50,
            material_density=2810,
            engine_cost=35000,
        )
        
        assert len(items) > 0
        assert all(hasattr(item, 'part_name') for item in items)
        assert all(hasattr(item, 'quantity') for item in items)


class TestGenerateBOM:
    """Tests for GenerateBOM tool."""

    def test_generate_bom_tool(self):
        """.Test BOM generation tool."""
        tool = GenerateBOM()
        result = tool.call(
            geometry={
                "wing_span_m": 12,
                "aspect_ratio": 10,
                "wing_area_m2": 50,
                "fuselage_length_m": 10,
                "fuselage_diameter_m": 1.3,
            },
            material_cost=12.50,
            material_density=2810,
            engine_cost=35000,
        )
        assert result.success is True
        assert len(result.data) > 0


class TestDesignStorage:
    """Tests for DesignStorage."""

    def test_store_and_retrieve(self):
        """Test storing and retrieving designs."""
        storage = DesignStorage()
        
        state = DesignState(
            payload_tons=2.0,
            material="al7075_t6",
            engine="lycoming_io720",
        )
        
        design_id = storage.store(state)
        assert design_id is not None
        
        retrieved = storage.retrieve(design_id)
        assert retrieved is not None
        assert retrieved.payload_tons == 2.0

    def test_retrieve_nonexistent(self):
        """Test retrieving non-existent design."""
        storage = DesignStorage()
        result = storage.retrieve("NONEXISTENT")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
