"""
Tests for Data Integrity, Provenance & Train/Test Separation
"""

import os
import json
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TRAIN_FILE = os.path.join(BASE_DIR, "data", "training", "labels.jsonl")
TEST_FILE = os.path.join(BASE_DIR, "data", "test_human_audited", "labels.jsonl")


def test_train_and_test_datasets_exist():
    assert os.path.exists(TRAIN_FILE), f"Missing {TRAIN_FILE}"
    assert os.path.exists(TEST_FILE), f"Missing {TEST_FILE}"


def test_zero_train_test_text_overlap():
    train_texts = set()
    with open(TRAIN_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                train_texts.add(item["text"].strip().lower())

    test_texts = set()
    with open(TEST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                test_texts.add(item["text"].strip().lower())

    overlap = train_texts.intersection(test_texts)
    assert len(overlap) == 0, f"Found {len(overlap)} overlapping samples between train and test: {overlap}"


def test_test_dataset_has_300_plus_samples():
    count = 0
    with open(TEST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    assert count >= 300, f"Held-out test set requires at least 300 audited samples, found {count}"


def test_all_eight_taxonomy_categories_present_in_test_set():
    categories_found = set()
    with open(TEST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                categories_found.add(item["category"])

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
    assert categories_found == expected
