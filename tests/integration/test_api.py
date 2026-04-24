"""
Integration tests for API endpoints.
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

from src.main import app
from tests.test_data import SAMPLE_WEBHOOK_PAYLOADS, TEST_EMPLOYEES


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def async_client():
    """Async test client fixture."""
    return AsyncClient(app=app, base_url="http://testserver")


class TestWebhooks:
    """Test cases for webhook endpoints."""

    def test_workday_new_hire_webhook(self, client):
        """Test new hire webhook from Workday."""
        payload = SAMPLE_WEBHOOK_PAYLOADS["new_hire"]

        # Mock the orchestrator to avoid database calls
        with patch("src.api.webhooks.OrchestratorAgent") as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.handle_new_hire.return_value = AsyncMock()
            mock_orchestrator_class.return_value = mock_orchestrator

            response = client.post("/webhooks/workday/new-hire", json=payload)

            assert response.status_code == 202
            assert "accepted" in response.json()["status"]
            assert "EMP001" in response.json()["message"]

            # Verify orchestrator was called
            mock_orchestrator_class.assert_called_once()
            mock_orchestrator.handle_new_hire.assert_called_once()

    def test_servicenow_task_update_webhook(self, client):
        """Test task update webhook from ServiceNow."""
        payload = SAMPLE_WEBHOOK_PAYLOADS["task_update"]

        with patch("src.api.webhooks.OrchestratorAgent") as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.handle_task_completion.return_value = None
            mock_orchestrator_class.return_value = mock_orchestrator

            response = client.post("/webhooks/servicenow/task-update", json=payload)

            assert response.status_code == 202
            assert "accepted" in response.json()["status"]

            # Verify orchestrator was called for completion
            mock_orchestrator.handle_task_completion.assert_called_once_with(
                "task_123", {"result": "success", "details": "Equipment provisioned"}
            )

    def test_lms_completion_webhook(self, client):
        """Test training completion webhook from LMS."""
        payload = {
            "task_id": "task_456",
            "status": "completed",
            "course_id": "COMP_001",
            "completion_date": "2024-01-16"
        }

        with patch("src.api.webhooks.OrchestratorAgent") as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.handle_task_completion.return_value = None
            mock_orchestrator_class.return_value = mock_orchestrator

            response = client.post("/webhooks/lms/completion-update", json=payload)

            assert response.status_code == 202
            assert "accepted" in response.json()["status"]

    def test_invalid_webhook_payload(self, client):
        """Test webhook with invalid payload."""
        invalid_payload = {
            "employee_id": "EMP001"
            # Missing required fields
        }

        response = client.post("/webhooks/workday/new-hire", json=invalid_payload)
        assert response.status_code == 422  # Validation error


class TestAPIEndpoints:
    """Test cases for REST API endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

    def test_get_onboarding_status_unauthorized(self, client):
        """Test onboarding status endpoint without authentication."""
        response = client.get("/api/v1/onboarding/EMP001")

        # Should fail due to missing user_role parameter
        assert response.status_code == 401
        assert "Authentication required" in response.json()["error"]

    def test_get_onboarding_status_hr_ops(self, client):
        """Test onboarding status endpoint with HR Ops access."""
        with patch("src.api.endpoints.OrchestratorAgent") as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_instance = AsyncMock()
            mock_instance.id = "instance_001"
            mock_instance.employee_id = "EMP001"
            mock_instance.status.value = "NEW_HIRE"
            mock_instance.hire_date.isoformat.return_value = "2024-01-15T00:00:00"
            mock_instance.employment_type = "full-time"
            mock_instance.jurisdiction = "US"
            mock_instance.department = "Engineering"
            mock_instance.job_level = "3"
            mock_instance.tasks = []
            mock_instance.judgment_escalations = []

            mock_orchestrator.get_onboarding_instance.return_value = mock_instance
            mock_orchestrator_class.return_value = mock_orchestrator

            response = client.get("/api/v1/onboarding/EMP001?user_role=hr_ops")

            assert response.status_code == 200
            data = response.json()
            assert data["employee_id"] == "EMP001"
            assert data["status"] == "NEW_HIRE"
            assert data["department"] == "Engineering"

    def test_get_onboarding_status_not_found(self, client):
        """Test onboarding status for non-existent employee."""
        with patch("src.api.endpoints.OrchestratorAgent") as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.get_onboarding_instance.return_value = None
            mock_orchestrator_class.return_value = mock_orchestrator

            response = client.get("/api/v1/onboarding/EMP999?user_role=hr_ops")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_get_pending_escalations_hr_ops(self, client):
        """Test getting pending escalations with HR Ops access."""
        with patch("src.api.endpoints.OrchestratorAgent") as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_escalations = [
                AsyncMock(
                    id="esc_001",
                    task_id="task_001",
                    escalation_type="UNKNOWN_JURISDICTION",
                    description="Unknown jurisdiction",
                    context={"jurisdiction": "XX"},
                    options_considered=["US", "CA"],
                    recommended_action="Select track",
                    created_at=AsyncMock(isoformat=lambda: "2024-01-15T10:00:00")
                )
            ]
            mock_orchestrator.get_pending_escalations.return_value = mock_escalations
            mock_orchestrator_class.return_value = mock_orchestrator

            response = client.get("/api/v1/escalations/pending?user_role=hr_ops")

            assert response.status_code == 200
            data = response.json()
            assert "escalations" in data
            assert len(data["escalations"]) == 1
            assert data["escalations"][0]["escalation_type"] == "UNKNOWN_JURISDICTION"

    def test_get_pending_escalations_unauthorized(self, client):
        """Test getting pending escalations without proper access."""
        response = client.get("/api/v1/escalations/pending?user_role=agent")

        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    def test_resolve_escalation_success(self, client):
        """Test resolving an escalation successfully."""
        resolution_payload = SAMPLE_WEBHOOK_PAYLOADS["escalation_resolution"]

        with patch("src.api.endpoints.OrchestratorAgent") as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.resolve_escalation.return_value = True
            mock_orchestrator_class.return_value = mock_orchestrator

            response = client.post(
                "/api/v1/escalations/esc_001/resolve?user_role=hr_ops",
                json=resolution_payload
            )

            assert response.status_code == 200
            assert "resolved" in response.json()["message"]

            # Verify orchestrator was called correctly
            mock_orchestrator.resolve_escalation.assert_called_once_with(
                "esc_001",
                "approved",
                {"compliance_track": "Standard US Compliance"},
                "hr_ops_user"
            )

    def test_resolve_escalation_not_found(self, client):
        """Test resolving a non-existent escalation."""
        resolution_payload = SAMPLE_WEBHOOK_PAYLOADS["escalation_resolution"]

        with patch("src.api.endpoints.OrchestratorAgent") as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.resolve_escalation.return_value = False
            mock_orchestrator_class.return_value = mock_orchestrator

            response = client.post(
                "/api/v1/escalations/esc_999/resolve?user_role=hr_ops",
                json=resolution_payload
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_resolve_escalation_unauthorized(self, client):
        """Test resolving escalation without proper permissions."""
        resolution_payload = SAMPLE_WEBHOOK_PAYLOADS["escalation_resolution"]

        response = client.post(
            "/api/v1/escalations/esc_001/resolve?user_role=agent",
            json=resolution_payload
        )

        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]


class TestErrorHandling:
    """Test cases for error handling."""

    def test_invalid_json_payload(self, client):
        """Test handling of invalid JSON payloads."""
        response = client.post(
            "/webhooks/workday/new-hire",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400

    def test_method_not_allowed(self, client):
        """Test handling of incorrect HTTP methods."""
        response = client.put("/api/v1/health")

        assert response.status_code == 405

    def test_not_found_endpoint(self, client):
        """Test handling of non-existent endpoints."""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == 404