"""
backend/risk/features.py
-------------------------
Computes all 8 risk signals from post-cap window data.

Signal formulas — exact per Plan v3 (P-06):
  harmful_negative_ratio: Wilson LB of weighted harmful share → normalize
  sentiment_decay:        Category-aware EWMA (banter_meme excluded) → max(0, baseline-current) → normalize
  fatigue_mockery:        Mix-weighted share (fatigue_mockery_mix from YAML) → normalize
  comment_acceleration:  (rate_now - rate_prior) / max(rate_prior, accel_eps) → normalize
  ctr_frequency:         mean(norm(ctr_decay_pct), norm(freq_increase_pct))
  critical_complaint:    Rate of critical_complaint=True among post-cap scored → normalize
  cpa_cpm_signal:        max(norm(cpa_delta_pct), norm(cpm_delta_pct))
  roas_conversion_signal:max(norm(roas_drop_pct), norm(conv_rate_drop_pct))

Baseline-dependent signals (sentiment_decay delta, cpa/roas deltas) return None
before warmup_steps are complete.

Authority: SPEC §7, master spec §10, Execution Prompt items 6,7, Plan v3 P-06.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.risk.aggregation import EnrichedComment
from backend.risk.normalization import normalize
from backend.risk.wilson import wilson_lb

_CANONICAL_CATEGORIES = frozenset({
    "product_complaint", "service_complaint", "fatigue",
    "mockery", "spam", "banter_meme", "neutral", "positive",
})


@dataclass
class SignalSet:
    """Raw normalized signals. None = uncomputable (baseline not warm, or N/A)."""
    harmful_negative_ratio: float | None = None
    sentiment_decay: float | None = None
    fatigue_mockery: float | None = None
    comment_acceleration: float | None = None
    ctr_frequency: float | None = None
    critical_complaint_signal: float | None = None
    cpa_cpm_signal: float | None = None
    roas_conversion_signal: float | None = None
    # Diagnostics (not used in scoring)
    wilson_lb_raw: float | None = None
    n_classified: int = 0
    n_post_cap: int = 0


def compute_signals(
    post_cap_comments: list[EnrichedComment],
    telemetry_sums: dict,
    rate_history: list[tuple],
    baseline_ewma: float | None,       # None until warmup complete
    prev_telemetry_sums: dict | None,  # previous window for delta computation
    cfg: dict,
    step_count: int,
) -> SignalSet:
    """Compute all 8 signals.

    Args:
        post_cap_comments:   Post-cap scored comments in the window.
        telemetry_sums:      Window telemetry sums dict from CampaignAggregator.
        rate_history:        [(step_boundary, count)] from get_comment_rate_history().
        baseline_ewma:       EWMA baseline for sentiment decay. None = not warm.
        prev_telemetry_sums: Previous window sums for delta computation. None = not warm.
        cfg:                 Full thresholds config.
        step_count:          Number of ticks so far (for warmup check).

    Returns:
        SignalSet with all computed signals.
    """
    norm_cfg = cfg["normalization"]
    aw = cfg["audience_weights"]
    cw = cfg["category_weights"]
    accel_eps: float = cfg.get("accel_eps", 0.01)
    warmup_steps: int = cfg["baseline"]["warmup_steps"]
    baseline_warm = step_count >= warmup_steps and baseline_ewma is not None

    out = SignalSet()

    # Scored comments = post-cap comments that have an NLP result
    scored = [c for c in post_cap_comments if c.category is not None]
    out.n_classified = len(scored)
    out.n_post_cap = len(post_cap_comments)

    # ------------------------------------------------------------------
    # 1. Harmful negative ratio
    # ------------------------------------------------------------------
    n = float(len(scored))
    if n > 0:
        k_eff = sum(cw.get(c.category or "neutral", 0.0) for c in scored)
        lb = wilson_lb(k_eff, n)
        out.wilson_lb_raw = lb
        out.harmful_negative_ratio = normalize(
            lb, norm_cfg["harmful_negative_ratio"]["low"], norm_cfg["harmful_negative_ratio"]["high"]
        )
    else:
        out.harmful_negative_ratio = 0.0
        out.wilson_lb_raw = 0.0

    # ------------------------------------------------------------------
    # 2. Sentiment decay (requires baseline warmup)
    # ------------------------------------------------------------------
    # CONFIRM default (P-06): sentiment_score in [0,1] is magnitude;
    # sign = +1 for positive, -1 for negative, 0 for neutral/other.
    # Apply category weight to signed polarity. Zero-weight classes (including
    # banter_meme) remain zero contributors instead of changing the EWMA mix.
    if scored:
        ewma_alpha: float = cfg["compute"]["ewma_alpha"]
        current_ewma = _compute_ewma([_polarity(c) * cw.get(c.category or "neutral", 0.0) for c in scored], ewma_alpha)
        if baseline_warm:
            decay_raw = max(0.0, (baseline_ewma or 0.0) - current_ewma)
            out.sentiment_decay = normalize(
                decay_raw,
                norm_cfg["sentiment_decay"]["low"],
                norm_cfg["sentiment_decay"]["high"],
            )
        # else: baseline not warm → None
        else:
            out.sentiment_decay = 0.0 if baseline_warm else None
    else:
        out.sentiment_decay = 0.0 if baseline_warm else None

    # ------------------------------------------------------------------
    # 3. Fatigue / mockery (P-06: mix-weighted share)
    # ------------------------------------------------------------------
    if n > 0:
        fatigue_count = sum(1 for c in scored if c.category == "fatigue")
        mockery_count = sum(1 for c in scored if c.category == "mockery")
        fm_raw = (
            cw.get("fatigue", 0.0) * fatigue_count
            + cw.get("mockery", 0.0) * mockery_count
        ) / n
        out.fatigue_mockery = normalize(
            fm_raw, norm_cfg["fatigue_mockery"]["low"], norm_cfg["fatigue_mockery"]["high"]
        )
    else:
        out.fatigue_mockery = 0.0

    # ------------------------------------------------------------------
    # 4. Comment acceleration (P-06: rate ratio with accel_eps)
    # ------------------------------------------------------------------
    if len(rate_history) >= 2:
        rates = [r for _, r in rate_history]
        rate_now = rates[-1]
        rate_prior = rates[-2] if len(rates) >= 2 else 0.0
        accel_raw = (rate_now - rate_prior) / max(rate_prior, accel_eps)
        out.comment_acceleration = normalize(
            accel_raw,
            norm_cfg["comment_acceleration"]["low"],
            norm_cfg["comment_acceleration"]["high"],
        )
    else:
        out.comment_acceleration = 0.0

    # ------------------------------------------------------------------
    # 5. CTR / frequency signal (from window sums)
    # ------------------------------------------------------------------
    if prev_telemetry_sums and baseline_warm:
        prev_ctr = prev_telemetry_sums.get("ctr")
        curr_ctr = telemetry_sums.get("ctr")
        prev_freq = prev_telemetry_sums.get("frequency")
        curr_freq = telemetry_sums.get("frequency")

        ctr_decay_pct = _pct_change(prev_ctr, curr_ctr, invert=True)   # decay = decrease
        freq_inc_pct = _pct_change(prev_freq, curr_freq, invert=False)  # increase = bad

        ctr_sig = normalize(ctr_decay_pct, norm_cfg["ctr_decay_pct"]["low"], norm_cfg["ctr_decay_pct"]["high"])
        freq_sig = normalize(freq_inc_pct, norm_cfg["frequency_increase_pct"]["low"], norm_cfg["frequency_increase_pct"]["high"])
        out.ctr_frequency = (ctr_sig + freq_sig) / 2.0
    else:
        out.ctr_frequency = 0.0 if not baseline_warm else None

    # ------------------------------------------------------------------
    # 6. Critical complaint signal
    # ------------------------------------------------------------------
    if n > 0:
        critical_count = sum(
            1 for c in scored
            if c.critical_complaint
            and c.category in cfg["critical_complaint"]["categories"]
            and (c.confidence or 0.0) >= cfg["critical_complaint"]["min_confidence"]
        )
        critical_rate = critical_count / n
        out.critical_complaint_signal = normalize(
            critical_rate,
            norm_cfg["critical_complaint"]["low"],
            norm_cfg["critical_complaint"]["high"],
        )
    else:
        out.critical_complaint_signal = 0.0

    # ------------------------------------------------------------------
    # 7. CPA/CPM signal (requires baseline warmup for delta)
    # ------------------------------------------------------------------
    if prev_telemetry_sums and baseline_warm:
        prev_cpa = prev_telemetry_sums.get("cpa")
        curr_cpa = telemetry_sums.get("cpa")
        prev_cpm = prev_telemetry_sums.get("cpm")
        curr_cpm = telemetry_sums.get("cpm")

        cpa_delta = _pct_change(prev_cpa, curr_cpa, invert=False)
        cpm_delta = _pct_change(prev_cpm, curr_cpm, invert=False)

        cpa_sig = normalize(cpa_delta, norm_cfg["cpa_delta_pct"]["low"], norm_cfg["cpa_delta_pct"]["high"])
        cpm_sig = normalize(cpm_delta, norm_cfg["cpm_delta_pct"]["low"], norm_cfg["cpm_delta_pct"]["high"])
        out.cpa_cpm_signal = max(cpa_sig, cpm_sig)
    else:
        out.cpa_cpm_signal = None

    # ------------------------------------------------------------------
    # 8. ROAS / conversion rate signal (requires baseline warmup)
    # ------------------------------------------------------------------
    if prev_telemetry_sums and baseline_warm:
        prev_roas = prev_telemetry_sums.get("roas")
        curr_roas = telemetry_sums.get("roas")
        prev_conversions = prev_telemetry_sums.get("conversions", 0.0) or 0.0
        curr_conversions = telemetry_sums.get("conversions", 0.0) or 0.0
        prev_impressions = prev_telemetry_sums.get("impressions", 0.0) or 0.0
        curr_impressions = telemetry_sums.get("impressions", 0.0) or 0.0
        prev_conv_rate = _safe_div(prev_conversions, prev_impressions)
        curr_conv_rate = _safe_div(curr_conversions, curr_impressions)

        roas_drop = _pct_change(prev_roas, curr_roas, invert=True)   # drop = bad
        conv_drop = _pct_change(prev_conv_rate, curr_conv_rate, invert=True)

        roas_sig = normalize(roas_drop, norm_cfg["roas_drop_pct"]["low"], norm_cfg["roas_drop_pct"]["high"])
        conv_sig = normalize(conv_drop, norm_cfg["conv_rate_drop_pct"]["low"], norm_cfg["conv_rate_drop_pct"]["high"])
        out.roas_conversion_signal = max(roas_sig, conv_sig)
    else:
        out.roas_conversion_signal = None

    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _polarity(c: EnrichedComment) -> float:
    """Per-comment polarity: positive → +score, negative → −score, neutral → 0.
    sentiment_score is magnitude in [0,1]. (CONFIRM P-06)
    """
    if c.sentiment == "positive":
        return c.sentiment_score or 0.0
    elif c.sentiment == "negative":
        return -(c.sentiment_score or 0.0)
    return 0.0


def _compute_ewma(values: list[float], alpha: float) -> float:
    """Compute EWMA of a list of values."""
    if not values:
        return 0.0
    ewma = values[0]
    for v in values[1:]:
        ewma = alpha * v + (1.0 - alpha) * ewma
    return ewma


def _pct_change(prev: float | None, curr: float | None, invert: bool = False) -> float:
    """Percentage change from prev to curr. Returns 0.0 if either is None or prev=0."""
    if prev is None or curr is None or prev == 0.0:
        return 0.0
    pct = ((curr - prev) / abs(prev)) * 100.0
    return -pct if invert else pct


def _safe_div(a: float, b: float) -> float | None:
    return a / b if b != 0.0 else None
