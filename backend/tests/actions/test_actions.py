from __future__ import annotations

import math
import os
import threading
from datetime import datetime, timezone

import pytest

os.environ.setdefault("ADFR_HMAC_SECRET", "test-secret")

from backend.actions.audit import AuditLog
from backend.actions.base import ActionSimulationError, apply
from backend.actions.readback import ReadbackVerifier
from backend.actions.sandbox import SandboxAdapter
from backend.models.backend_models import CampaignState, ReasonCode, RiskSnapshot, TelemetryEvent
from backend.risk.state_machine import CampaignStateMachine

T0 = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)


def potential() -> TelemetryEvent:
    return TelemetryEvent(event_id="t", timestamp=T0, campaign_id="c", ad_id="a", spend=100,
                          impressions=1000, reach=500, clicks=10, conversions=2, roas=3)


@pytest.mark.parametrize("state,mult", [(CampaignState.ACTIVE,1),(CampaignState.SOFT_REDUCED,.8),(CampaignState.PAUSED,0)])
def test_action_simulation_states(state, mult):
    result = apply(potential(), state)
    assert result.spend == 100 * mult
    assert result.impressions == 1000 * mult
    assert result.reach == 500 * mult
    assert result.clicks == 10 * mult
    assert result.conversions == 2 * mult


def test_action_simulation_blocked_uses_pre_state():
    result = apply(potential(), CampaignState.BLOCKED, pre_block_state=CampaignState.SOFT_REDUCED)
    assert result.spend == 80


def test_blocked_missing_pre_state_raises():
    with pytest.raises(ActionSimulationError):
        apply(potential(), CampaignState.BLOCKED)


def test_zero_volume_ratio_behavior_and_no_nan_or_inf():
    result = apply(potential(), CampaignState.PAUSED)
    assert (result.cpm, result.cpc, result.cpa, result.roas) == (None, None, None, None)
    for value in (result.spend, result.impressions, result.reach, result.clicks, result.conversions):
        assert math.isfinite(value)


def test_single_pause_idempotency_and_audit_every_state_change():
    machine, audit = CampaignStateMachine("c"), AuditLog("c")
    adapter = SandboxAdapter(machine, audit)
    risk = RiskSnapshot(audience_risk=.7)
    first = adapter.operator_pause(T0, risk)
    second = adapter.operator_pause(T0, risk)
    assert first.executed and not second.executed
    assert len(audit.get_all()) == 1
    assert audit.get_all()[0].audit_id == "audit_00001"


def test_concurrent_double_pause():
    machine, audit = CampaignStateMachine("c"), AuditLog("c")
    adapter = SandboxAdapter(machine, audit)
    lock = threading.Lock()
    results = []
    def pause():
        with lock:
            results.append(adapter.operator_pause(T0, RiskSnapshot(audience_risk=.2)))
    threads = [threading.Thread(target=pause) for _ in range(2)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sum(r.executed for r in results) == 1
    assert len(audit.get_all()) == 1


def test_sandbox_pause_readback_success():
    adapter = SandboxAdapter(CampaignStateMachine("c"), AuditLog("c"))
    result = adapter.operator_pause(T0, RiskSnapshot(audience_risk=.2))
    assert result.readback_verified and result.executed


def test_readback_getter_is_separate_sandbox_state():
    machine, audit = CampaignStateMachine("c"), AuditLog("c")
    adapter = SandboxAdapter(machine, audit)
    machine._state = CampaignState.PAUSED
    assert adapter._readback_getter() == CampaignState.ACTIVE


@pytest.mark.parametrize("getter", [lambda: CampaignState.ACTIVE, lambda: (_ for _ in ()).throw(RuntimeError("readback"))])
def test_readback_mismatch_and_exception(getter):
    verifier = ReadbackVerifier({"readback_max_retries": 2})
    failures = []
    ok, authoritative, exhausted = verifier.verify(CampaignState.PAUSED, getter, CampaignState.ACTIVE,
                                                    lambda reason, attempt: failures.append(attempt))
    assert not ok and exhausted and authoritative == CampaignState.ACTIVE
    assert failures == [1, 2]


def test_readback_retry_cap():
    verifier = ReadbackVerifier({"readback_max_retries": 3})
    attempts = []
    result = verifier.verify(CampaignState.PAUSED, lambda: CampaignState.ACTIVE, CampaignState.ACTIVE,
                             lambda reason, n: attempts.append(n))
    assert result == (False, CampaignState.ACTIVE, True)
    assert attempts == [1, 2, 3]


def test_no_cooldown_on_readback_failure():
    machine, audit = CampaignStateMachine("c"), AuditLog("c")
    adapter = SandboxAdapter(machine, audit)
    adapter._readback_getter = lambda: CampaignState.ACTIVE
    result = adapter.operator_pause(T0, RiskSnapshot(audience_risk=.2))
    assert not result.executed and not result.readback_verified
    assert machine._cooldown_until is None


def test_replay_reset_preserves_audit_history():
    audit = AuditLog("c")
    audit.append(T0, __import__("backend.models.backend_models", fromlist=["ActorType"]).ActorType.OPERATOR,
                 "PAUSE", [ReasonCode.OPERATOR_PAUSE], RiskSnapshot(audience_risk=.1))
    audit.reset(T0, RiskSnapshot(audience_risk=.1))
    entries = audit.get_all()
    assert [e.audit_id for e in entries] == ["audit_00001", "audit_00002"]
    assert entries[-1].reason_codes == [ReasonCode.REPLAY_RESET]


def test_audit_every_state_change_and_blocked_operator_actions():
    machine, audit = CampaignStateMachine("c"), AuditLog("c")
    adapter = SandboxAdapter(machine, audit)
    risk = RiskSnapshot(audience_risk=.1)
    adapter.operator_pause(T0, risk)
    adapter.operator_unpause(T0, risk)
    adapter.operator_block(T0, risk)
    adapter.operator_pause(T0, risk)
    assert machine.state == CampaignState.BLOCKED
    assert machine.pre_block_state == CampaignState.PAUSED
    adapter.operator_unpause(T0, risk)
    assert machine.state == CampaignState.BLOCKED
    assert machine.pre_block_state == CampaignState.ACTIVE
    adapter.operator_unblock(T0, risk)
    actions = [event.action for event in audit.get_all()]
    assert actions == ["PAUSE", "UNPAUSE", "BLOCK", "PAUSE", "UNPAUSE", "UNBLOCK"]


def test_replay_runner_reset_preserves_history():
    from backend.api.replay_runner import ReplayRunner
    machine, audit = CampaignStateMachine("c"), AuditLog("c")
    audit.append(T0, __import__("backend.models.backend_models", fromlist=["ActorType"]).ActorType.OPERATOR,
                 "OPERATOR_EVENT", [ReasonCode.OPERATOR_PAUSE], RiskSnapshot(audience_risk=.1))
    runner = ReplayRunner("c", machine, audit)
    machine.aggregator.clock.tick(T0)
    runner._last_sim_time = T0
    runner.reset()
    assert [e.audit_id for e in audit.get_all()] == ["audit_00001", "audit_00002"]
    assert audit.get_all()[-1].reason_codes == [ReasonCode.REPLAY_RESET]
    assert machine.state == CampaignState.ACTIVE


def test_operator_pause_racing_tick_is_serialized():
    machine, audit = CampaignStateMachine("c"), AuditLog("c")
    adapter = SandboxAdapter(machine, audit)
    lock = threading.Lock()
    def evaluate_tick():
        with lock:
            machine.aggregator.clock.tick(T0)
            machine.tick(T0, True)
    def pause():
        with lock:
            adapter.operator_pause(T0, RiskSnapshot(audience_risk=.1))
    threads = [threading.Thread(target=evaluate_tick), threading.Thread(target=pause)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert machine.state == CampaignState.PAUSED
    assert len(audit.get_all()) == 1
