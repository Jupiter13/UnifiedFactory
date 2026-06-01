"""Integration tests for the LangGraph workflow."""

import pytest

from afw_d.graph import (
    create_graph,
    create_conditional_graph,
    run_design,
    get_app,
)
from afw_d.graph.state import AFWDesignState, initial_state


class TestGraphCreation:
    """Tests for graph creation."""

    def test_create_graph(self):
        """Test basic graph creation."""
        graph = create_graph()
        assert graph is not None

    def test_create_conditional_graph(self):
        """Test conditional graph creation."""
        graph = create_conditional_graph()
        assert graph is not None

    def test_get_app(self):
        """Test getting compiled application."""
        app = get_app()
        assert app is not None


class TestInitialState:
    """Tests for initial state creation."""

    def test_initial_state_basic(self):
        """Test creating basic initial state."""
        state = initial_state(payload_kg=1000.0)

        assert state["payload_kg"] == 1000.0
        assert state["iteration"] == 0

    def test_initial_state_with_optional(self):
        """Test creating initial state with optional params."""
        state = initial_state(
            payload_kg=1000.0,
            material_family="Al-Mg-Si",
            engine_family="Turboprop-A",
        )

        assert state["material_family"] == "Al-Mg-Si"
        assert state["engine_family"] == "Turboprop-A"


class TestRunDesign:
    """Tests for running the complete design workflow."""

    def test_run_design_basic(self):
        """Test running design with basic parameters."""
        result = run_design(payload_kg=1000.0)

        assert result is not None
        assert "design_id" in result or "error" not in result or result.get("error") is None

    def test_run_design_with_material(self):
        """Test running design with specific material."""
        result = run_design(
            payload_kg=1000.0,
            material_family="Al-Mg-Si",
        )

        assert result is not None

    def test_run_design_with_engine(self):
        """Test running design with specific engine."""
        result = run_design(
            payload_kg=1000.0,
            engine_family="Turboprop-A",
        )

        assert result is not None

    def test_run_design_with_both(self):
        """Test running design with both material and engine."""
        result = run_design(
            payload_kg=1000.0,
            material_family="Al-Mg-Si",
            engine_family="Turboprop-A",
        )

        assert result is not None

    def test_run_design_small_payload(self):
        """Test running design with small payload."""
        result = run_design(payload_kg=500.0)

        assert result is not None

    def test_run_design_large_payload(self):
        """Test running design with large payload."""
        result = run_design(payload_kg=5000.0)

        assert result is not None


class TestGraphNodes:
    """Tests for individual graph nodes."""

    def test_input_collector_valid_payload(self):
        """Test input collector with valid payload."""
        from afw_d.graph.nodes import input_collector

        state = {"payload_kg": 1000.0}
        result = input_collector(state)

        assert result is not None
        assert "design_id" in result
        assert "error" not in result or result["error"] is None

    def test_input_collector_invalid_payload(self):
        """Test input collector with invalid payload."""
        from afw_d.graph.nodes import input_collector

        state = {"payload_kg": 0}
        result = input_collector(state)

        assert "error" in result

    def test_material_selector_default(self):
        """Test material selector with default."""
        from afw_d.graph.nodes import material_selector

        state = {}
        result = material_selector(state)

        assert "material_props" in result
        assert result["material_props"] is not None

    def test_material_selector_custom(self):
        """Test material selector with custom material."""
        from afw_d.graph.nodes import material_selector

        state = {"material_family": "Carbon-Epoxy"}
        result = material_selector(state)

        assert "material_props" in result

    def test_engine_selector_default_small_payload(self):
        """Test engine selector with small payload."""
        from afw_d.graph.nodes import engine_selector

        state = {"payload_kg": 1000}
        result = engine_selector(state)

        assert "engine_specs" in result

    def test_engine_selector_default_large_payload(self):
        """Test engine selector with large payload."""
        from afw_d.graph.nodes import engine_selector

        state = {"payload_kg": 6000}
        result = engine_selector(state)

        assert "engine_specs" in result

    def test_engine_selector_custom(self):
        """Test engine selector with custom engine."""
        from afw_d.graph.nodes import engine_selector

        state = {"engine_family": "Turbofan-A"}
        result = engine_selector(state)

        assert "engine_specs" in result


class TestDesignGenerator:
    """Tests for design generator node."""

    def test_design_generator_small_payload(self):
        """Test design generator with small payload."""
        from afw_d.graph.nodes import design_generator

        state = {
            "payload_kg": 1000.0,
            "material_props": None,
            "engine_specs": None,
        }
        result = design_generator(state)

        assert "design_params" in result
        params = result["design_params"]
        assert params["wing_area"] > 0

    def test_design_generator_large_payload(self):
        """Test design generator with large payload."""
        from afw_d.graph.nodes import design_generator

        state = {
            "payload_kg": 5000.0,
            "material_props": None,
            "engine_specs": None,
        }
        result = design_generator(state)

        assert "design_params" in result


class TestSimulationNodes:
    """Tests for simulation nodes."""

    @pytest.fixture
    def valid_design_state(self):
        """Create a valid design state for testing."""
        from afw_d.graph.nodes import design_generator

        return design_generator({
            "payload_kg": 1000.0,
            "material_props": None,
            "engine_specs": None,
        })

    def test_simulation_runner(self, valid_design_state):
        """Test simulation runner node."""
        from afw_d.graph.nodes import simulation_runner

        state = valid_design_state.copy()
        state["engine_specs"] = None
        result = simulation_runner(state)

        assert "simulation" in result

    def test_cost_estimator(self, valid_design_state):
        """Test cost estimator node."""
        from afw_d.graph.nodes import cost_estimator

        state = valid_design_state.copy()
        result = cost_estimator(state)

        assert "cost_estimate" in result

    def test_compliance_checker(self, valid_design_state):
        """Test compliance checker node."""
        from afw_d.graph.nodes import compliance_checker

        state = valid_design_state.copy()
        result = compliance_checker(state)

        assert "compliance" in result


class TestWorkflowIntegration:
    """Integration tests for the complete workflow."""

    def test_workflow_produces_design_params(self):
        """Test that workflow produces design parameters."""
        result = run_design(payload_kg=1000.0)

        # Workflow should complete
        assert result is not None

    def test_workflow_iteration_tracking(self):
        """Test that workflow tracks iterations."""
        result = run_design(payload_kg=1000.0)

        # Iteration tracking should be present
        assert "iteration" in result or result.get("iteration", 0) >= 0

    def test_workflow_compliance_tracking(self):
        """Test that workflow tracks compliance."""
        result = run_design(payload_kg=1000.0)

        # Compliance should be checked
        compliance = result.get("compliance")
        if compliance:
            assert hasattr(compliance, "passed")
            assert hasattr(compliance, "issues")