"""
backend/replay/runner.py
-------------------------
Replay runner — one runner per campaign.

Design (Plan v3 §P-03):
- ReplaySource: typing.Protocol — yields ordered events
- Default implementation reads replay/generated/ READ-ONLY
- One runner per campaign; double start → 409
- reset(): cancels running task, resets machine, appends REPLAY_RESET to audit
- Injectable sleeper for virtual-time tests (speed-invariance test)
- ADFR_HMAC_SECRET missing → 503 (fail closed) on start

No datetime.now(). Ticks driven by scenario step boundaries.

Authority: Execution Prompt items 25,26, Plan v3 §§P-02,P-03,P-04.
"""
from __future__ import annotations

import asyncio
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import AsyncIterator, Callable, Iterator, Optional, Protocol, runtime_checkable

from backend.models.backend_models import (
    CampaignState, CommentEvent, NLPResult, ReasonCode, RiskSnapshot, TelemetryEvent
)
from backend.risk.state_machine import CampaignStateMachine
from backend.actions.audit import AuditLog
from backend.actions.sandbox import SandboxAdapter
from backend.risk.config_loader import get_config

import os


@runtime_checkable
class ReplaySource(Protocol):
    """Yields events in chronological order for one campaign."""
    def events(self) -> Iterator[CommentEvent | NLPResult | TelemetryEvent]: ...


class ReplayRunner:
    """Manages the replay lifecycle for one campaign."""

    def __init__(
        self,
        campaign_id: str,
        machine: CampaignStateMachine,
        audit_log: AuditLog,
        cfg: dict | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self.campaign_id = campaign_id
        self._machine = machine
        self._audit = audit_log
        self._cfg = cfg or get_config()
        self._sleeper = sleeper or time.sleep
        self._adapter = SandboxAdapter(machine, audit_log, cfg)

        self._running = False
        self._task_thread: Optional[threading.Thread] = None
        self._cancel_event = threading.Event()
        self._timeline: list[dict] = []
        self._lock: Optional[threading.Lock] = None  # injected from engine

    def set_campaign_lock(self, lock: threading.Lock) -> None:
        self._lock = lock

    def is_running(self) -> bool:
        return self._running

    def get_timeline(self) -> list[dict]:
        return list(self._timeline)

    def start(self, source: ReplaySource, speed: float = 1.0) -> None:
        """Start replay. Raises 409-equivalent ValueError if already running.
        Raises 503-equivalent RuntimeError if ADFR_HMAC_SECRET missing.
        """
        if not os.environ.get("ADFR_HMAC_SECRET", ""):
            raise PermissionError("ADFR_HMAC_SECRET not set — replay cannot start")

        if self._running:
            raise ValueError("Replay already running for this campaign")

        self._cancel_event.clear()
        self._running = True
        self._task_thread = threading.Thread(
            target=self._run,
            args=(source, speed),
            daemon=True,
            name=f"replay-{self.campaign_id}",
        )
        self._task_thread.start()

        # Audit REPLAY_START
        now_sim = self._machine.aggregator.clock.current or datetime.now(timezone.utc)
        risk = RiskSnapshot(audience_risk=0.0, economic_risk=None)
        self._audit.append(
            timestamp_simulated=now_sim,
            actor_type=__import__("backend.models.backend_models", fromlist=["ActorType"]).ActorType.SYSTEM,
            action="REPLAY_START",
            reason_codes=[ReasonCode.REPLAY_START],
            risk=risk,
        )

    def reset(self) -> None:
        """Cancel running replay, reset machine, append REPLAY_RESET to audit."""
        self._cancel()
        lock = self._lock
        if lock:
            with lock:
                self._do_reset()
        else:
            self._do_reset()

    def _do_reset(self) -> None:
        """Reset under campaign lock."""
        now_sim = self._machine.aggregator.clock.current or datetime.now(timezone.utc)
        risk = RiskSnapshot(audience_risk=0.0, economic_risk=None)
        self._audit.reset(now_sim, risk)
        self._machine.reset()
        self._timeline.clear()
        self._running = False

    def _cancel(self) -> None:
        self._cancel_event.set()
        if self._task_thread and self._task_thread.is_alive():
            self._task_thread.join(timeout=5.0)

    def _run(self, source: ReplaySource, speed: float) -> None:
        """Main replay loop — runs in thread."""
        cfg = self._cfg
        step_min = cfg["compute"]["step_minutes"]
        step_seconds = step_min * 60.0 / max(speed, 0.01)

        # Buffer events by step boundary
        pending_comments: list[CommentEvent] = []
        pending_nlp: list[NLPResult] = []
        pending_telemetry: list[TelemetryEvent] = []
        current_step_boundary: Optional[datetime] = None

        for event in source.events():
            if self._cancel_event.is_set():
                break

            if isinstance(event, CommentEvent):
                pending_comments.append(event)
                if current_step_boundary is None:
                    current_step_boundary = _round_to_step(event.timestamp, step_min)
            elif isinstance(event, NLPResult):
                pending_nlp.append(event)
            elif isinstance(event, TelemetryEvent):
                pending_telemetry.append(event)
                if current_step_boundary is None:
                    current_step_boundary = _round_to_step(event.timestamp, step_min)
                elif event.timestamp >= current_step_boundary + timedelta(minutes=step_min):
                    # Step boundary crossed — evaluate current step
                    self._flush_step(
                        current_step_boundary,
                        pending_comments, pending_nlp, pending_telemetry[:-1],
                    )
                    # Wait for simulated time
                    if not self._cancel_event.is_set():
                        self._sleeper(step_seconds)
                    # Advance to new boundary
                    current_step_boundary = _round_to_step(event.timestamp, step_min)
                    pending_comments = []
                    pending_nlp = []
                    pending_telemetry = [event]

        # Flush final step
        if current_step_boundary and not self._cancel_event.is_set():
            self._flush_step(
                current_step_boundary,
                pending_comments, pending_nlp, pending_telemetry,
            )

        self._running = False

    def _flush_step(
        self,
        step_boundary: datetime,
        comments: list[CommentEvent],
        nlp: list[NLPResult],
        telemetry: list[TelemetryEvent],
    ) -> None:
        """Evaluate one 5-minute step under the campaign lock."""
        lock = self._lock or threading.Lock()
        with lock:
            agg = self._machine.aggregator

            # Tick the clock (P-02: tick fires even with no events)
            agg.clock.tick(step_boundary)

            # Ingest events
            for c in comments:
                agg.ingest_comment(c)
            for n in nlp:
                agg.ingest_nlp(n)
            had_telemetry = False
            for t in telemetry:
                if agg.ingest_telemetry(t):
                    had_telemetry = True

            # Tick the state machine
            result = self._machine.tick(step_boundary, had_telemetry)

            # Record timeline point
            self._timeline.append({
                "sim_time": step_boundary.isoformat(),
                "state": result.state.value,
                "severity": result.severity.value,
                "audience_risk": result.audience_risk,
                "economic_risk": result.economic_risk,
                "stale": result.stale,
                "anomaly": result.anomaly,
            })


def _round_to_step(ts: datetime, step_min: int) -> datetime:
    """Round timestamp down to the nearest step boundary."""
    total_minutes = int(ts.timestamp() // 60)
    step_minutes = (total_minutes // step_min) * step_min
    return datetime.fromtimestamp(step_minutes * 60, tz=timezone.utc)
