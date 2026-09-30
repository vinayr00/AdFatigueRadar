"""
backend/risk/gates.py
----------------------
Gate logic, PersistenceTracker, and severity computation.

Every gate returns GateDecision(passed, conditions, reason_codes).
ReasonCode values come from backend_models.py (single source).

Persistence (Execution Prompt item 2 — CONTINUOUS):
- Timer starts at first true step.
- Resets on any false step.
- Satisfied when now_sim - first_true_ts >= required_duration.

Severity (Plan v3 §P-16 [CONFIRM]):
- CRITICAL is instantaneous (≥ 0.85), display only, no action rights.
- WARNING requires persistence (0.5h).
- Recovery hysteresis applies per spec §11.6.

Cooldown (Execution Prompt item 10):
- Blocks ONLY pause gates (Path A, Path B).
- WARNING, SOFT, scoring, and severity continue during cooldown.

Action confidence (Execution Prompt item 15):
- Path A: min(mean classifier confidence of harmful comments, 1 - Wilson margin)
- Path B: mean NLP confidence of critical-flagged comments

Authority: SPEC §11, master spec §§11,12,13, Execution Prompt items 2,8,9,10,15,16.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from backend.models.backend_models import CampaignState, GateDecision, ReasonCode, Severity
from backend.risk.aggregation import EnrichedComment
from backend.risk.features import SignalSet
from backend.risk.wilson import wilson_lb, wilson_margin


# ---------------------------------------------------------------------------
# PersistenceTracker — continuous timer per gate
# ---------------------------------------------------------------------------

class PersistenceTracker:
    """Continuous persistence timer for a single gate condition.

    Timer starts at first true step. Resets on any false step.
    Satisfied when now_sim - first_true_ts >= required_hours.
    """

    def __init__(self, required_hours: float) -> None:
        self.required_hours = required_hours
        self._first_true_ts: Optional[datetime] = None

    def update(self, condition: bool, now_sim: datetime) -> bool:
        """Update tracker and return whether persistence is satisfied."""
        if not condition:
            self._first_true_ts = None
            return False
        if self._first_true_ts is None:
            self._first_true_ts = now_sim
        elapsed_hours = (now_sim - self._first_true_ts).total_seconds() / 3600.0
        return elapsed_hours >= self.required_hours

    def reset(self) -> None:
        self._first_true_ts = None

    @property
    def first_true_ts(self) -> Optional[datetime]:
        return self._first_true_ts


# ---------------------------------------------------------------------------
# Severity computation
# ---------------------------------------------------------------------------

class SeverityTracker:
    """Tracks severity with WARNING persistence and recovery hysteresis."""

    def __init__(self, cfg: dict) -> None:
        ag = cfg["audience_gates"]
        ph = cfg["persistence_hours"]
        self._watch_thresh = ag["watch"]
        self._warning_thresh = ag["warning"]
        self._soft_thresh = ag["soft"]
        self._critical_thresh = ag["critical"]
        self._warning_recovery = ag["warning_recovery"]
        self._soft_recovery = ag["soft_recovery"]
        self._warning_persistence_tracker = PersistenceTracker(ph["warning"])
        self._warning_recovery_tracker = PersistenceTracker(ph["recovery"])
        self._warning_latched = False

    def compute(self, audience_risk: float, now_sim: datetime) -> Severity:
        """Compute and return current severity.

        CRITICAL is instantaneous (P-16 [CONFIRM]).
        WARNING requires persistence.
        Recovery hysteresis per spec §11.6.
        """
        warning_condition = audience_risk >= self._warning_thresh
        warning_satisfied = self._warning_persistence_tracker.update(warning_condition, now_sim)
        if warning_satisfied:
            self._warning_latched = True

        # Keep WARNING latched until the full recovery interval completes.
        recovery_condition = audience_risk < self._warning_recovery
        if self._warning_latched:
            if self._warning_recovery_tracker.update(recovery_condition, now_sim):
                self._warning_latched = False
        else:
            self._warning_recovery_tracker.reset()

        # CRITICAL overlays a latched WARNING and carries no action rights.
        if audience_risk >= self._critical_thresh:
            return Severity.CRITICAL
        if self._warning_latched:
            return Severity.WARNING

        # WATCH: instantaneous
        if audience_risk >= self._watch_thresh:
            return Severity.WATCH
        return Severity.HEALTHY

    def reset(self) -> None:
        self._warning_persistence_tracker.reset()
        self._warning_recovery_tracker.reset()
        self._warning_latched = False


# ---------------------------------------------------------------------------
# Gate evaluators
# ---------------------------------------------------------------------------

def eval_watch(audience_risk: float, cfg: dict) -> GateDecision:
    thresh = cfg["audience_gates"]["watch"]
    passed = audience_risk >= thresh
    return GateDecision(
        passed=passed,
        conditions={"audience_risk_ge_watch": passed},
        reason_codes=[ReasonCode.AUDIENCE_RISK_HIGH] if passed else [],
    )


def eval_warning(
    audience_risk: float,
    persistence_tracker: PersistenceTracker,
    now_sim: datetime,
    cfg: dict,
) -> GateDecision:
    """Alert only — no state change."""
    thresh = cfg["audience_gates"]["warning"]
    condition = audience_risk >= thresh
    satisfied = persistence_tracker.update(condition, now_sim)
    return GateDecision(
        passed=satisfied,
        conditions={
            "audience_risk_ge_warning": condition,
            "persistence_satisfied": satisfied,
        },
        reason_codes=[ReasonCode.AUDIENCE_RISK_HIGH, ReasonCode.PERSISTENCE_MET] if satisfied else [],
    )


def eval_soft_reduced(
    audience_risk: float,
    persistence_tracker: PersistenceTracker,
    now_sim: datetime,
    cfg: dict,
) -> GateDecision:
    thresh = cfg["audience_gates"]["soft"]
    condition = audience_risk >= thresh
    satisfied = persistence_tracker.update(condition, now_sim)
    codes = []
    if satisfied:
        codes = [ReasonCode.AUDIENCE_RISK_HIGH, ReasonCode.PERSISTENCE_MET, ReasonCode.SOFT_REDUCTION]
    return GateDecision(
        passed=satisfied,
        conditions={
            "audience_risk_ge_soft": condition,
            "persistence_satisfied": satisfied,
        },
        reason_codes=codes,
    )


def eval_soft_recovery(
    audience_risk: float,
    recovery_tracker: PersistenceTracker,
    now_sim: datetime,
    cfg: dict,
) -> GateDecision:
    ag = cfg["audience_gates"]
    condition = audience_risk < ag["soft_recovery"]
    satisfied = recovery_tracker.update(condition, now_sim)
    codes = [ReasonCode.SOFT_RECOVERY] if satisfied else []
    return GateDecision(
        passed=satisfied,
        conditions={
            "audience_risk_lt_soft_recovery": condition,
            "persistence_satisfied": satisfied,
        },
        reason_codes=codes,
    )


def eval_pause_path_a(
    audience_risk: float,
    economic_risk: Optional[float],
    conversions_in_window: float,
    post_cap_scored: list[EnrichedComment],
    signals: SignalSet,
    persistence_tracker: PersistenceTracker,
    now_sim: datetime,
    cooldown_remaining_minutes: float,
    is_stale: bool,
    cfg: dict,
) -> GateDecision:
    """Path A — Economic Confirmation pause gate.

    Economic risk must not be None — is None check prevents false pause.
    Execution Prompt item 7: gate code uses `is None`, never falsy/== 0.
    """
    ag = cfg["audience_gates"]
    econ = cfg["economic"]
    ev = cfg["evidence"]

    n_scored = float(signals.n_classified)
    audience_ok = audience_risk >= ag["pause_audience"]
    economic_available = economic_risk is not None
    economic_ok = economic_available and economic_risk >= econ["pause_gate"]  # type: ignore[operator]
    conversions_ok = conversions_in_window >= econ["min_conversions_in_window"]

    # Evidence: min classified comments
    evidence_ok = n_scored >= ev["min_classified_comments"]

    # Classifier confidence: mean confidence of harmful-weighted scored comments
    harmful_comments = [
        c for c in post_cap_scored
        if c.category is not None
        and cfg["category_weights"].get(c.category, 0.0) > 0.0
        and c.confidence is not None
    ]
    mean_conf = (
        sum(c.confidence for c in harmful_comments) / len(harmful_comments)  # type: ignore[arg-type]
        if harmful_comments else 0.0
    )
    confidence_ok = mean_conf >= ev["min_classifier_confidence"]

    # Wilson LB threshold
    wilson_ok = (signals.wilson_lb_raw or 0.0) >= ev["harmful_wilson_lb_min"]

    # Cooldown
    cooldown_ok = cooldown_remaining_minutes <= 0.0

    # Staleness blocks Path A
    stale_ok = not is_stale

    core_condition = (
        audience_ok and economic_ok and conversions_ok
        and evidence_ok and confidence_ok and wilson_ok and stale_ok
    )
    persistence_satisfied = persistence_tracker.update(core_condition, now_sim)
    passed = persistence_satisfied and cooldown_ok

    codes: list[ReasonCode] = []
    if passed:
        codes = [ReasonCode.AUDIENCE_RISK_HIGH, ReasonCode.ECONOMIC_CONFIRMATION, ReasonCode.PERSISTENCE_MET]
    elif not economic_available:
        codes = [ReasonCode.ECONOMIC_UNAVAILABLE]
    elif not cooldown_ok:
        codes = [ReasonCode.COOLDOWN_ACTIVE]
    elif not evidence_ok:
        codes = [ReasonCode.INSUFFICIENT_EVIDENCE]

    return GateDecision(
        passed=passed,
        conditions={
            "audience_ok": audience_ok,
            "economic_available": economic_available,
            "economic_ok": economic_ok,
            "conversions_ok": conversions_ok,
            "evidence_ok": evidence_ok,
            "confidence_ok": confidence_ok,
            "wilson_ok": wilson_ok,
            "cooldown_ok": cooldown_ok,
            "stale_ok": stale_ok,
            "persistence_satisfied": persistence_satisfied,
        },
        reason_codes=codes,
    )


def eval_pause_path_b(
    post_cap_scored: list[EnrichedComment],
    anomaly: bool,
    persistence_tracker: PersistenceTracker,
    now_sim: datetime,
    cooldown_remaining_minutes: float,
    cfg: dict,
) -> tuple[GateDecision, float]:
    """Path B — Emergency Critical Complaint pause gate.

    No economic confirmation required.
    Returns (GateDecision, mean_confidence_of_critical_comments).
    """
    cc_cfg = cfg["critical_complaint"]
    pb = cfg.get("path_b", {})
    ev = cfg["evidence"]

    # Evidence definitions per Plan v3 §2.1 and Execution Prompt item 14
    scored = post_cap_scored
    critical_flagged = [
        c for c in scored
        if c.critical_complaint
        and c.category in cc_cfg["categories"]
        and (c.confidence or 0.0) >= cc_cfg["min_confidence"]
    ]
    n_scored = len(scored)

    rate = len(critical_flagged) / n_scored if n_scored > 0 else 0.0
    mean_conf = (
        sum(c.confidence for c in critical_flagged if c.confidence is not None)  # type: ignore[misc]
        / len([c for c in critical_flagged if c.confidence is not None])
        if any(c.confidence is not None for c in critical_flagged)
        else 0.0
    )
    distinct_authors = len({c.hmac_author_id for c in critical_flagged})

    rate_ok = rate >= cc_cfg["rate_min"]
    confidence_ok = mean_conf >= cc_cfg["min_confidence"]
    authors_ok = distinct_authors >= ev["min_distinct_authors"]
    anomaly_ok = not anomaly       # blocked when anomaly is True
    cooldown_ok = cooldown_remaining_minutes <= 0.0

    core_condition = rate_ok and confidence_ok and authors_ok and anomaly_ok
    persistence_satisfied = persistence_tracker.update(core_condition, now_sim)
    passed = persistence_satisfied and cooldown_ok

    codes: list[ReasonCode] = []
    if passed:
        codes = [ReasonCode.CRITICAL_COMPLAINT_RATE, ReasonCode.PERSISTENCE_MET]
    elif anomaly:
        codes = [ReasonCode.ANOMALY_DETECTED]
    elif not cooldown_ok:
        codes = [ReasonCode.COOLDOWN_ACTIVE]

    return GateDecision(
        passed=passed,
        conditions={
            "rate_ok": rate_ok,
            "confidence_ok": confidence_ok,
            "authors_ok": authors_ok,
            "anomaly_ok": anomaly_ok,
            "cooldown_ok": cooldown_ok,
            "persistence_satisfied": persistence_satisfied,
        },
        reason_codes=codes,
    ), mean_conf


def compute_path_a_confidence(
    harmful_comments: list[EnrichedComment],
    n_classified: float,
    k_eff: float,
    cfg: dict,
) -> float:
    """Action confidence for Path A.

    = min(mean classifier confidence of harmful-weighted comments,
          1 - Wilson margin at window n)
    """
    if not harmful_comments or n_classified <= 0:
        return 0.0
    mean_conf = sum(
        c.confidence for c in harmful_comments if c.confidence is not None  # type: ignore[misc]
    ) / len([c for c in harmful_comments if c.confidence is not None] or [1])
    margin = wilson_margin(k_eff, n_classified)
    return min(mean_conf, 1.0 - margin)
