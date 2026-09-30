from __future__ import annotations

import os
from fastapi.testclient import TestClient

from backend.api.campaign_registry import _reset_registry_for_tests, get_registry
from backend.api import routes_campaigns
from backend.main import app
from backend.models.backend_models import CommentEvent, NLPResult


def client(monkeypatch):
    monkeypatch.setenv("ADFR_API_KEY", "test-api-key")
    monkeypatch.setenv("ADFR_HMAC_SECRET", "test-hmac-secret")
    _reset_registry_for_tests()
    return TestClient(app)


def test_get_status_timeline_audit_and_unknown_campaign(monkeypatch):
    c = client(monkeypatch)
    assert c.get("/campaigns/missing/status").status_code == 404
    ctx = get_registry().get_or_create("api-campaign")
    assert c.get("/campaigns/api-campaign/status").status_code == 200
    assert c.get("/campaigns/api-campaign/timeline").json()["timeline"] == []
    assert c.get("/campaigns/api-campaign/audit").json()["audit_events"] == []
    assert c.get("/campaigns/unknown/timeline").status_code == 404


def test_invalid_and_missing_api_key_401(monkeypatch):
    c = client(monkeypatch)
    assert c.post("/campaigns/a/pause", headers={"X-API-Key": "wrong"}).status_code == 401
    assert c.post("/campaigns/a/pause").status_code == 401


def test_missing_api_or_hmac_secret_503(monkeypatch):
    c = client(monkeypatch)
    monkeypatch.delenv("ADFR_API_KEY")
    assert c.post("/campaigns/a/pause", headers={"X-API-Key": "whatever"}).status_code == 503
    monkeypatch.setenv("ADFR_API_KEY", "test-api-key")
    monkeypatch.delenv("ADFR_HMAC_SECRET")
    response = c.post("/campaigns/a/pause", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 503
    assert "test-hmac-secret" not in response.text


def test_threshold_validation_statuses_and_valid_override(monkeypatch):
    c = client(monkeypatch)
    url = "/campaigns/thresholds-c/thresholds"
    headers = {"X-API-Key": "test-api-key"}
    ctx = get_registry().get_or_create("thresholds-c")
    from datetime import datetime, timezone
    ctx.machine.aggregator.clock.tick(datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc))
    assert c.put(url, headers=headers, json={"overrides": {"unknown.key": .2}}).status_code == 422
    assert c.put(url, headers=headers, json={"overrides": {"category_weights.fatigue": .2}}).status_code == 422
    assert c.put(url, headers=headers, json={"overrides": {"persistence_hours.pause": .3}}).status_code == 422
    assert c.put(url, headers=headers, json={"overrides": {"audience_gates.warning": .99}}).status_code == 422
    assert c.put(url, headers=headers, json={"overrides": {"audience_gates.warning": .9}}).status_code == 422
    ok = c.put(url, headers=headers, json={"overrides": {"audience_gates.warning": .66}})
    assert ok.status_code == 200 and ok.json()["config_version"].endswith("override.1")
    assert get_registry().get("thresholds-c").audit_log.get_all()[-1].action == "THRESHOLD_CHANGED"


def test_invalid_speed_and_duplicate_replay(monkeypatch):
    c = client(monkeypatch)
    headers = {"X-API-Key": "test-api-key"}
    url = "/campaigns/replay-c/replay/start"
    for speed in (0, -1, 1001):
        assert c.post(url, params={"speed": speed}, headers=headers).status_code == 422
    ctx = get_registry().get_or_create("replay-c")
    ctx.runner._running = True
    assert c.post(url, headers=headers).status_code == 409


def test_json_security_headers_and_xss_is_inert_json(monkeypatch):
    c = client(monkeypatch)
    ctx = get_registry().get_or_create("xss")
    response = c.get("/campaigns/xss/status")
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["x-content-type-options"] == "nosniff"
    # The API exposes structured JSON only; comment text is never emitted as HTML.
    assert "<script>alert(1)</script>" not in response.text
    assert "Traceback" not in response.text
    assert "test-api-key" not in response.text and "test-hmac-secret" not in response.text
    payload = "<script>alert(1)"
    import urllib.parse
    encoded = urllib.parse.quote(payload, safe="")
    xss_response = c.get("/campaigns/" + encoded + "/status")
    assert xss_response.status_code == 404
    assert xss_response.headers["content-type"].startswith("application/json")
    assert xss_response.json()["detail"] == "Campaign '" + payload + "' not found"


def test_cors_is_not_wildcard(monkeypatch):
    c = client(monkeypatch)
    response = c.options("/campaigns/x/status", headers={"Origin": "https://untrusted.invalid", "Access-Control-Request-Method": "GET"})
    assert response.headers.get("access-control-allow-origin") != "*"


def test_status_timeline_audit_config_versions_match_overrides(monkeypatch):
    from datetime import datetime, timedelta, timezone
    c = client(monkeypatch)
    campaign_id = "versioned-campaign"
    ctx = get_registry().get_or_create(campaign_id)
    t0 = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    ctx.runner._flush_step(t0, [], [], [])

    assert c.get(f"/campaigns/{campaign_id}/status").json()["config_version"] == "thresholds_v4"
    base = c.get(f"/campaigns/{campaign_id}/thresholds")
    assert base.status_code == 200
    assert base.json()["config_version"] == "thresholds_v4"
    assert base.json()["effective_config"]["audience_gates"]["warning"] == .65
    assert base.json()["threshold_mutable_keys"] == list(base.json()["safe_bounds"])

    updated = c.put(
        f"/campaigns/{campaign_id}/thresholds",
        headers={"X-API-Key": "test-api-key"},
        json={"overrides": {"audience_gates.warning": .66}},
    )
    assert updated.status_code == 200
    assert c.get(f"/campaigns/{campaign_id}/status").json()["config_version"] == "thresholds_v4+override.1"
    effective = c.get(f"/campaigns/{campaign_id}/thresholds").json()
    assert effective["config_version"] == "thresholds_v4+override.1"
    assert effective["effective_config"]["audience_gates"]["warning"] == .66
    assert ctx.machine._cfg["audience_gates"]["warning"] == .66
    audit = c.get(f"/campaigns/{campaign_id}/audit").json()["audit_events"][-1]
    assert audit["config_version"] == "thresholds_v4+override.1"

    second = c.put(
        f"/campaigns/{campaign_id}/thresholds",
        headers={"X-API-Key": "test-api-key"},
        json={"overrides": {"audience_gates.warning": .67}},
    )
    assert second.status_code == 200
    assert c.get(f"/campaigns/{campaign_id}/status").json()["config_version"] == "thresholds_v4+override.2"
    assert c.get(f"/campaigns/{campaign_id}/thresholds").json()["config_version"] == "thresholds_v4+override.2"
    assert c.get(f"/campaigns/{campaign_id}/audit").json()["audit_events"][-1]["config_version"] == "thresholds_v4+override.2"

    ctx.runner._flush_step(t0 + timedelta(minutes=5), [], [], [])
    timeline = c.get(f"/campaigns/{campaign_id}/timeline").json()["timeline"]
    assert timeline[0]["config_version"] == "thresholds_v4"
    assert timeline[-1]["config_version"] == "thresholds_v4+override.2"
    action = c.post(f"/campaigns/{campaign_id}/pause", headers={"X-API-Key": "test-api-key"})
    assert action.status_code == 200
    assert ctx.audit_log.get_all()[-1].config_version == "thresholds_v4+override.2"
    ctx.runner._flush_step(t0 + timedelta(minutes=5), [], [], [])
    latest_point = c.get(f"/campaigns/{campaign_id}/timeline").json()["timeline"][-1]
    assert action.json()["audit_event_id"] in latest_point["action_events"]
    assert latest_point["config_version"] == "thresholds_v4+override.2"


def test_populated_timeline_exposes_tick_signals_transition_and_audit_reference(monkeypatch):
    from datetime import datetime, timedelta, timezone
    c = client(monkeypatch)
    campaign_id = "timeline-populated"
    ctx = get_registry().get_or_create(campaign_id)
    t0 = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    ctx.runner._flush_step(t0, [], [], [])
    t1 = t0 + timedelta(minutes=5)
    ctx.runner._flush_step(t1, [], [], [])
    action = c.post(f"/campaigns/{campaign_id}/pause", headers={"X-API-Key": "test-api-key"})
    assert action.status_code == 200

    response = c.get(f"/campaigns/{campaign_id}/timeline")
    assert response.status_code == 200
    point = response.json()["timeline"][-1]
    assert point["sim_time"] == t1.isoformat()
    assert point["state"] == "PAUSED"
    assert point["severity"] in {"HEALTHY", "WATCH", "WARNING", "CRITICAL"}
    assert set(point["signal_breakdown"]) >= {
        "harmful_negative_ratio", "sentiment_decay", "fatigue_mockery",
        "comment_acceleration", "ctr_frequency", "critical_complaint_signal",
        "cpa_cpm_signal", "roas_conversion_signal",
    }
    assert point["stale"] is True  # the prior active tick crossed the two-step telemetry gap
    assert point["anomaly"] is False
    assert "config_version" in point and point["config_version"] == "thresholds_v4"
    assert "reason_codes" in point
    assert action.json()["audit_event_id"] in point["action_events"]
    audit_ids = {event["audit_id"] for event in c.get(f"/campaigns/{campaign_id}/audit").json()["audit_events"]}
    assert set(point["action_events"]) <= audit_ids


def test_timeline_records_healthy_watch_and_warning_from_real_ticks(monkeypatch):
    from datetime import datetime, timedelta, timezone
    c = client(monkeypatch)
    campaign_id = "severity-timeline"
    ctx = get_registry().get_or_create(campaign_id)
    t0 = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    ctx.runner._flush_step(t0, [], [], [])
    event_index = 0
    for step in range(8):
        boundary = t0 + timedelta(minutes=5 * step)
        comments, results = [], []
        for offset in range(10 * (step + 1)):
            idx = event_index
            event_index += 1
            category = "product_complaint" if offset % 2 == 0 else "fatigue"
            event_id = f"severity-comment-{idx}"
            comments.append(CommentEvent(
                event_id=event_id, timestamp=boundary, campaign_id=campaign_id,
                ad_id="ad-severity", author_id=f"author-{idx}",
                text=f"unique severity comment {idx}", reactions=0, replies=0,
            ))
            results.append(NLPResult(
                comment_id=event_id, sentiment="negative", sentiment_score=.99,
                category=category, confidence=.99,
                critical_complaint=(category == "product_complaint"),
            ))
        ctx.runner._flush_step(boundary, comments, results, [])

    timeline = c.get(f"/campaigns/{campaign_id}/timeline").json()["timeline"]
    severities = [point["severity"] for point in timeline]
    assert severities[0] == "HEALTHY"
    assert "WATCH" in severities
    assert "WARNING" in severities


def test_comments_endpoint_returns_safe_nlp_summary_and_inert_json(monkeypatch):
    from datetime import datetime, timezone
    c = client(monkeypatch)
    campaign_id = "comments-api"
    ctx = get_registry().get_or_create(campaign_id)
    t0 = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    comment = CommentEvent(
        event_id="comment-xss", timestamp=t0, campaign_id=campaign_id, ad_id="ad-1",
        author_id="raw-private-author", text="<script>alert(1)</script>", reactions=0, replies=0,
    )
    nlp = NLPResult(
        comment_id="comment-xss", sentiment="negative", sentiment_score=.9,
        category="product_complaint", confidence=.95, critical_complaint=True,
    )
    ctx.runner._flush_step(t0, [comment], [nlp], [])

    response = c.get(f"/campaigns/{campaign_id}/comments?limit=1")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    entry = response.json()["comments"][0]
    assert entry["event_id"] == "comment-xss"
    assert entry["campaign_id"] == campaign_id and entry["ad_id"] == "ad-1"
    assert entry["sentiment"] == "negative" and entry["category"] == "product_complaint"
    assert entry["sentiment_score"] == .9 and entry["confidence"] == .95
    assert entry["critical_complaint"] is True
    assert entry["text"] == "<script>alert(1)</script>"  # inert JSON string; client renders as text
    assert "author_id" not in entry and "hmac_author_id" not in entry
    assert "raw-private-author" not in response.text and "test-hmac-secret" not in response.text
    assert c.get("/campaigns/missing/comments").status_code == 404
    assert c.get(f"/campaigns/{campaign_id}/comments?limit=1001").status_code == 422


def test_effective_threshold_get_unknown_campaign_and_no_secrets(monkeypatch):
    c = client(monkeypatch)
    assert c.get("/campaigns/not-there/thresholds").status_code == 404
    ctx = get_registry().get_or_create("threshold-read")
    response = c.get("/campaigns/threshold-read/thresholds")
    assert response.headers["content-type"].startswith("application/json")
    assert "test-api-key" not in response.text and "test-hmac-secret" not in response.text
    assert response.json()["effective_config"] == ctx.machine._cfg


def test_unknown_campaign_mutation_404(monkeypatch):
    c = client(monkeypatch)
    response = c.post("/campaigns/not-registered/pause", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 404
