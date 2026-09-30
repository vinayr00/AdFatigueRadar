"""
Dataset Construction and Validation Script for AdFatigueRadar
Generates high-diversity, realistic training, validation, and test datasets.
Enforces strict provenance, schema, zero overlap, and near-duplicate checks.
"""

import os
import sys
import json
import difflib
import random
from typing import List, Dict, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Categories in frozen taxonomy
CATEGORIES = [
    "product_complaint",
    "service_complaint",
    "fatigue",
    "mockery",
    "spam",
    "banter_meme",
    "neutral",
    "positive",
]

def jaccard_similarity(s1: str, s2: str) -> float:
    t1 = set(s1.lower().split())
    t2 = set(s2.lower().split())
    if not t1 or not t2:
        return 0.0
    return len(t1.intersection(t2)) / len(t1.union(t2))

def verify_and_save_splits(
    train_data: List[Dict],
    val_data: List[Dict],
    test_data: List[Dict],
    train_path: str,
    val_path: str,
    test_path: str,
    audit_sample_path: str,
):
    all_splits = {"train": train_data, "val": val_data, "test": test_data}
    split_texts = {"train": [], "val": [], "test": []}

    print("=== VALIDATING SPLITS ===")
    for split_name, items in all_splits.items():
        print(f"\nSplit: {split_name} (Total: {len(items)})")
        counts = {cat: 0 for cat in CATEGORIES}
        methods = {}
        for item in items:
            assert "text" in item and item["text"].strip(), f"Empty text in {split_name}"
            assert item["category"] in CATEGORIES, f"Invalid category {item['category']}"
            assert item["split"] == split_name, f"Split mismatch in {split_name}: {item['split']}"
            assert "source" in item, "Missing source"
            assert item["label_method"] in ["synthetic", "public_dataset_mapped", "human", "llm_prelabel_human_reviewed"], f"Invalid label_method: {item['label_method']}"
            
            counts[item["category"]] += 1
            methods[item["label_method"]] = methods.get(item["label_method"], 0) + 1
            split_texts[split_name].append(item["text"].strip().lower())
            
        for cat, c in counts.items():
            print(f"  - {cat:20}: {c}")
        print(f"  Provenance methods: {methods}")

    # Check Exact and Near Overlaps
    print("\n=== CHECKING OVERLAPS & NEAR-DUPLICATES ===")
    exact_duplicates = 0
    near_duplicates = 0
    split_names = ["train", "val", "test"]

    for i in range(len(split_names)):
        for j in range(i + 1, len(split_names)):
            s1, s2 = split_names[i], split_names[j]
            set1 = set(split_texts[s1])
            set2 = set(split_texts[s2])
            overlap = set1.intersection(set2)
            if overlap:
                print(f"EXACT OVERLAP ERROR between {s1} and {s2}: {len(overlap)} items!")
                for item in list(overlap)[:5]:
                    print(f"  - Overlap item: {item}")
                exact_duplicates += len(overlap)
            else:
                print(f"Exact overlap between {s1} and {s2}: 0 (PASSED)")

            # Check near-duplicates (Jaccard >= 0.90)
            for t1 in split_texts[s1]:
                for t2 in split_texts[s2]:
                    if jaccard_similarity(t1, t2) >= 0.90:
                        print(f"NEAR DUPLICATE between {s1} and {s2}:\n  1: {t1}\n  2: {t2}")
                        near_duplicates += 1

    print(f"Total Exact Duplicates across splits: {exact_duplicates}")
    print(f"Total Near Duplicates (Jaccard >= 0.90): {near_duplicates}")
    assert exact_duplicates == 0, f"Found {exact_duplicates} exact duplicates across splits!"
    assert near_duplicates == 0, f"Found {near_duplicates} near duplicates across splits!"

    # Save files
    os.makedirs(os.path.dirname(train_path), exist_ok=True)
    os.makedirs(os.path.dirname(test_path), exist_ok=True)

    with open(train_path, "w", encoding="utf-8") as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with open(val_path, "w", encoding="utf-8") as f:
        for item in val_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with open(test_path, "w", encoding="utf-8") as f:
        for item in test_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # Generate 50-item sample audit file from test set for human auditing
    random.seed(42)
    sample_audit = random.sample(test_data, min(50, len(test_data)))
    with open(audit_sample_path, "w", encoding="utf-8") as f:
        for item in sample_audit:
            audit_record = {
                "text": item["text"],
                "assigned_category": item["category"],
                "assigned_label_method": item["label_method"],
                "human_auditor_verified": None,
                "human_agreed_category": None,
                "notes": ""
            }
            f.write(json.dumps(audit_record, ensure_ascii=False) + "\n")

    print(f"\nSuccessfully wrote:\n- Train: {train_path}\n- Val: {val_path}\n- Test: {test_path}\n- Human Audit Sample: {audit_sample_path}")
