"""
backend/api/routes_thresholds.py
----------------------------------
PUT /campaigns/{id}/thresholds — runtime threshold override.

Rules (P-17):
- Only keys in threshold_mutable_keys allowlist → 422 for others
- Safe bounds validation → 422
- Gate ordering and recovery thresholds → 422
- Never rewrites config/thresholds.yaml
- Applies from NEXT tick boundary
- Resets persistence trackers
- Bumps config_version
- Audits old/new values with actor

Authority: SPEC §17, Execution Prompt item 13, Plan v3 §§P-17,4.2.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from backend.api.auth import verify_api_key
from backend.api.campaign_registry import get_registry
from backend.api.threshold_validator import ThresholdValidationError, validate_overrides
from backend.models.backend_models import ActorType, ReasonCode, RiskSnapshot, ThresholdOverrideRequest
from backend.risk.config_loader import get_config

router = APIRouter(prefix="/campaigns", tags=["thresholds"])


@router.get("/{campaign_id}/thresholds")
async def get_thresholds(campaign_id: str) -> JSONResponse:
    """Read the campaign's effective threshold configuration and override bounds."""
    reg = get_registry()
    ctx = reg.get(campaign_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="Unknown campaign")
    with ctx.lock:
        cfg = ctx.machine._cfg
        return JSONResponse(content={
            "campaign_id": campaign_id,
            "config_version": ctx.machine.config_version,
            "effective_config": cfg,
            "threshold_mutable_keys": cfg["threshold_mutable_keys"],
            "safe_bounds": cfg["safe_bounds"],
        })


@router.put("/{campaign_id}/thresholds")
async def update_thresholds(
    campaign_id: str,
    body: ThresholdOverrideRequest,
    _: None = Depends(verify_api_key),
) -> JSONResponse:
    reg = get_registry()
    ctx = reg.get(campaign_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="Unknown campaign")

    # Validate against the campaign's layered configuration.
    try:
        errors = validate_overrides(body.overrides, ctx.machine._cfg)
    except ThresholdValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if errors:
        raise HTTPException(status_code=422, detail="; ".join(errors))

    with ctx.lock:
        now = ctx.latest_sim_time or ctx.machine.aggregator.clock.current
        if now is None:
            raise HTTPException(status_code=409, detail="Campaign simulation clock has not started")
        # Snapshot old values for audit
        old_values = {
            k: _get_nested(ctx.machine._cfg, k)
            for k in body.overrides
        }
        # Apply override and reset persistence trackers
        ctx.machine.apply_threshold_override(body.overrides)
        new_config_version = ctx.machine.config_version

        # Audit the change
        risk = RiskSnapshot(
            audience_risk=ctx.runner.latest_tick.audience_risk if ctx.runner.latest_tick else 0.0,
            economic_risk=ctx.runner.latest_tick.economic_risk if ctx.runner.latest_tick else None,
        )
        ctx.audit_log.append(
            timestamp_simulated=now,
            actor_type=ActorType.OPERATOR,
            action="THRESHOLD_CHANGED",
            reason_codes=[ReasonCode.THRESHOLD_CHANGED],
            risk=risk,
            config_version=new_config_version,
        )

    return JSONResponse(content={
        "applied": True,
        "campaign_id": campaign_id,
        "config_version": new_config_version,
        "old_values": old_values,
        "new_values": body.overrides,
    })


def _get_nested(d: dict, dotted_key: str) -> object:
    keys = dotted_key.split(".")
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)  # type: ignore[assignment]
        else:
            return None
    return d
