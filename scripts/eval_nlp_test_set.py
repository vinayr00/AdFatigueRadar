"""
Held-out Evaluation Script for AdFatigueRadar (Phase 6 / Audit Verification)
Runs full evaluation ONCE on the 320-sample held-out test split.
Outputs Accuracy, Macro-F1, per-class precision/recall/F1, confusion matrix, ECE,
and reports failure examples for the 3 weakest classes.
"""

import os
import sys
import json
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.nlp.classifier import CommentClassifier
from backend.nlp.constants import TAXONOMY_CATEGORIES
from backend.nlp.calibration import compute_expected_calibration_error


def evaluate_test_set():
    print("================================================================")
    print("   AdFatigueRadar — Phase 6: Final Held-Out Test Evaluation     ")
    print("================================================================")

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    test_path = os.path.join(base_dir, "data", "test_human_audited", "labels.jsonl")
    test_data = [json.loads(l) for l in open(test_path, encoding="utf-8")]
    print(f"Loaded {len(test_data)} test samples from {test_path} (40 per class)\n")

    classifier = CommentClassifier(use_cache=False)

    texts = [d["text"] for d in test_data]
    y_true = [d["category"] for d in test_data]

    # Run batch inference with cache bypassed
    results = classifier.classify_batch(texts, bypass_cache=True)
    y_pred = [r.category for r in results]
    confidences = [r.confidence for r in results]

    # Calculate overall metrics
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    acc = correct / len(y_true)
    accuracies = [1 if yt == yp else 0 for yt, yp in zip(y_true, y_pred)]
    ece = compute_expected_calibration_error(confidences, accuracies)

    # Per-class metrics
    per_class = {}
    for cat in TAXONOMY_CATEGORIES:
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
            "tp": tp,
            "fp": fp,
            "fn": fn
        }

    macro_f1 = sum(v["f1"] for v in per_class.values()) / len(TAXONOMY_CATEGORIES)

    print(f"Overall Test Accuracy : {acc:.4f} ({acc*100:.2f}%) [{correct}/{len(y_true)}]")
    print(f"Overall Macro-F1      : {macro_f1:.4f}")
    print(f"Expected Calib. Error : {ece:.4f}")

    print("\n--- PER-CLASS PERFORMANCE TABLE ---")
    print(f"{'Category':<20} | {'Support':<7} | {'Precision':<9} | {'Recall':<7} | {'F1-Score':<8}")
    print("-" * 62)
    for cat, metrics in per_class.items():
        print(f"{cat:<20} | {metrics['count']:<7} | {metrics['precision']:<9.4f} | {metrics['recall']:<7.4f} | {metrics['f1']:<8.4f}")

    print("\n--- CONFUSION MATRIX (Row=True, Column=Pred) ---")
    header = f"{'True \\ Pred':<20} " + " ".join([c[:4].rjust(6) for c in TAXONOMY_CATEGORIES])
    print(header)
    print("-" * len(header))
    for true_cat in TAXONOMY_CATEGORIES:
        row = [sum(1 for yt, yp in zip(y_true, y_pred) if yt == true_cat and yp == pred_cat) for pred_cat in TAXONOMY_CATEGORIES]
        print(f"{true_cat:<20} " + " ".join([str(val).rjust(6) for val in row]))

    # Weakest 3 classes
    sorted_classes = sorted(per_class.items(), key=lambda x: x[1]["f1"])
    print("\n--- 3 WEAKEST CLASSES ---")
    for rank, (cat_name, m) in enumerate(sorted_classes[:3], 1):
        print(f"{rank}. {cat_name} (F1: {m['f1']:.4f}, Recall: {m['recall']:.4f}, Prec: {m['precision']:.4f})")
        # Find failure examples
        fails = [
            (texts[i], y_true[i], y_pred[i], confidences[i])
            for i in range(len(texts))
            if y_true[i] == cat_name and y_pred[i] != cat_name
        ]
        if fails:
            print(f"   Failure examples ({len(fails)} total):")
            for text, true_lbl, pred_lbl, conf in fails[:3]:
                print(f"     - Text: {repr(text)}")
                print(f"       True: {true_lbl} | Predicted: {pred_lbl} | Confidence: {conf:.4f}")
        else:
            print("   (Zero failures on this class in test set)")

    # Specifically check banter_meme vs mockery
    banter_as_mockery = sum(1 for yt, yp in zip(y_true, y_pred) if yt == "banter_meme" and yp == "mockery")
    mockery_as_banter = sum(1 for yt, yp in zip(y_true, y_pred) if yt == "mockery" and yp == "banter_meme")
    print(f"\n--- BANTER_MEME vs MOCKERY DISCRIMINATION ---")
    print(f"Banter predicted as Mockery : {banter_as_mockery} / 40")
    print(f"Mockery predicted as Banter : {mockery_as_banter} / 40")

    # Specifically check the 3 required 'again' prompts
    print("\n--- REQUIRED 'AGAIN' PROMPT TESTS ---")
    again_prompts = [
        "Bro this ad again 😂",
        "Bought again, love it",
        "Ordered again, thank you!"
    ]
    for prompt in again_prompts:
        res = classifier.classify_text(prompt)
        print(f"Prompt: {repr(prompt)}")
        print(f"  -> Category: {res.category} | Confidence: {res.confidence:.4f} | Sentiment: {res.sentiment} | Critical: {res.critical_complaint}")

    print("================================================================\n")


if __name__ == "__main__":
    evaluate_test_set()
