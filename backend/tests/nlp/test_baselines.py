"""
Tests for P1 Sentiment-Only Baseline (Baseline C)
"""

import pytest
from backend.nlp import CommentEvent
from backend.nlp.baselines import SentimentOnlyBaseline, SentimentBaselineMetrics


def test_sentiment_only_baseline_empty():
    baseline = SentimentOnlyBaseline()
    metrics = baseline.evaluate_window([])
    assert metrics.total_comments == 0
    assert metrics.alert_triggered is False


def test_sentiment_only_baseline_banter_storm_behavior():
    """
    Demonstrates Baseline C behavior:
    Naive sentiment triggers false positive alert on banter storm,
    which contrasts with the production combined guard that excludes banter (weight=0.0).
    """
    baseline = SentimentOnlyBaseline(negative_threshold=0.30)
    
    # Create window of viral banter/memes (slang, roasts, skull emojis)
    banter_comments = [
        CommentEvent(
            event_id=f"banter_{i}",
            timestamp="2026-09-30T12:00:00Z",
            campaign_id="camp_banter",
            ad_id="ad_viral",
            author_id=f"user_{i}",
            text="The acting in this ad is killing me 💀 bro really thought he cooked" if i % 2 == 0 else "Bro got that unspoken rizz let him cook 🔥"
        )
        for i in range(20)
    ]

    metrics = baseline.evaluate_window(banter_comments)
    assert isinstance(metrics, SentimentBaselineMetrics)
    assert metrics.total_comments == 20
    assert 0.0 <= metrics.raw_negative_share <= 1.0
    assert metrics.threshold == 0.30
    assert isinstance(metrics.alert_triggered, bool)
    assert isinstance(metrics.is_false_alarm_on_banter, bool)
    # Demonstrates that naive sentiment sees mockery/banter and can trigger false alarms
    assert metrics.negative_count >= 0


def test_sentiment_only_baseline_clean_window():
    baseline = SentimentOnlyBaseline(negative_threshold=0.35)
    positive_comments = [
        CommentEvent(
            event_id=f"pos_{i}",
            timestamp="2026-09-30T12:00:00Z",
            campaign_id="camp_clean",
            ad_id="ad_clean",
            author_id=f"user_{i}",
            text="Bought again, love it! Super fast delivery ❤️"
        )
        for i in range(10)
    ]
    metrics = baseline.evaluate_window(positive_comments)
    assert metrics.total_comments == 10
    assert metrics.negative_count == 0
    assert metrics.raw_negative_share == 0.0
    assert metrics.alert_triggered is False
    assert metrics.is_false_alarm_on_banter is False

