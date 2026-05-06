from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_openapi_available():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Voice-Pro API"


def test_health_response_shape():
    """Verify /health returns the expected keys regardless of dependency state."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "db" in data
    assert "redis" in data
    assert data["status"] in ("ok", "degraded")
    assert data["db"] in ("connected", "disconnected")
    assert data["redis"] in ("connected", "disconnected")
