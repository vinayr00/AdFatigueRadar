"""
backend/api/routes_campaigns.py
--------------------------------
Read-only campaign routes + replay control.

GET /campaigns/{id}/status
GET /campaigns/{id}/timeline
GET /campaigns/{id}/stream   (SSE)
GET /campaigns/{id}/audit
POST /campaigns/{id}/replay/start?speed=  (API key required)
POST /campaigns/{id}/replay/reset         (API key required)

Authority: Plan v3 §5, Execution Prompt items 25,26, P-03, P-18.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse

from backend.api.auth import verify_api_key
from backend.api.campaign_registry import get_registry
from backend.models.backend_models import CommentSummary, StatusResponse, TimelinePoint, SignalBreakdown, Severity

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("/{campaign_id}/status")
async def get_status(campaign_id: str) -> JSONResponse:
    reg = get_registry()
    ctx = reg.get(campaign_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")

    machine = ctx.machine
    lock = ctx.lock

    with lock:
        state = machine.state
        # Build a quick status from latest tick result if available
        latest = ctx.runner.latest_tick
        if latest is None:
            return JSONResponse(content={
                "campaign_id": campaign_id,
                "state": state.value,
                "severity": "HEALTHY",
                "audience_risk": 0.0,
                "economic_risk": None,
                "signal_breakdown": {},
                "stale": False,
                "anomaly": False,
                "cooldown_remaining_minutes": None,
                "config_version": machine.config_version,
                "reason_codes": [],
                "sim_time": None,
                "action_unverified": machine.action_unverified,
            })

        return JSONResponse(content={
            "campaign_id": campaign_id,
            "state": latest.state.value,
            "severity": latest.severity.value,
            "audience_risk": latest.audience_risk,
            "economic_risk": latest.economic_risk,
            "signal_breakdown": {
                k: v for k, v in {
                    "harmful_negative_ratio": latest.signals.harmful_negative_ratio,
                    "sentiment_decay": latest.signals.sentiment_decay,
                    "fatigue_mockery": latest.signals.fatigue_mockery,
                    "comment_acceleration": latest.signals.comment_acceleration,
                    "ctr_frequency": latest.signals.ctr_frequency,
                    "critical_complaint_signal": latest.signals.critical_complaint_signal,
                    "cpa_cpm_signal": latest.signals.cpa_cpm_signal,
                    "roas_conversion_signal": latest.signals.roas_conversion_signal,
                }.items()
            },
            "stale": latest.stale,
            "anomaly": latest.anomaly,
            "cooldown_remaining_minutes": latest.cooldown_remaining_minutes or None,
            "config_version": machine.config_version,
            "reason_codes": [r.value for r in latest.reason_codes],
            "sim_time": machine.aggregator.clock.current.isoformat() if machine.aggregator.clock.current else None,
            "action_unverified": machine.action_unverified,
        })


@router.get("/{campaign_id}/timeline")
async def get_timeline(campaign_id: str) -> JSONResponse:
    reg = get_registry()
    ctx = reg.get(campaign_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")
    runner = ctx.runner
    if runner is None:
        return JSONResponse(content={"campaign_id": campaign_id, "timeline": []})
    return JSONResponse(content={
        "campaign_id": campaign_id,
        "timeline": runner.get_timeline(),
    })


@router.get("/{campaign_id}/comments")
async def get_comments(
    campaign_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
) -> JSONResponse:
    """Return recent rolling-window comment/NLP fields without author identity."""
    reg = get_registry()
    ctx = reg.get(campaign_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")
    with ctx.lock:
        comments = ctx.machine.aggregator.get_window_comments()[-limit:]
        payload = [
            CommentSummary(
                event_id=item.event_id,
                timestamp=item.timestamp,
                campaign_id=item.campaign_id,
                ad_id=item.ad_id,
                text=item.text,
                sentiment=item.sentiment,
                sentiment_score=item.sentiment_score,
                category=item.category,
                confidence=item.confidence,
                critical_complaint=item.critical_complaint,
            ).model_dump(mode="json")
            for item in comments
        ]
    return JSONResponse(content={"campaign_id": campaign_id, "comments": payload})


@router.get("/{campaign_id}/stream")
async def stream_status(campaign_id: str) -> StreamingResponse:
    """SSE stream — event: status|action|heartbeat, JSON data, keepalive comment."""
    reg = get_registry()
    ctx = reg.get(campaign_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")

    async def event_generator() -> AsyncIterator[str]:
        try:
            while True:
                with ctx.lock:
                    latest = ctx.runner.latest_tick
                if latest:
                    data = json.dumps({
                        "state": latest.state.value,
                        "severity": latest.severity.value,
                        "audience_risk": latest.audience_risk,
                        "economic_risk": latest.economic_risk,
                    })
                    yield f"event: status\ndata: {data}\n\n"
                else:
                    yield ": keepalive\n\n"
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass  # tolerate client disconnect

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


@router.get("/{campaign_id}/audit")
async def get_audit(campaign_id: str, limit: int = Query(default=100, ge=1, le=1000)) -> JSONResponse:
    reg = get_registry()
    ctx = reg.get(campaign_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")
    entries = ctx.audit_log.get_latest(limit)
    return JSONResponse(content={
        "campaign_id": campaign_id,
        "audit_events": [e.model_dump(mode="json") for e in entries],
    })


@router.post("/{campaign_id}/replay/start")
async def replay_start(
    campaign_id: str,
    speed: float = Query(default=1.0, gt=0, le=1000),
    _: None = Depends(verify_api_key),
) -> JSONResponse:
    reg = get_registry()
    ctx = reg.get_or_create(campaign_id)
    runner = ctx.runner
    with ctx.lock:
        if runner.is_running():
            raise HTTPException(status_code=409, detail="Replay already running for this campaign")
        # Default source is read-only; API does not own replay generation.
        from backend.replay.file_source import FileReplaySource
        source = FileReplaySource(campaign_id)
        try:
            runner.start(source, speed=speed)
        except PermissionError:
            raise HTTPException(status_code=503, detail="Service unavailable")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

    return JSONResponse(content={"started": True, "campaign_id": campaign_id, "speed": speed})


@router.post("/{campaign_id}/replay/reset")
async def replay_reset(
    campaign_id: str,
    _: None = Depends(verify_api_key),
) -> JSONResponse:
    reg = get_registry()
    ctx = reg.get_or_create(campaign_id)
    try:
        ctx.runner.reset()
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    with ctx.lock:
        ctx.latest_tick = None
        ctx.latest_sim_time = None
    return JSONResponse(content={"reset": True, "campaign_id": campaign_id})
