"""
backend/actions/audit.py
-------------------------
Append-only audit log for all state-changing events.

Rules:
- IDs: audit_%05d, sequential, deterministic.
- Append-only — never modify existing entries.
- STALE_TELEMETRY and STALE_CLEARED: edge-triggered (on transition), not per tick.
- UNKNOWN_CATEGORY: once per (campaign, distinct category string) + counter.
- confidence: optional additive field (contract-change proposal).
- risk: typed RiskSnapshot so null survives serialization.
- Never log secrets, raw author IDs, or stack traces.

Replay reset preserves this log and appends REPLAY_RESET.
IDs keep counting across resets.

Authority: SPEC §17, Execution Prompt items 18, Plan v3 §P-14.
"""
from __future__ import annotations

import threading
from datetime import datetime
from typing import Optional

from backend.models.backend_models import (
    ActorType, AuditEvent, CampaignState, ReasonCode, RiskSnapshot
)


class AuditLog:
    """Thread-safe, append-only audit log for one campaign."""

    def __init__(self, campaign_id: str) -> None:
        self.campaign_id = campaign_id
        self._entries: list[AuditEvent] = []
        self._lock = threading.Lock()
        self._counter: int = 0  # keeps counting across resets
        from backend.db.repository import repository
        from backend.models.backend_models import ReasonCode
        for row in repository.list_audits(campaign_id):
            try:
                event = AuditEvent(
                    audit_id=row.audit_id, timestamp_simulated=row.timestamp_simulated,
                    campaign_id=row.campaign_id, actor_type=ActorType(row.actor_type),
                    action=row.action,
                    previous_state=CampaignState(row.previous_state) if row.previous_state else None,
                    new_state=CampaignState(row.new_state) if row.new_state else None,
                    reason_codes=[ReasonCode(code) for code in row.reason_codes],
                    risk=RiskSnapshot.model_validate(row.risk_json),
                    readback_verified=row.readback_verified, config_version=row.config_version,
                    confidence=row.confidence,
                )
                self._entries.append(event)
                self._counter = max(self._counter, int(row.audit_id.removeprefix("audit_")))
            except (ValueError, TypeError):
                # Corrupt historic rows are excluded from runtime state and remain
                # visible to DB operators; no stack trace or private data is logged.
                continue

    def append(
        self,
        timestamp_simulated: datetime,
        actor_type: ActorType,
        action: str,
        reason_codes: list[ReasonCode],
        risk: RiskSnapshot,
        previous_state: Optional[CampaignState] = None,
        new_state: Optional[CampaignState] = None,
        readback_verified: Optional[bool] = None,
        config_version: str = "thresholds_v4",
        confidence: Optional[float] = None,
    ) -> str:
        """Append an audit event. Returns the audit_id."""
        with self._lock:
            self._counter += 1
            audit_id = f"audit_{self._counter:05d}"
            entry = AuditEvent(
                audit_id=audit_id,
                timestamp_simulated=timestamp_simulated,
                campaign_id=self.campaign_id,
                actor_type=actor_type,
                action=action,
                previous_state=previous_state,
                new_state=new_state,
                reason_codes=reason_codes,
                risk=risk,
                readback_verified=readback_verified,
                config_version=config_version,
                confidence=confidence,
            )
            self._entries.append(entry)
        from backend.db.repository import repository
        repository.save_audit(entry)
        return audit_id

    def get_all(self) -> list[AuditEvent]:
        with self._lock:
            return list(self._entries)

    def get_latest(self, n: int) -> list[AuditEvent]:
        with self._lock:
            return list(self._entries[-n:])

    def reset(self, timestamp_simulated: datetime, risk: RiskSnapshot) -> str:
        """Preserve log, append REPLAY_RESET. IDs keep counting."""
        return self.append(
            timestamp_simulated=timestamp_simulated,
            actor_type=ActorType.SYSTEM,
            action="REPLAY_RESET",
            reason_codes=[ReasonCode.REPLAY_RESET],
            risk=risk,
        )
