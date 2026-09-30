from __future__ import annotations

import os
from fastapi.testclient import TestClient

from backend.api.campaign_registry import _reset_registry_for_tests, get_registry
from backend.api import routes_campaigns
from backend.main import app


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


def test_unknown_campaign_mutation_404(monkeypatch):
    c = client(monkeypatch)
    response = c.post("/campaigns/not-registered/pause", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 404
