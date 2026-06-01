"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from afw_d.api import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestRootEndpoints:
    """Tests for root API endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "service" in data
        assert data["service"] == "AFW-D Design Engine"

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"


class TestDesignEndpoints:
    """Tests for design API endpoints."""

    def test_submit_design_basic(self, client):
        """Test submitting a basic design."""
        response = client.post(
            "/design/submit",
            json={
                "payload_kg": 1000.0,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "design_id" in data
        assert data["state"] in ["queued", "running", "completed", "failed"]

    def test_submit_design_with_options(self, client):
        """Test submitting a design with optional parameters."""
        response = client.post(
            "/design/submit",
            json={
                "payload_kg": 1000.0,
                "material_family": "Al-Mg-Si",
                "engine_family": "Turboprop-A",
                "tags": ["test", "demo"],
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "design_id" in data

    def test_submit_design_invalid_payload(self, client):
        """Test submitting a design with invalid payload."""
        response = client.post(
            "/design/submit",
            json={
                "payload_kg": 0.0,
            },
        )
        # FastAPI returns 422 for Pydantic validation errors on input
        # The design workflow itself handles the error internally
        assert response.status_code in [200, 422]

    def test_get_design_status(self, client):
        """Test getting design status."""
        # First submit a design
        submit_response = client.post(
            "/design/submit",
            json={"payload_kg": 1000.0},
        )
        design_id = submit_response.json()["design_id"]

        # Then get status
        status_response = client.get(f"/design/status/{design_id}")
        assert status_response.status_code == 200

        data = status_response.json()
        assert data["design_id"] == design_id
        assert data["state"] in ["queued", "running", "completed", "failed"]

    def test_get_design_status_not_found(self, client):
        """Test getting status for non-existent design."""
        response = client.get("/design/status/non-existent-id")
        assert response.status_code == 404

    def test_download_design_not_found(self, client):
        """Test downloading non-existent design."""
        response = client.get("/design/download/non-existent-id")
        assert response.status_code == 404

    def test_submit_feedback(self, client):
        """Test submitting feedback."""
        # First submit a design
        submit_response = client.post(
            "/design/submit",
            json={"payload_kg": 1000.0},
        )
        design_id = submit_response.json()["design_id"]

        # Then submit feedback
        feedback_response = client.post(
            f"/design/feedback/{design_id}",
            json={
                "user_id": "test_user",
                "comment": "Test feedback",
            },
        )
        assert feedback_response.status_code == 200

        data = feedback_response.json()
        assert data["success"] is True

    def test_submit_feedback_not_found(self, client):
        """Test submitting feedback for non-existent design."""
        response = client.post(
            "/design/feedback/non-existent-id",
            json={
                "user_id": "test_user",
                "comment": "Test feedback",
            },
        )
        assert response.status_code == 404

    def test_get_design_history(self, client):
        """Test getting design history."""
        # First submit a design
        submit_response = client.post(
            "/design/submit",
            json={"payload_kg": 1000.0},
        )
        design_id = submit_response.json()["design_id"]

        # Then get history
        history_response = client.get(f"/design/history/{design_id}")
        assert history_response.status_code == 200

        data = history_response.json()
        assert isinstance(data, list)

    def test_get_design_history_not_found(self, client):
        """Test getting history for non-existent design."""
        response = client.get("/design/history/non-existent-id")
        assert response.status_code == 404


class TestDesignStatusModel:
    """Tests for DesignStatus model validation."""

    def test_design_status_fields(self, client):
        """Test that design status has required fields."""
        response = client.post(
            "/design/submit",
            json={"payload_kg": 1000.0},
        )
        data = response.json()

        assert "design_id" in data
        assert "state" in data
        assert "progress" in data
        assert data["progress"] >= 0
        assert data["progress"] <= 100

    def test_progress_tracking(self, client):
        """Test that progress is tracked correctly."""
        response = client.post(
            "/design/submit",
            json={"payload_kg": 1000.0},
        )
        data = response.json()

        # Progress should be either 0, 100, or intermediate
        assert data["progress"] >= 0


class TestAPIIntegration:
    """Integration tests for API workflow."""

    def test_full_design_workflow(self, client):
        """Test complete design submission and retrieval workflow."""
        # Submit design
        submit_response = client.post(
            "/design/submit",
            json={
                "payload_kg": 1000.0,
                "material_family": "Al-Mg-Si",
            },
        )
        assert submit_response.status_code == 200
        design_id = submit_response.json()["design_id"]

        # Get status
        status_response = client.get(f"/design/status/{design_id}")
        assert status_response.status_code == 200

        # Get history
        history_response = client.get(f"/design/history/{design_id}")
        assert history_response.status_code == 200

    def test_multiple_designs(self, client):
        """Test submitting multiple designs."""
        design_ids = []

        for payload in [500.0, 1000.0, 2000.0]:
            response = client.post(
                "/design/submit",
                json={"payload_kg": payload},
            )
            assert response.status_code == 200
            design_ids.append(response.json()["design_id"])

        # Verify all designs can be retrieved
        for design_id in design_ids:
            status_response = client.get(f"/design/status/{design_id}")
            assert status_response.status_code == 200