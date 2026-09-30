"""
backend/risk/engine.py
-----------------------
Thin orchestrator — zero business logic.

Exposes get_or_create_machine() as the single access point for
per-campaign CampaignStateMachine instances.

Authority: Plan v3 §Step 1.8.
"""
from __future__ import annotations

import threading
from typing import Optional

from backend.risk.state_machine import CampaignStateMachine
from backend.risk.config_loader import get_config

_lock = threading.Lock()
_machines: dict[str, CampaignStateMachine] = {}
_campaign_locks: dict[str, threading.Lock] = {}  # per-campaign locks (P-04)


def get_or_create_machine(campaign_id: str) -> CampaignStateMachine:
    """Return (or create) the CampaignStateMachine for campaign_id."""
    with _lock:
        if campaign_id not in _machines:
            _machines[campaign_id] = CampaignStateMachine(campaign_id, get_config())
            _campaign_locks[campaign_id] = threading.Lock()
        return _machines[campaign_id]


def get_campaign_lock(campaign_id: str) -> threading.Lock:
    """Return the per-campaign lock. Creates the machine if it doesn't exist."""
    get_or_create_machine(campaign_id)
    return _campaign_locks[campaign_id]


def all_campaign_ids() -> list[str]:
    with _lock:
        return list(_machines.keys())


def _reset_all_for_tests() -> None:
    """Reset all state — for tests only."""
    global _machines, _campaign_locks
    with _lock:
        _machines = {}
        _campaign_locks = {}
