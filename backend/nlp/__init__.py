"""
AdFatigueRadar — NLP Module Package
===================================
PERSON 1: AI / NLP Layer

Provides two-stage sentiment & 8-class ad-fatigue taxonomy classification,
temperature calibration, critical complaint detection, and replay caching.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from .constants import (
    MODEL_VERSION,
    PREPROCESSING_VERSION,
    TAXONOMY_CATEGORIES,
    CRITICAL_COMPLAINT_CATEGORIES,
    CRITICAL_COMPLAINT_CONFIDENCE_THRESHOLD,
    LOW_CONFIDENCE_FALLBACK_THRESHOLD,
    SENTIMENT_LABELS,
    DEFAULT_BATCH_SIZE,
    DEFAULT_MAX_SEQ_LENGTH,
)


@dataclass(frozen=True)
class CommentEvent:
    """Frozen input contract for comment ingestion."""
    event_id: str
    timestamp: str
    campaign_id: str
    ad_id: str
    author_id: str
    text: str
    reactions: int = 0
    replies: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommentEvent":
        return cls(
            event_id=str(data.get("event_id", "")),
            timestamp=str(data.get("timestamp", "")),
            campaign_id=str(data.get("campaign_id", "")),
            ad_id=str(data.get("ad_id", "")),
            author_id=str(data.get("author_id", "")),
            text=str(data.get("text", "") or ""),
            reactions=int(data.get("reactions", 0)),
            replies=int(data.get("replies", 0)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NLPResult:
    """Frozen output contract emitted by Person 1 for downstream risk consumption."""
    comment_id: str
    sentiment: str             # "positive" | "neutral" | "negative"
    sentiment_score: float     # [0.0, 1.0] calibrated probability of predicted sentiment
    category: str              # One of the 8 TAXONOMY_CATEGORIES
    confidence: float          # [0.0, 1.0] calibrated category confidence
    critical_complaint: bool   # True if category in {product, service}_complaint and confidence >= 0.85

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "sentiment": self.sentiment,
            "sentiment_score": round(self.sentiment_score, 4),
            "category": self.category,
            "confidence": round(self.confidence, 4),
            "critical_complaint": self.critical_complaint,
        }


__all__ = [
    "MODEL_VERSION",
    "PREPROCESSING_VERSION",
    "TAXONOMY_CATEGORIES",
    "CRITICAL_COMPLAINT_CATEGORIES",
    "CRITICAL_COMPLAINT_CONFIDENCE_THRESHOLD",
    "LOW_CONFIDENCE_FALLBACK_THRESHOLD",
    "SENTIMENT_LABELS",
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_MAX_SEQ_LENGTH",
    "CommentEvent",
    "NLPResult",
]
