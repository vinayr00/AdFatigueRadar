"""
AdFatigueRadar — NLP Configuration & Constants
==============================================
PERSON 1: AI / NLP Layer

Centralized configuration, version strings, frozen categories,
and decision threshold constants.
"""

from typing import Tuple, Set

# Model and Preprocessing Versions for Cache Keying & Reproducibility
MODEL_VERSION: str = "adfatigue-nlp-v2.0"
PREPROCESSING_VERSION: str = "preproc-v2.0"

# Frozen 8-Class Ad-Fatigue Taxonomy
TAXONOMY_CATEGORIES: Tuple[str, ...] = (
    "product_complaint",
    "service_complaint",
    "fatigue",
    "mockery",
    "spam",
    "banter_meme",
    "neutral",
    "positive",
)

# Critical Complaint Specification Constants
CRITICAL_COMPLAINT_CATEGORIES: Set[str] = {
    "product_complaint",
    "service_complaint",
}

# Minimum Calibrated Confidence required for critical_complaint flag
CRITICAL_COMPLAINT_CONFIDENCE_THRESHOLD: float = 0.85

# Minimum confidence required before falling back to neutral for ambiguous/unknown text
LOW_CONFIDENCE_FALLBACK_THRESHOLD: float = 0.20

# Sentiment Labels
SENTIMENT_LABELS: Tuple[str, ...] = (
    "negative",
    "neutral",
    "positive",
)

# Inference and Batch Processing Defaults
DEFAULT_BATCH_SIZE: int = 32
DEFAULT_MAX_SEQ_LENGTH: int = 128
