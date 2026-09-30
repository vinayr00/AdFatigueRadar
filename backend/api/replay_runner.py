"""Person-2-owned API adapter for deterministic campaign replay orchestration.

The adapter extends the shared runner's storage/adapter construction, while
owning scheduling, cancellation, tick boundaries, and campaign audit integration.
Replay generation remains in the read-only source module.
"""
from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterator, Protocol, runtime_checkable

from backend.models.backend_models import (
    ActorType, CampaignState, CommentEvent, NLPResult, ReasonCode,
    RiskSnapshot, TelemetryEvent,
)
from backend.replay.runner import ReplayRunner as _SharedReplayRunner
from backend.risk.state_machine import TickResult


@runtime_checkable
class ReplaySource(Protocol):
    def events(self) -> Iterator[CommentEvent | NLPResult | TelemetryEvent]: ...


class ReplayRunner(_SharedReplayRunner):
    """API-owned deterministic runner; one instance is registered per campaign."""

    def __init__(self, campaign_id, machine, audit_log, cfg=None, sleeper: Callable[[float], None] | None = None):
        super().__init__(campaign_id, machine, audit_log, cfg, sleeper)
        self._interruptible_default_sleeper = sleeper is None
        self._last_sim_time: datetime | None = None
        self._latest_tick: TickResult | None = None
        self._start_audited = False
        self._runner_error: str | None = None

    @property
    def latest_tick(self) -> TickResult | None:
        return self._latest_tick

    def record_action_reference(self, sim_time: datetime, action_result) -> None:
        """Attach an operator action to the existing point at its simulated time."""
        if not action_result.audit_event_id or not self._timeline:
            return
        point = self._timeline[-1]
        if point.get("sim_time") != sim_time.isoformat():
            return
        point["state"] = action_result.new_state.value
        point["config_version"] = self._machine.config_version
        if action_result.audit_event_id not in point["action_events"]:
            point["action_events"].append(action_result.audit_event_id)
        reason_by_action = {
            "PAUSE": ReasonCode.OPERATOR_PAUSE,
            "UNPAUSE": ReasonCode.OPERATOR_UNPAUSE,
            "BLOCK": ReasonCode.OPERATOR_BLOCK,
            "UNBLOCK": ReasonCode.OPERATOR_UNBLOCK,
        }
        reason = reason_by_action.get(action_result.action)
        if reason is not None and reason.value not in point["reason_codes"]:
            point["reason_codes"].append(reason.value)

    def start(self, source: ReplaySource, speed: float = 1.0) -> None:
        if not os.environ.get("ADFR_HMAC_SECRET", ""):
            raise PermissionError("server secret unavailable")
        if self._running:
            raise ValueError("Replay already running for this campaign")
        if not 0 < speed <= 1000:
            raise ValueError("Replay speed must be > 0 and <= 1000")
        events = list(source.events())
        if not events:
            raise ValueError("Replay source contains no events")
        self._cancel_event.clear()
        self._running = True
        self._start_audited = False
        self._runner_error = None
        self._task_thread = threading.Thread(
            target=self._run_guarded, args=(events, speed), daemon=True,
            name=f"replay-{self.campaign_id}",
        )
        self._task_thread.start()

    def _run_guarded(self, events: list[object], speed: float) -> None:
        try:
            self._run(events, speed)
        except Exception:
            self._runner_error = "Replay failed"
            self._machine.set_action_unverified(True)
        finally:
            self._running = False

    def reset(self) -> None:
        if self._machine.aggregator.clock.current is None and self._last_sim_time is None:
            raise ValueError("No simulated time is available for replay reset audit")
        self._cancel()
        if self._lock:
            with self._lock:
                self._do_reset()
        else:
            self._do_reset()

    def _do_reset(self) -> None:
        now_sim = self._machine.aggregator.clock.current or self._last_sim_time
        if now_sim is None:
            raise ValueError("No simulated time is available for replay reset audit")
        self._audit.reset(now_sim, RiskSnapshot(audience_risk=0.0, economic_risk=None))
        self._machine.reset()
        self._adapter._sandbox_state = CampaignState.ACTIVE
        self._timeline.clear()
        self._latest_tick = None
        self._running = False
        self._start_audited = False
        self._runner_error = None

    def _cancel(self) -> None:
        self._cancel_event.set()
        if self._task_thread and self._task_thread.is_alive():
            self._task_thread.join()

    def _run(self, events: list[object], speed: float) -> None:
        step_min = self._cfg["compute"]["step_minutes"]
        step_seconds = step_min * 60.0 / speed
        comment_times = {e.event_id: e.timestamp for e in events if isinstance(e, CommentEvent)}
        fallback = min((getattr(e, "timestamp") for e in events if hasattr(e, "timestamp")), default=None)

        def event_time(event: object) -> datetime | None:
            stamp = getattr(event, "timestamp", None)
            if stamp is not None:
                return stamp
            if isinstance(event, NLPResult):
                return comment_times.get(event.comment_id, fallback)
            return fallback

        eligible = [event for event in events if event_time(event) is not None]
        eligible.sort(key=lambda e: (event_time(e), getattr(e, "event_id", getattr(e, "comment_id", ""))))
        if not eligible:
            self._running = False
            return
        buckets: dict[datetime, list[object]] = {}
        for event in eligible:
            stamp = event_time(event)
            assert stamp is not None
            boundary = _round_to_step(stamp, step_min)
            buckets.setdefault(boundary, []).append(event)
        boundary, last = min(buckets), max(buckets)
        while boundary <= last and not self._cancel_event.is_set():
            items = buckets.get(boundary, [])
            self._flush_step(
                boundary,
                [e for e in items if isinstance(e, CommentEvent)],
                [e for e in items if isinstance(e, NLPResult)],
                [e for e in items if isinstance(e, TelemetryEvent)],
            )
            boundary += timedelta(minutes=step_min)
            if boundary <= last and not self._cancel_event.is_set():
                if self._interruptible_default_sleeper:
                    self._cancel_event.wait(step_seconds)
                else:
                    self._sleeper(step_seconds)
        self._running = False

    def _flush_step(self, step_boundary, comments, nlp, telemetry) -> None:
        lock = self._lock or threading.Lock()
        with lock:
            agg = self._machine.aggregator
            agg.clock.tick(step_boundary)
            self._last_sim_time = step_boundary
            if not self._start_audited:
                self._audit.append(step_boundary, ActorType.SYSTEM, "REPLAY_START",
                    [ReasonCode.REPLAY_START], RiskSnapshot(audience_risk=0.0, economic_risk=None),
                    config_version=self._machine.config_version)
                self._start_audited = True

            for comment in comments:
                _, codes = agg.ingest_comment(comment)
                self._audit_codes(codes, step_boundary)
            for result in nlp:
                _, codes = agg.ingest_nlp(result)
                self._audit_codes(codes, step_boundary)
            had_telemetry = False
            for event in telemetry:
                if agg.ingest_telemetry(event):
                    had_telemetry = True

            result = self._machine.tick(step_boundary, had_telemetry)
            self._latest_tick = result
            self._audit_codes(result.staleness_audit_codes, step_boundary,
                              RiskSnapshot(audience_risk=result.audience_risk, economic_risk=result.economic_risk))
            if result.state_changed and result.state == CampaignState.PAUSED:
                self._adapter.system_pause(
                    step_boundary, result.action_confidence or 0.0,
                    result.transition_reason_codes, result.path_taken or "PATH_A",
                    RiskSnapshot(audience_risk=result.audience_risk, economic_risk=result.economic_risk),
                    previous_state=result.previous_state,
                    config_version=self._machine.config_version,
                )
                self._latest_tick = result
            elif result.state_changed:
                self._audit.append(
                    step_boundary, ActorType.SYSTEM,
                    result.transition_reason_codes[0].value if result.transition_reason_codes else "STATE_CHANGE",
                    result.transition_reason_codes,
                    RiskSnapshot(audience_risk=result.audience_risk, economic_risk=result.economic_risk),
                    previous_state=result.previous_state, new_state=result.state,
                    config_version=self._machine.config_version,
                )

            from backend.models.backend_models import SignalBreakdown, TimelinePoint
            signals = result.signals
            point = TimelinePoint(
                sim_time=step_boundary,
                state=self._machine.state,
                severity=result.severity,
                audience_risk=result.audience_risk,
                economic_risk=result.economic_risk,
                signal_breakdown=SignalBreakdown(
                    harmful_negative_ratio=signals.harmful_negative_ratio,
                    sentiment_decay=signals.sentiment_decay,
                    fatigue_mockery=signals.fatigue_mockery,
                    comment_acceleration=signals.comment_acceleration,
                    ctr_frequency=signals.ctr_frequency,
                    critical_complaint_signal=signals.critical_complaint_signal,
                    cpa_cpm_signal=signals.cpa_cpm_signal,
                    roas_conversion_signal=signals.roas_conversion_signal,
                ),
                stale=result.stale,
                anomaly=result.anomaly,
                action_events=[],
                reason_codes=result.reason_codes,
                cooldown_remaining_minutes=result.cooldown_remaining_minutes,
                config_version=self._machine.config_version,
            )
            action_names = {
                "PAUSE", "UNPAUSE", "BLOCK", "UNBLOCK",
                "SOFT_REDUCTION", "SOFT_RECOVERY",
            }
            point.action_events = list(dict.fromkeys(
                point.action_events + [
                    event.audit_id for event in self._audit.get_all()
                    if event.timestamp_simulated == step_boundary and event.action in action_names
                ]
            ))
            serialized = point.model_dump()
            serialized["sim_time"] = step_boundary.isoformat()
            serialized["state"] = point.state.value
            serialized["severity"] = point.severity.value
            serialized["signal_breakdown"] = point.signal_breakdown.model_dump()
            serialized["reason_codes"] = [code.value for code in point.reason_codes]
            self._timeline.append(serialized)

    def _audit_codes(self, codes, timestamp, risk=None) -> None:
        for code in codes:
            self._audit.append(
                timestamp, ActorType.SYSTEM, code.value, [code],
                risk or RiskSnapshot(audience_risk=0.0, economic_risk=None),
                config_version=self._machine.config_version,
            )


def _round_to_step(ts: datetime, step_min: int) -> datetime:
    total_minutes = int(ts.timestamp() // 60)
    step_minutes = (total_minutes // step_min) * step_min
    return datetime.fromtimestamp(step_minutes * 60, tz=timezone.utc)
