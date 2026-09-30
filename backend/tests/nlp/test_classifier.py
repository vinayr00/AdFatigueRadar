"""
Tests for Unified CommentClassifier & Frozen JSON Contract
"""

import pytest
from backend.nlp import CommentEvent, NLPResult, TAXONOMY_CATEGORIES
from backend.nlp.classifier import CommentClassifier


@pytest.fixture
def classifier():
    return CommentClassifier(use_cache=False)


def test_classify_comment_event(classifier):
    event = CommentEvent(
        event_id="comment_0001",
        timestamp="2026-09-30T12:00:00Z",
        campaign_id="campaign_01",
        ad_id="ad_07",
        author_id="author_184",
        text="Bro this ad again 😂",
        reactions=12,
        replies=3
    )
    result = classifier.classify(event)

    assert isinstance(result, NLPResult)
    assert result.comment_id == "comment_0001"
    assert result.sentiment in {"positive", "neutral", "negative"}
    assert result.category in TAXONOMY_CATEGORIES
    assert 0.0 <= result.sentiment_score <= 1.0
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.critical_complaint, bool)


def test_frozen_json_contract_fields(classifier):
    event_dict = {
        "event_id": "comment_0042",
        "timestamp": "2026-09-30T12:05:00Z",
        "campaign_id": "campaign_01",
        "ad_id": "ad_07",
        "author_id": "author_99",
        "text": "The acting in this commercial is killing me 💀",
        "reactions": 5,
        "replies": 1
    }
    result = classifier.classify(event_dict)
    out_dict = result.to_dict()

    # Exact frozen schema keys required by Person 2 Risk Engine
    expected_keys = {
        "comment_id",
        "sentiment",
        "sentiment_score",
        "category",
        "confidence",
        "critical_complaint"
    }
    assert set(out_dict.keys()) == expected_keys
    assert out_dict["comment_id"] == "comment_0042"
    assert out_dict["category"] == "mockery"
    assert out_dict["sentiment"] == "negative"


def test_classify_batch_consistency(classifier):
    comments = [
        "Bro this ad again 😂",
        "Bought again, loved it ❤️",
        "The item broke on day 1 defect",
    ]
    single_results = [classifier.classify_text(t) for t in comments]
    batch_results = classifier.classify_batch(comments)

    assert len(single_results) == len(batch_results)
    for s, b in zip(single_results, batch_results):
        assert s.category == b.category
        assert s.sentiment == b.sentiment
        assert abs(s.confidence - b.confidence) < 1e-4
