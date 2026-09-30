"""
AdFatigueRadar — Unified Two-Stage Comment Classifier
====================================================
PERSON 1: AI / NLP Layer

Integrates:
  1. Preprocessing & Unicode normalization
  2. Stage 1: RoBERTa Sentiment Classification
  3. Stage 2: 8-Class Ad-Fatigue Taxonomy Classification
  4. Temperature-Calibrated Confidence Estimation
  5. Critical Complaint Identification
  6. Replay Cache lookup and population

Emits strictly the frozen NLPResult schema:
  - comment_id: str
  - sentiment: str
  - sentiment_score: float
  - category: str
  - confidence: float
  - critical_complaint: bool
"""

from typing import Union, Dict, Any, List, Optional

from .constants import (
    MODEL_VERSION,
    PREPROCESSING_VERSION,
    TAXONOMY_CATEGORIES,
)
from . import CommentEvent, NLPResult
from .preprocessing import normalize_text
from .sentiment import SentimentClassifier
from .taxonomy import TaxonomyClassifier
from .calibration import TemperatureScaler, default_scaler
from .cache import NLPCache


class CommentClassifier:
    """
    Main entrypoint for Person 1 NLP classification.
    Adheres strictly to the frozen input CommentEvent and output NLPResult contracts.
    """
    def __init__(
        self,
        use_cache: bool = True,
        cache_db_path: Optional[str] = None,
        model_dir: Optional[str] = None,
        scaler: Optional[TemperatureScaler] = None,
    ):
        self.scaler = scaler or default_scaler
        self.sentiment_stage = SentimentClassifier(
            model_dir=model_dir,
            scaler=self.scaler,
        )
        self.taxonomy_stage = TaxonomyClassifier(
            model_dir=model_dir,
            scaler=self.scaler,
        )
        self.use_cache = use_cache
        self.cache = NLPCache(db_path=cache_db_path) if use_cache else None

    def classify_text(self, text: Optional[str], comment_id: str = "temp_comment") -> NLPResult:
        """
        Classifies a single raw text string directly into an NLPResult.
        """
        clean = normalize_text(text) if text is not None else ""
        
        # 1. Stage 1: Sentiment Classification
        sentiment, sentiment_score, _ = self.sentiment_stage.predict(clean)
        
        # 2. Stage 2: Taxonomy Classification
        category, confidence, is_critical, _ = self.taxonomy_stage.classify(
            clean,
            sentiment_hint=sentiment
        )
        
        # 3. Construct frozen NLPResult
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
        comment: Union[CommentEvent, Dict[str, Any], str, None],
        bypass_cache: bool = False
    ) -> NLPResult:
        """
        Classifies a CommentEvent, dictionary, or string adhering to the frozen contract.
        """
        if isinstance(comment, CommentEvent):
            event_id = comment.event_id
            text = comment.text
        elif isinstance(comment, dict):
            event_id = str(comment.get("event_id") or comment.get("comment_id", "anon_comment"))
            text = str(comment.get("text", "") if comment.get("text") is not None else "")
        elif isinstance(comment, str):
            event_id = "text_comment"
            text = comment
        elif comment is None:
            event_id = "null_comment"
            text = ""
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
        comments: List[Union[CommentEvent, Dict[str, Any], str, None]],
        bypass_cache: bool = False
    ) -> List[NLPResult]:
        """
        High-performance batched classification preserving exact input order and ID mappings.
        """
        if not comments:
            return []

        # Parse inputs into structured lists
        event_ids: List[str] = []
        texts: List[str] = []
        
        for c in comments:
            if isinstance(c, CommentEvent):
                event_ids.append(c.event_id)
                texts.append(c.text or "")
            elif isinstance(c, dict):
                event_ids.append(str(c.get("event_id") or c.get("comment_id", "anon_comment")))
                texts.append(str(c.get("text", "") if c.get("text") is not None else ""))
            elif isinstance(c, str):
                event_ids.append("text_comment")
                texts.append(c)
            elif c is None:
                event_ids.append("null_comment")
                texts.append("")
            else:
                raise ValueError(f"Unsupported comment type: {type(c)}")

        results: List[Optional[NLPResult]] = [None] * len(comments)
        uncached_indices: List[int] = []

        # 1. Check cache for each item if enabled
        if self.use_cache and self.cache and not bypass_cache:
            for idx, event_id in enumerate(event_ids):
                cached = self.cache.get(event_id, MODEL_VERSION, PREPROCESSING_VERSION)
                if cached is not None:
                    results[idx] = cached
                else:
                    uncached_indices.append(idx)
        else:
            uncached_indices = list(range(len(comments)))

        # 2. Run batched inference on uncached items
        if uncached_indices:
            batch_texts = [texts[i] for i in uncached_indices]
            
            # Batch Stage 1
            sentiment_outputs = self.sentiment_stage.predict_batch(batch_texts)
            # Batch Stage 2
            taxonomy_outputs = self.taxonomy_stage.classify_batch(batch_texts)

            for j, original_idx in enumerate(uncached_indices):
                sent_label, sent_score, _ = sentiment_outputs[j]
                cat_label, cat_conf, is_crit, _ = taxonomy_outputs[j]
                
                res = NLPResult(
                    comment_id=event_ids[original_idx],
                    sentiment=sent_label,
                    sentiment_score=sent_score,
                    category=cat_label,
                    confidence=cat_conf,
                    critical_complaint=is_crit,
                )
                results[original_idx] = res
                
                # Store in cache
                if self.use_cache and self.cache and not bypass_cache:
                    self.cache.set(res, MODEL_VERSION, PREPROCESSING_VERSION)

        return results  # type: ignore

    def clear_cache(self) -> None:
        """Clears underlying replay cache."""
        if self.cache:
            self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Returns cache telemetry stats."""
        if self.cache:
            return self.cache.stats()
        return {"use_cache": False}
