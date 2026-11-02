"""
RetailOps Platform — User Service (FastAPI)
"""
from __future__ import annotations

import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

SERVICE_NAME = os.getenv("SERVICE_NAME", "user-service")
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


class UserProfile(BaseModel):
    user_id: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    tier: str = Field(default="standard")


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[user-service] Starting {SERVICE_NAME} v{SERVICE_VERSION}")
    yield
    print(f"[user-service] Shutting down {SERVICE_NAME}")


app = FastAPI(title="User Service", version=SERVICE_VERSION, lifespan=lifespan)


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


@app.get("/users/{user_id}", response_model=UserProfile, tags=["users"])
async def get_user(user_id: str):
    return UserProfile(user_id=user_id, email=f"{user_id}@retailops.local", tier="standard")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
