"""
backend/risk/wilson.py
-----------------------
Wilson score lower bound for fractional harmful counts.

Formula (z = 1.96, constant):
    p      = k_eff / n
    center = (p + z²/(2n)) / (1 + z²/n)
    margin = z × sqrt((p(1-p) + z²/(4n)) / n) / (1 + z²/n)
    wilson_lb = center - margin

Guards:
    n <= 0          → 0.0
    k_eff clamped to [0, n]

Authority: SPEC §8, master spec §12, Execution Prompt item 22.
"""
from __future__ import annotations

import math

_Z = 1.96
_Z2 = _Z * _Z


def wilson_lb(k_eff: float, n: float) -> float:
    """Wilson score lower bound.

    Args:
        k_eff: Effective harmful count (may be fractional). Clamped to [0, n].
        n:     Total classified comment count. Must be > 0.

    Returns:
        Wilson lower bound in [0, 1], or 0.0 when n <= 0.
    """
    if n <= 0:
        return 0.0
    k_eff = max(0.0, min(float(k_eff), float(n)))
    n = float(n)
    p = k_eff / n
    denom = 1.0 + _Z2 / n
    center = (p + _Z2 / (2.0 * n)) / denom
    variance = (p * (1.0 - p) + _Z2 / (4.0 * n)) / n
    margin = _Z * math.sqrt(max(0.0, variance)) / denom
    return max(0.0, center - margin)


def wilson_margin(k_eff: float, n: float) -> float:
    """Return the margin component only (used for action confidence calculation).

    Returns 1.0 (maximum uncertainty) when n <= 0.
    """
    if n <= 0:
        return 1.0
    k_eff = max(0.0, min(float(k_eff), float(n)))
    n = float(n)
    p = k_eff / n
    denom = 1.0 + _Z2 / n
    variance = (p * (1.0 - p) + _Z2 / (4.0 * n)) / n
    return _Z * math.sqrt(max(0.0, variance)) / denom
