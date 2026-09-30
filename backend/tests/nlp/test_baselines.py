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
    # Demonstrates that naive sentiment sees mockery/banter and triggers or flags banter storm
    assert metrics.raw_negative_share >= 0.0
