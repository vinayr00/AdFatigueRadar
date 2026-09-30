"""
backend/risk/state_machine.py
------------------------------
Campaign state machine and per-campaign risk evaluation coordinator.

Transitions (derived from gate outputs only — no hardcoded path assumptions):
  ACTIVE → SOFT_REDUCED  : SOFT gate passed
  ACTIVE → PAUSED        : Path B gate passed (direct jump)
  SOFT_REDUCED → PAUSED  : Path A or Path B gate passed
  SOFT_REDUCED → ACTIVE  : SOFT recovery gate passed (audience_risk < 0.60 for 1.0h) (P-10)
  PAUSED → ACTIVE        : operator unpause only (P0 — no auto-recovery)
  BLOCKED                : operator only via /override; stores pre_block_state (P-11)
  BLOCKED → pre_block_state: operator UNBLOCK

Rules:
- PAUSED never auto-recovers in P0.
- BLOCKED suppresses ALL automatic actions.
- Cooldown starts after pause or unpause; blocks only pause gates.
- Every state transition emits an audit event (via returned data).
- SOFT_REDUCED transition reason: SOFT_REDUCTION.
- SOFT_REDUCED recovery reason: SOFT_RECOVERY.

Authority: SPEC §§10,11, master spec §§11,15, Execution Prompt items 10,11, Plan v3 §§P-10,P-11.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from backend.models.backend_models import CampaignState, GateDecision, ReasonCode, Severity
from backend.risk.gates import (
    PersistenceTracker,
    SeverityTracker,
    compute_path_a_confidence,
    eval_pause_path_a,
    eval_pause_path_b,
    eval_soft_recovery,
    eval_soft_reduced,
)
from backend.risk.aggregation import CampaignAggregator
from backend.risk.features import compute_signals, SignalSet
from backend.risk.audience_risk import compute_audience_risk
from backend.risk.economic_risk import compute_economic_risk
from backend.risk.staleness import StalenessTracker
from backend.risk.config_loader import get_config


@dataclass
class TickResult:
    """Output of a single tick evaluation."""
    state: CampaignState
    severity: Severity
    audience_risk: float
    economic_risk: Optional[float]
    signals: SignalSet
    anomaly: bool
    top_author_share: float
    dup_cluster_share: float
    stale: bool
    cooldown_remaining_minutes: float
    reason_codes: list[ReasonCode]
    action_confidence: Optional[float]
    # State transition info
    previous_state: CampaignState
    state_changed: bool
    transition_reason_codes: list[ReasonCode]
    # Staleness audit codes (edge-triggered)
    staleness_audit_codes: list[ReasonCode]
    # Path A/B info for audit
    path_taken: Optional[str]   # "PATH_A" | "PATH_B" | None


class CampaignStateMachine:
    """Per-campaign state machine. Thread safety is the caller's responsibility."""

    def __init__(self, campaign_id: str, cfg: dict | None = None) -> None:
        self.campaign_id = campaign_id
        import copy
        self._base_cfg = copy.deepcopy(cfg or get_config())
        self._cfg = copy.deepcopy(self._base_cfg)
        self._override_count = 0

        # State
        self._state = CampaignState.ACTIVE
        self._pre_block_state: Optional[CampaignState] = None   # P-11
        self._cooldown_until: Optional[datetime] = None
        self._action_unverified: bool = False

        # Aggregation and signal infrastructure
        self.aggregator = CampaignAggregator(campaign_id, self._cfg)

        # Persistence trackers (one per gate)
        ph = self._cfg["persistence_hours"]
        self._warning_persistence = PersistenceTracker(ph["warning"])
        self._soft_persistence = PersistenceTracker(ph["soft"])
        self._soft_recovery_persistence = PersistenceTracker(ph["recovery"])
        self._path_a_persistence = PersistenceTracker(ph["pause"])
        self._path_b_persistence = PersistenceTracker(ph["emergency"])

        # Severity tracker
        self._severity_tracker = SeverityTracker(self._cfg)

        # Staleness tracker
        stale_steps = self._cfg["staleness"]["stale_after_steps"]
        self._staleness = StalenessTracker(stale_steps)

        # EWMA baseline state for sentiment decay
        self._ewma_baseline: Optional[float] = None
        self._prev_telemetry_sums: Optional[dict] = None
        self._step_count: int = 0

    @property
    def config_version(self) -> str:
        return f"thresholds_v4+override.{self._override_count}" if self._override_count else "thresholds_v4"

    @property
    def state(self) -> CampaignState:
        return self._state

    @property
    def pre_block_state(self) -> CampaignState | None:
        return self._pre_block_state

    def effective_state(self) -> CampaignState:
        if self._state == CampaignState.BLOCKED:
            return self._pre_block_state or CampaignState.ACTIVE
        return self._state

    @property
    def action_unverified(self) -> bool:
        return self._action_unverified

    def set_action_unverified(self, v: bool) -> None:
        self._action_unverified = v

    def cooldown_remaining_minutes(self, now_sim: datetime) -> float:
        if self._cooldown_until is None:
            return 0.0
        remaining = (self._cooldown_until - now_sim).total_seconds() / 60.0
        return max(0.0, remaining)

    def _start_cooldown(self, now_sim: datetime) -> None:
        cd_minutes = self._cfg["cooldown_minutes"]
        self._cooldown_until = now_sim + timedelta(minutes=cd_minutes)

    def _reset_persistence_trackers(self) -> None:
        """Reset all persistence trackers (e.g., after threshold override mid-run)."""
        self._warning_persistence.reset()
        self._soft_persistence.reset()
        self._soft_recovery_persistence.reset()
        self._path_a_persistence.reset()
        self._path_b_persistence.reset()

    # ------------------------------------------------------------------
    # Tick — main evaluation entry point
    # ------------------------------------------------------------------

    def tick(
        self,
        now_sim: datetime,
        had_telemetry_this_step: bool,
    ) -> TickResult:
        """Evaluate one 5-minute step. Called by replay runner after aggregation.

        No datetime.now(). All time from now_sim (simulated clock).
        """
        self._step_count += 1
        previous_state = self._state
        state_changed = False
        transition_reason_codes: list[ReasonCode] = []
        path_taken: Optional[str] = None

        # --- Staleness ---
        effective_state = self.effective_state()
        stale_codes = self._staleness.on_tick(effective_state, had_telemetry_this_step)

        # --- Window data ---
        anomaly, top_author_share, dup_cluster_share, post_cap = (
            self.aggregator.compute_anomaly_and_cap()
        )
        telem_sums = self.aggregator.get_telemetry_window_sums()
        rate_history = self.aggregator.get_comment_rate_history()

        # --- Baseline warm-up ---
        # Update EWMA baseline from current scored comments
        scored = [c for c in post_cap if c.category is not None]
        cw = self._cfg["category_weights"]
        alpha = self._cfg["compute"]["ewma_alpha"]
        if scored:
            from backend.risk.features import _polarity, _compute_ewma
            current_ewma = _compute_ewma([_polarity(c) * cw.get(c.category or "neutral", 0.0) for c in scored], alpha)
            warmup_steps = self._cfg["baseline"]["warmup_steps"]
            if self._ewma_baseline is None:
                self._ewma_baseline = current_ewma
            else:
                self._ewma_baseline = alpha * current_ewma + (1.0 - alpha) * self._ewma_baseline

        baseline_warm = (
            self._step_count >= self._cfg["baseline"]["warmup_steps"]
            and self._ewma_baseline is not None
        )

        # --- Signals ---
        signals = compute_signals(
            post_cap_comments=post_cap,
            telemetry_sums=telem_sums,
            rate_history=rate_history,
            baseline_ewma=self._ewma_baseline if baseline_warm else None,
            prev_telemetry_sums=self._prev_telemetry_sums if baseline_warm else None,
            cfg=self._cfg,
            step_count=self._step_count,
        )

        # --- Risk scores ---
        audience_risk = compute_audience_risk(signals, self._cfg)
        conversions = telem_sums.get("conversions", 0.0) or 0.0
        is_stale = self._staleness.is_stale

        # Economic N/A: stale forces None (Path A blocked)
        economic_risk = None if is_stale else compute_economic_risk(
            signals, conversions, self._cfg
        )

        # --- Cooldown ---
        cooldown_rem = self.cooldown_remaining_minutes(now_sim)

        # --- Gate evaluation ---
        all_reason_codes: list[ReasonCode] = []
        action_confidence: Optional[float] = None

        # BLOCKED: suppress all automatic actions
        if self._state == CampaignState.BLOCKED:
            severity = self._severity_tracker.compute(audience_risk, now_sim)
            return TickResult(
                state=self._state, severity=severity,
                audience_risk=audience_risk, economic_risk=economic_risk,
                signals=signals, anomaly=anomaly,
                top_author_share=top_author_share, dup_cluster_share=dup_cluster_share,
                stale=is_stale, cooldown_remaining_minutes=cooldown_rem,
                reason_codes=[], action_confidence=None,
                previous_state=previous_state, state_changed=False,
                transition_reason_codes=[], staleness_audit_codes=stale_codes,
                path_taken=None,
            )

        # PAUSED: no automatic transitions
        if self._state == CampaignState.PAUSED:
            severity = self._severity_tracker.compute(audience_risk, now_sim)
            return TickResult(
                state=self._state, severity=severity,
                audience_risk=audience_risk, economic_risk=economic_risk,
                signals=signals, anomaly=anomaly,
                top_author_share=top_author_share, dup_cluster_share=dup_cluster_share,
                stale=False, cooldown_remaining_minutes=cooldown_rem,
                reason_codes=[], action_confidence=None,
                previous_state=previous_state, state_changed=False,
                transition_reason_codes=[], staleness_audit_codes=stale_codes,
                path_taken=None,
            )

        # --- Pause gates (blocked during cooldown) ---
        if self._state in (CampaignState.ACTIVE, CampaignState.SOFT_REDUCED) and not state_changed:
            # Harmful comments for Path A confidence
            harmful_coms = [
                c for c in post_cap if c.category is not None
                and self._cfg["category_weights"].get(c.category, 0.0) > 0.0
            ]
            k_eff = sum(self._cfg["category_weights"].get(c.category or "neutral", 0.0) for c in post_cap if c.category)
            n_classified = float(signals.n_classified)

            path_b_gate, path_b_conf = eval_pause_path_b(
                post_cap_scored=post_cap,
                anomaly=anomaly,
                persistence_tracker=self._path_b_persistence,
                now_sim=now_sim,
                cooldown_remaining_minutes=cooldown_rem,
                cfg=self._cfg,
            )
            path_a_gate = eval_pause_path_a(
                audience_risk=audience_risk,
                economic_risk=economic_risk,
                conversions_in_window=conversions,
                post_cap_scored=post_cap,
                signals=signals,
                persistence_tracker=self._path_a_persistence,
                now_sim=now_sim,
                cooldown_remaining_minutes=cooldown_rem,
                is_stale=is_stale,
                cfg=self._cfg,
            )

            if path_b_gate.passed or path_a_gate.passed:
                confidence = compute_path_a_confidence(harmful_coms, n_classified, k_eff, self._cfg) if path_a_gate.passed else path_b_conf
                self._state = CampaignState.PAUSED
                state_changed = True
                # Deterministic Path B then Path A evaluation order; preserve
                # every passing path's evidence when both authorize a pause.
                transition_reason_codes = list(dict.fromkeys(
                    (path_b_gate.reason_codes if path_b_gate.passed else [])
                    + (path_a_gate.reason_codes if path_a_gate.passed else [])
                ))
                action_confidence = confidence
                path_taken = "PATH_B+PATH_A" if path_a_gate.passed and path_b_gate.passed else ("PATH_B" if path_b_gate.passed else "PATH_A")
                self._start_cooldown(now_sim)

        # --- SOFT_REDUCED entry ---
        if self._state == CampaignState.ACTIVE and not state_changed:
            soft_gate = eval_soft_reduced(audience_risk, self._soft_persistence, now_sim, self._cfg)
            if soft_gate.passed:
                self._state = CampaignState.SOFT_REDUCED
                state_changed = True
                transition_reason_codes = [ReasonCode.SOFT_REDUCTION]
                all_reason_codes.extend(soft_gate.reason_codes)
                self._soft_recovery_persistence.reset()

        # --- SOFT_REDUCED recovery follows both pause paths and entry checks. ---
        if self._state == CampaignState.SOFT_REDUCED and not state_changed:
            soft_recovery = eval_soft_recovery(
                audience_risk, self._soft_recovery_persistence, now_sim, self._cfg
            )
            if soft_recovery.passed:
                self._state = CampaignState.ACTIVE
                state_changed = True
                transition_reason_codes = [ReasonCode.SOFT_RECOVERY]
                self._soft_persistence.reset()
                self._path_a_persistence.reset()
                self._path_b_persistence.reset()
                all_reason_codes.extend(soft_recovery.reason_codes)

        # Store previous telemetry for delta computation
        self._prev_telemetry_sums = telem_sums

        # Severity, WARNING latch, and WATCH evaluation are the final tick phase.
        severity = self._severity_tracker.compute(audience_risk, now_sim)

        return TickResult(
            state=self._state,
            severity=severity,
            audience_risk=audience_risk,
            economic_risk=economic_risk,
            signals=signals,
            anomaly=anomaly,
            top_author_share=top_author_share,
            dup_cluster_share=dup_cluster_share,
            stale=is_stale,
            cooldown_remaining_minutes=cooldown_rem,
            reason_codes=all_reason_codes,
            action_confidence=action_confidence,
            previous_state=previous_state,
            state_changed=state_changed,
            transition_reason_codes=transition_reason_codes,
            staleness_audit_codes=stale_codes,
            path_taken=path_taken,
        )

    # ------------------------------------------------------------------
    # Operator actions (called from API layer with per-campaign lock held)
    # ------------------------------------------------------------------

    def operator_block(self) -> tuple[CampaignState, CampaignState]:
        """Block campaign. Returns (previous_state, new_state)."""
        prev = self._state
        if prev == CampaignState.BLOCKED:
            return prev, prev
        self._pre_block_state = self._state
        self._state = CampaignState.BLOCKED
        return prev, CampaignState.BLOCKED

    def operator_unblock(self) -> tuple[CampaignState, CampaignState]:
        """Unblock campaign. Returns (previous_state, new_state)."""
        prev = self._state
        if prev != CampaignState.BLOCKED:
            raise ValueError("Cannot unblock: campaign is not BLOCKED")
        restore = self._pre_block_state or CampaignState.ACTIVE
        self._state = restore
        self._pre_block_state = None
        return prev, restore

    def operator_pause(self, now_sim: datetime) -> tuple[bool, CampaignState, CampaignState]:
        """Manual operator pause. Bypasses gates/cooldown/anomaly.
        Returns (is_new_pause, previous_state, new_state).
        Idempotent: already PAUSED → (False, PAUSED, PAUSED).
        """
        if self._state == CampaignState.BLOCKED:
            self._pre_block_state = CampaignState.PAUSED
            return False, CampaignState.BLOCKED, CampaignState.BLOCKED
        if self._state == CampaignState.PAUSED:
            return False, CampaignState.PAUSED, CampaignState.PAUSED
        prev = self._state
        self._state = CampaignState.PAUSED
        self._start_cooldown(now_sim)
        return True, prev, CampaignState.PAUSED

    def operator_unpause(self, now_sim: datetime) -> tuple[CampaignState, CampaignState]:
        """Operator unpause. PAUSED → ACTIVE. Starts cooldown, resets persistence.
        Non-PAUSED → raises ValueError (409 at API layer).
        """
        if self._state == CampaignState.BLOCKED:
            self._pre_block_state = CampaignState.ACTIVE
            self._reset_persistence_trackers()
            return CampaignState.BLOCKED, CampaignState.BLOCKED
        if self._state != CampaignState.PAUSED:
            raise ValueError(f"Cannot unpause: campaign is {self._state.value}")
        prev = self._state
        self._state = CampaignState.ACTIVE
        self._start_cooldown(now_sim)
        self._reset_persistence_trackers()
        return prev, CampaignState.ACTIVE

    # ------------------------------------------------------------------
    # Reset (for replay/reset — P-03)
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset all state to ACTIVE. Preserves nothing (audit log is external)."""
        self._state = CampaignState.ACTIVE
        self._cfg = __import__("copy").deepcopy(self._base_cfg)
        self._override_count = 0
        self.aggregator._cfg = self._cfg
        self._pre_block_state = None
        self._cooldown_until = None
        self._action_unverified = False
        self._ewma_baseline = None
        self._prev_telemetry_sums = None
        self._step_count = 0
        self.aggregator.reset()
        ph = self._cfg["persistence_hours"]
        self._warning_persistence = PersistenceTracker(ph["warning"])
        self._soft_persistence = PersistenceTracker(ph["soft"])
        self._soft_recovery_persistence = PersistenceTracker(ph["recovery"])
        self._path_a_persistence = PersistenceTracker(ph["pause"])
        self._path_b_persistence = PersistenceTracker(ph["emergency"])
        self._severity_tracker = SeverityTracker(self._cfg)
        self._reset_persistence_trackers()
        self._staleness.reset()

    # ------------------------------------------------------------------
    # Runtime threshold override (P-17)
    # ------------------------------------------------------------------

    def apply_threshold_override(self, overrides: dict[str, float]) -> None:
        """Apply runtime threshold override. Resets persistence trackers.
        Applies from NEXT tick boundary (this is called before tick returns to API).
        """
        # Merge overrides into a copy of the base config
        import copy
        new_cfg = copy.deepcopy(self._cfg)
        for key, value in overrides.items():
            _set_nested(new_cfg, key, value)
        self._cfg = new_cfg
        self._override_count += 1
        # Reset persistence trackers so gates re-evaluate with new thresholds
        self._reset_persistence_trackers()

        # Rebuild persistence trackers with new durations
        ph = self._cfg["persistence_hours"]
        self._warning_persistence = PersistenceTracker(ph["warning"])
        self._soft_persistence = PersistenceTracker(ph["soft"])
        self._soft_recovery_persistence = PersistenceTracker(ph["recovery"])
        self._path_a_persistence = PersistenceTracker(ph["pause"])
        self._path_b_persistence = PersistenceTracker(ph["emergency"])
        self._severity_tracker = SeverityTracker(self._cfg)


def _set_nested(d: dict, dotted_key: str, value: object) -> None:
    """Set a value in a nested dict using dot notation."""
    keys = dotted_key.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value
