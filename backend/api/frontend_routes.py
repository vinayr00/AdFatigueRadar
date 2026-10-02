"""Frontend contract adapters serving hardcoded, consistent prototype data."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["frontend-adapter"])

# ---------------------------------------------------------------------------
# HARDCODED APPLICATION DATA
# ---------------------------------------------------------------------------

HARDCODED_CAMPAIGNS: list[dict[str, Any]] = [
    {
        "id": "camp_meta_fatigue",
        "name": "Summer Creator Campaign",
        "platform": "meta",
        "status": "CRITICAL",
        "risk_score": 0.87,
        "impressions": 66600.0,
        "clicks": 1832.0,
        "conversions": 143.0,
        "ctr": 0.0275,
        "cpa": 1450.0,
        "cpm": 1120.0,
        "spend": 5840.0,
        "roas": 3.77,
        "date_range": "Jun 15 - Jul 15, 2026",
        "created_at": "2026-09-17T10:00:00+05:30",
        "thumbnail_url": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&auto=format&fit=crop&q=60",
        "category": "Summer Apparel",
        "target_audience": "18-34 Fashion Shoppers",
        "last_7_days_trend": [120, 140, 160, 200, 280, 420, 680],
    },
    {
        "id": "camp_meta_healthy",
        "name": "Product Launch Campaign",
        "platform": "meta",
        "status": "ACTIVE",
        "risk_score": 0.12,
        "impressions": 45000.0,
        "clicks": 1950.0,
        "conversions": 180.0,
        "ctr": 0.0433,
        "cpa": 1050.0,
        "cpm": 1020.0,
        "spend": 3200.0,
        "roas": 4.85,
        "date_range": "Sep 01 - Sep 30, 2026",
        "created_at": "2026-09-22T10:00:00+05:30",
        "thumbnail_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&auto=format&fit=crop&q=60",
        "category": "Product Launch",
        "target_audience": "Broad Audience",
        "last_7_days_trend": [30, 25, 20, 15, 18, 14, 12],
    },
    {
        "id": "camp_tiktok_warning",
        "name": "Gen-Z Creator Campaign",
        "platform": "tiktok",
        "status": "WARNING",
        "risk_score": 0.58,
        "impressions": 82000.0,
        "clicks": 2100.0,
        "conversions": 95.0,
        "ctr": 0.0256,
        "cpa": 1380.0,
        "cpm": 200.00,
        "spend": 4650.0,
        "roas": 2.90,
        "date_range": "Aug 10 - Sep 20, 2026",
        "created_at": "2026-09-20T10:00:00+05:30",
        "thumbnail_url": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=800&auto=format&fit=crop&q=60",
        "category": "Creator UGC",
        "target_audience": "16-24 Short Video Viewers",
        "last_7_days_trend": [45, 50, 62, 58, 70, 75, 85],
    },
]

HARDCODED_ALERTS: list[dict[str, Any]] = [
    {
        "id": "alert-001",
        "time": "2026-09-30T20:00:00+05:30",
        "timestamp": "2026-09-30T20:00:00+05:30",
        "campaign_id": "camp_meta_fatigue",
        "campaign_name": "Summer Creator Campaign",
        "platform": "meta",
        "alert": "Critical Fatigue Threshold Crossed (Audience Risk: 87%)",
        "severity": "Critical",
        "metric_impact": "Audience risk 0.87 • CTR -46% • CPC +45%",
        "metric_trend": [40, 52, 68, 76, 87],
        "action_label": "Simulate Pause",
        "action_type": "pause",
        "status": "Open",
    },
    {
        "id": "alert-002",
        "time": "2026-09-30T18:00:00+05:30",
        "timestamp": "2026-09-30T18:00:00+05:30",
        "campaign_id": "camp_tiktok_warning",
        "campaign_name": "Gen-Z Creator Campaign",
        "platform": "tiktok",
        "alert": "Warning Fatigue Alert: Audience Risk 58%",
        "severity": "Warning",
        "metric_impact": "Audience risk 0.58 • CTR -20% • CPC +18%",
        "metric_trend": [30, 38, 44, 52, 58],
        "action_label": "Review Creative",
        "action_type": "review",
        "status": "Investigating",
    },
]

HARDCODED_RECOMMENDATIONS: list[dict[str, Any]] = [
    {
        "id": "pause:camp_meta_fatigue",
        "title": "Review Summer Creator Campaign",
        "description": "Critical fatigue threshold (87%) crossed. 83% negative comments with repeated exposure mockery. Automated simulated pause recommended.",
        "button_label": "Pause campaign",
        "button_variant": "red",
        "icon_name": "pause",
        "campaign_id": "camp_meta_fatigue",
        "action_type": "pause",
    },
    {
        "id": "rotate:camp_tiktok_warning",
        "title": "Rotate Gen-Z Creator Video",
        "description": "Audience risk rose to 58%. Creative frequency reaching fatigue limits. Rotate with fresh UGC variants.",
        "button_label": "Rotate Creative",
        "button_variant": "amber",
        "icon_name": "rotate",
        "campaign_id": "camp_tiktok_warning",
        "action_type": "rotate",
    },
]

HARDCODED_RULES: list[dict[str, Any]] = [
    {
        "id": "rule_critical_fatigue",
        "title": "Critical Ad Fatigue Protection",
        "name": "Critical Ad Fatigue Protection",
        "enabled": True,
        "action": "SIMULATED_PAUSE",
        "fatigue_score_min": 80,
        "confidence_min": 0.90,
        "require_guardrail": True,
        "simulation_mode": True,
    },
    {
        "id": "rule_warning_alert",
        "title": "Early Warning Fatigue Notification",
        "name": "Early Warning Fatigue Notification",
        "enabled": True,
        "action": "CREATE_ALERT",
        "fatigue_score_min": 60,
        "confidence_min": 0.85,
        "require_guardrail": False,
        "simulation_mode": True,
    },
]

HARDCODED_SETTINGS: dict[str, Any] = {
    "workspace_name": "AdFatigueRadar Demo",
    "timezone": "Asia/Kolkata",
    "currency": "INR",
    "simulation_mode": True,
    "auto_pause_enabled": False,
    "minimum_confidence": 0.90,
    "polling_interval_seconds": 60,
    "notifications": {
        "slack": True,
        "email": False
    },
}

HARDCODED_AUDIT_LOGS: list[dict[str, Any]] = [
    {
        "audit_id": "AUDIT001",
        "timestamp_simulated": "2026-09-30T19:55:00+05:30",
        "actor_type": "SYSTEM",
        "user_name": "System",
        "event_type": "SENTIMENT_ANALYSIS",
        "campaign_id": "camp_meta_fatigue",
        "campaign_name": "Summer Creator Campaign",
        "platform": "meta",
        "description": "Sentiment Analysis Spike Detected",
        "severity": "Info",
        "action": "SENTIMENT_ANALYSIS",
        "previous_state": "ACTIVE",
        "new_state": "ACTIVE",
        "reason_codes": ["NEGATIVE_SENTIMENT_SPIKE"],
        "risk": {"negative_sentiment": 83, "velocity": 5.1},
        "readback_verified": True,
        "config_version": "demo-v1",
    },
    {
        "audit_id": "AUDIT002",
        "timestamp_simulated": "2026-09-30T20:00:00+05:30",
        "actor_type": "SYSTEM",
        "user_name": "System",
        "event_type": "RISK_THRESHOLD_CROSSED",
        "campaign_id": "camp_meta_fatigue",
        "campaign_name": "Summer Creator Campaign",
        "platform": "meta",
        "description": "Risk Threshold Crossed: Critical",
        "severity": "Critical",
        "action": "RISK_THRESHOLD_CROSSED",
        "previous_state": "WARNING",
        "new_state": "CRITICAL",
        "reason_codes": ["CTR_DECLINE", "CPC_INCREASE", "NEGATIVE_SENTIMENT", "VELOCITY_SPIKE"],
        "risk": {"fatigue_score": 87, "audience_risk": 91, "economic_risk": 88},
        "readback_verified": True,
        "config_version": "demo-v1",
    },
    {
        "audit_id": "AUDIT003",
        "timestamp_simulated": "2026-09-30T20:05:00+05:30",
        "actor_type": "SYSTEM",
        "user_name": "System",
        "event_type": "CREATE_ALERT",
        "campaign_id": "camp_meta_fatigue",
        "campaign_name": "Summer Creator Campaign",
        "platform": "meta",
        "description": "Critical Alert Created",
        "severity": "Warning",
        "action": "CREATE_ALERT",
        "previous_state": "CRITICAL",
        "new_state": "CRITICAL",
        "reason_codes": ["FATIGUE_SCORE_ABOVE_THRESHOLD"],
        "risk": {"fatigue_score": 87},
        "readback_verified": True,
        "config_version": "demo-v1",
    },
    {
        "audit_id": "AUDIT004",
        "timestamp_simulated": "2026-09-30T20:10:00+05:30",
        "actor_type": "AUTOMATION",
        "user_name": "Automation Engine",
        "event_type": "SIMULATED_PAUSE",
        "campaign_id": "camp_meta_fatigue",
        "campaign_name": "Summer Creator Campaign",
        "platform": "meta",
        "description": "Simulated Campaign Pause Executed",
        "severity": "High",
        "action": "SIMULATED_PAUSE",
        "previous_state": "ACTIVE",
        "new_state": "PAUSED",
        "reason_codes": ["CRITICAL_FATIGUE", "GUARDRAIL_PASSED"],
        "risk": {"fatigue_score": 87, "confidence": 0.96},
        "readback_verified": True,
        "config_version": "demo-v1",
    },
    {
        "audit_id": "AUDIT005",
        "timestamp_simulated": "2026-09-30T20:11:00+05:30",
        "actor_type": "SYSTEM",
        "user_name": "System",
        "event_type": "SLACK_NOTIFICATION",
        "campaign_id": "camp_meta_fatigue",
        "campaign_name": "Summer Creator Campaign",
        "platform": "meta",
        "description": "Slack Alert Sent to #ad-ops",
        "severity": "Info",
        "action": "SLACK_NOTIFICATION",
        "previous_state": "PAUSED",
        "new_state": "PAUSED",
        "reason_codes": ["CRITICAL_ALERT"],
        "risk": {"notification": "sent"},
        "readback_verified": True,
        "config_version": "demo-v1",
    },
]

# ---------------------------------------------------------------------------
# API ROUTES
# ---------------------------------------------------------------------------

@router.get("/campaigns")
async def campaigns(status: str | None = None, platform: str | None = None, search: str | None = None):
    from demo_live_campaign import list_existing_campaigns, load_demo_campaign

    # Synchronize all existing demo campaign JSON files into HARDCODED_CAMPAIGNS
    for cid, cname in list_existing_campaigns():
        try:
            demo_data = load_demo_campaign(cid)
            match = next((c for c in HARDCODED_CAMPAIGNS if c["id"] == cid), None)
            if match:
                match["risk_score"] = float(demo_data.get("risk_score", 0.0))
                match["status"] = demo_data.get("status", "ACTIVE")
                match["health_score"] = demo_data.get("health_score", 100)
                match["severity"] = demo_data.get("severity", "HEALTHY")
            else:
                HARDCODED_CAMPAIGNS.insert(0, {
                    "id": cid,
                    "name": demo_data.get("name", cname),
                    "platform": "meta",
                    "status": demo_data.get("status", "ACTIVE"),
                    "risk_score": float(demo_data.get("risk_score", 0.0)),
                    "health_score": demo_data.get("health_score", 100),
                    "severity": demo_data.get("severity", "HEALTHY"),
                    "impressions": 5000.0 + len(demo_data.get("comments", [])) * 100,
                    "clicks": 180.0,
                    "conversions": 15.0,
                    "ctr": 0.036,
                    "cpa": 1050.0,
                    "cpm": 1020.0,
                    "spend": 1050.0,
                    "roas": 4.2,
                    "date_range": "Active",
                    "created_at": demo_data.get("created_at", ""),
                    "thumbnail_url": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&auto=format&fit=crop&q=60",
                    "category": "General",
                    "target_audience": "Broad Audience",
                    "last_7_days_trend": [10, 12, 10, 15, 14, 12, 10],
                })
        except Exception:
            pass

    result = copy.deepcopy(HARDCODED_CAMPAIGNS)
    if status and status.lower() not in {"all", ""}:
        result = [item for item in result if item["status"].lower() == status.lower()]
    if platform and platform.lower() not in {"all", ""}:
        result = [item for item in result if item["platform"] == platform.lower()]
    if search:
        s = search.lower()
        result = [item for item in result if s in item["name"].lower() or s in item["id"].lower()]
    return result


@router.get("/campaigns/{campaign_id}")
async def campaign_detail(campaign_id: str):
    from demo_live_campaign import campaign_exists, load_demo_campaign

    if campaign_exists(campaign_id):
        demo = load_demo_campaign(campaign_id)
        for c in HARDCODED_CAMPAIGNS:
            if c["id"] == campaign_id:
                c["risk_score"] = float(demo.get("risk_score", 0.0))
                c["status"] = demo.get("status", "ACTIVE")
                c["severity"] = demo.get("severity", "HEALTHY")
                c["health_score"] = demo.get("health_score", 100)
                return copy.deepcopy(c)
        camp_obj = {
            "id": campaign_id,
            "name": demo.get("name", campaign_id),
            "platform": "meta",
            "status": demo.get("status", "ACTIVE"),
            "risk_score": float(demo.get("risk_score", 0.0)),
            "health_score": demo.get("health_score", 100),
            "severity": demo.get("severity", "HEALTHY"),
            "impressions": 5000.0 + len(demo.get("comments", [])) * 100,
            "clicks": 180.0,
            "conversions": 15.0,
            "ctr": 0.036,
            "cpa": 1050.0,
            "cpm": 1020.0,
            "spend": 1050.0,
            "roas": 4.2,
            "date_range": "Active",
            "created_at": demo.get("created_at", ""),
            "thumbnail_url": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&auto=format&fit=crop&q=60",
            "category": "General",
            "target_audience": "Broad Audience",
            "last_7_days_trend": [10, 12, 10, 15, 14, 12, 10],
        }
        HARDCODED_CAMPAIGNS.insert(0, camp_obj)
        return copy.deepcopy(camp_obj)

    for c in HARDCODED_CAMPAIGNS:
        if c["id"] == campaign_id:
            return copy.deepcopy(c)
    # Default fallback to first campaign
    return copy.deepcopy(HARDCODED_CAMPAIGNS[0])


@router.post("/campaigns")
async def create_campaign(body: dict):
    from uuid import uuid4
    from demo_live_campaign import init_demo_campaign
    from backend.db.repository import repository

    campaign_id = body.get("id") or f"camp_{uuid4().hex[:8]}"
    name = body.get("name", "Untitled Campaign")
    platform = (body.get("platform") or "meta").lower()
    now_dt = datetime.now(timezone.utc)
    now_str = now_dt.isoformat()

    # Preserve database campaign creation flow
    try:
        repository.save_campaign({
            "id": campaign_id,
            "name": name,
            "platform": platform,
            "status": "ACTIVE",
            "created_at": now_dt,
            "budget": float(body.get("budget", 5000.0)),
            "metadata_json": {
                "category": body.get("category", "General"),
                "target_audience": body.get("target_audience", "Broad"),
                "date_range": body.get("date_range", "Active"),
            }
        })
    except Exception as e:
        print(f"[DB CAMPAIGN SAVE NOTICE] {e}")

    new_campaign = {
        "id": campaign_id,
        "name": name,
        "platform": platform,
        "status": "ACTIVE",
        "risk_score": 0.0,
        "impressions": 1000.0,
        "clicks": 45.0,
        "conversions": 10.0,
        "ctr": 0.045,
        "cpa": 1050.0,
        "cpm": 1020.0,
        "spend": 1050.0,
        "roas": 4.5,
        "date_range": body.get("date_range", "Active"),
        "created_at": now_str,
        "thumbnail_url": body.get("thumbnail_url") or "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&auto=format&fit=crop&q=60",
        "category": body.get("category", "General"),
        "target_audience": body.get("target_audience", "Broad Audience"),
        "last_7_days_trend": [10, 12, 10, 15, 14, 12, 10],
    }

    HARDCODED_CAMPAIGNS.insert(0, new_campaign)

    # ONLY AFTER the campaign is successfully created, initialize demo JSON
    init_demo_campaign(campaign_id, name)

    return new_campaign


@router.post("/demo/campaigns/{campaign_id}/init")
async def init_demo_campaign_endpoint(campaign_id: str, body: dict = None):
    from demo_live_campaign import init_demo_campaign
    name = (body or {}).get("name") or campaign_id
    data = init_demo_campaign(campaign_id, name)
    return data


@router.get("/demo/campaigns/{campaign_id}")
async def get_demo_campaign_endpoint(campaign_id: str):
    from demo_live_campaign import campaign_exists, load_demo_campaign
    if not campaign_exists(campaign_id):
        raise HTTPException(status_code=404, detail="demo campaign not initialized")
    return load_demo_campaign(campaign_id)


@router.post("/demo/campaigns/{campaign_id}/comments")
async def add_demo_comment_endpoint(campaign_id: str, body: dict):
    from demo_live_campaign import campaign_exists, process_demo_comment
    # If the JSON does not exist, return a clear "demo campaign not initialized" error
    if not campaign_exists(campaign_id):
        raise HTTPException(status_code=404, detail="demo campaign not initialized")

    comment_text = body.get("text") or body.get("comment") or ""
    if not comment_text.strip():
        raise HTTPException(status_code=400, detail="Comment text cannot be empty")

    author = body.get("author") or "Demo User"
    try:
        result = process_demo_comment(campaign_id, comment_text, author)
        updated_state = result[0] if isinstance(result, tuple) else result
        return updated_state
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="demo campaign not initialized")


@router.post("/campaigns/{campaign_id}/pause")
async def pause(campaign_id: str):
    for c in HARDCODED_CAMPAIGNS:
        if c["id"] == campaign_id:
            c["status"] = "PAUSED"
    return JSONResponse(content={
        "success": True,
        "new_state": "PAUSED",
        "readback_verified": True,
        "message": "Campaign paused successfully",
        "campaign_id": campaign_id,
    })


@router.post("/campaigns/{campaign_id}/unpause")
async def unpause(campaign_id: str):
    for c in HARDCODED_CAMPAIGNS:
        if c["id"] == campaign_id:
            c["status"] = "ACTIVE"
    return JSONResponse(content={
        "success": True,
        "new_state": "ACTIVE",
        "readback_verified": True,
        "message": "Campaign unpaused successfully",
        "campaign_id": campaign_id,
    })


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: str):
    import re
    from pathlib import Path
    from backend.db.repository import repository

    # Security: validate campaign_id to strictly prevent path traversal
    if not re.match(r"^[a-zA-Z0-9_-]+$", campaign_id):
        raise HTTPException(status_code=400, detail="Invalid campaign ID format")

    # 1. Delete from existing database repository flow
    try:
        repository.delete_campaign(campaign_id)
    except Exception as e:
        print(f"[DB CAMPAIGN DELETE NOTICE] {e}")

    # 2. Remove immediately from in-memory campaigns list
    global HARDCODED_CAMPAIGNS
    HARDCODED_CAMPAIGNS = [c for c in HARDCODED_CAMPAIGNS if c["id"] != campaign_id]

    # 3. Delete corresponding demo JSON if it exists (safe isolated path only)
    base_dir = Path(__file__).resolve().parent.parent.parent
    demo_file = base_dir / "demo_data" / "campaigns" / f"{campaign_id}.json"
    if demo_file.is_file():
        try:
            demo_file.unlink()
        except Exception as e:
            print(f"[DEMO JSON DELETE NOTICE] {e}")

    return {
        "success": True,
        "campaign_id": campaign_id,
        "message": "Campaign deleted successfully",
    }


@router.get("/alerts")
async def alerts():
    return copy.deepcopy(HARDCODED_ALERTS)


@router.get("/recommended-actions")
async def recommended_actions():
    return copy.deepcopy(HARDCODED_RECOMMENDATIONS)


@router.post("/actions/{action_id}/execute")
async def execute_action(action_id: str):
    return JSONResponse(content={
        "success": True,
        "message": "Action executed successfully",
        "action_id": action_id,
    })


@router.get("/automation-rules")
async def automation_rules():
    return copy.deepcopy(HARDCODED_RULES)


@router.patch("/automation-rules/{rule_id}")
async def toggle_rule(rule_id: str, body: dict):
    enabled = bool(body.get("enabled"))
    for r in HARDCODED_RULES:
        if r["id"] == rule_id:
            r["enabled"] = enabled
    return {"success": True, "rule_id": rule_id, "enabled": enabled}


@router.get("/settings")
async def get_settings():
    return copy.deepcopy(HARDCODED_SETTINGS)


@router.put("/settings")
async def put_settings(body: dict):
    HARDCODED_SETTINGS.update(body)
    return copy.deepcopy(HARDCODED_SETTINGS)


@router.get("/audit-logs")
async def global_audit(search: str | None = None, event_type: str | None = None, campaign: str | None = None, limit: int = 500):
    output = copy.deepcopy(HARDCODED_AUDIT_LOGS)
    if campaign:
        output = [item for item in output if item["campaign_id"] == campaign or item["campaign_name"] == campaign]
    if event_type:
        output = [item for item in output if event_type.lower() in item["event_type"].lower()]
    if search:
        s = search.lower()
        output = [item for item in output if s in item["description"].lower() or s in item["campaign_name"].lower()]
    return output[:limit]


@router.get("/analytics")
async def analytics(campaign_id: str | None = None):
    # 12-hour hourly telemetry trend demonstrating ad fatigue
    trend = [
        {"date": "10:00", "impressions": 5000, "clicks": 240, "conversions": 22, "cpa": 87.27, "cpm": 384.0, "risk_score": 0.18},
        {"date": "11:00", "impressions": 5100, "clicks": 230, "conversions": 20, "cpa": 99.00, "cpm": 388.2, "risk_score": 0.24},
        {"date": "12:00", "impressions": 5200, "clicks": 215, "conversions": 18, "cpa": 113.33, "cpm": 392.3, "risk_score": 0.32},
        {"date": "13:00", "impressions": 5300, "clicks": 195, "conversions": 16, "cpa": 134.06, "cpm": 404.7, "risk_score": 0.40},
        {"date": "14:00", "impressions": 5400, "clicks": 175, "conversions": 14, "cpa": 162.50, "cpm": 421.3, "risk_score": 0.48},
        {"date": "15:00", "impressions": 5500, "clicks": 155, "conversions": 12, "cpa": 206.67, "cpm": 450.9, "risk_score": 0.58},
        {"date": "16:00", "impressions": 5600, "clicks": 140, "conversions": 10, "cpa": 266.00, "cpm": 475.0, "risk_score": 0.67},
        {"date": "17:00", "impressions": 5700, "clicks": 125, "conversions": 9, "cpa": 319.44, "cpm": 504.4, "risk_score": 0.72},
        {"date": "18:00", "impressions": 5800, "clicks": 110, "conversions": 7, "cpa": 440.00, "cpm": 531.0, "risk_score": 0.78},
        {"date": "19:00", "impressions": 5900, "clicks": 95, "conversions": 6, "cpa": 554.17, "cpm": 563.6, "risk_score": 0.82},
        {"date": "20:00", "impressions": 6000, "clicks": 82, "conversions": 5, "cpa": 721.60, "cpm": 601.3, "risk_score": 0.87},
        {"date": "21:00", "impressions": 6100, "clicks": 70, "conversions": 4, "cpa": 962.50, "cpm": 631.1, "risk_score": 0.91},
    ]

    status_data = lambda val, change, is_pos, spark: {"value": val, "change": change, "is_positive": is_pos, "sparkline": spark}

    return {
        "impressions": status_data(66600, -12.4, False, [5000, 5200, 5500, 5800, 6100]),
        "clicks": status_data(1832, -70.8, False, [240, 215, 175, 125, 70]),
        "conversions": status_data(143, -81.8, False, [22, 18, 14, 9, 4]),
        "cpa": status_data(1450.0, 48.0, False, [1100, 1220, 1340, 1420, 1450]),
        "cpm": status_data(1120.0, 14.3, False, [1020, 1050, 1080, 1100, 1120]),
        "ctr": status_data(2.75, -76.0, False, [4.8, 4.1, 3.2, 2.2, 1.15]),
        "performance_trend": trend,
        "sentiment_overview": {
            "total_comments": 12,
            "positive_pct": 16.7,
            "neutral_pct": 0.0,
            "negative_pct": 83.3,
            "spam_pct": 0.0,
            "sentiment_decay": 0.88,
            "fatigue_mockery": 0.94,
            "comment_acceleration": 5.1,
        },
        "risk_analysis": {
            "audience_risk": 0.87,
            "economic_risk": 0.82,
            "state": "CRITICAL",
            "description": "High negative sentiment velocity and severe CTR decline triggered automated guardrails.",
            "thresholds": {"watch": 0.40, "warning": 0.60, "soft": 0.70, "critical": 0.80},
        },
        "platform_performance": [
            {"platform": "meta", "name": "Instagram / Meta", "impressions": 111600, "change_pct": -8.5, "is_increase": False, "color": "#0668E1"},
            {"platform": "tiktok", "name": "TikTok", "impressions": 82000, "change_pct": 14.2, "is_increase": True, "color": "#000000"},
        ],
        "audience_insights": {
            "age_groups": [
                {"group": "18-24", "percentage": 42},
                {"group": "25-34", "percentage": 38},
                {"group": "35-44", "percentage": 15},
                {"group": "45+", "percentage": 5},
            ],
            "gender": {"male": 44, "female": 52, "other": 4},
        },
    }


@router.get("/comparisons")
async def comparisons(campaign_a: str = Query("camp_meta_fatigue"), campaign_b: str = Query("camp_meta_healthy")):
    ca = next((c for c in HARDCODED_CAMPAIGNS if c["id"] == campaign_a), HARDCODED_CAMPAIGNS[0])
    cb = next((c for c in HARDCODED_CAMPAIGNS if c["id"] == campaign_b), HARDCODED_CAMPAIGNS[1])

    return {
        "campaign_a": {
            "id": ca["id"], "name": ca["name"], "platform": ca["platform"], "category": ca["category"],
            "thumbnail": ca["thumbnail_url"], "impressions": ca["impressions"], "clicks": ca["clicks"],
            "conversions": ca["conversions"], "cpa": ca["cpa"], "cpm": ca["cpm"], "ctr": ca["ctr"] * 100 if ca["ctr"] else None,
            "sentiment_decay": 0.88, "negative_ratio": 83.3, "comment_acceleration": 5.1, "ctr_frequency": 0.42,
            "critical_complaints": 1, "sentiment": {"positive": 16.7, "neutral": 0.0, "negative": 83.3},
        },
        "campaign_b": {
            "id": cb["id"], "name": cb["name"], "platform": cb["platform"], "category": cb["category"],
            "thumbnail": cb["thumbnail_url"], "impressions": cb["impressions"], "clicks": cb["clicks"],
            "conversions": cb["conversions"], "cpa": cb["cpa"], "cpm": cb["cpm"], "ctr": cb["ctr"] * 100 if cb["ctr"] else None,
            "sentiment_decay": 0.05, "negative_ratio": 5.0, "comment_acceleration": 0.2, "ctr_frequency": 0.08,
            "critical_complaints": 0, "sentiment": {"positive": 85.0, "neutral": 10.0, "negative": 5.0},
        },
        "risk_timeline": [
            {"date": "10:00", "risk_a": 0.18, "risk_b": 0.10},
            {"date": "12:00", "risk_a": 0.32, "risk_b": 0.11},
            {"date": "14:00", "risk_a": 0.48, "risk_b": 0.12},
            {"date": "16:00", "risk_a": 0.67, "risk_b": 0.12},
            {"date": "18:00", "risk_a": 0.78, "risk_b": 0.13},
            {"date": "20:00", "risk_a": 0.87, "risk_b": 0.12},
            {"date": "21:00", "risk_a": 0.91, "risk_b": 0.12},
        ],
        "platform_breakdown": [],
        "top_comment_categories": [
            {"category": "AD_FATIGUE", "pct_a": 83.3, "pct_b": 0.0},
            {"category": "GENERAL_POSITIVE", "pct_a": 16.7, "pct_b": 85.0},
            {"category": "PRICE_COMPLAINT", "pct_a": 8.3, "pct_b": 5.0},
        ],
        "insights": [
            "Summer Creator Campaign displays severe ad fatigue: CTR dropped 76% while negative sentiment reached 83.3%.",
            "Product Launch Campaign remains healthy with 85% positive reactions and stable ₹102 CPA.",
        ],
    }


@router.get("/replay/{campaign_id}/snapshot")
async def replay_snapshot(campaign_id: str):
    from demo_live_campaign import campaign_exists, load_demo_campaign

    # For demo campaigns, load state directly from the campaign JSON
    if campaign_exists(campaign_id):
        demo = load_demo_campaign(campaign_id)
        c_name = demo.get("name", campaign_id)
        aud_risk = float(demo.get("risk_score", 0.0))
        health = int(demo.get("health_score", 100))
        status = demo.get("status", "ACTIVE")
        severity = demo.get("severity", "HEALTHY")
        econ_risk = float(demo.get("economic_risk", round(aud_risk * 0.82, 2) if aud_risk > 0 else 0.05))
        cpa_val = float(demo.get("cpa", round(1050.0 * (1.0 + econ_risk * 0.60), 2)))
        now_str = datetime.now(timezone.utc).isoformat()

        comments_list = demo.get("comments", [])

        # Build timeline where every step reflects the demo campaign's current metrics
        hours = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72]
        timeline = [
            {
                "hour": h,
                "timestamp_simulated": now_str,
                "potential_impressions": 5000 + len(comments_list) * 100,
                "observed_impressions": 5000 + len(comments_list) * 100,
                "potential_spend": 1050.0 + len(comments_list) * 50,
                "observed_spend": 1050.0 + len(comments_list) * 50,
                "audience_risk": aud_risk,
                "economic_risk": econ_risk,
                "cpa": cpa_val,
                "cpm": 1020.0,
                "state": status,
            }
            for h in hours
        ]

        live_comments = [
            {
                "id": c.get("comment_id") or c.get("id", f"c-{i}"),
                "event_id": c.get("comment_id") or c.get("id", f"c-{i}"),
                "author": c.get("author", "Demo User"),
                "author_name": c.get("author", "Demo User"),
                "text": c.get("text", ""),
                "sentiment": c.get("sentiment", "NEUTRAL").upper(),
                "category": c.get("category", "neutral"),
                "confidence": c.get("confidence", 0.90),
                "critical_complaint": c.get("critical_complaint", False),
            }
            for i, c in enumerate(reversed(comments_list[-15:]))
        ]
        if not live_comments:
            live_comments = [
                {
                    "id": "c-0",
                    "event_id": "c-0",
                    "author": "System",
                    "author_name": "System",
                    "text": "Campaign initialized with 100% health score.",
                    "sentiment": "POSITIVE",
                    "category": "positive",
                    "confidence": 1.0,
                    "critical_complaint": False,
                }
            ]

        actions_history = [
            {
                "action": "SIMULATED_PAUSE" if status == "PAUSED" else ("GUARD_ALERT" if status == "SOFT_REDUCED" else "MONITORING"),
                "time": now_str[11:16],
                "state": status,
                "reason": f"Live simulation health: {health}/100, risk: {aud_risk:.2f}",
            }
        ]

        return {
            "campaign_id": campaign_id,
            "scenario_name": f"{c_name} Live Demo Replay",
            "seed": 42,
            "current_hour": 12,
            "simulated_timestamp": now_str,
            "is_running": False,
            "speed": 1.0,
            "current_state": status,
            "previous_state": "ACTIVE",
            "state_reason": f"Demo Simulation: Health {health}/100, Severity: {severity}, Status: {status}",
            "points": timeline,
            "live_comments": live_comments,
            "actions_history": actions_history,
            "audit_trail": HARDCODED_AUDIT_LOGS,
        }

    timeline = [
        {"hour": 0, "timestamp_simulated": "2026-09-30T10:00:00+05:30", "potential_impressions": 5000, "observed_impressions": 5000, "potential_spend": 1920, "observed_spend": 1920, "audience_risk": 0.18, "economic_risk": 0.15, "cpa": 87.27, "cpm": 384.0, "state": "HEALTHY"},
        {"hour": 2, "timestamp_simulated": "2026-09-30T12:00:00+05:30", "potential_impressions": 10300, "observed_impressions": 10300, "potential_spend": 3960, "observed_spend": 3960, "audience_risk": 0.32, "economic_risk": 0.28, "cpa": 113.33, "cpm": 392.3, "state": "WATCH"},
        {"hour": 4, "timestamp_simulated": "2026-09-30T14:00:00+05:30", "potential_impressions": 21000, "observed_impressions": 21000, "potential_spend": 8380, "observed_spend": 8380, "audience_risk": 0.48, "economic_risk": 0.43, "cpa": 162.50, "cpm": 421.3, "state": "WATCH"},
        {"hour": 6, "timestamp_simulated": "2026-09-30T16:00:00+05:30", "potential_impressions": 32100, "observed_impressions": 32100, "potential_spend": 13520, "observed_spend": 13520, "audience_risk": 0.67, "economic_risk": 0.61, "cpa": 266.00, "cpm": 475.0, "state": "WARNING"},
        {"hour": 8, "timestamp_simulated": "2026-09-30T18:00:00+05:30", "potential_impressions": 43600, "observed_impressions": 43600, "potential_spend": 19475, "observed_spend": 19475, "audience_risk": 0.78, "economic_risk": 0.73, "cpa": 440.00, "cpm": 531.0, "state": "WARNING"},
        {"hour": 10, "timestamp_simulated": "2026-09-30T20:00:00+05:30", "potential_impressions": 55500, "observed_impressions": 55500, "potential_spend": 26408, "observed_spend": 26408, "audience_risk": 0.87, "economic_risk": 0.82, "cpa": 721.60, "cpm": 601.3, "state": "CRITICAL"},
        {"hour": 11, "timestamp_simulated": "2026-09-30T21:00:00+05:30", "potential_impressions": 61600, "observed_impressions": 61600, "potential_spend": 30258, "observed_spend": 30258, "audience_risk": 0.91, "economic_risk": 0.88, "cpa": 962.50, "cpm": 631.1, "state": "CRITICAL"},
    ]

    return {
        "campaign_id": campaign_id,
        "scenario_name": "Summer Creator Fatigue Replay",
        "seed": 42,
        "current_hour": 11,
        "simulated_timestamp": "2026-09-30T21:00:00+05:30",
        "is_running": False,
        "speed": 1.0,
        "current_state": "CRITICAL",
        "previous_state": "WARNING",
        "state_reason": "CRITICAL_FATIGUE,GUARDRAIL_PASSED",
        "points": timeline,
        "live_comments": [
            {"id": "c-1", "author": "User @fashion_fan", "text": "Stop showing me this ad again 🙄", "sentiment": "NEGATIVE", "category": "AD_FATIGUE"},
            {"id": "c-2", "author": "User @insta_shopper", "text": "I have seen this like ten times already", "sentiment": "NEGATIVE", "category": "AD_FATIGUE"},
        ],
        "actions_history": [
            {"action": "SIMULATED_PAUSE", "time": "20:10", "state": "PAUSED", "reason": "Fatigue score 87 above critical threshold"}
        ],
        "audit_trail": HARDCODED_AUDIT_LOGS,
    }


@router.get("/replay/config")
async def replay_config(campaign_id: str = Query("camp_meta_fatigue")):
    return {
        "campaign_id": campaign_id,
        "config_version": "demo-v1",
        "step_minutes": 60,
        "guard_window_minutes": 720,
        "speed": 1.0,
        "is_running": False,
    }


@router.post("/replay/start")
async def replay_start_adapter(body: dict):
    return {"status": "started", "speed": body.get("speed", 1.0), "campaign_id": body.get("campaign_id")}


@router.post("/replay/pause")
async def replay_pause_adapter(body: dict):
    return {"status": "paused", "campaign_id": body.get("campaign_id")}


@router.post("/replay/reset")
async def replay_reset_adapter(body: dict):
    return {"status": "reset", "campaign_id": body.get("campaign_id")}

# ---------------------------------------------------------------------------
# Direct /campaigns compatibility router for replay controls & SSE
# ---------------------------------------------------------------------------
router_campaigns = APIRouter(prefix="/campaigns", tags=["campaigns-compat"])

@router_campaigns.get("/{campaign_id}/stream")
async def stream_compat(campaign_id: str):
    import asyncio
    from fastapi.responses import StreamingResponse
    from demo_live_campaign import campaign_exists
    cur_h = 12 if campaign_exists(campaign_id) else 11
    async def sse_gen():
        yield f"event: STEP_UPDATE\ndata: {{\"is_running\": false, \"current_hour\": {cur_h}}}\n\n"
        while True:
            await asyncio.sleep(20)
            yield ": ping\n\n"
    return StreamingResponse(sse_gen(), media_type="text/event-stream")

@router_campaigns.post("/{campaign_id}/replay/start")
async def replay_start_direct(campaign_id: str, speed: float = 1.0):
    return {"started": True, "campaign_id": campaign_id, "speed": speed}

@router_campaigns.post("/{campaign_id}/replay/pause")
async def replay_pause_direct(campaign_id: str):
    return {"paused": True, "campaign_id": campaign_id}

@router_campaigns.post("/{campaign_id}/replay/resume")
async def replay_resume_direct(campaign_id: str):
    return {"resumed": True, "campaign_id": campaign_id}

@router_campaigns.post("/{campaign_id}/replay/reset")
async def replay_reset_direct(campaign_id: str):
    return {"reset": True, "campaign_id": campaign_id, "current_hour": 0}
