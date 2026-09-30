"""
Tests for Deterministic Replay NLP Cache
"""

import os
import pytest
import tempfile
from backend.nlp import MODEL_VERSION, PREPROCESSING_VERSION, NLPResult
from backend.nlp.cache import NLPCache


def test_cache_memory_set_and_get():
    cache = NLPCache()
    result = NLPResult(
        comment_id="c_101",
        sentiment="negative",
        sentiment_score=0.92,
        category="fatigue",
        confidence=0.95,
        critical_complaint=False,
    )
    
    # Miss before setting
    assert cache.get("c_101") is None
    assert cache.misses == 1
    
    # Set and hit
    cache.set(result)
    retrieved = cache.get("c_101")
    assert retrieved is not None
    assert retrieved.comment_id == "c_101"
    assert retrieved.category == "fatigue"
    assert cache.hits == 1


def test_cache_version_invalidation():
    cache = NLPCache()
    result = NLPResult(
        comment_id="c_102",
        sentiment="positive",
        sentiment_score=0.88,
        category="positive",
        confidence=0.91,
        critical_complaint=False,
    )
    cache.set(result, model_ver="model_v1.0", preproc_ver="pre_v1.0")

    # Match exact versions
    assert cache.get("c_102", model_ver="model_v1.0", preproc_ver="pre_v1.0") is not None
    
    # Invalidation on different model version
    assert cache.get("c_102", model_ver="model_v2.0", preproc_ver="pre_v1.0") is None
    
    # Invalidation on different preprocessing version
    assert cache.get("c_102", model_ver="model_v1.0", preproc_ver="pre_v2.0") is None


def test_cache_sqlite_persistence(tmp_path):
    db_path = str(tmp_path / "test_nlp_cache.db")

    cache1 = NLPCache(db_path=db_path)
    result = NLPResult(
        comment_id="c_103",
        sentiment="negative",
        sentiment_score=0.94,
        category="product_complaint",
        confidence=0.89,
        critical_complaint=True,
    )
    cache1.set(result)

    # Open fresh instance with same DB
    cache2 = NLPCache(db_path=db_path)
    retrieved = cache2.get("c_103")
    assert retrieved is not None
    assert retrieved.comment_id == "c_103"
    assert retrieved.critical_complaint is True
