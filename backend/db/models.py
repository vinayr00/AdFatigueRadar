from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CampaignRow(Base):
    __tablename__ = "campaigns"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    pre_block_state: Mapped[str | None] = mapped_column(String(32))
    budget: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class AdRow(Base):
    __tablename__ = "ads"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), index=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class CommentRow(Base):
    __tablename__ = "comments"
    comment_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    ad_id: Mapped[str] = mapped_column(String(128), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author_id_hmac: Mapped[str] = mapped_column(String(128), nullable=False)
    __table_args__ = (Index("ix_comments_campaign_timestamp", "campaign_id", "timestamp"),
                      Index("ix_comments_campaign_author_hmac", "campaign_id", "author_id_hmac"))


class NLPResultRow(Base):
    __tablename__ = "nlp_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    comment_id: Mapped[str] = mapped_column(ForeignKey("comments.comment_id", ondelete="CASCADE"), unique=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(32), nullable=False)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False)
    critical_complaint: Mapped[bool] = mapped_column(Boolean, nullable=False)


class TelemetryRow(Base):
    __tablename__ = "telemetry"
    event_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    ad_id: Mapped[str] = mapped_column(String(128), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    impressions: Mapped[float] = mapped_column(Float, nullable=False)
    clicks: Mapped[float] = mapped_column(Float, nullable=False)
    conversions: Mapped[float] = mapped_column(Float, nullable=False)
    spend: Mapped[float] = mapped_column(Float, nullable=False)
    reach: Mapped[float] = mapped_column(Float, nullable=False)
    revenue: Mapped[float | None] = mapped_column(Float)
    __table_args__ = (Index("ix_telemetry_campaign_timestamp", "campaign_id", "timestamp"),)


class RiskSnapshotRow(Base):
    __tablename__ = "risk_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    timestamp_simulated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    audience_risk: Mapped[float] = mapped_column(Float, nullable=False)
    economic_risk: Mapped[float | None] = mapped_column(Float)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    signals_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    __table_args__ = (Index("ix_risk_snapshots_campaign_timestamp", "campaign_id", "timestamp_simulated"),)


class ActionRow(Base):
    __tablename__ = "actions"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    timestamp_simulated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_state: Mapped[str | None] = mapped_column(String(32))
    new_state: Mapped[str | None] = mapped_column(String(32))
    result_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class AuditEventRow(Base):
    __tablename__ = "audit_events"
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), primary_key=True)
    audit_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    timestamp_simulated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_state: Mapped[str | None] = mapped_column(String(32))
    new_state: Mapped[str | None] = mapped_column(String(32))
    reason_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    risk_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    readback_verified: Mapped[bool | None] = mapped_column(Boolean)
    config_version: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    log_hash: Mapped[str | None] = mapped_column(String(128))
    __table_args__ = (Index("ix_audit_campaign_timestamp", "campaign_id", "timestamp_simulated"),)


class ThresholdOverrideRow(Base):
    __tablename__ = "threshold_overrides"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), index=True)
    overrides_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    config_version: Mapped[str] = mapped_column(String(128), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AutomationRuleRow(Base):
    __tablename__ = "automation_rules"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    settings_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class WorkspaceSettingsRow(Base):
    __tablename__ = "workspace_settings"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    settings_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class ReplaySessionRow(Base):
    __tablename__ = "replay_sessions"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), index=True)
    seed: Mapped[int | None] = mapped_column(Integer)
    speed: Mapped[float] = mapped_column(Float, nullable=False)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    started_at_simulated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reset_at_simulated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), nullable=False)


class UserRow(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(64), nullable=False, default="VIEWER")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

