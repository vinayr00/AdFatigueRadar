"""
AdFatigueRadar — Deduplication and Near-Duplicate Detection Module
================================================================
PERSON 1: AI / NLP Layer (Phase 1 Remediation)

Provides deterministic exact, normalized, and near-duplicate detection for real-world comments:
1. Exact Text Match
2. Normalized Text Match (ignoring case, excess spaces, punctuation differences)
3. Source ID Collisions
4. Near-Duplicate Grouping (Token Jaccard >= threshold)

Emits audit report to data/reports/deduplication_report.json.
"""

import os
import re
import json
import unicodedata
from typing import List, Dict, Any, Tuple, Set, Optional
from collections import defaultdict


def normalize_for_dedup(text: str) -> str:
    """
    Normalizes text strictly for duplicate detection.
    Does NOT mutate canonical raw text.
    """
    if not text:
        return ""
    norm = unicodedata.normalize("NFKC", text).lower()
    # Strip punctuation and collapse whitespace
    norm = re.sub(r"[^\w\s]", "", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm


def tokenize_for_jaccard(text: str) -> Set[str]:
    """Token set for Jaccard similarity."""
    norm = normalize_for_dedup(text)
    return set(norm.split()) if norm else set()


def jaccard_similarity(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    """Calculates token Jaccard similarity."""
    if not tokens_a or not tokens_b:
        return 0.0
    inter = len(tokens_a.intersection(tokens_b))
    union = len(tokens_a.union(tokens_b))
    return inter / union if union > 0 else 0.0


class Deduplicator:
    """
    Deduplicator and Leakage Auditor.
    """
    def __init__(self, jaccard_threshold: float = 0.85, version: str = "dedup-v1.0"):
        self.jaccard_threshold = jaccard_threshold
        self.version = version

    def process_records(
        self,
        records: List[Dict[str, Any]],
        report_path: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Deduplicates a list of record dictionaries.
        Preserves the first occurrence and tracks duplicates in duplicate_groups.
        """
        records_before = len(records)
        seen_source_ids = set()
        seen_exact_texts = {}  # text -> first_record_id
        seen_norm_texts = {}   # norm_text -> first_record_id
        
        unique_records = []
        duplicate_groups = defaultdict(list)
        
        exact_dups = 0
        norm_dups = 0
        source_id_dups = 0
        near_dup_flagged = 0

        # Pass 1: Exact & Normalized Deduplication
        for r in records:
            cid = r.get("comment_id", "")
            raw_text = r.get("text", "")
            source_id = r.get("source_record_id") or cid
            norm_text = normalize_for_dedup(raw_text)

            # Check Source ID collision
            if source_id in seen_source_ids:
                source_id_dups += 1
                duplicate_groups[f"source_id:{source_id}"].append(cid)
                continue

            # Check Exact Raw Text collision
            if raw_text in seen_exact_texts:
                exact_dups += 1
                canonical_id = seen_exact_texts[raw_text]
                duplicate_groups[f"exact:{canonical_id}"].append(cid)
                continue

            # Check Normalized Text collision
            if norm_text in seen_norm_texts:
                norm_dups += 1
                canonical_id = seen_norm_texts[norm_text]
                duplicate_groups[f"norm:{canonical_id}"].append(cid)
                continue

            # First time seeing this record
            seen_source_ids.add(source_id)
            seen_exact_texts[raw_text] = cid
            seen_norm_texts[norm_text] = cid
            unique_records.append(r)

        # Pass 2: Near-Duplicate Detection on unique records
        # Tokens cache
        record_tokens = [(r, tokenize_for_jaccard(r.get("text", ""))) for r in unique_records]
        final_records = []
        seen_near_indices = set()

        for i in range(len(record_tokens)):
            if i in seen_near_indices:
                continue
            rec_i, tokens_i = record_tokens[i]
            final_records.append(rec_i)
            
            # Compare against remaining
            for j in range(i + 1, len(record_tokens)):
                if j in seen_near_indices:
                    continue
                rec_j, tokens_j = record_tokens[j]
                sim = jaccard_similarity(tokens_i, tokens_j)
                if sim >= self.jaccard_threshold:
                    near_dup_flagged += 1
                    seen_near_indices.add(j)
                    duplicate_groups[f"near_jaccard_{self.jaccard_threshold}:{rec_i.get('comment_id')}"].append({
                        "duplicate_id": rec_j.get("comment_id"),
                        "similarity": round(sim, 4),
                        "text": rec_j.get("text")
                    })

        report = {
            "deduplication_version": self.version,
            "methodology": {
                "exact_match": "Strict raw text identity",
                "normalized_match": "Unicode NFKC, lowercase, punctuation removed",
                "near_duplicate_method": "Token Jaccard similarity",
                "near_duplicate_threshold": self.jaccard_threshold,
            },
            "summary": {
                "records_before": records_before,
                "exact_duplicates": exact_dups,
                "normalized_duplicates": norm_dups,
                "source_id_duplicates": source_id_dups,
                "near_duplicates_removed": len(seen_near_indices),
                "records_after": len(final_records),
            },
            "duplicate_groups_count": len(duplicate_groups),
            "sample_duplicate_groups": {k: duplicate_groups[k][:3] for k in list(duplicate_groups.keys())[:10]}
        }

        if report_path:
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

        return final_records, report
