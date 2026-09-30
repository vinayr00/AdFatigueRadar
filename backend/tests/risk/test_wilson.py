"""
backend/tests/risk/test_wilson.py
----------------------------------
Wilson lower bound tests.

All ground-truth literals are hardcoded here — NOT computed by the engine.
Tolerance: 1e-4.

Authority: Plan v3 §§Step 1.1, 6 (risk arithmetic tests), Execution Prompt item 22.
"""
from __future__ import annotations

import pytest
from backend.risk.wilson import wilson_lb, wilson_margin

# ---------------------------------------------------------------------------
# Ground-truth literals — hardcoded, never derived from the code under test
# ---------------------------------------------------------------------------
GROUND_TRUTH = [
    # (n, p, expected_lb)
    (24,  0.25, 0.1200),
    (24,  0.50, 0.3143),
    (24,  0.75, 0.5510),
    (30,  0.25, 0.1298),
    (30,  0.50, 0.3315),
    (30,  0.75, 0.5730),
    (60,  0.25, 0.1578),
    (60,  0.50, 0.3773),
    (60,  0.75, 0.6277),
    (120, 0.25, 0.1811),
    (120, 0.50, 0.4119),
    (120, 0.75, 0.6656),
    (480, 0.25, 0.2134),
    (480, 0.50, 0.4554),
    (480, 0.75, 0.7094),
]

TOLERANCE = 1e-4


@pytest.mark.parametrize("n,p,expected", GROUND_TRUTH)
def test_wilson_lb_ground_truth(n: float, p: float, expected: float) -> None:
    k_eff = p * n
    result = wilson_lb(k_eff, n)
    assert abs(result - expected) <= TOLERANCE, (
        f"wilson_lb(k={k_eff}, n={n}): got {result:.6f}, expected {expected:.4f} "
        f"(diff={abs(result - expected):.6f})"
    )


def test_wilson_lb_n_zero() -> None:
    assert wilson_lb(10, 0) == 0.0


def test_wilson_lb_n_negative() -> None:
    assert wilson_lb(10, -5) == 0.0


def test_wilson_lb_k_negative_clamped() -> None:
    """Negative k_eff is clamped to 0."""
    result_neg = wilson_lb(-5, 30)
    result_zero = wilson_lb(0, 30)
    assert result_neg == result_zero


def test_wilson_lb_k_exceeds_n_clamped() -> None:
    """k_eff > n is clamped to n."""
    result_over = wilson_lb(35, 30)
    result_n = wilson_lb(30, 30)
    assert result_over == result_n


def test_wilson_lb_in_range() -> None:
    """wilson_lb result always in [0, 1]."""
    for n, p, _ in GROUND_TRUTH:
        result = wilson_lb(p * n, n)
        assert 0.0 <= result <= 1.0, f"Out of range: wilson_lb(k={p*n}, n={n})={result}"


def test_wilson_margin_n_zero() -> None:
    """wilson_margin returns 1.0 when n <= 0 (maximum uncertainty)."""
    assert wilson_margin(5, 0) == 1.0
