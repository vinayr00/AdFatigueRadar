"""
AdFatigueRadar — Production FastAPI Server Application (Phase 4)
=================================================================
Provides hardened, secure REST endpoints for single/batch comment classification,
health/readiness probes, observability metrics, and prediction drift detection.
"""

import os
import sys
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.nlp.schemas import (
    NLPRequest,
    NLPResponse,
    BatchNLPRequest,
    BatchNLPResponse,
    HealthResponse,
    ReadinessResponse,
    MetricsResponse,
    DriftStatusResponse,
    ErrorResponse
)
from backend.nlp.serving_engine import ProductionServingEngine
from backend.nlp.drift_monitor import PredictionDriftMonitor
from backend.nlp.constants import MODEL_VERSION

# Instantiate FastAPI application with metadata
app = FastAPI(
    title="AdFatigueRadar Production NLP API",
    description="High-throughput, calibrated multi-signal ad comment analysis & fatigue detection API.",
    version=MODEL_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

APP_START_TIME = time.time()


# Global Exception Handlers ensuring zero internal leakages / stack traces
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Sanitizes validation errors into clean, structured JSON."""
    errors = exc.errors()
    msg = errors[0].get("msg", "Invalid request body") if errors else "Validation failed"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="ValidationError",
            message=msg,
            request_id=request.headers.get("x-request-id"),
            timestamp_utc=datetime.now(timezone.utc).isoformat()
        ).model_dump()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handles standard HTTP exceptions gracefully."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTPError",
            message=str(exc.detail),
            request_id=request.headers.get("x-request-id"),
            timestamp_utc=datetime.now(timezone.utc).isoformat()
        ).model_dump()
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catches unhandled errors and redacts internal traces."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected server error occurred. Please verify your request parameters.",
            request_id=request.headers.get("x-request-id"),
            timestamp_utc=datetime.now(timezone.utc).isoformat()
        ).model_dump()
    )


# --- Health & Readiness Endpoints ---

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Liveness probe confirming the server process is responsive."""
    return HealthResponse(
        status="healthy",
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=round(time.time() - APP_START_TIME, 2)
    )


import torch

@app.get("/ready", response_model=ReadinessResponse, tags=["Health"])
async def readiness_check():
    """Readiness probe verifying that model weights are loaded and checksums verified."""
    try:
        engine = ProductionServingEngine.get_instance()
        vram = (torch.cuda.memory_allocated(0) / (1024 ** 2)) if engine.device.type == "cuda" else 0.0
        dev_name = torch.cuda.get_device_name(0) if engine.device.type == "cuda" else "Host CPU"
        
        return ReadinessResponse(
            status="ready",
            model_loaded=True,
            checksum_verified=True,
            device=str(engine.device),
            device_name=dev_name,
            vram_allocated_mb=round(vram, 2),
            model_version=engine.bundle.model_version,
            operational_threshold=engine.bundle.operational_threshold,
            timestamp_utc=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Serving engine not ready: {str(e)}"
        )


# --- Core Prediction Endpoints ---

@app.post("/api/nlp/predict", response_model=NLPResponse, tags=["Inference"])
async def predict_single_comment(request: NLPRequest):
    """
    Classifies a single ad comment into 8-class taxonomy + 3-class sentiment.
    Applies PII sanitization, temperature calibration, and critical complaint gating.
    """
    engine = ProductionServingEngine.get_instance()
    drift_mon = PredictionDriftMonitor.get_instance()
    
    response = engine.predict_single(request)
    
    # Record to drift monitor
    drift_mon.record_prediction(
        category=response.category,
        confidence=response.confidence,
        is_critical=response.critical_complaint
    )
    
    return response


@app.post("/api/nlp/predict/batch", response_model=BatchNLPResponse, tags=["Inference"])
async def predict_batch_comments(batch_request: BatchNLPRequest):
    """
    High-throughput batched comment classification with VRAM safety chunking.
    """
    engine = ProductionServingEngine.get_instance()
    drift_mon = PredictionDriftMonitor.get_instance()
    
    response = engine.predict_batch(batch_request.items)
    
    # Record items to drift monitor
    for res in response.results:
        drift_mon.record_prediction(
            category=res.category,
            confidence=res.confidence,
            is_critical=res.critical_complaint
        )
        
    return response


# --- Observability & Monitoring Endpoints ---

@app.get("/api/nlp/metrics", response_model=MetricsResponse, tags=["Observability"])
async def get_runtime_metrics():
    """Returns real-time latency percentiles, throughput, and cache metrics."""
    engine = ProductionServingEngine.get_instance()
    return MetricsResponse(**engine.get_metrics())


@app.get("/api/nlp/drift", response_model=DriftStatusResponse, tags=["Observability"])
async def get_drift_status():
    """Returns current PSI & JS-divergence drift metrics against the Phase 3 baseline."""
    drift_mon = PredictionDriftMonitor.get_instance()
    return drift_mon.evaluate_drift()


@app.post("/api/nlp/drift/check", response_model=DriftStatusResponse, tags=["Observability"])
async def trigger_drift_check():
    """Forces an immediate evaluation of the active drift monitoring window."""
    drift_mon = PredictionDriftMonitor.get_instance()
    return drift_mon.evaluate_drift()


# Ensure backend/api package directory
os.makedirs(os.path.dirname(__file__), exist_ok=True)
