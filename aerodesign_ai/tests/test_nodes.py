"""Integration tests for AeroDesign-AI LangGraph pipeline."""

import pytest
from datetime import datetime

from aerodesign_ai.nodes.graph_state import DesignState, create_initial_state
from aerodesign_ai.nodes.nodes import (
    StartNode,
    ValidateInputNode,
    FetchMaterialPropsNode,
    FetchEngineSpecsNode,
    GenerateInitialGeometryNode,
    OptimizeDesignNode,
    ComplianceCheckNode,
    CADExportNode,
    GenerateBOMNode,
    StoreDesignNode,
    EndNode,
)


class TestGraphState:
    """Tests for graph state management."""

    def test_create_initial_state(self):
        """Test creating initial state."""
        state = create_initial_state(
            payload_tons=2.0,
            material="al7075_t6",
            engine="lycoming_io720",
            user_id="test_user",
        )
        assert state["payload_tons"] == 2.0
        assert state["material"] == "al7075_t6"
        assert state["engine"] == "lycoming_io720"
        assert state["user_id"] == "test_user"
        assert state["status"] == "queued"
        assert "errors" in state

    def test_create_state_with_constraints(self):
        """Test creating state with optional constraints."""
        state = create_initial_state(
            payload_tons=5.0,
            material="ti6al4v",
            engine="potez_4e",
            optional_constraints={"aspect_ratio": 12},
        )
        assert state["optional_constraints"]["aspect_ratio"] == 12


class TestStartNode:
    """Tests for StartNode."""

    def test_start_node(self):
        """Test start node execution."""
        node = StartNode()
        state = create_initial_state(
            payload_tons=2.0,
            material="al7075_t6",
            engine="lycoming_io720",
        )
        result = node.execute(state)
        assert result["status"] == "running"


class TestValidateInputNode:
    """Tests for ValidateInputNode."""

    def test_valid_input(self):
        """Test validation passes for valid input."""
        node = ValidateInputNode()
        state = {
            "payload_tons": 2.0,
            "material": "al7075_t6",
            "engine": "lycoming_io720",
            "errors": [],
        }
        result = node.execute(state)
        assert len(result["errors"]) == 0

    def test_invalid_payload(self):
        """Test validation catches invalid payload."""
        node = ValidateInputNode()
        state = {
            "payload_tons": -1,
            "material": "al7075_t6",
            "engine": "lycoming_io720",
            "errors": [],
        }
        result = node.execute(state)
        assert len(result["errors"]) > 0

    def test_empty_material(self):
        """Test validation catches empty material."""
        node = ValidateInputNode()
        state = {
            "payload_tons": 2.0,
            "material": "",
            "engine": "lycoming_io720",
            "errors": [],
        }
        result = node.execute(state)
        assert len(result["errors"]) > 0


class TestFetchMaterialPropsNode:
    """Tests for FetchMaterialPropsNode."""

    def test_fetch_material(self):
        """Test fetching material properties."""
        node = FetchMaterialPropsNode()
        state = {
            "material": "al7075_t6",
            "errors": [],
        }
        result = node.execute(state)
        assert "material_props" in result
        assert result["material_props"]["name"] == "Aluminum 7075-T6"


class TestFetchEngineSpecsNode:
    """Tests for FetchEngineSpecsNode."""

    def test_fetch_engine(self):
        """Test fetching engine specifications."""
        node = FetchEngineSpecsNode()
        state = {
            "engine": "lycoming_io720",
            "errors": [],
        }
        result = node.execute(state)
        assert "engine_specs" in result
        assert result["engine_specs"]["name"] == "Lycoming IO-720"


class TestGenerateInitialGeometryNode:
    """Tests for GenerateInitialGeometryNode."""

    def test_generate_geometry(self):
        """Test geometry generation."""
        node = GenerateInitialGeometryNode()
        state = {
            "payload_tons": 2.0,
            "material": "al7075_t6",
            "engine": "lycoming_io720",
            "material_props": {
                "density_kg_m3": 2810,
                "cost_per_kg": 12.50,
                "manufacturability_score": 0.9,
            },
            "engine_specs": {
                "thrust_newtons": 29420,
                "weight_kg": 240,
                "fuel_flow_kg_s": 0.055,
            },
            "optional_constraints": {},
            "errors": [],
        }
        result = node.execute(state)
        assert "geometry" in result
        assert "wing_span_m" in result["geometry"]
        assert result["geometry"]["wing_span_m"] > 0


class TestOptimizeDesignNode:
    """Tests for OptimizeDesignNode."""

    def test_optimize_design(self):
        """Test design optimization."""
        node = OptimizeDesignNode()
        state = {
            "payload_tons": 2.0,
            "geometry": {
                "wing_span_m": 12,
                "aspect_ratio": 10,
                "taper_ratio": 0.4,
                "wing_thickness_ratio": 0.12,
                "fuselage_length_m": 10,
                "fuselage_diameter_m": 1.3,
            },
            "material_props": {
                "density_kg_m3": 2810,
                "cost_per_kg": 12.50,
                "tensile_strength_pa": 5.24e8,
            },
            "engine_specs": {
                "thrust_newtons": 29420,
                "weight_kg": 240,
                "fuel_flow_kg_s": 0.055,
            },
            "errors": [],
        }
        result = node.execute(state)
        assert "optimization_metrics" in result
        assert "cruise_speed_kt" in result["optimization_metrics"]


class TestComplianceCheckNode:
    """Tests for ComplianceCheckNode."""

    def test_compliance_check(self):
        """Test compliance check."""
        node = ComplianceCheckNode()
        state = {
            "geometry": {
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
            },
            "payload_tons": 2.0,
            "errors": [],
        }
        result = node.execute(state)
        assert "compliance_report" in result


class TestCADExportNode:
    """Tests for CADExportNode."""

    def test_cad_export(self):
        """Test CAD export."""
        node = CADExportNode()
        state = {
            "geometry": {
                "wing_span_m": 12,
                "aspect_ratio": 10,
            },
            "version_id": "TEST-001",
            "errors": [],
        }
        result = node.execute(state)
        assert "cad_file_path" in result


class TestGenerateBOMNode:
    """Tests for GenerateBOMNode."""

    def test_generate_bom(self):
        """Test BOM generation."""
        node = GenerateBOMNode()
        state = {
            "geometry": {
                "wing_span_m": 12,
                "wing_area_m2": 50,
                "fuselage_length_m": 10,
                "fuselage_diameter_m": 1.3,
                "tail_span_m": 2.5,
                "tail_area_m2": 3,
                "material": "Aluminum",
            },
            "material_props": {
                "cost_per_kg": 12.50,
                "density_kg_m3": 2810,
            },
            "engine_specs": {
                "cost_usd": 35000,
            },
            "errors": [],
        }
        result = node.execute(state)
        assert "bom" in result
        assert len(result["bom"]) > 0


class TestEndNode:
    """Tests for EndNode."""

    def test_end_node_success(self):
        """Test end node with successful execution."""
        node = EndNode()
        state = {
            "bom": [
                {"part_name": "Wing", "total_cost_usd": 5000},
                {"part_name": "Fuselage", "total_cost_usd": 8000},
            ],
            "status": "running",
            "errors": [],
        }
        result = node.execute(state)
        assert result["status"] == "completed"
        assert result["total_cost_usd"] == 13000

    def test_end_node_failure(self):
        """Test end node with errors."""
        node = EndNode()
        state = {
            "errors": ["Some error"],
            "status": "running",
        }
        result = node.execute(state)
        assert result["status"] == "failed"


class TestNodeIntegration:
    """Integration tests for full node pipeline."""

    def test_full_pipeline_nodes(self):
        """Test executing key nodes in sequence."""
        # Start with valid state
        state = create_initial_state(
            payload_tons=2.0,
            material="al7075_t6",
            engine="lycoming_io720",
        )
        
        # Execute nodes
        start_node = StartNode()
        validate_node = ValidateInputNode()
        fetch_mat_node = FetchMaterialPropsNode()
        fetch_eng_node = FetchEngineSpecsNode()
        geom_node = GenerateInitialGeometryNode()
        opt_node = OptimizeDesignNode()
        
        # Run pipeline
        state = start_node.execute(state)
        assert state["status"] == "running"
        
        state = validate_node.execute(state)
        assert len(state["errors"]) == 0
        
        state = fetch_mat_node.execute(state)
        assert "material_props" in state
        
        state = fetch_eng_node.execute(state)
        assert "engine_specs" in state
        
        state = geom_node.execute(state)
        assert "geometry" in state
        
        state = opt_node.execute(state)
        assert "optimization_metrics" in state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
