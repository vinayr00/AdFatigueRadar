"""
backend/actions/readback.py
----------------------------
Readback verification — reads state from the sandbox store INDEPENDENTLY
of the variable just written (not from the same in-memory reference).

Rules:
- Mismatch or exception → readback_verified=False, executed=False
- Authoritative state = readback result (or previous_state on exception)
- Audit READBACK_FAILED on each attempt (once per attempt, not per tick)
- Cooldown NOT started on readback failure
- Retry cap: readback_max_retries from YAML (P-13)
- After exhausting retries: action_unverified=True in status, stop auto-retrying

Authority: SPEC §14, Execution Prompt item 17, Plan v3 §P-13.
"""
from __future__ import annotations

import threading
from typing import Callable, Optional

from backend.models.backend_models import CampaignState
from backend.risk.config_loader import get_config


class ReadbackVerifier:
    """Manages readback verification with retry cap."""

    def __init__(self, cfg: dict | None = None) -> None:
        self._cfg = cfg or get_config()
        self._max_retries: int = self._cfg.get("readback_max_retries", 3)

    def verify(
        self,
        expected_state: CampaignState,
        get_state: Callable[[], CampaignState],
        previous_state: CampaignState,
        on_failure: Callable[[str, int], None],  # (reason, attempt_number)
    ) -> tuple[bool, CampaignState, bool]:
        """Run readback with retry cap.

        Args:
            expected_state:  State we expect to read back.
            get_state:       Independent getter — reads from store, not from written var.
            previous_state:  State before the action (authoritative on exception).
            on_failure:      Called once per failed attempt with reason and attempt number.

        Returns:
            (verified: bool, authoritative_state: CampaignState, retries_exhausted: bool)
        """
        for attempt in range(1, self._max_retries + 1):
            try:
                actual = get_state()
                if actual == expected_state:
                    return True, actual, False
                else:
                    on_failure(
                        f"Readback mismatch: expected {expected_state.value}, got {actual.value}",
                        attempt,
                    )
                    if attempt >= self._max_retries:
                        return False, actual, True
            except Exception as exc:
                on_failure(f"Readback exception attempt {attempt}: {exc}", attempt)
                if attempt >= self._max_retries:
                    return False, previous_state, True

        return False, previous_state, True
