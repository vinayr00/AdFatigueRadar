#!/usr/bin/env python3
"""
AdFatigueRadar — Real-World / Human-Authored Evaluation Script
=============================================================
PERSON 1: AI / NLP Layer

Evaluates the trained Stage 1 + Stage 2 NLP pipeline on real-world / hand-written
comment evaluation sets (e.g. data/test_human_audited/real_world_set.jsonl).
Outputs Accuracy, Macro-F1, per-class metrics, confusion matrix, and detailed error reports.

Usage:
    python scripts/eval_real_world.py [path_to_jsonl]
"""

import os
import sys
import json
import argparse
import numpy as np

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.nlp.classifier import CommentClassifier
from backend.nlp.constants import TAXONOMY_CATEGORIES


def eval_real_world(data_path: str):
    print("================================================================")
    print("    AdFatigueRadar — Real-World Evaluation Benchmark          ")
    print("================================================================")
    print(f"Dataset path: {data_path}")

    if not os.path.exists(data_path):
        print(f"\n[!] Dataset file not found at '{data_path}'.")
        print("Populate data/test_human_audited/real_world_set.jsonl with real-world comments to score.")
        print("================================================================\n")
        return

    records = [json.loads(l) for l in open(data_path, encoding="utf-8") if l.strip()]
    print(f"Total records loaded: {len(records)}\n")

    if not records:
        print("[NOTE] Target file is empty (0 samples).")
        print("Real-world evaluation is pending user-supplied hand-written comments.")
        print("================================================================\n")
        return

    classifier = CommentClassifier(use_cache=False)
    texts = [r["text"] for r in records]
    y_true = [r["category"] for r in records]

    results = classifier.classify_batch(texts, bypass_cache=True)
    y_pred = [res.category for res in results]
    confidences = [res.confidence for res in results]

    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    acc = correct / len(y_true)

    # Per-class metrics
    present_categories = sorted(list(set(y_true) | set(y_pred)))
    per_class = {}
    for cat in present_categories:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cat and yp == cat)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != cat and yp == cat)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cat and yp != cat)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        per_class[cat] = {
            "count": sum(1 for yt in y_true if yt == cat),
            "precision": prec,
            "recall": rec,
            "f1": f1,
        }

    macro_f1 = sum(v["f1"] for v in per_class.values()) / len(present_categories) if present_categories else 0.0

    print(f"Overall Accuracy : {acc:.4f} ({acc*100:.2f}%) [{correct}/{len(y_true)}]")
    print(f"Macro-F1         : {macro_f1:.4f}\n")

    print("--- PER-CLASS PERFORMANCE TABLE ---")
    print(f"{'Category':<22} | {'Count':<5} | {'Precision':<9} | {'Recall':<7} | {'F1-Score':<8}")
    print("-" * 62)
    for cat, m in per_class.items():
        print(f"{cat:<22} | {m['count']:<5} | {m['precision']:<9.4f} | {m['recall']:<7.4f} | {m['f1']:<8.4f}")

    print("\n--- CONFUSION MATRIX (Row=True, Column=Pred) ---")
    header = f"{'True \\ Pred':<22} " + " ".join([c[:4].rjust(6) for c in present_categories])
    print(header)
    print("-" * len(header))
    for true_cat in present_categories:
        row = [sum(1 for yt, yp in zip(y_true, y_pred) if yt == true_cat and yp == pred_cat) for pred_cat in present_categories]
        print(f"{true_cat:<22} " + " ".join([str(val).rjust(6) for val in row]))

    # List all errors
    errors = [
        (i, texts[i], y_true[i], y_pred[i], confidences[i])
        for i in range(len(records))
        if y_true[i] != y_pred[i]
    ]

    print(f"\n--- ERROR ANALYSIS ({len(errors)} errors found) ---")
    if errors:
        for idx, text, true_lbl, pred_lbl, conf in errors:
            print(f"Item #{idx+1}: {repr(text)}")
            print(f"  Ground Truth : {true_lbl}")
            print(f"  Predicted    : {pred_lbl}")
            print(f"  Confidence   : {conf:.4f}\n")
    else:
        print("Zero errors! Perfect classification on this dataset.\n")

    print("================================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate real-world comment sets.")
    default_path = os.path.join(BASE_DIR, "data", "test_human_audited", "real_world_set.jsonl")
    parser.add_argument("data_path", nargs="?", default=default_path, help="Path to evaluation JSONL")
    args = parser.parse_args()
    eval_real_world(args.data_path)
