from fastapi.testclient import TestClient

from backend.api.campaign_registry import _reset_registry_for_tests
from backend.main import app


def _client(monkeypatch):
    monkeypatch.setenv("ADFR_API_KEY", "test-api-key")
    monkeypatch.setenv("ADFR_HMAC_SECRET", "test-hmac-secret")
    _reset_registry_for_tests()
    return TestClient(app)


def test_frontend_campaign_create_list_detail_and_auth(monkeypatch):
    client = _client(monkeypatch)
    created = client.post("/api/campaigns", json={"name": "Demo", "platform": "meta"}, headers={"X-API-Key": "test-api-key"})
    assert created.status_code == 201
    campaign = created.json()
    assert campaign["name"] == "Demo"
    assert campaign["status"] == "ACTIVE"
    assert campaign["cpa"] is None
    assert client.get("/api/campaigns").json()[0]["id"] == campaign["id"]
    assert client.get(f"/api/campaigns/{campaign['id']}").json() == campaign
    assert client.post("/api/campaigns", json={"name": "Unauthorized"}).status_code == 401
    assert client.get("/api/campaigns/missing").status_code == 404


def test_analytics_and_replay_snapshot_use_empty_authoritative_runtime(monkeypatch):
    client = _client(monkeypatch)
    ctx = __import__("backend.api.campaign_registry", fromlist=["get_registry"]).get_registry().get_or_create("analytics-campaign")
    analytics = client.get("/api/analytics?campaign_id=analytics-campaign")
    assert analytics.status_code == 200
    body = analytics.json()
    assert body["impressions"]["value"] == 0
    assert body["risk_analysis"]["economic_risk"] is None
    assert body["risk_analysis"]["audience_risk"] == 0
    assert client.get("/api/replay/analytics-campaign/snapshot").json()["points"] == []
    assert client.get("/api/analytics?campaign_id=unknown").status_code == 404


def test_comparison_rejects_unknown_and_identical_campaigns(monkeypatch):
    client = _client(monkeypatch)
    registry = __import__("backend.api.campaign_registry", fromlist=["get_registry"]).get_registry()
    registry.get_or_create("a")
    registry.get_or_create("b")
    assert client.get("/api/comparisons?campaign_a=a&campaign_b=b").status_code == 200
    assert client.get("/api/comparisons?campaign_a=a&campaign_b=a").status_code == 422
    assert client.get("/api/comparisons?campaign_a=a&campaign_b=missing").status_code == 404
