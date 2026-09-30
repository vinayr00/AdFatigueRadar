"""
backend/api/routes_webhooks.py
--------------------------------
POST /webhooks/slack/test — test Slack webhook.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from backend.api.auth import verify_api_key

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/slack/test")
async def slack_test(_: None = Depends(verify_api_key)) -> JSONResponse:
    """P0 stub — returns success. Real Slack integration in P1."""
    return JSONResponse(content={"sent": True, "note": "Slack webhook stub — P1 integration pending"})
