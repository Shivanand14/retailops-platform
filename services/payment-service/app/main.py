"""
RetailOps Platform — Payment Service (FastAPI)
"""
from __future__ import annotations

import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

SERVICE_NAME = os.getenv("SERVICE_NAME", "payment-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")

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


class PaymentRequest(BaseModel):
    order_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    amount: float = Field(..., ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class PaymentResponse(BaseModel):
    payment_id: str
    order_id: str
    status: str
    amount: float
    currency: str
    processed_at: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[payment-service] Starting {SERVICE_NAME} v{SERVICE_VERSION}")
    yield
    print(f"[payment-service] Shutting down {SERVICE_NAME}")


app = FastAPI(title="Payment Service", version=SERVICE_VERSION, lifespan=lifespan)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    start = time.time()
    try:
        response = await call_next(request)
        status = response.status_code
    except Exception:
        status = 500
        raise
    finally:
        duration = time.time() - start
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            service=SERVICE_NAME,
            status=str(status),
        ).inc()
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path,
            service=SERVICE_NAME,
        ).observe(duration)
        response.headers["x-request-id"] = request_id
        return response


@app.get("/healthz", response_model=HealthResponse, tags=["health"])
async def liveness():
    return HealthResponse(status="healthy", service=SERVICE_NAME, version=SERVICE_VERSION)


@app.get("/ready", response_model=HealthResponse, tags=["health"])
async def readiness():
    return HealthResponse(status="ready", service=SERVICE_NAME, version=SERVICE_VERSION)


@app.get("/metrics", tags=["observability"])
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/payments", response_model=PaymentResponse, status_code=201, tags=["payments"])
async def process_payment(payment: PaymentRequest, request: Request):
    request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())
    payment_id = f"PAY-{int(time.time())}-{request_id[:8]}"

    print(
        f'{{"event":"payment_processed","payment_id":"{payment_id}","order_id":"{payment.order_id}",'
        f'"amount":{payment.amount},"currency":"{payment.currency}","request_id":"{request_id}"}}'
    )

    return PaymentResponse(
        payment_id=payment_id,
        order_id=payment.order_id,
        status="succeeded",
        amount=payment.amount,
        currency=payment.currency,
        processed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
