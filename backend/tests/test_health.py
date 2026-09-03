"""
IntelliVault ~ Backend Health and Diagnostics Unit Tests
"""

import pytest
from backend.app import create_app


@pytest.fixture
def client():
    """Provides a test client with testing configuration."""
    app = create_app(config_name="testing")
    with app.test_client() as client:
        yield client


def test_liveness_endpoint(client):
    """Verifies that GET /api/health returns HTTP 200 with healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert data["data"]["service"] == "IntelliVault API"
    assert "timestamp" in data


def test_system_readiness_endpoint(client):
    """Verifies that GET /api/system/status returns diagnostic details."""
    response = client.get("/api/system/status")
    assert response.status_code == 200

    data = response.get_json()
    assert data["success"] is True
    assert "status" in data["data"]
    assert "services" in data["data"]
    assert "database" in data["data"]["services"]
    assert "storage" in data["data"]["services"]
    assert "platform" in data["data"]


def test_not_found_endpoint(client):
    """Verifies that unknown routes return standardized JSON 404 error envelope."""
    response = client.get("/api/non_existent_endpoint")
    assert response.status_code == 404

    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"


def test_method_not_allowed(client):
    """Verifies that unpermitted HTTP methods return standardized JSON 405 error envelope."""
    response = client.post("/api/health")
    assert response.status_code == 405

    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "METHOD_NOT_ALLOWED"
