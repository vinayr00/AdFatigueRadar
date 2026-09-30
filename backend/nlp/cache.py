"""
AdFatigueRadar — Replay NLP Cache Module
========================================
PERSON 1: AI / NLP Layer

Provides high-performance, deterministic caching for replay runs.
Keyed by: (comment_id + model_version + preprocessing_version).

IMPORTANT:
- Replay runs use cached outputs to ensure rapid replay simulation.
- Live latency benchmarks MUST bypass this cache to report true wall-clock times.
"""

import os
import json
import sqlite3
import hashlib
from typing import Optional, Dict, Any, Tuple

from .constants import MODEL_VERSION, PREPROCESSING_VERSION
from . import NLPResult


class NLPCache:
    """
    Two-tier (In-Memory + SQLite) Replay Cache.
    Ensures zero redundant NLP computation during multi-seed replay simulation
    while maintaining strict version isolation.
    Gracefully handles corrupt databases by falling back to memory caching.
    """
    def __init__(self, db_path: Optional[str] = None):
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.hits: int = 0
        self.misses: int = 0
        self.db_path = db_path
        
        if self.db_path:
            try:
                self._init_db()
            except Exception:
                # Corrupt DB or disk error -> safely disable SQLite L2 cache and rely on memory L1
                self.db_path = None

    def _init_db(self):
        """Initializes SQLite cache schema."""
        if not self.db_path:
            return
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nlp_cache (
                    cache_key TEXT PRIMARY KEY,
                    comment_id TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    preprocessing_version TEXT NOT NULL,
                    sentiment TEXT NOT NULL,
                    sentiment_score REAL NOT NULL,
                    category TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    critical_complaint INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    @staticmethod
    def generate_key(
        comment_id: str,
        model_ver: str = MODEL_VERSION,
        preproc_ver: str = PREPROCESSING_VERSION
    ) -> str:
        """
        Builds a deterministic SHA-256 cache key.
        """
        raw = f"{comment_id}::{model_ver}::{preproc_ver}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(
        self,
        comment_id: str,
        model_ver: str = MODEL_VERSION,
        preproc_ver: str = PREPROCESSING_VERSION
    ) -> Optional[NLPResult]:
        """Retrieves cached NLPResult if present and versions match."""
        key = self.generate_key(comment_id, model_ver, preproc_ver)
        
        # 1. Check L1 Memory Cache
        if key in self.memory_cache:
            self.hits += 1
            data = self.memory_cache[key]
            return NLPResult(
                comment_id=data["comment_id"],
                sentiment=data["sentiment"],
                sentiment_score=data["sentiment_score"],
                category=data["category"],
                confidence=data["confidence"],
                critical_complaint=bool(data["critical_complaint"]),
            )

        # 2. Check L2 SQLite Cache
        if self.db_path and os.path.exists(self.db_path):
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT comment_id, sentiment, sentiment_score, category, confidence, critical_complaint "
                        "FROM nlp_cache WHERE cache_key = ?",
                        (key,)
                    )
                    row = cursor.fetchone()
                    if row:
                        self.hits += 1
                        result_dict = {
                            "comment_id": row[0],
                            "sentiment": row[1],
                            "sentiment_score": float(row[2]),
                            "category": row[3],
                            "confidence": float(row[4]),
                            "critical_complaint": bool(row[5]),
                        }
                        self.memory_cache[key] = result_dict
                        return NLPResult(**result_dict)
            except Exception:
                pass

        self.misses += 1
        return None

    def set(
        self,
        result: NLPResult,
        model_ver: str = MODEL_VERSION,
        preproc_ver: str = PREPROCESSING_VERSION
    ) -> None:
        """Stores an NLPResult in both memory and SQLite cache."""
        key = self.generate_key(result.comment_id, model_ver, preproc_ver)
        data_dict = result.to_dict()
        self.memory_cache[key] = data_dict

        if self.db_path:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO nlp_cache
                        (cache_key, comment_id, model_version, preprocessing_version,
                         sentiment, sentiment_score, category, confidence, critical_complaint)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        key,
                        result.comment_id,
                        model_ver,
                        preproc_ver,
                        result.sentiment,
                        result.sentiment_score,
                        result.category,
                        result.confidence,
                        1 if result.critical_complaint else 0
                    ))
                    conn.commit()
            except Exception:
                pass

    def clear(self) -> None:
        """Clears memory and database cache."""
        self.memory_cache.clear()
        self.hits = 0
        self.misses = 0
        if self.db_path and os.path.exists(self.db_path):
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM nlp_cache")
                    conn.commit()
            except Exception:
                pass

    def stats(self) -> Dict[str, Any]:
        """Returns cache telemetry statistics."""
        total = self.hits + self.misses
        hit_ratio = (self.hits / total) if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_ratio": round(hit_ratio, 4),
            "memory_items": len(self.memory_cache),
            "model_version": MODEL_VERSION,
            "preprocessing_version": PREPROCESSING_VERSION,
        }
