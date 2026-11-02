from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_service_status():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "inventory-service"


def test_inventory_check_reports_availability():
    response = client.post(
        "/inventory/check",
        json={"product_id": "product-1", "quantity": 3},
    )

    assert response.status_code == 200
    assert response.json()["product_id"] == "product-1"
    assert response.json()["available"] is True
    assert response.json()["quantity_on_hand"] == 100


def test_inventory_check_rejects_zero_quantity():
    response = client.post(
        "/inventory/check",
        json={"product_id": "product-1", "quantity": 0},
    )

    assert response.status_code == 422
