from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_service_status():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "order-service"


def test_create_order_calculates_total_and_propagates_request_id():
    response = client.post(
        "/orders",
        headers={"x-request-id": "ci-order-request"},
        json={
            "customer_id": "customer-1",
            "items": [
                {"product_id": "product-1", "quantity": 2, "unit_price": 49.99},
                {"product_id": "product-2", "quantity": 1, "unit_price": 199.99},
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["total_amount"] == 299.97
    assert response.json()["status"] == "confirmed"
    assert response.headers["x-request-id"] == "ci-order-request"


def test_create_order_rejects_empty_items():
    response = client.post(
        "/orders",
        json={"customer_id": "customer-1", "items": []},
    )

    assert response.status_code == 422
