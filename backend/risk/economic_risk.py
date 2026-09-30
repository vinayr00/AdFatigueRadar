"""
backend/risk/economic_risk.py
------------------------------
Computes economic_risk from the 2 economic signals.

economic_risk = 0.55×cpa_cpm_signal + 0.45×roas_conversion_signal

N/A rule lives HERE (not in normalization.py):
  - Returns None when conversions_in_window < min_conversions_in_window
  - Returns None when either economic signal is uncomputable (None)
  - Returns None when baseline is not warm (either signal is None due to warmup)

None is serialized as JSON null. NEVER coerced to 0.
Gate code must use `is None` check — never == 0 or falsy.

Authority: SPEC §6.2, master spec §10.2, Execution Prompt item 7.
"""
from __future__ import annotations

from backend.risk.features import SignalSet
from backend.risk.config_loader import get_config


def compute_economic_risk(
    signals: SignalSet,
    conversions_in_window: float,
    cfg: dict | None = None,
) -> float | None:
    """Compute economic risk.

    Returns None when:
    - conversions_in_window < min_conversions_in_window (economic N/A)
    - either economic signal is None (baseline not warm / uncomputable)

    Returns float in [0,1] otherwise.
    """
    if cfg is None:
        cfg = get_config()

    min_conv = cfg["economic"]["min_conversions_in_window"]

    # N/A: insufficient conversions
    if conversions_in_window < min_conv:
        return None

    # N/A: signals not computable (baseline warmup or missing data)
    if signals.cpa_cpm_signal is None or signals.roas_conversion_signal is None:
        return None

    ew = cfg["economic_weights"]
    return (
        ew["cpa_cpm"] * signals.cpa_cpm_signal
        + ew["roas_conversion"] * signals.roas_conversion_signal
    )
