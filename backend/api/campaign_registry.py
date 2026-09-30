"""
backend/api/campaign_registry.py
----------------------------------
Central registry of per-campaign context (machine, audit log, runner, lock).
Single instance shared across routes.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from backend.actions.audit import AuditLog
from backend.api.replay_runner import ReplayRunner
from backend.risk.state_machine import CampaignStateMachine
from backend.risk.state_machine import TickResult
from backend.risk.config_loader import get_config


@dataclass
class CampaignContext:
    campaign_id: str
    machine: CampaignStateMachine
    audit_log: AuditLog
    runner: ReplayRunner
    lock: threading.Lock
    latest_tick: Optional[TickResult] = None
    latest_sim_time: Optional[datetime] = None


class CampaignRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._registry: dict[str, CampaignContext] = {}

    def get(self, campaign_id: str) -> Optional[CampaignContext]:
        with self._lock:
            return self._registry.get(campaign_id)

    def get_or_create(self, campaign_id: str) -> CampaignContext:
        with self._lock:
            if campaign_id not in self._registry:
                cfg = get_config()
                machine = CampaignStateMachine(campaign_id, cfg)
                audit_log = AuditLog(campaign_id)
                campaign_lock = threading.Lock()
                runner = ReplayRunner(campaign_id, machine, audit_log, cfg)
                runner.set_campaign_lock(campaign_lock)
                ctx = CampaignContext(
                    campaign_id=campaign_id,
                    machine=machine,
                    audit_log=audit_log,
                    runner=runner,
                    lock=campaign_lock,
                )
                self._registry[campaign_id] = ctx
            return self._registry[campaign_id]

    def all_ids(self) -> list[str]:
        with self._lock:
            return list(self._registry.keys())


_registry: Optional[CampaignRegistry] = None
_reg_lock = threading.Lock()


def get_registry() -> CampaignRegistry:
    global _registry
    with _reg_lock:
        if _registry is None:
            _registry = CampaignRegistry()
    return _registry


def _reset_registry_for_tests() -> None:
    global _registry
    with _reg_lock:
        _registry = None
