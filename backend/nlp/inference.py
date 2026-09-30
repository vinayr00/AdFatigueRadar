"""
AdFatigueRadar — High-Throughput NLP Inference Engine
=====================================================
PERSON 1: AI / NLP Layer

Provides optimized streaming and batched inference pipelines for live comment feeds
and replay simulation.
"""

from typing import List, Dict, Any, Generator, Optional, Union
import time

from . import CommentEvent, NLPResult
from .classifier import CommentClassifier


class StreamCommentProcessor:
    """
    Streaming processor for comment events.
    Supports micro-batching, latency profiling, and streaming generator consumption.
    """
    def __init__(
        self,
        classifier: Optional[CommentClassifier] = None,
        batch_size: int = 32,
        use_cache: bool = True
    ):
        self.classifier = classifier or CommentClassifier(use_cache=use_cache)
        self.batch_size = batch_size

    def process_event(self, event: Union[CommentEvent, Dict[str, Any]]) -> NLPResult:
        """Processes a single live event with sub-minute latency guarantee."""
        return self.classifier.classify(event)

    def process_stream(
        self,
        event_stream: Generator[Union[CommentEvent, Dict[str, Any]], None, None]
    ) -> Generator[NLPResult, None, None]:
        """
        Consumes an incoming stream/generator of events and yields NLPResults.
        """
        buffer = []
        for event in event_stream:
            buffer.append(event)
            if len(buffer) >= self.batch_size:
                results = self.classifier.classify_batch(buffer)
                for r in results:
                    yield r
                buffer = []

        if buffer:
            results = self.classifier.classify_batch(buffer)
            for r in results:
                yield r

    def process_bulk(
        self,
        events: List[Union[CommentEvent, Dict[str, Any]]],
        chunk_size: Optional[int] = None
    ) -> List[NLPResult]:
        """
        Processes a static list of events in chunks.
        """
        chunk_size = chunk_size or self.batch_size
        results: List[NLPResult] = []
        
        for i in range(0, len(events), chunk_size):
            chunk = events[i : i + chunk_size]
            results.extend(self.classifier.classify_batch(chunk))
            
        return results
