"""Deterministic sandbox volume scaling shared by replay simulations."""
from __future__ import annotations

import math

from backend.models.backend_models import CampaignState, TelemetryEvent


class ActionSimulationError(ValueError):
    """Action simulation lacks authoritative state required to fail safely."""


def _state_multiplier(state: CampaignState, pre_block_state: CampaignState | None, soft_budget_multiplier: float) -> float:
    if state == CampaignState.ACTIVE:
        return 1.0
    if state == CampaignState.SOFT_REDUCED:
        return soft_budget_multiplier
    if state == CampaignState.PAUSED:
        return 0.0
    if state == CampaignState.BLOCKED:
        if pre_block_state is None:
            raise ActionSimulationError("pre_block_state is required when campaign_state is BLOCKED")
        return _state_multiplier(pre_block_state, None, soft_budget_multiplier)
    raise ActionSimulationError(f"unsupported campaign state: {state}")


def _apply(
    potential_event: TelemetryEvent,
    campaign_state: CampaignState,
    pre_block_state: CampaignState | None,
    soft_budget_multiplier: float,
) -> TelemetryEvent:
    """Scale extensive values, then recompute ratios from those values."""
    multiplier = _state_multiplier(campaign_state, pre_block_state, soft_budget_multiplier)
    spend = potential_event.spend * multiplier
    impressions = potential_event.impressions * multiplier
    reach = potential_event.reach * multiplier
    clicks = potential_event.clicks * multiplier
    conversions = potential_event.conversions * multiplier
    revenue = (potential_event.roas * potential_event.spend * multiplier) if potential_event.roas is not None else None

    def div(a: float | None, b: float) -> float | None:
        result = a / b if a is not None and b else None
        if result is None or not math.isfinite(result):
            return None
        return result

    raw_cpm = div(spend, impressions)
    cpm = raw_cpm * 1000 if raw_cpm is not None and math.isfinite(raw_cpm * 1000) else None
    return TelemetryEvent(
        event_id=potential_event.event_id, timestamp=potential_event.timestamp,
        campaign_id=potential_event.campaign_id, ad_id=potential_event.ad_id,
        spend=spend, impressions=impressions, reach=reach, clicks=clicks,
        conversions=conversions,
        cpm=cpm,
        cpc=div(spend, clicks), cpa=div(spend, conversions),
        roas=div(revenue, spend),
    )


class ActionSimulation:
    def __init__(self, soft_budget_multiplier: float = 0.80) -> None:
        self._soft_budget_multiplier = soft_budget_multiplier

    def apply(self, potential_event: TelemetryEvent, campaign_state: CampaignState, *, pre_block_state: CampaignState | None = None) -> TelemetryEvent:
        return _apply(potential_event, campaign_state, pre_block_state, self._soft_budget_multiplier)


def apply(potential_event: TelemetryEvent, campaign_state: CampaignState, *, pre_block_state: CampaignState | None = None) -> TelemetryEvent:
    """Default frozen-contract entry point using thresholds_v4 soft multiplier."""
    return _apply(potential_event, campaign_state, pre_block_state, 0.80)


def apply_action_simulation(potential_event: TelemetryEvent, state: CampaignState, pre_block_state: CampaignState | None, soft_budget_multiplier: float) -> TelemetryEvent:
    """Compatibility adapter for the former positional call contract."""
    return _apply(potential_event, state, pre_block_state, soft_budget_multiplier)
