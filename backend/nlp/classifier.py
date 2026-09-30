"""
AdFatigueRadar — Unified Two-Stage Comment Classifier
====================================================
PERSON 1: AI / NLP Layer

Integrates:
  1. Preprocessing & Unicode normalization
  2. Stage 1: General sentiment classification
  3. Stage 2: 8-class ad-fatigue taxonomy classification
  4. Temperature-calibrated confidence estimation
  5. Critical complaint identification
  6. Replay cache lookup and population

Primary interface consumed by Person 2 (Backend Risk) and Person 3 (Replay/Frontend).
"""

from typing import Union, Dict, Any, List, Optional

from . import (
    MODEL_VERSION,
    PREPROCESSING_VERSION,
    TAXONOMY_CATEGORIES,
    CommentEvent,
    NLPResult,
)
from .preprocessing import normalize_text
from .sentiment import SentimentClassifier
from .taxonomy import TaxonomyClassifier
from .calibration import TemperatureScaler, default_scaler
from .cache import NLPCache


class CommentClassifier:
    """
    Main entrypoint for Person 1 NLP classification.
    
    Adheres strictly to the frozen input CommentEvent and output NLPResult contracts.
    Does NOT modify backend risk, action logic, or database state.
    """
    def __init__(
        self,
        use_cache: bool = True,
        cache_db_path: Optional[str] = None,
        use_transformer: bool = False,
        temperature: float = 1.12
    ):
        self.scaler = TemperatureScaler(temperature=temperature)
        self.sentiment_stage = SentimentClassifier(
            scaler=self.scaler,
            use_transformer=use_transformer
        )
        self.taxonomy_stage = TaxonomyClassifier(scaler=self.scaler)
        
        self.use_cache = use_cache
        self.cache = NLPCache(db_path=cache_db_path) if use_cache else None

    def classify_text(self, text: str, comment_id: str = "temp_comment") -> NLPResult:
        """
        Classifies raw text directly into an NLPResult.
        """
        clean = normalize_text(text)
        
        # 1. Stage 1: Sentiment Classification
        sentiment, sentiment_score, _ = self.sentiment_stage.predict(clean)
        
        # 2. Stage 2: Taxonomy Classification (conditioned with sentiment hint)
        category, confidence, is_critical, _ = self.taxonomy_stage.classify(
            clean,
            sentiment_hint=sentiment
        )
        
        # 3. Create frozen NLPResult
        return NLPResult(
            comment_id=comment_id,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            category=category,
            confidence=confidence,
            critical_complaint=is_critical,
        )

    def classify(
        self,
        comment: Union[CommentEvent, Dict[str, Any], str],
        bypass_cache: bool = False
    ) -> NLPResult:
        """
        Classifies a CommentEvent or dictionary adhering to the frozen contract.
        
        Input Schema:
            {
                "event_id": str,
                "timestamp": str,
                "campaign_id": str,
                "ad_id": str,
                "author_id": str,
                "text": str,
                "reactions": int,
                "replies": int
            }
        """
        # Parse input
        if isinstance(comment, CommentEvent):
            event_id = comment.event_id
            text = comment.text
        elif isinstance(comment, dict):
            event_id = str(comment.get("event_id") or comment.get("comment_id", "anon_comment"))
            text = str(comment.get("text", ""))
        elif isinstance(comment, str):
            event_id = "text_comment"
            text = comment
        else:
            raise ValueError(f"Unsupported comment type: {type(comment)}")

        # 1. Check Replay Cache if active and not bypassed
        if self.use_cache and self.cache and not bypass_cache:
            cached_result = self.cache.get(event_id, MODEL_VERSION, PREPROCESSING_VERSION)
            if cached_result is not None:
                return cached_result

        # 2. Compute inference
        result = self.classify_text(text=text, comment_id=event_id)

        # 3. Store in cache
        if self.use_cache and self.cache and not bypass_cache:
            self.cache.set(result, MODEL_VERSION, PREPROCESSING_VERSION)

        return result

    def classify_batch(
        self,
        comments: List[Union[CommentEvent, Dict[str, Any], str]],
        bypass_cache: bool = False
    ) -> List[NLPResult]:
        """
        Batched classification for high-throughput stream processing.
        """
        return [self.classify(c, bypass_cache=bypass_cache) for c in comments]

    def clear_cache(self) -> None:
        """Clears underlying replay cache."""
        if self.cache:
            self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Returns cache telemetry stats."""
        if self.cache:
            return self.cache.stats()
        return {"use_cache": False}
