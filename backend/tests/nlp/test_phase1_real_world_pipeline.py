"""
AdFatigueRadar — Phase 1 Real-World Pipeline Unit & Integration Tests
====================================================================
PERSON 1: AI / NLP Layer (Phase 1 Remediation)

Tests:
1. PII Sanitization (detection, replacement, emoji & punctuation preservation)
2. Exact & Near-Duplicate Detection (Token Jaccard, normalized matching)
3. Annotation schema validation, double-labeling, Cohen's kappa calculation
4. 4-Way split isolation & zero leakage verification (TRAIN, VAL, TEST, OOD)
5. CardiffNLP auxiliary signal extraction (Sentiment, Irony, Multilingual XLM-R)
6. Dataset manifests integrity and file alignment
"""

import os
import json
import pytest
from backend.nlp.pii_sanitizer import PIISanitizer
from backend.nlp.deduplication import Deduplicator, normalize_for_dedup, jaccard_similarity, tokenize_for_jaccard
from backend.nlp.annotation_pipeline import (
    validate_annotation_record,
    compute_cohens_kappa,
    resolve_and_adjudicate,
    TAXONOMY_CATEGORIES
)
from backend.nlp.signals import CardiffNLPSignals, preprocess_for_twitter_roberta
from backend.nlp.leakage_checker import check_4way_split_leakage


# 1. PII Sanitization Tests
def test_pii_sanitizer_redacts_sensitive_tokens():
    sanitizer = PIISanitizer()
    raw = "Contact john.doe@acme.org or +1 (555) 234-5678, user @alex_promo visited https://tracker.com/u/123 from 192.168.1.50"
    clean, counts = sanitizer.sanitize(raw)
    
    assert "[email]" in clean
    assert "john.doe@acme.org" not in clean
    assert "[phone]" in clean
    assert "555" not in clean
    assert "[user]" in clean
    assert "@alex_promo" not in clean
    assert "[url]" in clean
    assert "https://tracker.com" not in clean
    assert "[ip]" in clean
    assert "192.168.1.50" not in clean
    assert counts["email"] >= 1
    assert counts["phone"] >= 1
    assert counts["url"] >= 1
    assert counts["user_handle"] >= 1
    assert counts["ip"] >= 1


def test_pii_sanitizer_preserves_emojis_punctuation_slang():
    sanitizer = PIISanitizer()
    text = "Bro this ad again 😂💀🔥!! Rizz level 100... let him cook fr fr??"
    clean, counts = sanitizer.sanitize(text)
    
    assert clean == text
    assert "😂" in clean
    assert "💀" in clean
    assert "🔥" in clean
    assert "!!" in clean
    assert "??" in clean
    assert all(v == 0 for v in counts.values())


# 2. Deduplication Tests
def test_deduplicator_exact_and_normalized():
    dedup = Deduplicator(jaccard_threshold=0.85)
    records = [
        {"comment_id": "c1", "text": "This ad is so cringe 💀", "source_record_id": "s1"},
        {"comment_id": "c2", "text": "This ad is so cringe 💀", "source_record_id": "s2"}, # Exact dup
        {"comment_id": "c3", "text": "THIS AD IS SO CRINGE 💀!!", "source_record_id": "s3"}, # Norm dup
        {"comment_id": "c4", "text": "Completely different product review", "source_record_id": "s4"},
    ]
    unique, report = dedup.process_records(records)
    assert len(unique) == 2
    assert report["summary"]["records_before"] == 4
    assert report["summary"]["exact_duplicates"] == 1
    assert report["summary"]["normalized_duplicates"] == 1
    assert report["summary"]["records_after"] == 2


def test_deduplicator_near_duplicate_jaccard():
    dedup = Deduplicator(jaccard_threshold=0.80)
    records = [
        {"comment_id": "c1", "text": "why do I see this ad every 5 minutes on my feed", "source_record_id": "s1"},
        {"comment_id": "c2", "text": "why do I see this ad every 5 minutes in my feed", "source_record_id": "s2"}, # High Jaccard
        {"comment_id": "c3", "text": "super fast delivery and great packaging love it", "source_record_id": "s3"},
    ]
    unique, report = dedup.process_records(records)
    assert len(unique) == 2
    assert report["summary"]["near_duplicates_removed"] == 1


# 3. Annotation Schema & Cohen's Kappa Tests
def test_annotation_record_schema_validation():
    valid = {
        "comment_id": "comm_01",
        "label": "fatigue",
        "annotator_id": "ann_01",
        "annotation_timestamp": "2026-09-30T12:00:00Z",
        "guideline_version": "v2.0",
        "confidence": 1.0,
        "notes": "Verified frequency complaint"
    }
    assert validate_annotation_record(valid) is True

    invalid_cat = dict(valid, label="unsupported_category")
    assert validate_annotation_record(invalid_cat) is False

    missing_id = dict(valid, comment_id="")
    assert validate_annotation_record(missing_id) is False


def test_cohens_kappa_perfect_agreement():
    ann_a = {"c1": "fatigue", "c2": "mockery", "c3": "spam", "c4": "positive"}
    ann_b = {"c1": "fatigue", "c2": "mockery", "c3": "spam", "c4": "positive"}
    res = compute_cohens_kappa(ann_a, ann_b, TAXONOMY_CATEGORIES)
    
    assert res["raw_agreement"] == 1.0
    assert res["cohens_kappa"] == 1.0
    assert res["disagreement_count"] == 0
    assert res["interpretation"] == "Almost Perfect Agreement"


def test_adjudication_resolution_workflow():
    records = [
        {"comment_id": "c1", "text": "c1 text"},
        {"comment_id": "c2", "text": "c2 text"}
    ]
    ann_a = {
        "c1": {"comment_id": "c1", "label": "fatigue"},
        "c2": {"comment_id": "c2", "label": "mockery"},
    }
    ann_b = {
        "c1": {"comment_id": "c1", "label": "fatigue"},
        "c2": {"comment_id": "c2", "label": "banter_meme"},
    }
    finalized, adjudications = resolve_and_adjudicate(
        records, ann_a, ann_b, adjudication_rules_applied={"c2": "banter_meme"}
    )
    assert len(finalized) == 2
    assert finalized[0]["category"] == "fatigue"
    assert finalized[0]["annotation_status"] == "auto_agreed"
    assert finalized[1]["category"] == "banter_meme"
    assert finalized[1]["annotation_status"] == "adjudicated"
    assert len(adjudications) == 1


# 4. 4-Way Split Zero Leakage Audit Test
def test_real_world_4way_split_zero_leakage():
    report = check_4way_split_leakage(near_dup_threshold=0.85)
    assert report["passed"] is True, f"Leakage detected in splits: {report}"
    assert report["total_exact_leaks"] == 0
    assert report["total_normalized_leaks"] == 0
    assert report["total_near_leaks"] == 0
    assert report["total_id_collisions"] == 0


# 5. CardiffNLP Auxiliary Signal Models Tests
def test_cardiffnlp_twitter_preprocessing():
    raw = "Hey @elonmusk check https://x.com/ad this is fire 🔥"
    prep = preprocess_for_twitter_roberta(raw)
    assert "@user" in prep
    assert "http" in prep
    assert "🔥" in prep


def test_cardiffnlp_signals_execution():
    signals = CardiffNLPSignals()
    text = "Bro this ad is pure comedy 😂🔥"
    res = signals.extract_auxiliary_signals(text)
    
    assert res["sentiment_en_label"] in ["positive", "neutral", "negative"]
    assert 0.0 <= res["sentiment_en_score"] <= 1.0
    assert res["irony_label"] in ["irony", "non_irony"]
    assert 0.0 <= res["irony_score"] <= 1.0
    assert res["sentiment_multilingual_label"] in ["positive", "neutral", "negative"]
    assert 0.0 <= res["sentiment_multilingual_score"] <= 1.0


# 6. Manifests & Split Alignment Tests
def test_dataset_manifests_exist_and_match_splits():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    splits = ["real_world_train", "real_world_val", "real_world_test", "real_world_ood", "multilingual_test"]
    
    for s in splits:
        split_path = os.path.join(base_dir, "data", "splits", f"{s}.jsonl")
        manifest_path = os.path.join(base_dir, "data", "manifests", f"{s}.json")
        
        assert os.path.exists(split_path), f"Split file missing: {split_path}"
        assert os.path.exists(manifest_path), f"Manifest file missing: {manifest_path}"
        
        with open(split_path, "r", encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        with open(manifest_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            
        assert len(lines) == meta["record_count"], f"Mismatch in {s}: lines={len(lines)}, meta={meta['record_count']}"
        assert meta["dataset_version"] == "real-world-v1.0"
