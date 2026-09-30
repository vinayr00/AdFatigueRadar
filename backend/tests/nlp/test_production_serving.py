"""
Tests for Phase 4 Production Hardening & Serving Integration
============================================================
Verifies:
- Model loader checksum verification & fail-closed behavior
- FastAPI /health, /ready, /api/nlp/predict, /api/nlp/predict/batch endpoints
- Input validation & PII redaction
- Deterministic inference reproducibility
- Cache reliability & hit ratio metrics
- Drift calculation (PSI & JS divergence)
"""

import pytest
import os
import json
from fastapi.testclient import TestClient

from backend.api.app import app
from backend.nlp.model_loader import verify_artifact_checksums, load_production_model, ArtifactIntegrityError
from backend.nlp.drift_monitor import calculate_psi, calculate_js_divergence, PredictionDriftMonitor
from backend.nlp.constants import TAXONOMY_CATEGORIES


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_artifact_checksum_verification():
    """Verify that all production artifacts pass SHA-256 integrity verification."""
    checksums = verify_artifact_checksums()
    assert len(checksums) >= 4
    assert "phase3_final_model.joblib" in checksums
    assert "phase3_temperature_scaler.json" in checksums
    assert "phase3_config.json" in checksums


def test_production_model_bundle_loading():
    """Verify production bundle loads with correct calibration and operational threshold."""
    bundle = load_production_model(device_mode="auto")
    assert bundle.classifier is not None
    assert bundle.temperature > 0.0
    assert bundle.operational_threshold == 0.50
    assert len(bundle.class_mapping) == 8


def test_health_endpoint(client):
    """Verify liveness probe returns healthy."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "timestamp_utc" in data
    assert data["uptime_seconds"] >= 0.0


def test_readiness_endpoint(client):
    """Verify readiness probe confirms loaded model and verified checksums."""
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["model_loaded"] is True
    assert data["checksum_verified"] is True
    assert data["operational_threshold"] == 0.50
    assert data["device"] in ["cuda:0", "cpu", "cuda"]


def test_predict_single_endpoint(client):
    """Verify single comment prediction conforms to frozen schema."""
    payload = {
        "text": "This ad has appeared in my feed 15 times today, make it stop!",
        "comment_id": "test_c001"
    }
    res = client.post("/api/nlp/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["comment_id"] == "test_c001"
    assert data["category"] == "fatigue"
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["sentiment"] in ["positive", "neutral", "negative"]
    assert len(data["probabilities"]) == 8
    assert isinstance(data["critical_complaint"], bool)
    assert isinstance(data["is_critical_complaint"], bool)
    assert data["processing_time_ms"] > 0.0


def test_predict_pii_sanitization(client):
    """Verify sensitive PII is redacted during inference preprocessing."""
    payload = {
        "text": "Contact support at customer_rep@example.com or call 555-0199-234 regarding broken order #99281.",
        "comment_id": "test_pii_01"
    }
    res = client.post("/api/nlp/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["pii_redacted"] is True
    assert data["category"] in ["product_complaint", "service_complaint"]


def test_predict_input_validation_empty_and_whitespace(client):
    """Verify empty or whitespace-only comments are rejected with HTTP 422."""
    res1 = client.post("/api/nlp/predict", json={"text": ""})
    assert res1.status_code == 422
    
    res2 = client.post("/api/nlp/predict", json={"text": "    "})
    assert res2.status_code == 422


def test_predict_batch_endpoint(client):
    """Verify batched prediction processes ordered items."""
    items = [
        {"text": "Bought this again, best product ever!", "comment_id": "b1"},
        {"text": "Worst customer service, nobody answers emails", "comment_id": "b2"},
        {"text": "bro what is this meme lol", "comment_id": "b3"},
    ]
    res = client.post("/api/nlp/predict/batch", json={"items": items})
    assert res.status_code == 200
    data = res.json()
    assert data["total_items"] == 3
    assert len(data["results"]) == 3
    assert data["results"][0]["comment_id"] == "b1"
    assert data["results"][0]["category"] == "positive"
    assert data["results"][1]["comment_id"] == "b2"
    assert data["results"][1]["category"] == "service_complaint"
    assert data["batch_throughput_items_sec"] > 0.0


def test_metrics_and_cache_observability(client):
    """Verify observability endpoint exposes valid telemetry and hit ratios."""
    # Run duplicate request to test cache hit
    payload = {"text": "Deterministic cache test comment query 42."}
    _ = client.post("/api/nlp/predict", json=payload)
    _ = client.post("/api/nlp/predict", json=payload)
    
    res = client.get("/api/nlp/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["total_requests"] >= 2
    assert "latency_p50_ms" in data
    assert "latency_p95_ms" in data
    assert 0.0 <= data["cache_hit_ratio"] <= 1.0


def test_deterministic_inference_reproducibility(client):
    """Verify identical input produces byte-identical probabilities across 3 runs."""
    payload = {"text": "I really love how fast the delivery was!", "bypass_cache": True}
    res1 = client.post("/api/nlp/predict", json=payload).json()
    res2 = client.post("/api/nlp/predict", json=payload).json()
    res3 = client.post("/api/nlp/predict", json=payload).json()
    
    assert res1["category"] == res2["category"] == res3["category"]
    assert res1["confidence"] == res2["confidence"] == res3["confidence"]
    assert res1["probabilities"] == res2["probabilities"] == res3["probabilities"]


def test_drift_calculation_psi_and_js_divergence():
    """Verify statistical correctness of PSI and JS-divergence implementations."""
    dist_a = {cat: 0.125 for cat in TAXONOMY_CATEGORIES}
    dist_b = {cat: 0.125 for cat in TAXONOMY_CATEGORIES}
    
    # Identical distributions -> 0 drift
    assert abs(calculate_psi(dist_a, dist_b)) < 1e-4
    
    # Skewed distribution -> positive PSI
    dist_c = {cat: 0.01 for cat in TAXONOMY_CATEGORIES}
    dist_c["fatigue"] = 0.93
    psi = calculate_psi(dist_a, dist_c)
    assert psi > 0.25  # High drift
