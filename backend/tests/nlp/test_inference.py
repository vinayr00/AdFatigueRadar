"""
Tests for Streaming & Batched Inference Engine
"""

import pytest
from backend.nlp import CommentEvent, NLPResult
from backend.nlp.inference import StreamCommentProcessor


def test_stream_comment_processor_bulk():
    processor = StreamCommentProcessor(batch_size=4, use_cache=False)
    events = [
        CommentEvent(
            event_id=f"stream_event_{i}",
            timestamp="2026-09-30T12:00:00Z",
            campaign_id="camp_1",
            ad_id="ad_1",
            author_id=f"auth_{i}",
            text=f"Sample comment {i} about the product"
        )
        for i in range(10)
    ]

    results = processor.process_bulk(events)
    assert len(results) == 10
    assert all(isinstance(r, NLPResult) for r in results)


def test_stream_comment_processor_generator():
    processor = StreamCommentProcessor(batch_size=3, use_cache=False)
    
    def event_gen():
        for i in range(7):
            yield CommentEvent(
                event_id=f"gen_{i}",
                timestamp="2026-09-30T12:00:00Z",
                campaign_id="camp_1",
                ad_id="ad_1",
                author_id=f"auth_{i}",
                text="Bro this ad again 😂"
            )

    results = list(processor.process_stream(event_gen()))
    assert len(results) == 7
    assert all(r.category == "fatigue" for r in results)
