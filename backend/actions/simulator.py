"""
backend/actions/simulator.py
-----------------------------
Economic evaluation (P0): excess cost, conversions forgone, tradeoff.

Formula (master spec §21):
  excess_cost = spend × max(0, 1 − baseline_CPA / current_CPA)
  excess_cost_avoided = no_action_excess_cost − protected_excess_cost
  conversions_forgone = max(0, no_action_conversions − protected_conversions)
  tradeoff = excess_cost_avoided / max(1, conversions_forgone)

Rules:
- current_CPA null → 0 contribution to excess_cost; spend → zero_conversion_spend
- Protected and no-action consume IDENTICAL potential-world curves and seeds
- Never call the result "savings" — it is "excess cost avoided"
- Telemetry: risk engine consumes OBSERVED (post-ActionSimulation) stream (P-08 [CONFIRM])
- No-action run consumes RAW potential-world stream

Authority: SPEC §21, master spec §21, Execution Prompt item 21, Plan v3 §P-08.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class EconomicEvaluationResult:
    """Output of economic evaluation for one campaign window."""
    no_action_spend: float
    no_action_conversions: float
    no_action_excess_cost: float
    protected_spend: float
    protected_conversions: float
    protected_excess_cost: float
    excess_cost_avoided: float
    conversions_forgone: float
    tradeoff: float               # excess_cost_avoided / max(1, conversions_forgone)
    zero_conversion_spend: float  # spend where CPA was null (conversions=0)
    action_taken: bool
    note: str = "Simulated result — not real monetary savings"


def _excess_cost(spend: float, baseline_cpa: float, current_cpa: Optional[float]) -> tuple[float, float]:
    """Return (excess_cost, zero_conversion_spend).

    current_CPA = null → 0 excess_cost contribution; spend → zero_conversion_spend.
    """
    if current_cpa is None:
        return 0.0, spend
    factor = max(0.0, 1.0 - baseline_cpa / current_cpa)
    return spend * factor, 0.0


def evaluate_economics(
    no_action_spend: float,
    no_action_conversions: float,
    no_action_cpa: Optional[float],
    protected_spend: float,
    protected_conversions: float,
    protected_cpa: Optional[float],
    baseline_cpa: float,
    action_taken: bool,
) -> EconomicEvaluationResult:
    """Compute economic evaluation.

    Args:
        no_action_*:   Window telemetry from raw potential-world stream.
        protected_*:   Window telemetry from observed (post-ActionSimulation) stream.
        baseline_cpa:  Baseline CPA = baseline_a_cpa_multiplier × healthy-window CPA.
        action_taken:  Whether a protective action is active.
    """
    no_action_excess, no_action_zero_spend = _excess_cost(no_action_spend, baseline_cpa, no_action_cpa)
    protected_excess, protected_zero_spend = _excess_cost(protected_spend, baseline_cpa, protected_cpa)

    excess_cost_avoided = no_action_excess - protected_excess
    conversions_forgone = max(0.0, no_action_conversions - protected_conversions)
    tradeoff = excess_cost_avoided / max(1.0, conversions_forgone)

    return EconomicEvaluationResult(
        no_action_spend=no_action_spend,
        no_action_conversions=no_action_conversions,
        no_action_excess_cost=no_action_excess,
        protected_spend=protected_spend,
        protected_conversions=protected_conversions,
        protected_excess_cost=protected_excess,
        excess_cost_avoided=excess_cost_avoided,
        conversions_forgone=conversions_forgone,
        tradeoff=tradeoff,
        zero_conversion_spend=no_action_zero_spend + protected_zero_spend,
        action_taken=action_taken,
    )
