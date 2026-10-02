"""
backend/api/routes_actions.py
------------------------------
Operator action routes.

POST /campaigns/{id}/pause       (API key required)
POST /campaigns/{id}/unpause     (API key required)
POST /campaigns/{id}/override    (API key required — P0: BLOCK/UNBLOCK only)

Authority: SPEC §§14,15, Execution Prompt items 12,19,20, Plan v3 §§P-11,P-12.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from backend.api.auth import verify_api_key
from backend.api.campaign_registry import get_registry
from backend.models.backend_models import OverrideRequest, ReasonCode, RiskSnapshot

router = APIRouter(prefix="/campaigns", tags=["actions"])


def _context(campaign_id: str):
    registry = get_registry()
    ctx = registry.get(campaign_id)
    if ctx is None:
        from backend.db.repository import repository
        if repository.get_campaign_state(campaign_id) is not None:
            ctx = registry.get_or_create(campaign_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="Unknown campaign")
    return ctx


def _now_sim(campaign_id: str) -> datetime:
    """Return only campaign simulated time; wall time is not business time."""
    reg = get_registry()
    ctx = reg.get(campaign_id)
    if ctx and ctx.latest_sim_time:
        return ctx.latest_sim_time
    if ctx:
        current = ctx.machine.aggregator.clock.current
        if current is not None:
            return current
    raise HTTPException(status_code=409, detail="Campaign simulation clock has not started")


@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: str,
    _: None = Depends(verify_api_key),
) -> JSONResponse:
    ctx = _context(campaign_id)

    with ctx.lock:
        now = _now_sim(campaign_id)
        risk = RiskSnapshot(audience_risk=0.0, economic_risk=None)
        if ctx.runner.latest_tick:
            risk = RiskSnapshot(
                audience_risk=ctx.runner.latest_tick.audience_risk,
                economic_risk=ctx.runner.latest_tick.economic_risk,
            )
        result = ctx.runner._adapter.operator_pause(now, risk, config_version=ctx.machine.config_version)
        from backend.db.repository import repository
        repository.save_campaign_state(campaign_id, ctx.machine.state.value,
            ctx.machine.pre_block_state.value if ctx.machine.pre_block_state else None)
        repository.save_action(campaign_id, result, now)
        ctx.runner.record_action_reference(now, result)

    return JSONResponse(content=result.model_dump(mode="json"))


@router.post("/{campaign_id}/unpause")
async def unpause_campaign(
    campaign_id: str,
    _: None = Depends(verify_api_key),
) -> JSONResponse:
    ctx = _context(campaign_id)

    with ctx.lock:
        now = _now_sim(campaign_id)
        risk = RiskSnapshot(audience_risk=0.0, economic_risk=None)
        if ctx.runner.latest_tick:
            risk = RiskSnapshot(
                audience_risk=ctx.runner.latest_tick.audience_risk,
                economic_risk=ctx.runner.latest_tick.economic_risk,
            )
        try:
            result = ctx.runner._adapter.operator_unpause(now, risk, config_version=ctx.machine.config_version)
            from backend.db.repository import repository
            repository.save_campaign_state(campaign_id, ctx.machine.state.value,
                ctx.machine.pre_block_state.value if ctx.machine.pre_block_state else None)
            repository.save_action(campaign_id, result, now)
            ctx.runner.record_action_reference(now, result)
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

    return JSONResponse(content=result.model_dump(mode="json"))


@router.post("/{campaign_id}/override")
async def override_campaign(
    campaign_id: str,
    body: OverrideRequest,
    _: None = Depends(verify_api_key),
) -> JSONResponse:
    """P0: BLOCK and UNBLOCK only."""
    action = body.action.upper()
    if action not in ("BLOCK", "UNBLOCK"):
        raise HTTPException(status_code=422, detail="Only BLOCK and UNBLOCK supported in P0")

    ctx = _context(campaign_id)

    with ctx.lock:
        now = _now_sim(campaign_id)
        risk = RiskSnapshot(audience_risk=0.0, economic_risk=None)
        if ctx.runner.latest_tick:
            risk = RiskSnapshot(
                audience_risk=ctx.runner.latest_tick.audience_risk,
                economic_risk=ctx.runner.latest_tick.economic_risk,
            )
        if action == "BLOCK":
            result = ctx.runner._adapter.operator_block(now, risk, config_version=ctx.machine.config_version)
        else:
            try:
                result = ctx.runner._adapter.operator_unblock(now, risk, config_version=ctx.machine.config_version)
            except ValueError as e:
                raise HTTPException(status_code=409, detail=str(e))
        from backend.db.repository import repository
        repository.save_campaign_state(campaign_id, ctx.machine.state.value,
            ctx.machine.pre_block_state.value if ctx.machine.pre_block_state else None)
        repository.save_action(campaign_id, result, now)
        ctx.runner.record_action_reference(now, result)

    return JSONResponse(content=result.model_dump(mode="json"))
