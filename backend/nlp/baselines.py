"""
AdFatigueRadar — P1 Sentiment-Only Baseline Module
==================================================
PERSON 1: AI / NLP Layer (P1 Extension)

Implements Baseline C: Stage-1 Raw Sentiment-Only Guard.
Used to benchmark and demonstrate why naive sentiment models generate false-positive
alarms during harmless banter-storms, contrasting with the combined 8-class taxonomy guard.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from . import CommentEvent, NLPResult
from .classifier import CommentClassifier


@dataclass(frozen=True)
class SentimentBaselineMetrics:
    """Baseline metrics output for a rolling observation window."""
    total_comments: int
    negative_count: int
    raw_negative_share: float
    threshold: float
    alert_triggered: bool
    is_false_alarm_on_banter: bool


class SentimentOnlyBaseline:
    """
    Baseline C: Evaluates ad risk using ONLY raw negative sentiment from Stage 1.
    Ignores category weighting and includes banter/memes indiscriminately.
    """
    def __init__(
        self,
        classifier: Optional[CommentClassifier] = None,
        negative_threshold: float = 0.35
    ):
        self.classifier = classifier or CommentClassifier(use_cache=True)
        self.negative_threshold = negative_threshold

    def evaluate_window(
        self,
        comments: List[CommentEvent]
    ) -> SentimentBaselineMetrics:
        """
        Evaluates a window of comments under the naive sentiment-only approach.
        """
        if not comments:
            return SentimentBaselineMetrics(
                total_comments=0,
                negative_count=0,
                raw_negative_share=0.0,
                threshold=self.negative_threshold,
                alert_triggered=False,
                is_false_alarm_on_banter=False,
            )

        nlp_results = self.classifier.classify_batch(comments)
        
        negative_count = sum(1 for r in nlp_results if r.sentiment == "negative")
        banter_count = sum(1 for r in nlp_results if r.category == "banter_meme")
        
        total = len(nlp_results)
        raw_negative_share = round(negative_count / total, 4)
        alert_triggered = raw_negative_share >= self.negative_threshold
        
        # If alert fired primarily because banter/memes were treated as negative
        is_false_alarm = alert_triggered and (banter_count / total >= 0.25) and (
            sum(1 for r in nlp_results if r.category in {"product_complaint", "service_complaint", "fatigue"}) / total < 0.15
        )

        return SentimentBaselineMetrics(
            total_comments=total,
            negative_count=negative_count,
            raw_negative_share=raw_negative_share,
            threshold=self.negative_threshold,
            alert_triggered=alert_triggered,
            is_false_alarm_on_banter=is_false_alarm,
        )
