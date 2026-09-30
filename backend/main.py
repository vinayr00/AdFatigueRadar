"""
backend/main.py
----------------
FastAPI application entry point.

Startup: check required secrets, mount CORS, set security headers.
Authority: Plan v3 §§4.1,5,P-18.
"""
from __future__ import annotations

import os

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.auth import check_secrets_on_startup, get_cors_origins
from backend.api import routes_campaigns, routes_actions, routes_thresholds, routes_webhooks

app = FastAPI(
    title="AdFatigueRadar — Person 2 Backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)


@app.exception_handler(Exception)
async def safe_internal_error(request: Request, exc: Exception) -> JSONResponse:
    """Return JSON without exception text or traceback leakage."""
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# ---------------------------------------------------------------------------
# CORS — explicit allowlist, no wildcard with credentials (P-18)
# ---------------------------------------------------------------------------
origins = get_cors_origins()
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["X-API-Key", "Content-Type"],
    )


# ---------------------------------------------------------------------------
# Security headers on every response
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next: object) -> Response:
    response: Response = await call_next(request)  # type: ignore[arg-type,misc]
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


# ---------------------------------------------------------------------------
# Startup check
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup() -> None:
    try:
        check_secrets_on_startup()
    except RuntimeError as e:
        # Log and allow startup to fail — will return 503 on all authenticated calls
        print(f"[STARTUP WARNING] {e}")


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(routes_campaigns.router)
app.include_router(routes_actions.router)
app.include_router(routes_thresholds.router)
app.include_router(routes_webhooks.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
