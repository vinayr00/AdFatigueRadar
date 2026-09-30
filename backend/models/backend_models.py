"""
backend/models/backend_models.py
---------------------------------
All typed models, enums, and contracts for Person 2 backend.
Single source of truth — imported everywhere, never re-defined.

Authority: Execution Prompt > SPEC §5,§16,§17 > Plan v3
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums — closed sets; adding a value requires a plan amendment
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    HEALTHY = "HEALTHY"
    WATCH = "WATCH"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class CampaignState(str, Enum):
    ACTIVE = "ACTIVE"
    SOFT_REDUCED = "SOFT_REDUCED"
    PAUSED = "PAUSED"
    BLOCKED = "BLOCKED"


class ActorType(str, Enum):
    SYSTEM = "SYSTEM"
    OPERATOR = "OPERATOR"


class ActionMode(str, Enum):
    SANDBOX = "SANDBOX"


class ReasonCode(str, Enum):
    """Closed enum — 23 codes exactly. Any addition requires a plan amendment."""
    AUDIENCE_RISK_HIGH = "AUDIENCE_RISK_HIGH"
    ECONOMIC_CONFIRMATION = "ECONOMIC_CONFIRMATION"
    ECONOMIC_UNAVAILABLE = "ECONOMIC_UNAVAILABLE"
    CRITICAL_COMPLAINT_RATE = "CRITICAL_COMPLAINT_RATE"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    PERSISTENCE_MET = "PERSISTENCE_MET"
    COOLDOWN_ACTIVE = "COOLDOWN_ACTIVE"
    BASELINE_WARMUP = "BASELINE_WARMUP"
    STALE_TELEMETRY = "STALE_TELEMETRY"
    STALE_CLEARED = "STALE_CLEARED"
    SOFT_REDUCTION = "SOFT_REDUCTION"
    SOFT_RECOVERY = "SOFT_RECOVERY"
    READBACK_FAILED = "READBACK_FAILED"
    ALREADY_PAUSED = "ALREADY_PAUSED"
    OPERATOR_PAUSE = "OPERATOR_PAUSE"
    OPERATOR_UNPAUSE = "OPERATOR_UNPAUSE"
    OPERATOR_BLOCK = "OPERATOR_BLOCK"
    OPERATOR_UNBLOCK = "OPERATOR_UNBLOCK"
    THRESHOLD_CHANGED = "THRESHOLD_CHANGED"
    REPLAY_START = "REPLAY_START"
    REPLAY_RESET = "REPLAY_RESET"
    UNKNOWN_CATEGORY = "UNKNOWN_CATEGORY"


# ---------------------------------------------------------------------------
# Frozen input contracts — schema-parity tested against replay/schemas/*
# ---------------------------------------------------------------------------

class CommentEvent(BaseModel):
    """Frozen contract §5.1. author_id is raw here; HMAC-replaced at ingestion boundary."""
    event_id: str
    timestamp: datetime          # UTC tz-aware
    campaign_id: str
    ad_id: str
    author_id: str               # raw — never stored after HMAC replacement
    text: str
    reactions: int = 0
    replies: int = 0

    @field_validator("timestamp")
    @classmethod
    def require_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return value

    model_config = {"frozen": True, "allow_inf_nan": False}


class TelemetryEvent(BaseModel):
    """Frozen contract §5.2. Ratio fields nullable — heartbeat carries nulls."""
    event_id: str
    timestamp: datetime
    campaign_id: str
    ad_id: str
    spend: float
    impressions: float
    reach: float
    clicks: float
    conversions: float
    cpm: Optional[float] = None  # nullable; heartbeat may carry null
    cpc: Optional[float] = None
    cpa: Optional[float] = None  # null, never inf, when conversions=0
    roas: Optional[float] = None

    @field_validator("timestamp")
    @classmethod
    def require_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return value

    model_config = {"frozen": True, "allow_inf_nan": False}


class NLPResult(BaseModel):
    """Frozen contract §5.3 / master spec §5. comment_id matches CommentEvent.event_id."""
    comment_id: str
    sentiment: str               # "positive" | "negative" | "neutral"
    sentiment_score: float = Field(ge=0, le=1)  # magnitude in [0,1]
    category: str                # one of 8 canonical categories
    confidence: float = Field(ge=0, le=1)
    critical_complaint: bool

    @field_validator("sentiment")
    @classmethod
    def validate_sentiment(cls, value: str) -> str:
        if value not in {"positive", "negative", "neutral"}:
            raise ValueError("unsupported sentiment")
        return value

    model_config = {"frozen": True, "allow_inf_nan": False}


# ---------------------------------------------------------------------------
# Internal typed models
# ---------------------------------------------------------------------------

class RiskSnapshot(BaseModel):
    """Typed risk dict for AuditEvent — survives null serialization."""
    audience_risk: float
    economic_risk: Optional[float] = None


class RiskScores(BaseModel):
    audience_risk: float
    economic_risk: Optional[float] = None  # None serialized as JSON null; never coerced to 0


class SignalBreakdown(BaseModel):
    harmful_negative_ratio: Optional[float] = None
    sentiment_decay: Optional[float] = None
    fatigue_mockery: Optional[float] = None
    comment_acceleration: Optional[float] = None
    ctr_frequency: Optional[float] = None
    critical_complaint_signal: Optional[float] = None
    cpa_cpm_signal: Optional[float] = None
    roas_conversion_signal: Optional[float] = None


class GateDecision(BaseModel):
    """Every gate returns this — never a bare bool."""
    passed: bool
    conditions: dict[str, bool]
    reason_codes: list[ReasonCode]


# ---------------------------------------------------------------------------
# Frozen output contracts — §16 Action/Readback, §17 Audit Event
# ---------------------------------------------------------------------------

class ActionResult(BaseModel):
    """Frozen schema §5.4 / §16."""
    action: str
    mode: ActionMode
    executed: bool
    confidence: Optional[float] = None
    reason: str                  # human sentence (frozen example from spec §16)
    previous_state: CampaignState
    new_state: CampaignState
    readback_verified: bool
    audit_event_id: str


class AuditEvent(BaseModel):
    """Frozen schema §5.5 / §17. confidence is additive optional (contract-change proposal)."""
    audit_id: str                # format: audit_%05d; sequential deterministic
    timestamp_simulated: datetime
    campaign_id: str
    actor_type: ActorType
    action: str
    previous_state: Optional[CampaignState] = None
    new_state: Optional[CampaignState] = None
    reason_codes: list[ReasonCode]
    risk: RiskSnapshot
    readback_verified: Optional[bool] = None
    config_version: str
    confidence: Optional[float] = None  # additive — contract-change proposal in report

    @field_validator("timestamp_simulated")
    @classmethod
    def require_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp_simulated must be timezone-aware")
        return value


class ReplayRecord(BaseModel):
    """Typed replay envelope; the event payload retains its frozen input model."""
    type: str
    event: CommentEvent | TelemetryEvent | NLPResult


# ---------------------------------------------------------------------------
# API response models
# ---------------------------------------------------------------------------

class StatusResponse(BaseModel):
    campaign_id: str
    state: CampaignState
    severity: Severity
    audience_risk: float
    economic_risk: Optional[float] = None   # null when N/A
    signal_breakdown: SignalBreakdown
    stale: bool
    anomaly: bool
    cooldown_remaining_minutes: Optional[float] = None
    config_version: str
    reason_codes: list[ReasonCode]
    sim_time: datetime
    action_unverified: bool = False          # set true after readback retry cap exhausted


class TimelinePoint(BaseModel):
    """One 5-minute tick entry in /timeline response."""
    sim_time: datetime
    state: CampaignState
    severity: Severity
    audience_risk: float
    economic_risk: Optional[float] = None
    signal_breakdown: SignalBreakdown
    stale: bool
    anomaly: bool
    action_events: list[str] = Field(default_factory=list)   # audit_ids of actions at this tick


# ---------------------------------------------------------------------------
# Threshold override request model
# ---------------------------------------------------------------------------

class ThresholdOverrideRequest(BaseModel):
    """Body for PUT /campaigns/{id}/thresholds.
    Only keys in the mutable-key allowlist are accepted.
    """
    overrides: dict[str, float]

    @model_validator(mode="before")
    @classmethod
    def reject_boolean_values(cls, value):
        if isinstance(value, dict):
            overrides = value.get("overrides", {})
            if isinstance(overrides, dict) and any(isinstance(item, bool) for item in overrides.values()):
                raise ValueError("threshold values must be numeric, not boolean")
        return value


# ---------------------------------------------------------------------------
# Operator override request model (P0: BLOCK/UNBLOCK only)
# ---------------------------------------------------------------------------

class OverrideRequest(BaseModel):
    action: str   # "BLOCK" or "UNBLOCK" only in P0; 422 on anything else
