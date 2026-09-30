"""
AdFatigueRadar — Production API & Serving Schemas (Phase 4)
===========================================================
Defines strict Pydantic v2 schemas for single/batch prediction,
health/readiness probes, metrics observability, drift monitoring, and error handling.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator


class NLPRequest(BaseModel):
    """Single comment inference request."""
    text: str = Field(..., description="Raw text of the comment to analyze", max_length=4000)
    comment_id: Optional[str] = Field(None, description="Optional client-provided unique identifier", max_length=128)
    campaign_id: Optional[str] = Field(None, description="Optional advertising campaign ID", max_length=128)
    ad_id: Optional[str] = Field(None, description="Optional ad creative ID", max_length=128)
    bypass_cache: bool = Field(False, description="Whether to bypass inference cache")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if v is None:
            raise ValueError("Input text cannot be null")
        if not isinstance(v, str):
            raise ValueError("Input text must be a string")
        if not v.strip():
            raise ValueError("Input text cannot be empty or whitespace-only")
        return v


class BatchNLPRequest(BaseModel):
    """Batch comment inference request."""
    items: List[NLPRequest] = Field(..., min_length=1, max_length=128, description="List of comment items (1 to 128)")
    bypass_cache: bool = Field(False, description="Whether to bypass cache for all items in batch")


class NLPResponse(BaseModel):
    """Frozen production NLP result contract."""
    comment_id: str = Field(..., description="Unique comment identifier")
    category: str = Field(..., description="Predicted 8-class taxonomy category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Temperature-calibrated posterior probability")
    sentiment: str = Field(..., description="3-class sentiment label ('positive', 'neutral', 'negative')")
    sentiment_score: float = Field(..., ge=0.0, le=1.0, description="Sentiment confidence score")
    probabilities: Dict[str, float] = Field(..., description="Calibrated probabilities across all 8 taxonomy classes")
    critical_complaint: bool = Field(..., description="Whether category is a complaint and confidence >= threshold")
    is_critical_complaint: bool = Field(..., description="Alias for critical_complaint adhering to person 2 contract")
    pii_redacted: bool = Field(False, description="Whether PII entities were scrubbed prior to tokenization")
    cached: bool = Field(False, description="Whether result was served from L1/L2 cache")
    model_version: str = Field(..., description="Version of the serving model")
    processing_time_ms: float = Field(..., ge=0.0, description="Wall-clock inference latency in milliseconds")


class BatchNLPResponse(BaseModel):
    """Batch inference response."""
    results: List[NLPResponse] = Field(..., description="Ordered list of predictions matching request items")
    total_items: int = Field(..., description="Total items processed")
    total_time_ms: float = Field(..., description="Total batch processing latency in milliseconds")
    batch_throughput_items_sec: float = Field(..., description="Effective throughput (items/sec)")


class HealthResponse(BaseModel):
    """Process liveness probe response."""
    status: str = Field("healthy", description="Process health state")
    timestamp_utc: str = Field(..., description="ISO 8601 UTC timestamp")
    uptime_seconds: float = Field(..., description="Server process uptime in seconds")


class ReadinessResponse(BaseModel):
    """Model readiness & integrity probe response."""
    status: str = Field("ready", description="Serving engine readiness state ('ready' or 'not_ready')")
    model_loaded: bool = Field(True, description="Whether model artifact is loaded into memory")
    checksum_verified: bool = Field(True, description="Whether SHA-256 artifact integrity matches manifest")
    device: str = Field(..., description="Active compute device ('cuda:0' or 'cpu')")
    device_name: Optional[str] = Field(None, description="Hardware device name (e.g., 'NVIDIA GeForce GTX 1650')")
    vram_allocated_mb: float = Field(0.0, description="VRAM currently allocated by PyTorch in MiB")
    model_version: str = Field(..., description="Serving model version")
    operational_threshold: float = Field(..., description="Operational critical complaint threshold (tau = 0.50)")
    timestamp_utc: str = Field(..., description="ISO 8601 UTC timestamp")


class MetricsResponse(BaseModel):
    """Runtime observability & performance telemetry."""
    total_requests: int = Field(..., description="Total prediction requests received")
    total_items_processed: int = Field(..., description="Total individual comments classified")
    cache_hits: int = Field(..., description="Total cache hits")
    cache_misses: int = Field(..., description="Total cache misses")
    cache_hit_ratio: float = Field(..., ge=0.0, le=1.0, description="Cache hit ratio")
    latency_p50_ms: float = Field(..., description="50th percentile latency in ms")
    latency_p95_ms: float = Field(..., description="95th percentile latency in ms")
    latency_p99_ms: float = Field(..., description="99th percentile latency in ms")
    avg_latency_ms: float = Field(..., description="Mean latency in ms")
    error_count: int = Field(0, description="Total unhandled/rejected request errors")
    active_device: str = Field(..., description="Active device ('cuda:0' or 'cpu')")
    vram_usage_mb: float = Field(..., description="VRAM in use (MiB)")


class DriftStatusResponse(BaseModel):
    """Prediction distribution drift status."""
    status: str = Field("NORMAL", description="Drift state ('NORMAL', 'WARNING', 'CRITICAL', 'INSUFFICIENT_DATA')")
    psi_score: float = Field(..., description="Population Stability Index across 8 taxonomy categories")
    js_divergence: float = Field(..., description="Jensen-Shannon divergence against baseline distribution")
    sample_window_size: int = Field(..., description="Number of observed live predictions in window")
    critical_complaint_rate: float = Field(..., description="Current critical complaint frequency in window")
    avg_confidence: float = Field(..., description="Mean confidence in window")
    low_confidence_rate: float = Field(..., description="Fraction of predictions with confidence < 0.40")
    baseline_distribution: Dict[str, float] = Field(..., description="Reference category distribution from Phase 3")
    current_distribution: Dict[str, float] = Field(..., description="Observed category distribution in window")
    last_evaluated_utc: str = Field(..., description="Timestamp of last drift evaluation")


class ErrorResponse(BaseModel):
    """Standard sanitized error response."""
    error: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="User-safe error explanation (no stack traces or internals)")
    request_id: Optional[str] = Field(None, description="Traceable request ID")
    timestamp_utc: str = Field(..., description="ISO 8601 UTC timestamp")
