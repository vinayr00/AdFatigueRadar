"""
AdFatigueRadar — NLP Preprocessing Module
=========================================
PERSON 1: AI / NLP Layer

Handles text normalization, Unicode normalization, whitespace cleanup,
and preservation of critical semantic signals (emojis, repetition, sentiment cues).
Deterministic and strictly versioned.
"""

import re
import unicodedata
from typing import Dict, Any

from . import PREPROCESSING_VERSION


def normalize_text(text: str) -> str:
    """
    Deterministically cleans and normalizes raw comment text.
    
    Preserves:
    - Emojis (crucial for mockery, sentiment, banter detection e.g. 😂, 💀, 🤡, 🔥, 😡)
    - Punctuation cues (e.g., '??', '!!', ellipses)
    - Semantic distinctions ('again', 'bought again', 'this ad again')
    
    Removes:
    - Invisible zero-width and control characters
    - Excess internal whitespace and linebreaks
    - Leading/trailing whitespace
    """
    if not text:
        return ""
    
    # 1. Unicode NFC Normalization
    normalized = unicodedata.normalize("NFC", text)
    
    # 2. Strip non-printable / control characters (keep standard whitespace and normal text/emojis)
    # Remove zero-width spaces, soft hyphens, BOM, control codes
    normalized = re.sub(r"[\u200B-\u200D\uFEFF\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", normalized)
    
    # 3. Collapse multiple whitespace characters/newlines into a single space
    normalized = re.sub(r"\s+", " ", normalized)
    
    # 4. Collapse excessive character repetition (> 3 repetitions to 3, e.g., "noooooooo" -> "nooo")
    # This preserves emphasis while preventing regex/tokenization pathological blowups
    normalized = re.sub(r"(\S)\1{3,}", r"\1\1\1", normalized)
    
    # 5. Trim leading and trailing whitespace
    return normalized.strip()


def extract_features_meta(text: str) -> Dict[str, Any]:
    """
    Extracts structural metadata useful for taxonomy discrimination.
    """
    clean = normalize_text(text)
    lower = clean.lower()
    
    has_question = "?" in clean
    has_exclamation = "!" in clean
    all_caps_words = len([w for w in clean.split() if w.isupper() and len(w) > 1])
    
    # Check for presence of key marker patterns
    has_again = bool(re.search(r"\bagain\b", lower))
    has_ad_reference = bool(re.search(r"\b(ad|commercial|sponsor|sponsored|promo|feed|algorithm|timeline|fyp)\b", lower))
    has_purchase_reference = bool(re.search(r"\b(bought|ordered|purchase|purchased|arrived|received|shipped|delivery|item|package|refund|return)\b", lower))
    
    return {
        "clean_text": clean,
        "char_len": len(clean),
        "word_count": len(clean.split()),
        "has_question": has_question,
        "has_exclamation": has_exclamation,
        "all_caps_words": all_caps_words,
        "has_again": has_again,
        "has_ad_reference": has_ad_reference,
        "has_purchase_reference": has_purchase_reference,
        "preprocessing_version": PREPROCESSING_VERSION,
    }
