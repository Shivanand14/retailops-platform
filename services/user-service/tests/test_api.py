from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_service_status():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "user-service"


def test_get_user_returns_profile():
    response = client.get("/users/customer-1")

    assert response.status_code == 200
    assert response.json() == {
        "user_id": "customer-1",
        "email": "customer-1@retailops.local",
        "tier": "standard",
    }
