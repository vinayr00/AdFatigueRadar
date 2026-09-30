"""
Tests for Unified CommentClassifier & Frozen JSON Contract
"""

import pytest
import random
from backend.nlp import CommentEvent, NLPResult, TAXONOMY_CATEGORIES
from backend.nlp.classifier import CommentClassifier


@pytest.fixture(scope="module")
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
    assert result.category == "fatigue"
    assert 0.0 <= result.sentiment_score <= 1.0
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.critical_complaint, bool)


def test_frozen_json_contract_fields_and_no_extra_keys(classifier):
    event_dict = {
        "event_id": "comment_0042",
        "timestamp": "2026-09-30T12:05:00Z",
        "campaign_id": "campaign_01",
        "ad_id": "ad_07",
        "author_id": "author_99",
        "text": "The acting in this commercial is making my teeth hurt from pure cringe 💀",
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
    assert len(out_dict.keys()) == 6
    assert out_dict["comment_id"] == "comment_0042"
    assert out_dict["category"] == "mockery"
    assert out_dict["sentiment"] == "negative"


def test_classify_batch_order_and_id_alignment(classifier):
    samples = [
        ("c_01", "The plastic clip snapped the very first time I attached it."),
        ("c_02", "I placed this order three weeks ago and tracking has not updated."),
        ("c_03", "Bro this ad again 😂 I see it on my feed every five minutes."),
        ("c_04", "The acting in this commercial is making my teeth hurt from cringe 💀"),
        ("c_05", "Click the link in my bio for guaranteed 100x crypto signals daily 🚀"),
        ("c_06", "Bro got that unspoken rizz let him cook 🔥"),
        ("c_07", "What is the current retail price including local sales taxes?"),
        ("c_08", "Bought again, love it! Absolute best quality item I have ever owned ❤️"),
    ]
    # Shuffle samples
    shuffled = list(samples)
    random.seed(123)
    random.shuffle(shuffled)

    events = [
        CommentEvent(
            event_id=cid,
            timestamp="2026-09-30T12:00:00Z",
            campaign_id="camp_1",
            ad_id="ad_1",
            author_id="user_1",
            text=text
        )
        for cid, text in shuffled
    ]

    single_results = [classifier.classify(e) for e in events]
    batch_results = classifier.classify_batch(events)

    assert len(batch_results) == len(events)
    for idx, (s, b, e) in enumerate(zip(single_results, batch_results, events)):
        assert b.comment_id == e.event_id, f"Position {idx} ID mismatch: {b.comment_id} != {e.event_id}"
        assert s.comment_id == b.comment_id
        assert s.category == b.category
        assert s.sentiment == b.sentiment
        assert abs(s.confidence - b.confidence) < 1e-4
        assert abs(s.sentiment_score - b.sentiment_score) < 1e-4
        assert s.critical_complaint == b.critical_complaint


def test_determinism_100_inputs_3_runs(classifier):
    texts = [
        f"Comment sample {i} with varied content: " + (
            "Bought again love it ❤️" if i % 4 == 0 else
            "Bro this ad again 😂" if i % 4 == 1 else
            "Broken item defect poor quality" if i % 4 == 2 else
            "What is the retail price?"
        )
        for i in range(100)
    ]
    
    run1 = [r.to_dict() for r in classifier.classify_batch(texts)]
    run2 = [r.to_dict() for r in classifier.classify_batch(texts)]
    run3 = [r.to_dict() for r in classifier.classify_batch(texts)]

    assert run1 == run2
    assert run2 == run3


def test_none_empty_whitespace_and_non_english(classifier):
    # None input
    res_none = classifier.classify(None)
    assert res_none.category == "neutral"
    assert res_none.critical_complaint is False

    # Whitespace input
    res_ws = classifier.classify("   \t\n  ")
    assert res_ws.category == "neutral"
    assert res_ws.critical_complaint is False

    # Empty text event
    res_empty = classifier.classify(CommentEvent(
        event_id="e_empty",
        timestamp="2026-09-30T12:00:00Z",
        campaign_id="c1",
        ad_id="a1",
        author_id="u1",
        text=""
    ))
    assert res_empty.category == "neutral"
    assert res_empty.critical_complaint is False

    # Regional language inputs must not crash or fall into bogus complaint defaults
    telugu_res = classifier.classify_text("ఈ యాడ్ చాలా బాగుంది super quality ❤️")
    assert telugu_res.sentiment in {"positive", "neutral", "negative"}
    assert telugu_res.critical_complaint is False

    hinglish_res = classifier.classify_text("Bhai delivery bohot fast thi aur product ekdum top class hai ❤️")
    assert hinglish_res.category == "positive"
    assert hinglish_res.sentiment == "positive"
