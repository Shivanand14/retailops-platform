"""
RetailOps Platform — Order Service (FastAPI)

Production-grade microservice demonstrating:
  - Structured logging with request IDs
  - Prometheus metrics (RED: Rate, Errors, Duration)
  - Health / readiness / liveness endpoints
  - Graceful shutdown
  - Pydantic request/response validation
  - Distributed tracing context propagation
"""

from __future__ import annotations

import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

# --------------------------------------------------------------------------- #
# Prometheus metrics (RED method)
# --------------------------------------------------------------------------- #
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "service", "status"],
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "service"],
)

SERVICE_NAME = os.getenv("SERVICE_NAME", "order-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")


# --------------------------------------------------------------------------- #
# Pydantic schemas
# --------------------------------------------------------------------------- #
class OrderItem(BaseModel):
    product_id: str = Field(..., min_length=1, max_length=64)
    quantity: int = Field(..., ge=1, le=100)
    unit_price: float = Field(..., ge=0)


class OrderCreate(BaseModel):
    customer_id: str = Field(..., min_length=1, max_length=64)
    items: list[OrderItem] = Field(..., min_length=1, max_length=50)


class OrderResponse(BaseModel):
    order_id: str
    customer_id: str
    status: str
    total_amount: float
    created_at: str
    service: str
    version: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


# --------------------------------------------------------------------------- #
# Application lifecycle
# --------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    # Startup
    print(f"[order-service] Starting {SERVICE_NAME} v{SERVICE_VERSION}")
    yield
    # Shutdown
    print(f"[order-service] Shutting down {SERVICE_NAME}")


app = FastAPI(
    title="Order Service",
    description="RetailOps order processing microservice",
    version=SERVICE_VERSION,
    lifespan=lifespan,
)


# --------------------------------------------------------------------------- #
# Middleware: request ID + metrics
# --------------------------------------------------------------------------- #
@app.middleware("http")
async def metrics_and_request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id

    start_time = time.time()
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        status_code = 500
        raise
    finally:
        duration = time.time() - start_time
        endpoint = request.url.path
        method = request.method

        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            service=SERVICE_NAME,
            status=str(status_code),
        ).inc()
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint,
            service=SERVICE_NAME,
        ).observe(duration)

        response.headers["x-request-id"] = request_id
        response.headers["x-service"] = SERVICE_NAME
        return response


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@app.get("/healthz", response_model=HealthResponse, tags=["health"])
async def liveness():
    """Kubernetes liveness probe."""
    return HealthResponse(
        status="healthy", service=SERVICE_NAME, version=SERVICE_VERSION
    )


@app.get("/ready", response_model=HealthResponse, tags=["health"])
async def readiness():
    """Kubernetes readiness probe."""
    # In production, check DB / downstream dependencies here
    return HealthResponse(status="ready", service=SERVICE_NAME, version=SERVICE_VERSION)


@app.get("/metrics", tags=["observability"])
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/orders", response_model=OrderResponse, status_code=201, tags=["orders"])
async def create_order(order: OrderCreate, request: Request):
    """Create a new order."""
    request_id = request.state.request_id

    # Simulate business logic
    total_amount = sum(item.quantity * item.unit_price for item in order.items)
    order_id = f"ORD-{int(time.time())}-{request_id[:8]}"

    # Structured log (JSON-friendly for Loki)
    print(
        f'{{"event":"order_created","order_id":"{order_id}","customer_id":"{order.customer_id}",'
        f'"total_amount":{total_amount},"request_id":"{request_id}","service":"{SERVICE_NAME}"}}'
    )

    return OrderResponse(
        order_id=order_id,
        customer_id=order.customer_id,
        status="confirmed",
        total_amount=round(total_amount, 2),
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
    )


@app.get("/orders/{order_id}", response_model=OrderResponse, tags=["orders"])
async def get_order(order_id: str):
    """Retrieve an order by ID (mock implementation)."""
    raise HTTPException(status_code=404, detail="Order not found (demo mode)")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
