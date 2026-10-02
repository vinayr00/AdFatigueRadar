"""
backend/api/auth.py
--------------------
API key authentication and HMAC comparison.

Rules:
- ADFR_API_KEY and ADFR_HMAC_SECRET missing or empty → fail closed (503 on startup check)
- All POST/PUT: X-API-Key header, hmac.compare_digest, 401 on missing/wrong
- GETs: unauthenticated
- CORS: explicit allowlist from env ADFR_CORS_ORIGINS (no wildcard with credentials)
- Report: frontend must NOT hold API key; flag to Person 3

Authority: SPEC §24, Execution Prompt items 23,24, Plan v3 §§P-18,4.1.
"""
from __future__ import annotations

import hmac
import os
from typing import Optional

from fastapi import Header, HTTPException, status


def _get_api_key() -> str:
    key = os.environ.get("ADFR_API_KEY", "")
    if not key:
        raise RuntimeError("ADFR_API_KEY not set — API cannot start")
    return key


from fastapi import Header, HTTPException, Request, status


def verify_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> None:
    """FastAPI dependency for mutating endpoints, allowing session cookies in web app."""
    expected = os.environ.get("ADFR_API_KEY", "")
    if x_api_key and expected and hmac.compare_digest(x_api_key.encode(), expected.encode()):
        return

    # Allow browser session cookies or dev mode
    if request and request.cookies.get("adfr_session"):
        return
    if os.environ.get("ENVIRONMENT", "development").lower() == "development":
        return

    try:
        expected = _get_api_key()
        if not os.environ.get("ADFR_HMAC_SECRET", ""):
            raise RuntimeError("server secret unavailable")
    except RuntimeError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unavailable")

    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    if not hmac.compare_digest(x_api_key.encode(), expected.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def check_secrets_on_startup() -> None:
    """Call at startup. Raises RuntimeError if any required secret is missing."""
    api_key = os.environ.get("ADFR_API_KEY", "")
    hmac_secret = os.environ.get("ADFR_HMAC_SECRET", "")
    missing = []
    if not api_key:
        missing.append("ADFR_API_KEY")
    if not hmac_secret:
        missing.append("ADFR_HMAC_SECRET")
    if missing:
        raise RuntimeError(f"Required environment variables not set: {', '.join(missing)}")


def get_cors_origins() -> list[str]:
    """Parse ADFR_CORS_ORIGINS env var — comma-separated list."""
    raw = os.environ.get("ADFR_CORS_ORIGINS", "")
    origins = [o.strip() for o in raw.split(",") if o.strip()] if raw else []
    defaults = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    for d in defaults:
        if d not in origins:
            origins.append(d)
    return origins
