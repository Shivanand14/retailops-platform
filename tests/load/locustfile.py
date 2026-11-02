"""
RetailOps Platform — Load Test (Locust)

Run with:
    locust -f tests/load/locustfile.py --host http://localhost:80

Usage:
    1. Port-forward the ingress or API gateway: kubectl port-forward svc/order-service 8080:80 -n retailops
    2. Run: locust -f tests/load/locustfile.py --host http://localhost:8080
    3. Open http://localhost:8089 (Locust web UI)
"""

from locust import HttpUser, task, between
import random


class RetailOpsUser(HttpUser):
    """Simulated user placing orders and checking inventory."""

    wait_time = between(1, 3)
    host = "http://localhost:8080"

    @task(3)
    def create_order(self):
        """POST /orders — simulate order creation."""
        payload = {
            "customer_id": f"CUST-{random.randint(1000, 9999)}",
            "items": [
                {
                    "product_id": f"PROD-{random.randint(1, 100)}",
                    "quantity": random.randint(1, 5),
                    "unit_price": round(random.uniform(10.0, 500.0), 2),
                }
                for _ in range(random.randint(1, 3))
            ],
        }
        with self.client.post("/orders", json=payload, catch_response=True) as response:
            if response.status_code in (200, 201):
                response.success()
            else:
                response.failure(f"Order creation failed: {response.status_code}")

    @task(2)
    def check_inventory(self):
        """POST /inventory/check — simulate inventory lookup."""
        payload = {
            "product_id": f"PROD-{random.randint(1, 100)}",
            "quantity": random.randint(1, 10),
        }
        with self.client.post("/inventory/check", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Inventory check failed: {response.status_code}")

    @task(1)
    def health_check(self):
        """GET /healthz — synthetic health probe."""
        self.client.get("/healthz")


class ChaosUser(HttpUser):
    """Lower-frequency user to simulate background traffic during chaos tests."""

    wait_time = between(5, 15)
    host = "http://localhost:8080"

    @task
    def steady_health(self):
        self.client.get("/healthz")
