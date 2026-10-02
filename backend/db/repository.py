from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func

from backend.db.models import (
    ActionRow,
    AuditEventRow,
    CampaignRow,
    ReplaySessionRow,
    RiskSnapshotRow,
    TelemetryRow,
    ThresholdOverrideRow,
    UserRow,
    WorkspaceSettingsRow,
)
from backend.db.session import SessionLocal


class PostgreSQLRepository:
    """Small persistence boundary; runtime state remains owned by the campaign machine."""

    @staticmethod
    def _session():
        if SessionLocal is None:
            return None
        return SessionLocal()

    _known_campaigns: set[str] = set()

    @classmethod
    def _ensure_campaign(cls, session, campaign_id: str, timestamp: datetime | None = None) -> None:
        if not campaign_id or campaign_id in cls._known_campaigns:
            return
        if session.get(CampaignRow, campaign_id) is None:
            now = timestamp or datetime.now(timezone.utc)
            session.add(CampaignRow(
                id=campaign_id,
                name=campaign_id,
                platform="meta",
                status="ACTIVE",
                created_at=now,
                metadata_json={},
            ))
            session.flush()
        cls._known_campaigns.add(campaign_id)

    def save_campaign(self, values: dict[str, Any]) -> None:
        session = self._session()
        if session is None:
            return
        try:
            row = session.get(CampaignRow, values["id"])
            if row is None:
                row = CampaignRow(**values)
                session.add(row)
            else:
                for key, value in values.items():
                    setattr(row, key, value)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list_campaigns(self) -> list[CampaignRow]:
        session = self._session()
        if session is None:
            return []
        try:
            return list(session.scalars(select(CampaignRow).order_by(CampaignRow.created_at)))
        finally:
            session.close()

    def get_campaign_view(self, campaign_id: str) -> dict[str, Any] | None:
        session = self._session()
        if session is None: return None
        try:
            campaign = session.get(CampaignRow, campaign_id)
            if campaign is None: return None
            totals = session.execute(select(
                func.coalesce(func.sum(TelemetryRow.spend), 0),
                func.coalesce(func.sum(TelemetryRow.impressions), 0),
                func.coalesce(func.sum(TelemetryRow.clicks), 0),
                func.coalesce(func.sum(TelemetryRow.conversions), 0),
                func.coalesce(func.sum(TelemetryRow.revenue), 0),
            ).where(TelemetryRow.campaign_id == campaign_id)).one()
            spend, impressions, clicks, conversions, revenue = map(float, totals)
            snapshot = session.scalar(select(RiskSnapshotRow).where(
                RiskSnapshotRow.campaign_id == campaign_id
            ).order_by(RiskSnapshotRow.timestamp_simulated.desc(), RiskSnapshotRow.id.desc()).limit(1))
            meta = campaign.metadata_json or {}
            return {"id": campaign.id, "name": campaign.name, "platform": campaign.platform,
                "status": campaign.status, "risk_score": snapshot.audience_risk if snapshot else 0.0,
                "impressions": impressions, "clicks": clicks, "conversions": conversions,
                "ctr": clicks / impressions if impressions else None,
                "cpa": spend / conversions if conversions else None,
                "cpm": spend * 1000 / impressions if impressions else None,
                "spend": spend, "roas": revenue / spend if spend else None,
                "date_range": "Persisted telemetry", "created_at": campaign.created_at.isoformat(),
                "thumbnail_url": meta.get("thumbnail_url", ""), "category": meta.get("category", ""),
                "target_audience": meta.get("target_audience", ""), "last_7_days_trend": []}
        finally:
            session.close()

    def get_campaign_state(self, campaign_id: str) -> tuple[str, str | None] | None:
        session = self._session()
        if session is None: return None
        try:
            row = session.get(CampaignRow, campaign_id)
            return (row.status, row.pre_block_state) if row else None
        finally:
            session.close()

    def save_campaign_state(self, campaign_id: str, state: str, pre_block_state: str | None) -> None:
        session = self._session()
        if session is None: return
        try:
            row = session.get(CampaignRow, campaign_id)
            if row:
                row.status = state
                row.pre_block_state = pre_block_state
                session.commit()
        except Exception:
            session.rollback(); raise
        finally:
            session.close()

    def list_audits(self, campaign_id: str | None = None) -> list[AuditEventRow]:
        session = self._session()
        if session is None: return []
        try:
            query = select(AuditEventRow)
            if campaign_id is not None:
                query = query.where(AuditEventRow.campaign_id == campaign_id)
            return list(session.scalars(query.order_by(AuditEventRow.timestamp_simulated, AuditEventRow.audit_id)))
        finally:
            session.close()

    def save_audit(self, event) -> None:
        session = self._session()
        if session is None:
            return
        try:
            self._ensure_campaign(session, event.campaign_id, event.timestamp_simulated)
            if session.get(AuditEventRow, (event.campaign_id, event.audit_id)) is None:
                session.add(AuditEventRow(
                    campaign_id=event.campaign_id, audit_id=event.audit_id,
                    timestamp_simulated=event.timestamp_simulated, actor_type=event.actor_type.value,
                    action=event.action, previous_state=event.previous_state.value if event.previous_state else None,
                    new_state=event.new_state.value if event.new_state else None,
                    reason_codes=[code.value for code in event.reason_codes],
                    risk_json=event.risk.model_dump(mode="json"), readback_verified=event.readback_verified,
                    config_version=event.config_version, confidence=event.confidence,
                ))
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def save_action(self, campaign_id: str, result, timestamp_simulated) -> None:
        values = result.model_dump(mode="json") if hasattr(result, "model_dump") else dict(result)
        audit_id = values.get("audit_event_id", values.get("id"))
        if not audit_id: return
        session = self._session()
        if session is None: return
        try:
            self._ensure_campaign(session, campaign_id, timestamp_simulated)
            if session.get(ActionRow, audit_id) is None:
                session.add(ActionRow(id=audit_id, campaign_id=campaign_id,
                    timestamp_simulated=timestamp_simulated, action=values["action"],
                    previous_state=values.get("previous_state"),
                    new_state=values.get("new_state"), result_json=values))
                session.commit()
        except Exception:
            session.rollback(); raise
        finally:
            session.close()

    def save_snapshot(self, campaign_id: str, tick, sim_time) -> None:
        session = self._session()
        if session is None:
            return
        try:
            self._ensure_campaign(session, campaign_id, sim_time)
            session.add(RiskSnapshotRow(
                campaign_id=campaign_id, timestamp_simulated=sim_time,
                audience_risk=tick.audience_risk, economic_risk=tick.economic_risk,
                state=tick.state.value, severity=tick.severity.value,
                signals_json={key: getattr(tick.signals, key) for key in (
                    "harmful_negative_ratio", "sentiment_decay", "fatigue_mockery",
                    "comment_acceleration", "ctr_frequency", "critical_complaint_signal",
                    "cpa_cpm_signal", "roas_conversion_signal")},
            ))
            campaign = session.get(CampaignRow, campaign_id)
            if campaign is not None:
                campaign.status = tick.state.value
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def save_comment(self, comment) -> None:
        from backend.db.models import CommentRow
        session = self._session()
        if session is None:
            return
        try:
            self._ensure_campaign(session, comment.campaign_id, comment.timestamp)
            if session.get(CommentRow, comment.event_id) is None:
                session.add(CommentRow(
                    comment_id=comment.event_id, campaign_id=comment.campaign_id,
                    ad_id=comment.ad_id, timestamp=comment.timestamp, text=comment.text,
                    author_id_hmac=comment.hmac_author_id,
                ))
                session.commit()
            # NLP can precede a comment at ingestion. Its row is inserted once
            # the foreign-key target exists, using the joined in-memory record.
            if comment.category is not None:
                self._save_joined_nlp(session, comment)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def save_comments(self, comments: list) -> None:
        if not comments:
            return
        from backend.db.models import CommentRow
        session = self._session()
        if session is None:
            return
        try:
            self._ensure_campaign(session, comments[0].campaign_id, comments[0].timestamp)
            for comment in comments:
                if session.get(CommentRow, comment.event_id) is None:
                    session.add(CommentRow(
                        comment_id=comment.event_id, campaign_id=comment.campaign_id,
                        ad_id=comment.ad_id, timestamp=comment.timestamp, text=comment.text,
                        author_id_hmac=comment.hmac_author_id,
                    ))
                if comment.category is not None:
                    self._save_joined_nlp(session, comment)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def save_nlp_result(self, result) -> None:
        from backend.db.models import CommentRow, NLPResultRow
        session = self._session()
        if session is None:
            return
        try:
            if session.get(CommentRow, result.comment_id) is None:
                return
            row = session.scalar(select(NLPResultRow).where(NLPResultRow.comment_id == result.comment_id))
            if row is None:
                session.add(NLPResultRow(
                    comment_id=result.comment_id, category=result.category, confidence=result.confidence,
                    sentiment=result.sentiment, sentiment_score=result.sentiment_score,
                    critical_complaint=result.critical_complaint,
                ))
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def save_nlp_results(self, results: list) -> None:
        if not results:
            return
        from backend.db.models import CommentRow, NLPResultRow
        session = self._session()
        if session is None:
            return
        try:
            for result in results:
                if session.get(CommentRow, result.comment_id) is None:
                    continue
                row = session.scalar(select(NLPResultRow).where(NLPResultRow.comment_id == result.comment_id))
                if row is None:
                    session.add(NLPResultRow(
                        comment_id=result.comment_id, category=result.category, confidence=result.confidence,
                        sentiment=result.sentiment, sentiment_score=result.sentiment_score,
                        critical_complaint=result.critical_complaint,
                    ))
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def _save_joined_nlp(session, comment) -> None:
        from backend.db.models import NLPResultRow
        row = session.scalar(select(NLPResultRow).where(NLPResultRow.comment_id == comment.event_id))
        if row is None:
            session.add(NLPResultRow(comment_id=comment.event_id, category=comment.category,
                confidence=comment.confidence or 0.0, sentiment=comment.sentiment or "neutral",
                sentiment_score=comment.sentiment_score or 0.0, critical_complaint=comment.critical_complaint))
            session.commit()

    def save_telemetry(self, event) -> None:
        from backend.db.models import TelemetryRow
        session = self._session()
        if session is None:
            return
        try:
            self._ensure_campaign(session, event.campaign_id, event.timestamp)
            if session.get(TelemetryRow, event.event_id) is None:
                session.add(TelemetryRow(
                    event_id=event.event_id, campaign_id=event.campaign_id, ad_id=event.ad_id,
                    timestamp=event.timestamp, impressions=event.impressions, clicks=event.clicks,
                    conversions=event.conversions, spend=event.spend, reach=event.reach,
                    revenue=(event.roas * event.spend if event.roas is not None else None),
                ))
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def save_telemetry_batch(self, events: list) -> None:
        if not events:
            return
        from backend.db.models import TelemetryRow
        session = self._session()
        if session is None:
            return
        try:
            self._ensure_campaign(session, events[0].campaign_id, events[0].timestamp)
            for event in events:
                if session.get(TelemetryRow, event.event_id) is None:
                    session.add(TelemetryRow(
                        event_id=event.event_id, campaign_id=event.campaign_id, ad_id=event.ad_id,
                        timestamp=event.timestamp, impressions=event.impressions, clicks=event.clicks,
                        conversions=event.conversions, spend=event.spend, reach=event.reach,
                        revenue=(event.roas * event.spend if event.roas is not None else None),
                    ))
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def save_threshold_override(self, campaign_id: str, overrides: dict, version: str, updated_at) -> None:
        session = self._session()
        if session is None:
            return
        try:
            self._ensure_campaign(session, campaign_id, updated_at)
            session.add(ThresholdOverrideRow(campaign_id=campaign_id, overrides_json=overrides,
                                             config_version=version, updated_at=updated_at))
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_latest_threshold_override(self, campaign_id: str) -> tuple[dict, str] | None:
        session = self._session()
        if session is None: return None
        try:
            row = session.scalar(select(ThresholdOverrideRow).where(
                ThresholdOverrideRow.campaign_id == campaign_id
            ).order_by(ThresholdOverrideRow.id.desc()).limit(1))
            return (dict(row.overrides_json), row.config_version) if row else None
        finally:
            session.close()

    def get_workspace_settings(self, settings_id: str = "workspace") -> dict | None:
        session = self._session()
        if session is None: return None
        try:
            row = session.get(WorkspaceSettingsRow, settings_id) or session.scalar(select(WorkspaceSettingsRow).limit(1))
            return dict(row.settings_json) if row else None
        finally:
            session.close()

    def save_workspace_settings(self, settings: dict, settings_id: str = "workspace") -> None:
        session = self._session()
        if session is None: return
        try:
            row = session.get(WorkspaceSettingsRow, settings_id)
            if row is None: session.add(WorkspaceSettingsRow(id=settings_id, settings_json=settings))
            else: row.settings_json = settings
            session.commit()
        except Exception:
            session.rollback(); raise
        finally:
            session.close()

    def save_replay_session(self, session_id: str, campaign_id: str, speed: float, status: str,
                            started_at=None, reset_at=None, config: dict | None = None) -> None:
        session = self._session()
        if session is None: return
        try:
            self._ensure_campaign(session, campaign_id, started_at)
            row = session.get(ReplaySessionRow, session_id)
            values = {"campaign_id": campaign_id, "speed": speed, "status": status,
                      "started_at_simulated": started_at, "reset_at_simulated": reset_at,
                      "config_json": config or {}}
            if row is None: session.add(ReplaySessionRow(id=session_id, **values))
            else:
                for key, value in values.items(): setattr(row, key, value)
            session.commit()
        except Exception:
            session.rollback(); raise
        finally:
            session.close()

    def get_user_by_email(self, email: str) -> UserRow | None:
        session = self._session()
        if session is None: return None
        try:
            return session.scalar(select(UserRow).where(UserRow.email == email))
        finally:
            session.close()

    def get_user(self, user_id: str) -> UserRow | None:
        session = self._session()
        if session is None: return None
        try:
            return session.get(UserRow, user_id)
        finally:
            session.close()

    def create_user(self, values: dict[str, Any]) -> UserRow | None:
        session = self._session()
        if session is None: return None
        try:
            val_copy = dict(values)
            now = datetime.now(timezone.utc)
            if "created_at" not in val_copy or val_copy["created_at"] is None:
                val_copy["created_at"] = now
            if "updated_at" not in val_copy or val_copy["updated_at"] is None:
                val_copy["updated_at"] = now
            row = UserRow(**val_copy)
            session.add(row)
            session.commit()
            return row
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list_users(self) -> list[UserRow]:
        session = self._session()
        if session is None: return []
        try:
            return list(session.scalars(select(UserRow).order_by(UserRow.created_at)))
        finally:
            session.close()

    def delete_user(self, user_id: str) -> bool:
        session = self._session()
        if session is None: return False
        try:
            row = session.get(UserRow, user_id)
            if row is not None:
                session.delete(row)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_campaign(self, campaign_id: str) -> bool:
        self._known_campaigns.discard(campaign_id)
        session = self._session()
        if session is None: return False
        try:
            row = session.get(CampaignRow, campaign_id)
            if row is not None:
                session.delete(row)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


repository = PostgreSQLRepository()
