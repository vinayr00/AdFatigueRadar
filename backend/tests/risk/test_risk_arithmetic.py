"""
backend/tests/risk/test_risk_arithmetic.py
-------------------------------------------
Risk arithmetic tests against master-spec worked example literals.
Covers: two-score arithmetic, N/A rule, CPA null, banter storm, warm-up,
dedup, unknown category, anomaly duplicate cluster.

Authority: Plan v3 §6 (risk arithmetic), master spec §10.4.
"""
from __future__ import annotations

import os
import json
import math
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

os.environ.setdefault("ADFR_HMAC_SECRET", "test-secret-12345")

from backend.risk.config_loader import get_config
from backend.risk.wilson import wilson_lb
from backend.risk.normalization import normalize
from backend.risk.audience_risk import compute_audience_risk
from backend.risk.economic_risk import compute_economic_risk
from backend.risk.features import SignalSet, compute_signals
from backend.risk.aggregation import CampaignAggregator, _normalize_text
from backend.models.backend_models import (
    CommentEvent, NLPResult, TelemetryEvent, CampaignState
)
from backend.risk.aggregation import SimClock
from backend.risk.state_machine import CampaignStateMachine


CFG = get_config()
TOLERANCE = 0.05  # "approximately" from master spec §10.4


# ---------------------------------------------------------------------------
# Worked example — master spec §10.4
# ---------------------------------------------------------------------------

def _audience_from_raw(
    n: float, k_eff: float, decay: float, fatigue_share: float,
    accel: float, ctr_decay: float, freq_inc: float, critical_rate: float,
    cfg: dict | None = None,
) -> float:
    cfg = cfg or CFG
    norm = cfg["normalization"]
    aw = cfg["audience_weights"]
    fmm = cfg.get("fatigue_mockery_mix", {"fatigue": 0.5, "mockery": 0.5})

    lb = wilson_lb(k_eff, n)
    harmful_sig = normalize(lb, norm["harmful_negative_ratio"]["low"], norm["harmful_negative_ratio"]["high"])
    decay_sig = normalize(decay, norm["sentiment_decay"]["low"], norm["sentiment_decay"]["high"])
    # For worked example, fatigue_share is the combined mix-weighted share already
    fatigue_sig = normalize(fatigue_share, norm["fatigue_mockery"]["low"], norm["fatigue_mockery"]["high"])
    accel_sig = normalize(accel, norm["comment_acceleration"]["low"], norm["comment_acceleration"]["high"])
    ctr_sig = normalize(ctr_decay, norm["ctr_decay_pct"]["low"], norm["ctr_decay_pct"]["high"])
    freq_sig = normalize(freq_inc, norm["frequency_increase_pct"]["low"], norm["frequency_increase_pct"]["high"])
    ctr_freq = (ctr_sig + freq_sig) / 2.0
    crit_sig = normalize(critical_rate, norm["critical_complaint"]["low"], norm["critical_complaint"]["high"])

    return (
        aw["harmful_negative_ratio"] * harmful_sig
        + aw["sentiment_decay"] * decay_sig
        + aw["fatigue_mockery"] * fatigue_sig
        + aw["comment_acceleration"] * accel_sig
        + aw["ctr_frequency"] * ctr_freq
        + aw["critical_complaint"] * crit_sig
    )


def _economic_from_raw(
    cpa_delta: float, cpm_delta: float,
    roas_drop: float, conv_drop: float,
    cfg: dict | None = None,
) -> float:
    cfg = cfg or CFG
    norm = cfg["normalization"]
    ew = cfg["economic_weights"]
    cpa_sig = normalize(cpa_delta, norm["cpa_delta_pct"]["low"], norm["cpa_delta_pct"]["high"])
    cpm_sig = normalize(cpm_delta, norm["cpm_delta_pct"]["low"], norm["cpm_delta_pct"]["high"])
    roas_sig = normalize(roas_drop, norm["roas_drop_pct"]["low"], norm["roas_drop_pct"]["high"])
    conv_sig = normalize(conv_drop, norm["conv_rate_drop_pct"]["low"], norm["conv_rate_drop_pct"]["high"])
    return ew["cpa_cpm"] * max(cpa_sig, cpm_sig) + ew["roas_conversion"] * max(roas_sig, conv_sig)


def test_worked_example_audience_risk() -> None:
    """Two-score arithmetic matches master-spec worked-example literal."""
    result = _audience_from_raw(
        n=120, k_eff=56, decay=0.14, fatigue_share=0.30,
        accel=0.08, ctr_decay=25, freq_inc=55, critical_rate=0.04,
    )
    assert abs(result - 0.781) <= TOLERANCE, f"audience_risk={result:.4f}, expected ~0.781"


def test_worked_example_economic_risk() -> None:
    result = _economic_from_raw(
        cpa_delta=12, cpm_delta=8, roas_drop=9.5, conv_drop=6,
    )
    assert abs(result - 0.178) <= TOLERANCE, f"economic_risk={result:.4f}, expected ~0.178"


# ---------------------------------------------------------------------------
# N/A rules
# ---------------------------------------------------------------------------

def test_low_volume_lull_economic_na() -> None:
    """< 20 conversions → economic_risk = None (N/A guard)."""
    signals = SignalSet(cpa_cpm_signal=0.5, roas_conversion_signal=0.5)
    result = compute_economic_risk(signals, conversions_in_window=15.0, cfg=CFG)
    assert result is None


def test_economic_risk_none_is_not_zero() -> None:
    """Verify None is distinct from 0 — critical for gate logic."""
    signals = SignalSet(cpa_cpm_signal=0.5, roas_conversion_signal=0.5)
    result = compute_economic_risk(signals, conversions_in_window=5.0, cfg=CFG)
    assert result is None
    assert result != 0


def test_economic_risk_computes_when_sufficient_conversions() -> None:
    signals = SignalSet(cpa_cpm_signal=0.6, roas_conversion_signal=0.5)
    result = compute_economic_risk(signals, conversions_in_window=25.0, cfg=CFG)
    assert result is not None
    assert 0.0 <= result <= 1.0


def test_economic_risk_none_when_signals_none() -> None:
    """Uncomputable signals → None even with sufficient conversions."""
    signals = SignalSet(cpa_cpm_signal=None, roas_conversion_signal=0.5)
    result = compute_economic_risk(signals, conversions_in_window=30.0, cfg=CFG)
    assert result is None


# ---------------------------------------------------------------------------
# CPA null
# ---------------------------------------------------------------------------

def test_cpa_null_not_infinity() -> None:
    """CPA = null when conversions = 0; never infinity."""
    agg = CampaignAggregator("test_cpa", CFG)
    from backend.actions.base import apply_action_simulation
    event = TelemetryEvent(
        event_id="t1",
        timestamp=datetime.now(timezone.utc),
        campaign_id="test_cpa",
        ad_id="ad1",
        spend=1000.0,
        impressions=10000.0,
        reach=5000.0,
        clicks=100.0,
        conversions=0.0,  # zero conversions
        cpm=None, cpc=None, cpa=None, roas=None,
    )
    # ACTIVE simulation should produce cpa=null when conversions=0
    result = apply_action_simulation(event, CampaignState.ACTIVE, None, 0.80)
    assert result.cpa is None
    assert result.conversions == 0.0
    import math
    if result.cpa is not None:
        assert not math.isinf(result.cpa)


# ---------------------------------------------------------------------------
# Banter storm — must not pause
# ---------------------------------------------------------------------------

def test_banter_storm_does_not_contribute_to_harmful_ratio() -> None:
    """High banter_meme, stable economics → harmful ratio stays low."""
    norm = CFG["normalization"]
    cw = CFG["category_weights"]

    # All banter_meme (weight=0.0)
    n = 120.0
    k_eff = sum([cw.get("banter_meme", 0.0)] * 120)  # = 0.0
    lb = wilson_lb(k_eff, n)
    harm_sig = normalize(lb, norm["harmful_negative_ratio"]["low"], norm["harmful_negative_ratio"]["high"])
    assert harm_sig < 0.1, f"Banter should not inflate harmful ratio, got {harm_sig}"


# ---------------------------------------------------------------------------
# Normalization edge cases
# ---------------------------------------------------------------------------

def test_normalize_low_equals_high() -> None:
    """Low == high → 0.0, not ZeroDivisionError."""
    result = normalize(0.5, 0.5, 0.5)
    assert result == 0.0


def test_normalize_clips_below_zero() -> None:
    result = normalize(-1.0, 0.0, 1.0)
    assert result == 0.0


def test_normalize_clips_above_one() -> None:
    result = normalize(2.0, 0.0, 1.0)
    assert result == 1.0


# ---------------------------------------------------------------------------
# Duplicate cluster — P-07 false-collision prevention
# ---------------------------------------------------------------------------

def test_normalize_text_emoji_only() -> None:
    """Emoji-only text normalizes to empty string."""
    result = _normalize_text("😂😂😂")
    assert len(result) == 0 or len(result) < 3


def test_duplicate_cluster_excludes_short_texts() -> None:
    """Comments with normalized text < dup_min_chars must not cluster."""
    agg = CampaignAggregator("test_dup", CFG)
    dup_min = CFG.get("dup_min_chars", 3)
    now = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)
    agg.clock.tick(now)

    # Inject many emoji-only comments (they should NOT cluster together)
    for i in range(20):
        event = CommentEvent(
            event_id=f"e_{i}",
            timestamp=now,
            campaign_id="test_dup",
            ad_id="ad1",
            author_id=f"author_{i}",
            text="😂",
            reactions=0, replies=0,
        )
        nlp = NLPResult(
            comment_id=f"e_{i}",
            sentiment="neutral",
            sentiment_score=0.5,
            category="banter_meme",
            confidence=0.8,
            critical_complaint=False,
        )
        agg.ingest_comment(event)
        agg.ingest_nlp(nlp)

    anomaly, _, dup_share, _ = agg.compute_anomaly_and_cap()
    # No duplicate cluster should form from emoji-only (normalized to "" or short text)
    assert not anomaly, f"Emoji-only comments should not trigger anomaly, dup_share={dup_share}"


def test_duplicate_cluster_lol_spam() -> None:
    """Many 'lol' comments with dup_min_chars > 3 should cluster; with dup_min_chars=3 they pass threshold."""
    agg = CampaignAggregator("test_lol", CFG)
    now = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)
    agg.clock.tick(now)
    total = 50
    for i in range(total):
        event = CommentEvent(
            event_id=f"lol_{i}",
            timestamp=now,
            campaign_id="test_lol",
            ad_id="ad1",
            author_id=f"author_{i}",  # distinct authors to avoid author cap confusion
            text="lol",
            reactions=0, replies=0,
        )
        agg.ingest_comment(event)

    # "lol" normalized = "lol" (3 chars = dup_min_chars, eligible for clustering)
    dup_min = CFG.get("dup_min_chars", 3)
    _, _, dup_share, _ = agg.compute_anomaly_and_cap()
    # If dup_min_chars = 3, "lol" (3 chars) is eligible → dup_share = 50/50 = 1.0
    # This tests that clustering works correctly when text >= dup_min_chars
    if dup_min <= 3:
        assert dup_share > 0.0, "lol spam should produce non-zero dup_share"


# ---------------------------------------------------------------------------
# Dedup — idempotent ingestion
# ---------------------------------------------------------------------------

def test_comment_dedup_idempotent() -> None:
    """Ingesting the same comment twice does not double-count."""
    agg = CampaignAggregator("test_dedup", CFG)
    now = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)
    agg.clock.tick(now)
    event = CommentEvent(
        event_id="dup_e1",
        timestamp=now,
        campaign_id="test_dedup",
        ad_id="ad1",
        author_id="author_1",
        text="This ad is annoying",
        reactions=1, replies=0,
    )
    agg.ingest_comment(event)
    agg.ingest_comment(event)  # duplicate
    window = agg.get_window_comments()
    assert len(window) == 1


def test_nlp_dedup_idempotent() -> None:
    """Ingesting NLP twice does not produce two entries."""
    agg = CampaignAggregator("test_nlp_dedup", CFG)
    now = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)
    agg.clock.tick(now)
    event = CommentEvent(
        event_id="nd_e1",
        timestamp=now,
        campaign_id="test_nlp_dedup",
        ad_id="ad1",
        author_id="author_1",
        text="Product broke",
        reactions=0, replies=0,
    )
    nlp = NLPResult(
        comment_id="nd_e1",
        sentiment="negative",
        sentiment_score=0.9,
        category="product_complaint",
        confidence=0.85,
        critical_complaint=True,
    )
    agg.ingest_comment(event)
    agg.ingest_nlp(nlp)
    agg.ingest_nlp(nlp)  # duplicate
    window = agg.get_window_comments()
    assert len(window) == 1
    assert window[0].category == "product_complaint"


# ---------------------------------------------------------------------------
# Missing NLP — comment goes to unclassified, no crash
# ---------------------------------------------------------------------------

def test_missing_nlp_does_not_crash() -> None:
    """Comment without NLPResult is ingested; goes to unclassified metric."""
    agg = CampaignAggregator("test_missing_nlp", CFG)
    now = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)
    agg.clock.tick(now)
    event = CommentEvent(
        event_id="mn_e1",
        timestamp=now,
        campaign_id="test_missing_nlp",
        ad_id="ad1",
        author_id="author_1",
        text="No NLP result for me",
        reactions=0, replies=0,
    )
    agg.ingest_comment(event)  # no NLP
    window = agg.get_window_comments()
    assert len(window) == 1
    assert window[0].category is None  # unclassified


# ---------------------------------------------------------------------------
# Unknown category — one audit event per distinct category, not per comment
# ---------------------------------------------------------------------------

def test_unknown_category_single_audit_per_category() -> None:
    """Unknown category emits one audit code per distinct category string."""
    agg = CampaignAggregator("test_unk", CFG)
    now = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)
    agg.clock.tick(now)

    audit_codes_collected = []
    for i in range(5):
        event = CommentEvent(
            event_id=f"unk_{i}",
            timestamp=now,
            campaign_id="test_unk",
            ad_id="ad1",
            author_id=f"author_{i}",
            text="test",
            reactions=0, replies=0,
        )
        nlp = NLPResult(
            comment_id=f"unk_{i}",
            sentiment="neutral",
            sentiment_score=0.5,
            category="alien_robot_dislike",  # unknown category
            confidence=0.8,
            critical_complaint=False,
        )
        agg.ingest_comment(event)
        _, codes = agg.ingest_nlp(nlp)
        audit_codes_collected.extend(codes)

    from backend.models.backend_models import ReasonCode
    unknown_audits = [c for c in audit_codes_collected if c == ReasonCode.UNKNOWN_CATEGORY]
    # Should be exactly 1 — one per distinct category string, not per comment
    assert len(unknown_audits) == 1, f"Expected 1 UNKNOWN_CATEGORY audit, got {len(unknown_audits)}"


def test_fractional_wilson():
    assert abs(wilson_lb(7.5, 30) - 0.127) < 0.01


def test_late_nlp_inside_window():
    agg = CampaignAggregator("late_inside", CFG)
    now = datetime(2026, 9, 30, 12, 30, tzinfo=timezone.utc)
    agg.clock.tick(now)
    event = CommentEvent(event_id="late1", timestamp=now-timedelta(minutes=10), campaign_id="late_inside",
                         ad_id="a", author_id="privacy-user", text="bad", reactions=0, replies=0)
    agg.ingest_comment(event)
    joined, _ = agg.ingest_nlp(NLPResult(comment_id="late1", sentiment="negative", sentiment_score=.8,
        category="product_complaint", confidence=.9, critical_complaint=False))
    assert joined and agg.get_window_comments()[0].category == "product_complaint"
    assert agg.late_nlp_dropped == 0
    assert not hasattr(agg.get_window_comments()[0], "author_id")
    assert agg.get_window_comments()[0].hmac_author_id != "privacy-user"


def test_late_nlp_outside_window():
    agg = CampaignAggregator("late_outside", CFG)
    now = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    agg.clock.tick(now)
    event = CommentEvent(event_id="late2", timestamp=now, campaign_id="late_outside",
                         ad_id="a", author_id="private", text="old", reactions=0, replies=0)
    agg.ingest_comment(event)
    agg.clock.tick(now+timedelta(minutes=65))
    joined, _ = agg.ingest_nlp(NLPResult(comment_id="late2", sentiment="negative", sentiment_score=.8,
        category="product_complaint", confidence=.9, critical_complaint=False))
    assert not joined and agg.late_nlp_dropped == 1
    assert agg.get_window_comments() == []


def test_pre_cap_anomaly_post_cap_scoring():
    agg = CampaignAggregator("cap_order", CFG)
    now = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    agg.clock.tick(now)
    for i in range(5):
        agg.ingest_comment(CommentEvent(event_id=f"cap{i}", timestamp=now, campaign_id="cap_order",
            ad_id="a", author_id="same-author", text=f"unique {i}", reactions=0, replies=0))
    anomaly, top_share, _, post_cap = agg.compute_anomaly_and_cap()
    assert anomaly and top_share == 1
    assert len(post_cap) == 3
    assert sum(c.excluded_from_scoring for c in agg.get_window_comments()) == 2
    for comment in post_cap:
        comment.category = "product_complaint"
        comment.confidence = .9
    scored = compute_signals(post_cap, {}, [], None, None, CFG, 1)
    assert scored.n_classified == 3
    assert scored.wilson_lb_raw == wilson_lb(3, 3)


def test_multi_ad_campaign_window_sums():
    agg = CampaignAggregator("multi", CFG)
    now = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    agg.clock.tick(now)
    for i, ad in enumerate(("ad_A", "ad_B")):
        agg.ingest_telemetry(TelemetryEvent(event_id=f"multi{i}", timestamp=now, campaign_id="multi", ad_id=ad,
            spend=50, impressions=500, reach=250, clicks=5, conversions=1, cpm=999, cpc=999, cpa=999, roas=2))
    sums = agg.get_telemetry_window_sums()
    assert sums["spend"] == 100 and sums["impressions"] == 1000
    assert sums["cpa"] == 50 and sums["cpm"] == 100


def test_sentiment_decay_uses_configured_category_weights_and_excludes_banter():
    from backend.risk.aggregation import EnrichedComment
    now = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    comments = [EnrichedComment(event_id="b", timestamp=now, hmac_author_id="h1", text="meme", reactions=0,
        replies=0, campaign_id="sent", ad_id="a", sentiment="negative", sentiment_score=1,
        category="banter_meme", confidence=.9)]
    signals = compute_signals(comments, {}, [], baseline_ewma=0.0, prev_telemetry_sums=None,
                              cfg=CFG, step_count=CFG["baseline"]["warmup_steps"])
    assert signals.sentiment_decay == 0.0


def test_schema_parity_and_model_constraints():
    from pathlib import Path
    from pydantic import ValidationError
    schemas = Path(__file__).resolve().parents[3] / "replay" / "schemas"
    for filename, model in (("comment_event.json", CommentEvent), ("telemetry_event.json", TelemetryEvent), ("nlp_result.json", NLPResult)):
        schema = json.loads((schemas / filename).read_text(encoding="utf-8"))
        assert set(schema["required"]) <= set(model.model_fields)
        assert set(schema["properties"]) == set(model.model_fields)
    with pytest.raises(ValidationError):
        NLPResult(comment_id="x", sentiment="angry", sentiment_score=1.2, category="fatigue", confidence=.9, critical_complaint=False)
    with pytest.raises(ValidationError):
        CommentEvent(event_id="x", timestamp="2026-09-30T12:00:00", campaign_id="c", ad_id="a", author_id="h", text="t")


def test_simclock_requires_five_minute_aware_utc_ticks():
    clock = SimClock()
    with pytest.raises(ValueError):
        clock.tick(datetime(2026, 9, 30, 12, 2, tzinfo=timezone.utc))
    with pytest.raises(ValueError):
        clock.tick(datetime(2026, 9, 30, 12, 0))


def test_safe_bounds_equal_mutable_keys_and_cover_them():
    assert set(CFG["safe_bounds"]) == set(CFG["threshold_mutable_keys"])
    assert all(key in CFG["safe_bounds"] for key in CFG["threshold_mutable_keys"])


def test_config_durations_multiplier_and_recovery_constraints():
    from copy import deepcopy
    from backend.api.threshold_validator import validate_config
    cfg = deepcopy(CFG)
    assert validate_config(cfg) == []
    cfg["persistence_hours"]["pause"] = 0
    assert any("persistence" in e for e in validate_config(cfg))
    cfg = deepcopy(CFG); cfg["cooldown_minutes"] = 0
    assert any("cooldown" in e for e in validate_config(cfg))
    cfg = deepcopy(CFG); cfg["actions"]["soft_budget_multiplier"] = 1.1
    assert any("soft_budget_multiplier" in e for e in validate_config(cfg))
    cfg = deepcopy(CFG); cfg["audience_gates"]["warning_recovery"] = .7
    assert any("warning recovery" in e for e in validate_config(cfg))
    cfg = deepcopy(CFG); cfg["category_weights"]["banter_meme"] = .01
    assert any("banter_meme" in e for e in validate_config(cfg))


def test_shared_validator_used_by_checker_and_api():
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    checker = (root / "scripts" / "check_config.py").read_text(encoding="utf-8")
    api_validator = (root / "backend" / "api" / "routes_thresholds.py").read_text(encoding="utf-8")
    assert "from backend.api.threshold_validator import validate_config" in checker
    assert "from backend.api.threshold_validator import ThresholdValidationError, validate_overrides" in api_validator


def test_unknown_category_is_neutral_and_retained():
    agg = CampaignAggregator("unknown-retain", CFG)
    now = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    agg.clock.tick(now)
    event = CommentEvent(event_id="u", timestamp=now, campaign_id="unknown-retain", ad_id="a",
                         author_id="raw-should-not-persist", text="x", reactions=0, replies=0)
    agg.ingest_comment(event)
    _, codes = agg.ingest_nlp(NLPResult(comment_id="u", sentiment="neutral", sentiment_score=.5,
        category="unexpected-category", confidence=.8, critical_complaint=False))
    item = agg.get_window_comments()[0]
    assert item.category == "neutral" and item.unknown_category
    assert item.unknown_category_name == "unexpected-category"
    assert codes


def test_out_of_order_future_comment_not_scored_until_clock_reaches_it():
    agg = CampaignAggregator("future", CFG)
    now = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    agg.clock.tick(now)
    future = CommentEvent(event_id="future", timestamp=now+timedelta(minutes=5), campaign_id="future",
        ad_id="a", author_id="a", text="later", reactions=0, replies=0)
    agg.ingest_comment(future)
    assert agg.get_window_comments() == []
    agg.clock.tick(now+timedelta(minutes=5))
    assert len(agg.get_window_comments()) == 1


def test_runtime_threshold_validator_rejects_immutable_and_ordering():
    from backend.api.threshold_validator import validate_overrides
    assert validate_overrides({"category_weights.fatigue": .5}, CFG)
    assert validate_overrides({"audience_gates.warning": .9}, CFG)


def test_simclock_no_backward_movement():
    clock = SimClock()
    now = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    clock.tick(now)
    with pytest.raises(ValueError):
        clock.tick(now-timedelta(minutes=5))


def test_replay_speed_invariance_and_event_free_ticks():
    from backend.actions.audit import AuditLog
    from backend.api.replay_runner import ReplayRunner

    t0 = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    class Source:
        def events(self):
            return iter([
                TelemetryEvent(event_id="z", timestamp=t0+timedelta(minutes=10), campaign_id="speed", ad_id="b",
                    spend=10, impressions=100, reach=50, clicks=2, conversions=1, roas=2),
                TelemetryEvent(event_id="a", timestamp=t0, campaign_id="speed", ad_id="a",
                    spend=10, impressions=100, reach=50, clicks=2, conversions=1, roas=2),
            ])
    outputs = []
    delays = []
    for speed in (1, 10):
        machine = CampaignStateMachine(f"speed{speed}", CFG)
        runner = ReplayRunner(f"speed{speed}", machine, AuditLog(f"speed{speed}"), CFG,
                              sleeper=lambda seconds: delays.append(seconds))
        runner.start(Source(), speed=speed)
        runner._task_thread.join()
        outputs.append(runner.get_timeline())
    assert [p["sim_time"] for p in outputs[0]] == [p["sim_time"] for p in outputs[1]]
    assert len(outputs[0]) == 3  # 12:05 is ticked with no event.
    assert outputs[0] == outputs[1]
    assert delays[0] > delays[-1]


def test_comment_only_replay_ticks_through_empty_steps():
    from backend.actions.audit import AuditLog
    from backend.api.replay_runner import ReplayRunner
    t0 = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    class CommentSource:
        def events(self):
            return iter([
                CommentEvent(event_id="c1", timestamp=t0, campaign_id="comments", ad_id="a", author_id="one", text="hi"),
                CommentEvent(event_id="c2", timestamp=t0+timedelta(minutes=10), campaign_id="comments", ad_id="b", author_id="two", text="hello"),
            ])
    machine = CampaignStateMachine("comments", CFG)
    runner = ReplayRunner("comments", machine, AuditLog("comments"), CFG, sleeper=lambda _: None)
    runner.start(CommentSource(), speed=2)
    runner._task_thread.join()
    assert machine.aggregator.clock.step_count == 3
    assert [row["sim_time"] for row in runner.get_timeline()][1].endswith("12:05:00+00:00")
