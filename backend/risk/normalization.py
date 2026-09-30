"""
backend/risk/normalization.py
------------------------------
Signal normalization: clip((x - low) / (high - low), 0, 1).

All bounds loaded from thresholds.yaml — never hardcoded here.
Division by zero (low == high) → 0.0, not error.
N/A rule does NOT live here; see economic_risk.py.

Authority: SPEC §6.3, master spec §10.3, Execution Prompt item 7.
"""
from __future__ import annotations


def normalize(x: float | None, low: float, high: float) -> float:
    """Normalize x into [0, 1] using clip((x-low)/(high-low), 0, 1).

    Args:
        x:    Raw signal value. None → 0.0.
        low:  Lower bound from thresholds.yaml.
        high: Upper bound from thresholds.yaml.

    Returns:
        Normalized value in [0, 1].
    """
    if x is None:
        return 0.0
    span = high - low
    if span == 0.0:
        return 0.0
    return max(0.0, min(1.0, (x - low) / span))
