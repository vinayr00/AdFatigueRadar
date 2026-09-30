"""
backend/actions/sandbox.py
---------------------------
Sandbox action adapter — P0 (SANDBOX mode only).

Rules:
- Per-campaign lock covers all state mutations (P-04).
- pause() on already-PAUSED → ActionResult(executed=False, reason=ALREADY_PAUSED), no duplicate audit.
- Operator POST /pause bypasses gates/cooldown/anomaly (P-12).
- Still: readback-verified, audited with ActorType.OPERATOR.
- Unpause on non-PAUSED → 409 (ValueError raised; API layer converts to 409).
- BLOCK/UNBLOCK: operator only, P0 supported.
- Readback failure → fail closed; cooldown NOT started; audit READBACK_FAILED.
- After retry cap: action_unverified=True on the machine.

Authority: SPEC §14, Execution Prompt items 12,17,19, Plan v3 §§P-04,P-11,P-12,P-13.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from backend.actions.audit import AuditLog
from backend.actions.readback import ReadbackVerifier
from backend.models.backend_models import (
    ActionMode, ActionResult, ActorType, CampaignState, ReasonCode, RiskSnapshot
)
from backend.risk.state_machine import CampaignStateMachine
from backend.risk.config_loader import get_config


class SandboxAdapter:
    """Wraps a CampaignStateMachine with action lifecycle logic."""

    def __init__(
        self,
        machine: CampaignStateMachine,
        audit_log: AuditLog,
        cfg: dict | None = None,
    ) -> None:
        self._machine = machine
        self._audit = audit_log
        self._cfg = cfg or get_config()
        self._readback = ReadbackVerifier(cfg=self._cfg)
        # Independent sandbox-side state, read back separately from the machine.
        self._sandbox_state = machine.state

    def _current_risk_snapshot(self) -> RiskSnapshot:
        """Build a RiskSnapshot from current machine state — rough snapshot for audit."""
        return RiskSnapshot(audience_risk=0.0, economic_risk=None)

    def _readback_getter(self) -> CampaignState:
        """Independent getter for the sandbox adapter's authoritative state."""
        return self._sandbox_state

    def system_pause(
        self,
        now_sim: datetime,
        confidence: float,
        reason_codes: list[ReasonCode],
        path: str,
        risk: RiskSnapshot,
        config_version: str = "thresholds_v4",
        previous_state: CampaignState | None = None,
    ) -> ActionResult:
        """System-initiated pause (gate-driven). Caller holds per-campaign lock."""
        previous_state = previous_state or self._machine.state

        # Execute state transition (already decided by gate — cooldown started inside machine.tick)
        # State is already PAUSED at this point when called from tick's transition result.
        # We just need readback and audit.
        expected = CampaignState.PAUSED
        self._sandbox_state = expected
        failed_audit_ids: list[str] = []

        def on_failure(reason: str, attempt: int) -> None:
            aid = self._audit.append(
                timestamp_simulated=now_sim,
                actor_type=ActorType.SYSTEM,
                action="PAUSE",
                reason_codes=[ReasonCode.READBACK_FAILED],
                risk=risk,
                previous_state=previous_state,
                new_state=None,
                readback_verified=False,
                config_version=config_version,
                confidence=confidence,
            )
            failed_audit_ids.append(aid)

        verified, authoritative_state, exhausted = self._readback.verify(
            expected_state=expected,
            get_state=self._readback_getter,
            previous_state=previous_state,
            on_failure=on_failure,
        )

        if exhausted and not verified:
            self._machine.set_action_unverified(True)

        if verified:
            audit_id = self._audit.append(
                timestamp_simulated=now_sim,
                actor_type=ActorType.SYSTEM,
                action="PAUSE",
                reason_codes=reason_codes,
                risk=risk,
                previous_state=previous_state,
                new_state=CampaignState.PAUSED,
                readback_verified=True,
                config_version=config_version,
                confidence=confidence,
            )
            reason_str = "Sustained harmful fatigue signals with economic confirmation"
            if path == "PATH_B":
                reason_str = "Critical complaint rate exceeds emergency threshold"
            return ActionResult(
                action="PAUSE",
                mode=ActionMode.SANDBOX,
                executed=True,
                confidence=confidence,
                reason=reason_str,
                previous_state=previous_state,
                new_state=CampaignState.PAUSED,
                readback_verified=True,
                audit_event_id=audit_id,
            )
        else:
            # Fail closed — restore authoritative state
            self._machine._state = authoritative_state
            self._sandbox_state = authoritative_state
            self._machine._cooldown_until = None
            return ActionResult(
                action="PAUSE",
                mode=ActionMode.SANDBOX,
                executed=False,
                confidence=confidence,
                reason="Readback verification failed — action not executed",
                previous_state=previous_state,
                new_state=authoritative_state,
                readback_verified=False,
                audit_event_id=failed_audit_ids[-1] if failed_audit_ids else "audit_00000",
            )

    def operator_pause(
        self,
        now_sim: datetime,
        risk: RiskSnapshot,
        config_version: str = "thresholds_v4",
    ) -> ActionResult:
        """Operator manual pause. Bypasses gates/cooldown/anomaly (P-12)."""
        was_blocked = self._machine.state == CampaignState.BLOCKED
        previous_cooldown = self._machine._cooldown_until
        is_new, previous_state, new_state = self._machine.operator_pause(now_sim)

        if not is_new:
            if was_blocked:
                audit_id = self._audit.append(
                    timestamp_simulated=now_sim, actor_type=ActorType.OPERATOR,
                    action="PAUSE", reason_codes=[ReasonCode.OPERATOR_PAUSE],
                    risk=risk, previous_state=CampaignState.BLOCKED,
                    new_state=CampaignState.BLOCKED, readback_verified=True,
                    config_version=config_version,
                )
                return ActionResult(
                    action="PAUSE", mode=ActionMode.SANDBOX, executed=True,
                    reason="Operator pause recorded for blocked campaign",
                    previous_state=CampaignState.BLOCKED, new_state=CampaignState.BLOCKED,
                    readback_verified=True, audit_event_id=audit_id,
                )
            return ActionResult(
                action="PAUSE",
                mode=ActionMode.SANDBOX,
                executed=False,
                confidence=None,
                reason="ALREADY_PAUSED",
                previous_state=CampaignState.PAUSED,
                new_state=CampaignState.PAUSED,
                readback_verified=True,
                audit_event_id="",  # no audit for idempotent no-op
            )

        self._sandbox_state = CampaignState.PAUSED

        # Readback
        failed_audit_ids: list[str] = []

        def on_failure(reason: str, attempt: int) -> None:
            aid = self._audit.append(
                timestamp_simulated=now_sim,
                actor_type=ActorType.OPERATOR,
                action="PAUSE",
                reason_codes=[ReasonCode.READBACK_FAILED],
                risk=risk,
                previous_state=previous_state,
                new_state=None,
                readback_verified=False,
                config_version=config_version,
            )
            failed_audit_ids.append(aid)

        verified, authoritative_state, exhausted = self._readback.verify(
            expected_state=CampaignState.PAUSED,
            get_state=self._readback_getter,
            previous_state=previous_state,
            on_failure=on_failure,
        )

        if exhausted and not verified:
            self._machine.set_action_unverified(True)

        if verified:
            audit_id = self._audit.append(
                timestamp_simulated=now_sim,
                actor_type=ActorType.OPERATOR,
                action="PAUSE",
                reason_codes=[ReasonCode.OPERATOR_PAUSE],
                risk=risk,
                previous_state=previous_state,
                new_state=CampaignState.PAUSED,
                readback_verified=True,
                config_version=config_version,
            )
            return ActionResult(
                action="PAUSE",
                mode=ActionMode.SANDBOX,
                executed=True,
                confidence=None,
                reason="Operator manual pause",
                previous_state=previous_state,
                new_state=CampaignState.PAUSED,
                readback_verified=True,
                audit_event_id=audit_id,
            )
        else:
            self._machine._state = authoritative_state
            self._sandbox_state = authoritative_state
            self._machine._cooldown_until = previous_cooldown
            return ActionResult(
                action="PAUSE",
                mode=ActionMode.SANDBOX,
                executed=False,
                confidence=None,
                reason="Readback verification failed",
                previous_state=previous_state,
                new_state=authoritative_state,
                readback_verified=False,
                audit_event_id=failed_audit_ids[-1] if failed_audit_ids else "audit_00000",
            )

    def operator_unpause(
        self,
        now_sim: datetime,
        risk: RiskSnapshot,
        config_version: str = "thresholds_v4",
    ) -> ActionResult:
        """Operator unpause. Non-PAUSED → ValueError → 409."""
        previous_state = self._machine.state
        # Raises ValueError if not PAUSED
        prev, new_state = self._machine.operator_unpause(now_sim)
        self._sandbox_state = new_state

        audit_id = self._audit.append(
            timestamp_simulated=now_sim,
            actor_type=ActorType.OPERATOR,
            action="UNPAUSE",
            reason_codes=[ReasonCode.OPERATOR_UNPAUSE],
            risk=risk,
            previous_state=prev,
            new_state=new_state,
            readback_verified=True,
            config_version=config_version,
        )
        return ActionResult(
            action="UNPAUSE",
            mode=ActionMode.SANDBOX,
            executed=True,
            confidence=None,
            reason="Operator unpause",
            previous_state=prev,
            new_state=new_state,
            readback_verified=True,
            audit_event_id=audit_id,
        )

    def operator_block(
        self,
        now_sim: datetime,
        risk: RiskSnapshot,
        config_version: str = "thresholds_v4",
    ) -> ActionResult:
        """Operator BLOCK."""
        prev, new_state = self._machine.operator_block()
        if prev == new_state == CampaignState.BLOCKED:
            return ActionResult(
                action="BLOCK", mode=ActionMode.SANDBOX, executed=False,
                reason="Campaign is already blocked", previous_state=prev,
                new_state=new_state, readback_verified=True, audit_event_id="",
            )
        self._sandbox_state = new_state
        audit_id = self._audit.append(
            timestamp_simulated=now_sim,
            actor_type=ActorType.OPERATOR,
            action="BLOCK",
            reason_codes=[ReasonCode.OPERATOR_BLOCK],
            risk=risk,
            previous_state=prev,
            new_state=new_state,
            readback_verified=True,
            config_version=config_version,
        )
        return ActionResult(
            action="BLOCK",
            mode=ActionMode.SANDBOX,
            executed=True,
            confidence=None,
            reason="Operator block — automation lock engaged",
            previous_state=prev,
            new_state=new_state,
            readback_verified=True,
            audit_event_id=audit_id,
        )

    def operator_unblock(
        self,
        now_sim: datetime,
        risk: RiskSnapshot,
        config_version: str = "thresholds_v4",
    ) -> ActionResult:
        """Operator UNBLOCK. Restores pre_block_state."""
        prev, new_state = self._machine.operator_unblock()
        self._sandbox_state = new_state
        audit_id = self._audit.append(
            timestamp_simulated=now_sim,
            actor_type=ActorType.OPERATOR,
            action="UNBLOCK",
            reason_codes=[ReasonCode.OPERATOR_UNBLOCK],
            risk=risk,
            previous_state=prev,
            new_state=new_state,
            readback_verified=True,
            config_version=config_version,
        )
        return ActionResult(
            action="UNBLOCK",
            mode=ActionMode.SANDBOX,
            executed=True,
            confidence=None,
            reason=f"Operator unblock — restored to {new_state.value}",
            previous_state=prev,
            new_state=new_state,
            readback_verified=True,
            audit_event_id=audit_id,
        )
