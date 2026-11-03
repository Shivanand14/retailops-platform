from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_service_status():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "payment-service"


def test_process_payment_returns_payment_details():
    response = client.post(
        "/payments",
        json={
            "order_id": "order-1",
            "customer_id": "customer-1",
            "amount": 49.99,
            "currency": "USD",
        },
    )

    assert response.status_code == 201
    assert response.json()["order_id"] == "order-1"
    assert response.json()["amount"] == 49.99
    assert response.json()["status"] == "succeeded"


def test_process_payment_rejects_negative_amount():
    response = client.post(
        "/payments",
        json={
            "order_id": "order-1",
            "customer_id": "customer-1",
            "amount": -1,
        },
    )

    assert response.status_code == 422
