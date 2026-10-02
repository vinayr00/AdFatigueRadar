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


def _context_or_404(campaign_id: str):
    registry = get_registry()
    ctx = registry.get(campaign_id)
    if ctx is None:
        from backend.db.repository import repository
        if repository.get_campaign_state(campaign_id) is not None:
            ctx = registry.get_or_create(campaign_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")
    return ctx


@router.get("/{campaign_id}/status")
async def get_status(campaign_id: str) -> JSONResponse:
    ctx = _context_or_404(campaign_id)

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
    ctx = _context_or_404(campaign_id)
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
    ctx = _context_or_404(campaign_id)
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
    ctx = _context_or_404(campaign_id)

    async def event_generator() -> AsyncIterator[str]:
        seen_comments: set[str] = set()
        last_state = None
        last_alert_signature = None
        try:
            while True:
                with ctx.lock:
                    latest = ctx.runner.latest_tick
                    comments = ctx.machine.aggregator.get_window_comments()
                if latest:
                    data = json.dumps({
                        "state": latest.state.value,
                        "severity": latest.severity.value,
                        "audience_risk": latest.audience_risk,
                        "economic_risk": latest.economic_risk,
                        "sim_time": ctx.machine.aggregator.clock.current.isoformat() if ctx.machine.aggregator.clock.current else None,
                        "is_running": ctx.runner.is_running(),
                    })
                    yield f"event: STEP_UPDATE\ndata: {data}\n\n"
                    if latest.state.value != last_state:
                        last_state = latest.state.value
                        yield f"event: STATE_CHANGE\ndata: {data}\n\n"
                    for comment in comments:
                        if comment.event_id in seen_comments:
                            continue
                        seen_comments.add(comment.event_id)
                        comment_data = json.dumps({"event_id": comment.event_id,
                            "timestamp": comment.timestamp.isoformat(), "campaign_id": comment.campaign_id,
                            "ad_id": comment.ad_id, "text": comment.text, "sentiment": comment.sentiment,
                            "sentiment_score": comment.sentiment_score, "category": comment.category,
                            "confidence": comment.confidence, "critical_complaint": comment.critical_complaint})
                        yield f"event: COMMENT\ndata: {comment_data}\n\n"
                    alert_signature = (latest.severity.value, latest.stale, latest.anomaly)
                    if (latest.severity.value in {"WARNING", "CRITICAL"} or latest.stale or latest.anomaly) and alert_signature != last_alert_signature:
                        last_alert_signature = alert_signature
                        yield f"event: ALERT\ndata: {data}\n\n"
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


@router.get("/{campaign_id}/replay/snapshot")
async def replay_snapshot(campaign_id: str) -> JSONResponse:
    """Frontend adapter over recorded simulation ticks; unavailable potential-world values are null."""
    ctx = _context_or_404(campaign_id)
    timeline = ctx.runner.get_timeline()
    points = []
    first_ts = datetime.fromisoformat(timeline[0]["sim_time"]) if timeline else None
    for item in timeline:
        sim_time = datetime.fromisoformat(item["sim_time"])
        spend = item.get("observed_spend")
        impressions = item.get("observed_impressions")
        clicks = item.get("observed_clicks")
        conversions = item.get("observed_conversions")
        points.append({
            "hour": (sim_time-first_ts).total_seconds()/3600 if first_ts else 0,
            "timestamp_simulated": sim_time.isoformat(),
            "potential_impressions": None, "observed_impressions": impressions,
            "potential_spend": None, "observed_spend": spend,
            "audience_risk": item["audience_risk"], "economic_risk": item["economic_risk"],
            "cpa": spend/conversions if conversions else None,
            "cpm": item.get("cpm"),
            "state": item["state"], "events": item.get("reason_codes", []),
            "action_applied": item.get("action_events", [None])[-1] if item.get("action_events") else None,
            "signals": item.get("signal_breakdown", {}), "stale": item.get("stale", False),
        })
    agg = ctx.machine.aggregator
    comments = [{"event_id": c.event_id, "timestamp": c.timestamp.isoformat(), "campaign_id": c.campaign_id,
                 "ad_id": c.ad_id, "text": c.text, "sentiment": c.sentiment, "sentiment_score": c.sentiment_score,
                 "category": c.category, "confidence": c.confidence, "critical_complaint": c.critical_complaint}
                for c in agg.get_window_comments() if c.sentiment is not None]
    now = agg.clock.current
    start = first_ts
    audits = ctx.audit_log.get_all()
    return JSONResponse(content={
        "campaign_id": campaign_id, "scenario_name": campaign_id, "seed": 0,
        "current_hour": points[-1]["hour"] if points else 0,
        "simulated_timestamp": now.isoformat() if now else None,
        "is_running": ctx.runner.is_running(), "speed": ctx.runner.speed,
        "current_state": ctx.machine.state.value,
        "previous_state": None,
        "state_reason": ", ".join(points[-1].get("events", [])) if points else None,
        "points": points, "live_comments": comments,
        "actions_history": [{"id": e.audit_id, "action": e.action, "mode": "SANDBOX",
            "executed": bool(e.readback_verified), "confidence": e.confidence or 0,
            "reason": e.action.replace("_", " ").title(),
            "previous_state": e.previous_state.value if e.previous_state else e.new_state.value if e.new_state else "ACTIVE",
            "new_state": e.new_state.value if e.new_state else "ACTIVE",
            "readback_verified": bool(e.readback_verified), "audit_event_id": e.audit_id,
            "timestamp": e.timestamp_simulated.isoformat()} for e in audits if e.action in {"PAUSE", "UNPAUSE", "SOFT_REDUCTION", "SOFT_RECOVERY"}],
        "audit_trail": [e.model_dump(mode="json") for e in audits],
    })


@router.get("/{campaign_id}/audit")
async def get_audit(campaign_id: str, limit: int = Query(default=100, ge=1, le=1000)) -> JSONResponse:
    ctx = _context_or_404(campaign_id)
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


@router.post("/{campaign_id}/replay/pause")
async def replay_pause(campaign_id: str, _: None = Depends(verify_api_key)) -> JSONResponse:
    ctx = _context_or_404(campaign_id)
    if not ctx.runner.pause():
        raise HTTPException(status_code=409, detail="Replay is not running")
    return JSONResponse(content={"paused": True, "campaign_id": campaign_id})


@router.post("/{campaign_id}/replay/resume")
async def replay_resume(campaign_id: str, _: None = Depends(verify_api_key)) -> JSONResponse:
    ctx = _context_or_404(campaign_id)
    if not ctx.runner.resume():
        raise HTTPException(status_code=409, detail="Replay is not paused")
    return JSONResponse(content={"resumed": True, "campaign_id": campaign_id})
