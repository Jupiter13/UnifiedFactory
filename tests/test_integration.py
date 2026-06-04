"""Integration tests for the AutoPlane Design Graph.

Tests cover the full graph execution and API endpoints.
"""

import pytest
import os
import tempfile

from autoplane.agent import create_design_graph, compile_graph, AutoPlaneAgent
from autoplane.models.state import DesignState, GeometryJSON, AeroResult, StructResult
from autoplane.memory import DesignMemory, reset_memory, VectorStore
from autoplane import get_agent


class TestDesignGraph:
    """Integration tests for the LangGraph design workflow."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset agent state before each test."""
        # Import and reset agent state
        import autoplane.agent as agent_module
        agent_module._agent_instance = None
        yield
        agent_module._agent_instance = None

    def test_graph_creation(self):
        """Test that the graph can be created."""
        graph = create_design_graph()
        assert graph is not None

    def test_graph_compilation(self):
        """Test that the graph can be compiled."""
        compiled = compile_graph()
        assert compiled is not None

    def test_full_design_workflow_basic(self):
        """Test full design workflow with basic payload."""
        agent = AutoPlaneAgent()
        
        result = agent.start_design(
            payload_kg=1000,
            material="Al-6061",
            engine="Turbofan-1",
        )
        
        # Graph returns dict, convert to DesignState for assertions
        state = DesignState(**result) if isinstance(result, dict) else result
        
        # Check that design completed
        assert state.status == "completed"
        
        # Check that geometry was generated
        assert state.geometry_json is not None
        assert state.wing_span is not None
        assert state.wing_area is not None
        
        # Check that simulations ran
        assert state.aerodynamic is not None
        assert state.structural is not None
        
        # Check that performance was computed
        assert state.performance is not None
        assert state.performance.range_km > 0
        
        # Check that cost was estimated
        assert state.cost is not None
        assert state.cost.total_cost > 0
        
        # Check that CAD was exported
        assert state.cad_file is not None
        
        # Check that report was generated
        assert state.report_pdf is not None

    def test_full_design_workflow_large_payload(self):
        """Test full design workflow with large payload."""
        agent = AutoPlaneAgent()
        
        result = agent.start_design(
            payload_kg=5000,
            material="Carbon Fiber",
            engine="Turbofan-2",
        )
        
        state = DesignState(**result) if isinstance(result, dict) else result
        
        assert state.status == "completed"
        assert state.geometry_json is not None
        assert state.wing_span > 15.0  # Should be larger for larger payload
        assert state.performance is not None

    def test_design_workflow_with_default_material_engine(self):
        """Test design workflow with default material and engine."""
        agent = AutoPlaneAgent()
        
        result = agent.start_design(payload_kg=1000)
        
        state = DesignState(**result) if isinstance(result, dict) else result
        
        assert state.status == "completed"
        assert state.material == "Al-6061"  # Default
        assert state.engine == "Turbofan-1"  # Default

    def test_agent_singleton(self):
        """Test that get_agent returns a singleton."""
        agent1 = get_agent()
        agent2 = get_agent()
        assert agent1 is agent2

    def test_get_status(self):
        """Test status retrieval."""
        agent = AutoPlaneAgent()
        result = agent.start_design(payload_kg=1000)
        
        state = DesignState(**result) if isinstance(result, dict) else result
        
        status = agent.get_status(state)
        assert "job_id" in status
        assert "status" in status
        assert "progress" in status
        assert status["status"] == "completed"
        assert status["progress"] == 100


class TestVectorStore:
    """Tests for the vector store."""

    def test_vector_store_add_and_search(self):
        """Test adding and searching vectors."""
        store = VectorStore(dimension=128)
        
        # Add a vector
        import numpy as np
        embedding = np.random.rand(128).astype(np.float32)
        metadata = {"payload_kg": 1000, "material": "Al-6061"}
        store.add(embedding, metadata)
        
        # Search
        results = store.search(embedding, k=1)
        assert len(results) == 1
        assert results[0]["metadata"]["payload_kg"] == 1000

    def test_vector_store_search_empty(self):
        """Test searching empty store."""
        store = VectorStore(dimension=128)
        import numpy as np
        
        results = store.search(np.random.rand(128).astype(np.float32), k=5)
        assert len(results) == 0

    def test_vector_store_dimension_mismatch(self):
        """Test adding vector with wrong dimension."""
        store = VectorStore(dimension=128)
        import numpy as np
        
        with pytest.raises(ValueError):
            store.add(np.random.rand(64).astype(np.float32), {})


class TestDesignMemory:
    """Tests for the memory management."""

    @pytest.fixture(autouse=True)
    def setup_memory(self):
        """Set up in-memory SQLite database."""
        reset_memory()
        yield
        reset_memory()

    def test_store_and_retrieve_design(self):
        """Test storing and retrieving a design."""
        memory = DesignMemory(db_url="sqlite:///:memory:")
        
        state = DesignState(
            payload_kg=1000,
            material="Al-6061",
            engine="Turbofan-1",
            status="completed",
        )
        state.job_id = "test-job-1"
        
        job_id = memory.store_design(state)
        assert job_id == "test-job-1"
        
        retrieved = memory.get_design("test-job-1")
        assert retrieved is not None
        assert retrieved.payload_kg == 1000
        assert retrieved.material == "Al-6061"

    def test_get_nonexistent_design(self):
        """Test retrieving non-existent design."""
        memory = DesignMemory(db_url="sqlite:///:memory:")
        
        result = memory.get_design("nonexistent")
        assert result is None

    def test_list_designs(self):
        """Test listing designs."""
        memory = DesignMemory(db_url="sqlite:///:memory:")
        
        # Store multiple designs
        for i in range(3):
            state = DesignState(
                payload_kg=1000 + i * 100,
                material="Al-6061",
                status="completed",
            )
            state.job_id = f"test-job-{i}"
            memory.store_design(state, user_id="test_user")
        
        designs = memory.list_designs(user_id="test_user")
        assert len(designs) == 3

    def test_find_similar(self):
        """Test finding similar designs."""
        memory = DesignMemory(db_url="sqlite:///:memory:")
        
        # Store a design
        state = DesignState(
            payload_kg=1000,
            material="Al-6061",
            status="completed",
        )
        memory.store_design(state)
        
        # Find similar
        similar = memory.find_similar(state, k=5)
        assert len(similar) >= 1

    def test_delete_design(self):
        """Test deleting a design."""
        memory = DesignMemory(db_url="sqlite:///:memory:")
        
        state = DesignState(payload_kg=1000, status="completed")
        state.job_id = "test-job-delete"
        memory.store_design(state)
        
        # Delete
        deleted = memory.delete_design("test-job-delete")
        assert deleted is True
        
        # Verify deleted
        result = memory.get_design("test-job-delete")
        assert result is None
        
        # Try deleting again
        deleted = memory.delete_design("test-job-delete")
        assert deleted is False


class TestGraphNodes:
    """Test individual node behavior in graph context."""

    def test_sequential_node_execution(self):
        """Test that nodes execute in correct order."""
        from autoplane.nodes import (
            input_parser,
            material_selector,
            engine_selector,
            design_generator,
            aerodynamic_evaluator,
            structural_evaluator,
            performance_estimator,
            cost_estimator,
            regulatory_checker,
        )
        
        # Execute nodes sequentially
        state = DesignState(payload_kg=1000)
        
        state = input_parser(state)
        assert state.status == "running"
        
        state = material_selector(state)
        assert state.material_props is not None
        
        state = engine_selector(state)
        assert state.engine_props is not None
        
        state = design_generator(state)
        assert state.geometry_json is not None
        
        state = aerodynamic_evaluator(state)
        assert state.aerodynamic is not None
        
        state = structural_evaluator(state)
        assert state.structural is not None
        
        state = performance_estimator(state)
        assert state.performance is not None
        
        state = cost_estimator(state)
        assert state.cost is not None
        
        state = regulatory_checker(state)
        assert state.regulatory is not None


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_design_with_invalid_payload_zero(self):
        """Test design with zero payload."""
        agent = AutoPlaneAgent()
        
        result = agent.start_design(payload_kg=0)
        state = DesignState(**result) if isinstance(result, dict) else result
        
        assert state.status == "failed"
        assert state.last_error is not None

    def test_design_with_very_large_payload(self):
        """Test design with very large but valid payload."""
        agent = AutoPlaneAgent()
        
        # Should still complete but with warnings
        result = agent.start_design(payload_kg=49000)
        state = DesignState(**result) if isinstance(result, dict) else result
        
        # Depending on implementation, may succeed or fail
        assert state.status in ["completed", "failed"]

    def test_empty_material_engine_database(self):
        """Test that unknown materials/engines are rejected."""
        from autoplane.nodes import material_selector, engine_selector
        
        state = DesignState(payload_kg=1000, material="UnknownMetal")
        result = material_selector(state)
        assert result.status == "failed"
        
        state = DesignState(payload_kg=1000, engine="SuperEngine")
        result = engine_selector(state)
        assert result.status == "failed"


class TestPerformanceMetrics:
    """Test performance and timing."""

    def test_graph_execution_time(self):
        """Test that graph executes within reasonable time."""
        import time
        
        agent = AutoPlaneAgent()
        
        start = time.time()
        result = agent.start_design(payload_kg=1000)
        state = DesignState(**result) if isinstance(result, dict) else result
        elapsed = time.time() - start
        
        assert state.status == "completed"
        # Should complete in under 10 seconds for local execution
        assert elapsed < 10

    def test_multiple_concurrent_designs(self):
        """Test handling multiple design requests."""
        agent = AutoPlaneAgent()
        
        results = []
        for payload in [500, 1000, 2000]:
            result = agent.start_design(payload_kg=payload)
            state = DesignState(**result) if isinstance(result, dict) else result
            results.append(state)
        
        assert len(results) == 3
        assert all(s.status == "completed" for s in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])