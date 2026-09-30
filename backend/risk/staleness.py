"""
backend/risk/staleness.py
--------------------------
Staleness detection — only for ACTIVE and SOFT_REDUCED campaigns.

Rules (SPEC §12, Execution Prompt item 13, Plan v3):
- stale_after_steps: 2 consecutive steps without valid telemetry
- Only checks ACTIVE and SOFT_REDUCED
- While stale: economic_risk=None, Path A blocked
- STALE_TELEMETRY and STALE_CLEARED are EDGE-triggered (on transition), not every tick
- Stale NEVER causes automatic pause
- PAUSED campaigns are never stale (heartbeat keeps them alive)
- Fresh telemetry clears stale automatically
"""
from __future__ import annotations

from backend.models.backend_models import CampaignState, ReasonCode


class StalenessTracker:
    """Tracks staleness for one campaign."""

    def __init__(self, stale_after_steps: int = 2) -> None:
        self._stale_after_steps = stale_after_steps
        self._steps_without_telemetry: int = 0
        self._is_stale: bool = False

    @property
    def is_stale(self) -> bool:
        return self._is_stale

    def on_tick(
        self,
        state: CampaignState,
        had_telemetry_this_step: bool,
    ) -> list[ReasonCode]:
        """Call once per tick. Returns edge-triggered reason codes to audit."""
        if state not in (CampaignState.ACTIVE, CampaignState.SOFT_REDUCED):
            # Not a tracked state — reset counter, never mark stale
            if self._is_stale:
                self._is_stale = False
                return [ReasonCode.STALE_CLEARED]
            return []

        codes: list[ReasonCode] = []

        if had_telemetry_this_step:
            self._steps_without_telemetry = 0
            if self._is_stale:
                self._is_stale = False
                codes.append(ReasonCode.STALE_CLEARED)
        else:
            self._steps_without_telemetry += 1
            if not self._is_stale and self._steps_without_telemetry >= self._stale_after_steps:
                self._is_stale = True
                codes.append(ReasonCode.STALE_TELEMETRY)

        return codes

    def reset(self) -> None:
        self._steps_without_telemetry = 0
        self._is_stale = False
