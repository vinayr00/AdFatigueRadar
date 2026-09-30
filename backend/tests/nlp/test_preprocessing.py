"""
Tests for NLP Preprocessing and Normalization Module
"""

import pytest
from backend.nlp.preprocessing import normalize_text, extract_features_meta
from backend.nlp import PREPROCESSING_VERSION


def test_normalize_text_whitespace():
    raw = "   Bro   this   ad    again   \n\n  😂   "
    clean = normalize_text(raw)
    assert clean == "Bro this ad again 😂"


def test_normalize_text_repetition():
    raw = "nooooooooo waaaaaaay brooooo"
    clean = normalize_text(raw)
    # Characters repeated > 3 times should be capped at 3
    assert clean == "nooo waaay brooo"


def test_normalize_text_preserves_emojis_and_punctuation():
    raw = "The acting in this ad is killing me 💀💀😭 !!! ???"
    clean = normalize_text(raw)
    assert "💀" in clean
    assert "😭" in clean
    assert "!!!" in clean
    assert "???" in clean


def test_normalize_text_zero_width_and_control_chars():
    # Insert zero-width space and BOM
    raw = "Hello\u200B\uFEFF World\x00"
    clean = normalize_text(raw)
    assert clean == "Hello World"


def test_extract_features_meta():
    text = "Bro this ad again 😂 Is this real? Bought again!"
    meta = extract_features_meta(text)
    assert meta["preprocessing_version"] == PREPROCESSING_VERSION
    assert meta["has_question"] is True
    assert meta["has_exclamation"] is True
    assert meta["has_again"] is True
    assert meta["has_ad_reference"] is True
    assert meta["has_purchase_reference"] is True
    assert meta["word_count"] > 0
