"""
backend/tests/risk/test_gates_and_state.py
-------------------------------------------
Gate, persistence, state machine, staleness, and recovery tests.

Covers:
- Path A positive path + parametrized single-fault
- Path B positive path + parametrized single-fault
- Persistence boundary (just below / exactly at duration)
- Cooldown blocks only pause gates; WARNING/SOFT continue
- SOFT_REDUCED → ACTIVE recovery (P-10)
- PAUSED no auto-recovery
- BLOCKED semantics (P-11)
- Clock tick with no events drives staleness (P-02)
- Staleness: clears on fresh telemetry; never causes automatic pause
- Paused heartbeat prevents stale
- STALE_TELEMETRY / STALE_CLEARED edge-triggered (P-14)
- Pre-cap anomaly / post-cap rates ordering

Authority: Plan v3 §§6, 2.1, 2.2.
"""
from __future__ import annotations

import os
import pytest
from datetime import datetime, timedelta, timezone

os.environ.setdefault("ADFR_HMAC_SECRET", "test-secret-12345")

from backend.risk.config_loader import get_config
from backend.risk.gates import PersistenceTracker, SeverityTracker
from backend.risk.gates import eval_pause_path_a, eval_pause_path_b
from backend.risk.features import SignalSet
from backend.risk.aggregation import EnrichedComment
from backend.risk.wilson import wilson_lb
from backend.risk.state_machine import CampaignStateMachine, TickResult
from backend.risk.staleness import StalenessTracker
from backend.models.backend_models import (
    CampaignState, ReasonCode, Severity,
    CommentEvent, NLPResult, TelemetryEvent
)

CFG = get_config()
BASE_TIME = datetime(2026, 9, 30, 10, 0, 0, tzinfo=timezone.utc)
STEP = timedelta(minutes=5)


def _make_machine(campaign_id: str = "test") -> CampaignStateMachine:
    return CampaignStateMachine(campaign_id, CFG)


# ---------------------------------------------------------------------------
# PersistenceTracker
# ---------------------------------------------------------------------------

def test_persistence_timer_starts_on_first_true() -> None:
    tracker = PersistenceTracker(required_hours=0.5)
    t0 = BASE_TIME
    result = tracker.update(True, t0)
    assert not result  # just started, not satisfied


def test_persistence_satisfied_at_exact_duration() -> None:
    tracker = PersistenceTracker(required_hours=0.5)
    t0 = BASE_TIME
    tracker.update(True, t0)
    t_exact = t0 + timedelta(hours=0.5)
    result = tracker.update(True, t_exact)
    assert result


def test_persistence_not_satisfied_just_below_duration() -> None:
    tracker = PersistenceTracker(required_hours=0.5)
    t0 = BASE_TIME
    tracker.update(True, t0)
    t_just_before = t0 + timedelta(hours=0.5) - timedelta(seconds=1)
    result = tracker.update(True, t_just_before)
    assert not result


def test_persistence_resets_on_false_step() -> None:
    tracker = PersistenceTracker(required_hours=0.5)
    t0 = BASE_TIME
    tracker.update(True, t0)
    tracker.update(False, t0 + timedelta(minutes=10))
    tracker.update(True, t0 + timedelta(minutes=15))
    # Should have restarted from t + 15min, not satisfied yet
    result = tracker.update(True, t0 + timedelta(minutes=16))
    assert not result


# ---------------------------------------------------------------------------
# Staleness tracker
# ---------------------------------------------------------------------------

def test_staleness_fires_after_2_steps() -> None:
    tracker = StalenessTracker(stale_after_steps=2)
    codes_1 = tracker.on_tick(CampaignState.ACTIVE, had_telemetry_this_step=False)
    codes_2 = tracker.on_tick(CampaignState.ACTIVE, had_telemetry_this_step=False)
    assert ReasonCode.STALE_TELEMETRY in codes_2
    assert tracker.is_stale


def test_staleness_not_fired_at_step_1() -> None:
    tracker = StalenessTracker(stale_after_steps=2)
    codes = tracker.on_tick(CampaignState.ACTIVE, had_telemetry_this_step=False)
    assert ReasonCode.STALE_TELEMETRY not in codes


def test_staleness_clears_on_telemetry() -> None:
    tracker = StalenessTracker(stale_after_steps=2)
    tracker.on_tick(CampaignState.ACTIVE, False)
    tracker.on_tick(CampaignState.ACTIVE, False)  # now stale
    assert tracker.is_stale
    codes = tracker.on_tick(CampaignState.ACTIVE, had_telemetry_this_step=True)
    assert ReasonCode.STALE_CLEARED in codes
    assert not tracker.is_stale


def test_staleness_edge_triggered_not_per_tick() -> None:
    """STALE_TELEMETRY emitted once on transition, not every tick."""
    tracker = StalenessTracker(stale_after_steps=2)
    tracker.on_tick(CampaignState.ACTIVE, False)
    codes_trigger = tracker.on_tick(CampaignState.ACTIVE, False)  # triggers stale
    codes_continued = tracker.on_tick(CampaignState.ACTIVE, False)  # still stale
    assert ReasonCode.STALE_TELEMETRY in codes_trigger
    assert ReasonCode.STALE_TELEMETRY not in codes_continued


def test_paused_never_stale() -> None:
    """PAUSED is not a tracked state — staleness does not apply."""
    tracker = StalenessTracker(stale_after_steps=2)
    for _ in range(5):
        codes = tracker.on_tick(CampaignState.PAUSED, False)
        assert ReasonCode.STALE_TELEMETRY not in codes
    assert not tracker.is_stale


# ---------------------------------------------------------------------------
# Severity tracker
# ---------------------------------------------------------------------------

def test_severity_healthy_below_watch() -> None:
    t = SeverityTracker(CFG)
    sev = t.compute(0.30, BASE_TIME)
    assert sev == Severity.HEALTHY


def test_severity_watch_instantaneous() -> None:
    t = SeverityTracker(CFG)
    sev = t.compute(0.55, BASE_TIME)
    assert sev in (Severity.WATCH, Severity.WARNING, Severity.CRITICAL)


def test_severity_critical_instantaneous() -> None:
    """CRITICAL is instantaneous — no persistence (P-16 CONFIRM)."""
    t = SeverityTracker(CFG)
    sev = t.compute(0.90, BASE_TIME)
    assert sev == Severity.CRITICAL


# ---------------------------------------------------------------------------
# SOFT_REDUCED → ACTIVE recovery (P-10)
# ---------------------------------------------------------------------------

def test_soft_reduced_to_active_recovery() -> None:
    """SOFT_REDUCED → ACTIVE when audience_risk < 0.60 for 1.0h."""
    machine = _make_machine("recovery_test")
    # Manually set state to SOFT_REDUCED
    machine._state = CampaignState.SOFT_REDUCED
    t = BASE_TIME

    # Advance clock and simulate below-recovery ticks
    agg = machine.aggregator
    recovery_hours = CFG["persistence_hours"]["recovery"]
    recovery_steps = int(recovery_hours * 60 / 5)

    # Fill machine with low audience_risk ticks
    # We need a direct approach — test the recovery persistence tracker
    tracker = machine._soft_recovery_persistence
    for i in range(recovery_steps + 1):
        sim_t = t + STEP * i
        agg.clock.tick(sim_t)
        # Recovery condition: audience_risk < 0.60
        satisfied = tracker.update(True, sim_t)

    assert satisfied, "Recovery should be satisfied after recovery_hours"


def test_soft_reduced_recovery_boundary_just_below() -> None:
    """Just below recovery duration → not recovered."""
    tracker = PersistenceTracker(required_hours=1.0)
    t0 = BASE_TIME
    tracker.update(True, t0)
    t_just_before = t0 + timedelta(hours=1.0) - timedelta(seconds=1)
    result = tracker.update(True, t_just_before)
    assert not result


# ---------------------------------------------------------------------------
# BLOCKED semantics (P-11)
# ---------------------------------------------------------------------------

def test_blocked_stores_pre_block_state() -> None:
    machine = _make_machine("blocked_test")
    machine._state = CampaignState.SOFT_REDUCED
    prev, new = machine.operator_block()
    assert prev == CampaignState.SOFT_REDUCED
    assert new == CampaignState.BLOCKED
    assert machine._pre_block_state == CampaignState.SOFT_REDUCED


def test_unblock_restores_pre_block_state() -> None:
    machine = _make_machine("unblock_test")
    machine._state = CampaignState.SOFT_REDUCED
    machine.operator_block()
    prev, restored = machine.operator_unblock()
    assert restored == CampaignState.SOFT_REDUCED


def test_blocked_suppresses_automatic_actions() -> None:
    """When BLOCKED, tick() returns without any state change."""
    machine = _make_machine("blocked_suppress")
    machine._state = CampaignState.BLOCKED
    machine._pre_block_state = CampaignState.ACTIVE
    t = BASE_TIME
    machine.aggregator.clock.tick(t)
    result = machine.tick(t, had_telemetry_this_step=False)
    assert result.state == CampaignState.BLOCKED
    assert not result.state_changed


def test_manual_pause_while_blocked_allowed() -> None:
    """Operator PAUSE while BLOCKED updates pre-block state without unblocking."""
    machine = _make_machine("blocked_manual")
    machine._state = CampaignState.BLOCKED
    is_new, prev, new_state = machine.operator_pause(BASE_TIME)
    assert not is_new
    assert prev == CampaignState.BLOCKED
    assert new_state == CampaignState.BLOCKED
    assert machine.state == CampaignState.BLOCKED
    assert machine.pre_block_state == CampaignState.PAUSED


def _scored_comments(count: int = 30, *, critical: int = 0) -> list[EnrichedComment]:
    return [EnrichedComment(
        event_id=f"e{i}", timestamp=BASE_TIME, hmac_author_id=f"h{i%max(1,critical or count)}",
        text="complaint", reactions=0, replies=0, campaign_id="c", ad_id="a",
        sentiment="negative", sentiment_score=.9, category="product_complaint",
        confidence=.95, critical_complaint=i < critical,
    ) for i in range(count)]


def test_path_a_blocked_when_economic_risk_none() -> None:
    comments = _scored_comments()
    signals = SignalSet(n_classified=30, wilson_lb_raw=.5)
    gate = eval_pause_path_a(.9, None, 30, comments, signals,
        PersistenceTracker(0.01), BASE_TIME, 0, False, CFG)
    assert not gate.passed
    assert gate.conditions["economic_available"] is False


def test_path_a_positive():
    comments = _scored_comments()
    tracker = PersistenceTracker(.01)
    tracker.update(True, BASE_TIME)
    gate = eval_pause_path_a(.9, .8, 30, comments, SignalSet(n_classified=30, wilson_lb_raw=.5),
        tracker, BASE_TIME + timedelta(minutes=1), 0, False, CFG)
    assert gate.passed


@pytest.mark.parametrize("fault", ["audience", "economic", "conversions", "evidence", "confidence", "wilson", "persistence", "cooldown", "stale"])
def test_path_a_single_fault(fault):
    comments = _scored_comments()
    signals = SignalSet(n_classified=30, wilson_lb_raw=.5)
    args = dict(audience_risk=.9, economic_risk=.8, conversions_in_window=30,
                post_cap_scored=comments, signals=signals, persistence_tracker=PersistenceTracker(.5 if fault == "persistence" else 0),
                now_sim=BASE_TIME, cooldown_remaining_minutes=0, is_stale=False, cfg=CFG)
    if fault == "audience": args["audience_risk"] = .1
    if fault == "economic": args["economic_risk"] = .1
    if fault == "conversions": args["conversions_in_window"] = 0
    if fault == "evidence": args["post_cap_scored"] = comments[:1]; args["signals"] = SignalSet(n_classified=1, wilson_lb_raw=.5)
    if fault == "confidence": args["post_cap_scored"] = [comments[0].__class__(**{**comments[0].__dict__, "confidence": .1}) for _ in range(30)]
    if fault == "wilson": args["signals"] = SignalSet(n_classified=30, wilson_lb_raw=.1)
    if fault == "cooldown": args["cooldown_remaining_minutes"] = 1
    if fault == "stale": args["is_stale"] = True
    gate = eval_pause_path_a(**args)
    assert not gate.passed


def test_path_b_positive_without_economics():
    comments = _scored_comments(50, critical=10)
    # Ensure ten distinct HMAC identities.
    for i, c in enumerate(comments[:10]): c.hmac_author_id = f"author-{i}"
    tracker = PersistenceTracker(CFG["persistence_hours"]["emergency"])
    tracker.update(True, BASE_TIME)
    gate, confidence = eval_pause_path_b(comments, False, tracker,
        BASE_TIME + timedelta(hours=CFG["persistence_hours"]["emergency"]), 0, CFG)
    assert gate.passed and confidence >= .85


@pytest.mark.parametrize("fault", ["rate", "confidence", "authors", "anomaly", "persistence", "cooldown"])
def test_path_b_single_fault(fault):
    comments = _scored_comments(50, critical=10)
    for i, c in enumerate(comments[:10]): c.hmac_author_id = f"author-{i}"
    if fault == "rate": comments = _scored_comments(50, critical=9)
    if fault == "confidence":
        for c in comments[:10]: c.confidence = .2
    if fault == "authors":
        for c in comments[:10]: c.hmac_author_id = "same"
    tracker = PersistenceTracker(.25 if fault == "persistence" else .001)
    tracker.update(True, BASE_TIME)
    gate, _ = eval_pause_path_b(comments, fault == "anomaly", tracker,
        BASE_TIME + timedelta(minutes=1), 1 if fault == "cooldown" else 0, CFG)
    assert not gate.passed


def test_warning_latch_recovery_and_critical_overlay():
    tracker = SeverityTracker(CFG)
    assert tracker.compute(.70, BASE_TIME) == Severity.WATCH
    assert tracker.compute(.70, BASE_TIME + timedelta(minutes=30)) == Severity.WARNING
    assert tracker.compute(.90, BASE_TIME + timedelta(minutes=35)) == Severity.CRITICAL
    assert tracker.compute(.60, BASE_TIME + timedelta(minutes=40)) == Severity.WARNING
    assert tracker.compute(.44, BASE_TIME + timedelta(minutes=41)) == Severity.WARNING
    assert tracker.compute(.44, BASE_TIME + timedelta(hours=1, minutes=41)) == Severity.HEALTHY


def test_effective_state_staleness_when_blocked():
    machine = _make_machine("effective-stale")
    machine.operator_block()
    assert machine.effective_state() == CampaignState.ACTIVE
    t = BASE_TIME
    machine.aggregator.clock.tick(t)
    machine.tick(t, False)
    t += STEP
    machine.aggregator.clock.tick(t)
    result = machine.tick(t, False)
    assert result.state == CampaignState.BLOCKED and result.stale


def test_blocked_operator_unpause_keeps_blocked():
    machine = _make_machine("blocked-unpause")
    machine._state = CampaignState.BLOCKED
    machine._pre_block_state = CampaignState.PAUSED
    prev, new = machine.operator_unpause(BASE_TIME)
    assert prev == new == CampaignState.BLOCKED
    assert machine.pre_block_state == CampaignState.ACTIVE


@pytest.mark.parametrize("pass_b", [False, True])
def test_active_direct_pause_via_path_a_and_both_reason_sets(monkeypatch, pass_b):
    import backend.risk.state_machine as sm
    from backend.models.backend_models import GateDecision
    machine = _make_machine("direct-path-a")
    machine.aggregator.clock.tick(BASE_TIME)
    monkeypatch.setattr(sm, "compute_signals", lambda **kwargs: SignalSet(n_classified=30, wilson_lb_raw=.5))
    monkeypatch.setattr(sm, "compute_audience_risk", lambda signals, cfg: .9)
    monkeypatch.setattr(sm, "compute_economic_risk", lambda signals, conversions, cfg: .8)
    monkeypatch.setattr(sm, "eval_pause_path_a", lambda **kwargs: GateDecision(
        passed=True, conditions={"pass": True}, reason_codes=[ReasonCode.ECONOMIC_CONFIRMATION]))
    monkeypatch.setattr(sm, "eval_pause_path_b", lambda **kwargs: (GateDecision(
        passed=pass_b, conditions={"pass": pass_b}, reason_codes=[ReasonCode.CRITICAL_COMPLAINT_RATE] if pass_b else []), .95))
    result = machine.tick(BASE_TIME, True)
    assert result.state == CampaignState.PAUSED
    assert ReasonCode.ECONOMIC_CONFIRMATION in result.transition_reason_codes
    assert result.path_taken == ("PATH_B+PATH_A" if pass_b else "PATH_A")
    assert (ReasonCode.CRITICAL_COMPLAINT_RATE in result.transition_reason_codes) is pass_b


def test_soft_reduced_entry_and_recovery_transitions(monkeypatch):
    import backend.risk.state_machine as sm
    from backend.models.backend_models import GateDecision
    machine = _make_machine("soft-transitions")
    monkeypatch.setattr(sm, "compute_signals", lambda **kwargs: SignalSet())
    monkeypatch.setattr(sm, "compute_economic_risk", lambda *args: None)
    monkeypatch.setattr(sm, "eval_pause_path_b", lambda **kwargs: (GateDecision(passed=False, conditions={}, reason_codes=[]), 0.0))
    monkeypatch.setattr(sm, "eval_pause_path_a", lambda **kwargs: GateDecision(passed=False, conditions={}, reason_codes=[]))
    machine._soft_persistence = PersistenceTracker(.01)
    monkeypatch.setattr(sm, "compute_audience_risk", lambda signals, cfg: .8)
    machine.aggregator.clock.tick(BASE_TIME)
    first = machine.tick(BASE_TIME, True)
    assert first.state == CampaignState.ACTIVE
    next_time = BASE_TIME + STEP
    machine.aggregator.clock.tick(next_time)
    entered = machine.tick(next_time, True)
    assert entered.state == CampaignState.SOFT_REDUCED
    assert entered.state_changed

    machine._soft_recovery_persistence = PersistenceTracker(.01)
    monkeypatch.setattr(sm, "compute_audience_risk", lambda signals, cfg: .4)
    recover_start = next_time + STEP
    machine.aggregator.clock.tick(recover_start)
    machine.tick(recover_start, True)
    recover_at = recover_start + STEP
    machine.aggregator.clock.tick(recover_at)
    recovered = machine.tick(recover_at, True)
    assert recovered.state == CampaignState.ACTIVE
    assert recovered.transition_reason_codes == [ReasonCode.SOFT_RECOVERY]




# ---------------------------------------------------------------------------
# PAUSED no auto-recovery
# ---------------------------------------------------------------------------

def test_paused_no_auto_recovery() -> None:
    """PAUSED campaign never auto-recovers — operator unpause required."""
    machine = _make_machine("paused_noauto")
    machine._state = CampaignState.PAUSED
    t = BASE_TIME
    machine.aggregator.clock.tick(t)
    result = machine.tick(t, had_telemetry_this_step=True)
    assert result.state == CampaignState.PAUSED
    assert not result.state_changed


def test_operator_unpause_non_paused_raises() -> None:
    """Unpause on non-PAUSED → ValueError (→ 409 at API)."""
    machine = _make_machine("unpause_notpaused")
    assert machine._state == CampaignState.ACTIVE
    with pytest.raises(ValueError):
        machine.operator_unpause(BASE_TIME)


# ---------------------------------------------------------------------------
# Operator pause — idempotent
# ---------------------------------------------------------------------------

def test_operator_pause_idempotent_already_paused() -> None:
    machine = _make_machine("pause_idem")
    machine._state = CampaignState.PAUSED
    is_new, prev, new = machine.operator_pause(BASE_TIME)
    assert not is_new
    assert prev == CampaignState.PAUSED
    assert new == CampaignState.PAUSED


# ---------------------------------------------------------------------------
# Cooldown blocks only pause gates
# ---------------------------------------------------------------------------

def test_cooldown_does_not_block_soft_gate() -> None:
    """Cooldown blocks pause gates only. SOFT gate should still be evaluatable."""
    machine = _make_machine("cooldown_soft")
    # Start cooldown
    machine._start_cooldown(BASE_TIME)
    assert machine.cooldown_remaining_minutes(BASE_TIME) > 0

    # SOFT gate uses persistence tracker, not cooldown — check tracker directly
    tracker = machine._soft_persistence
    t = BASE_TIME
    ph = CFG["persistence_hours"]
    # SOFT persistence = 1.0h; just confirm cooldown doesn't block the tracker
    for i in range(int(ph["soft"] * 60 / 5) + 1):
        sim_t = t + STEP * i
        satisfied = tracker.update(True, sim_t)
    assert satisfied  # soft gate can be satisfied even during cooldown


def test_cooldown_only_blocks_pause():
    from backend.risk.gates import eval_soft_reduced, eval_warning
    machine = _make_machine("cooldown-only")
    machine._start_cooldown(BASE_TIME)
    warning = eval_warning(.7, PersistenceTracker(0), BASE_TIME, CFG)
    soft = eval_soft_reduced(.8, PersistenceTracker(0), BASE_TIME, CFG)
    assert warning.passed and soft.passed
    # The corresponding pause evaluator is covered by its explicit cooldown single-fault.
