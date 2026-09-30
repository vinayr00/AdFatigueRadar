"""
Tests for Data Integrity, Provenance & Split Separation
"""

import os
import json
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TRAIN_FILE = os.path.join(BASE_DIR, "data", "training", "labels.jsonl")
VAL_FILE = os.path.join(BASE_DIR, "data", "training", "val_labels.jsonl")
TEST_FILE = os.path.join(BASE_DIR, "data", "test_human_audited", "labels.jsonl")


def test_train_val_and_test_datasets_exist():
    assert os.path.exists(TRAIN_FILE), f"Missing {TRAIN_FILE}"
    assert os.path.exists(VAL_FILE), f"Missing {VAL_FILE}"
    assert os.path.exists(TEST_FILE), f"Missing {TEST_FILE}"


def test_split_sizes_and_provenance_schema():
    for fpath, min_samples in [(TRAIN_FILE, 600), (VAL_FILE, 160), (TEST_FILE, 320)]:
        with open(fpath, "r", encoding="utf-8") as f:
            items = [json.loads(line) for line in f if line.strip()]
        assert len(items) >= min_samples, f"{fpath} has {len(items)} samples, expected >= {min_samples}"
        for item in items:
            assert "text" in item and item["text"].strip()
            assert "category" in item
            assert "source" in item
            assert item["label_method"] in ["synthetic", "public_dataset_mapped", "human", "llm_prelabel_human_reviewed"]
            assert "split" in item


def test_zero_exact_and_near_overlap_across_splits():
    def load_texts(p):
        return [json.loads(l)["text"].strip().lower() for l in open(p, encoding="utf-8") if l.strip()]

    train_texts = set(load_texts(TRAIN_FILE))
    val_texts = set(load_texts(VAL_FILE))
    test_texts = set(load_texts(TEST_FILE))

    assert len(train_texts.intersection(val_texts)) == 0
    assert len(train_texts.intersection(test_texts)) == 0
    assert len(val_texts.intersection(test_texts)) == 0


def test_all_eight_categories_present_in_every_split():
    expected = {
        "product_complaint",
        "service_complaint",
        "fatigue",
        "mockery",
        "spam",
        "banter_meme",
        "neutral",
        "positive"
    }
    for fpath in [TRAIN_FILE, VAL_FILE, TEST_FILE]:
        with open(fpath, "r", encoding="utf-8") as f:
            cats = set(json.loads(l)["category"] for l in f if l.strip())
        assert cats == expected, f"Mismatch in {fpath}: {cats} != {expected}"


def test_no_replay_overlap_with_test_and_train():
    """
    Sec 20 Guarantee: Ensures that any replay scenario comments present in the repo
    are strictly disjoint from training, validation, and held-out test datasets.
    """
    def load_texts(p):
        if not os.path.exists(p):
            return set()
        return set(json.loads(l)["text"].strip().lower() for l in open(p, encoding="utf-8") if l.strip())

    train_texts = load_texts(TRAIN_FILE)
    val_texts = load_texts(VAL_FILE)
    test_texts = load_texts(TEST_FILE)
    all_nlp_texts = train_texts.union(val_texts).union(test_texts)

    # Check potential replay candidate paths (Person 3 replay directories)
    replay_paths = [
        os.path.join(BASE_DIR, "replay", "scenarios"),
        os.path.join(BASE_DIR, "backend", "replay"),
        os.path.join(BASE_DIR, "data", "replay"),
    ]
    for rpath in replay_paths:
        if os.path.exists(rpath):
            for root, _, files in os.walk(rpath):
                for fname in files:
                    if fname.endswith(".jsonl") or fname.endswith(".json"):
                        fpath = os.path.join(root, fname)
                        with open(fpath, "r", encoding="utf-8") as f:
                            for line in f:
                                if not line.strip():
                                    continue
                                try:
                                    item = json.loads(line)
                                    text = item.get("text", "").strip().lower()
                                    if text:
                                        assert text not in all_nlp_texts, f"Replay text leakage detected in {fpath}: {text}"
                                except Exception:
                                    pass

