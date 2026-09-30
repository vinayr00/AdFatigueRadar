"""
backend/risk/audience_risk.py
------------------------------
Computes audience_risk from the 6 normalized signals.

audience_risk = 0.30×harmful + 0.25×sentiment_decay + 0.20×fatigue_mockery
              + 0.10×comment_acceleration + 0.10×ctr_frequency + 0.05×critical_complaint

All weights loaded from thresholds.yaml.

Authority: SPEC §6.1, master spec §10.1.
"""
from __future__ import annotations

from backend.risk.features import SignalSet


def compute_audience_risk(signals: SignalSet, cfg: dict) -> float:
    """Compute audience risk score in [0, 1].

    None signals contribute 0.0 (treated as no signal — not absence of risk).
    """
    aw = cfg["audience_weights"]

    def _val(v: float | None) -> float:
        return v if v is not None else 0.0

    return (
        aw["harmful_negative_ratio"] * _val(signals.harmful_negative_ratio)
        + aw["sentiment_decay"]       * _val(signals.sentiment_decay)
        + aw["fatigue_mockery"]       * _val(signals.fatigue_mockery)
        + aw["comment_acceleration"]  * _val(signals.comment_acceleration)
        + aw["ctr_frequency"]         * _val(signals.ctr_frequency)
        + aw["critical_complaint"]    * _val(signals.critical_complaint_signal)
    )
