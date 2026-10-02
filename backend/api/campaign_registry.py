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
                from backend.db.repository import repository
                saved_state = repository.get_campaign_state(campaign_id)
                if saved_state:
                    from backend.models.backend_models import CampaignState
                    machine._state = CampaignState(saved_state[0])
                    machine._pre_block_state = CampaignState(saved_state[1]) if saved_state[1] else None
                saved_override = repository.get_latest_threshold_override(campaign_id)
                if saved_override:
                    from backend.api.threshold_validator import validate_overrides
                    overrides, version = saved_override
                    if not validate_overrides(overrides, cfg):
                        machine.apply_threshold_override(overrides)
                        try:
                            machine._override_count = int(version.rsplit(".", 1)[1])
                        except (IndexError, ValueError):
                            pass
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
                from datetime import timezone
                if saved_state is None:
                    repository.save_campaign({
                        "id": campaign_id, "name": campaign_id, "platform": "meta",
                        "status": machine.state.value, "budget": None,
                        "pre_block_state": machine.pre_block_state.value if machine.pre_block_state else None,
                        "created_at": datetime.now(timezone.utc), "metadata_json": {},
                    })
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
    try:
        from backend.db.repository import repository
        for cid in ("api-campaign", "thresholds-c", "replay-c", "xss", "versioned-campaign",
                    "real-timeline-c", "full-audit-c", "health-c", "replay-stream", "race-c",
                    "replay-abort", "threshold-read", "timeline-populated", "healthy-watch", "a"):
            repository.delete_campaign(cid)
    except Exception:
        pass
