#!/usr/bin/env python3
"""
AdFatigueRadar — NLP Replay Data Leakage & Provenance Checker
============================================================
PERSON 1: AI / NLP Layer

Utility script for Person 1, Person 2, and Person 3 to verify that
candidate replay comment files / scenario streams have ZERO exact or
near-duplicate overlap with training, validation, and held-out test splits.

Usage:
    python -m backend.nlp.leakage_checker <path_to_replay_file_or_dir>
"""

import sys
import os
import json
import argparse
from typing import Set, List, Dict, Tuple, Any

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TRAIN_FILE = os.path.join(BASE_DIR, "data", "training", "labels.jsonl")
VAL_FILE = os.path.join(BASE_DIR, "data", "training", "val_labels.jsonl")
TEST_FILE = os.path.join(BASE_DIR, "data", "test_human_audited", "labels.jsonl")
STRESS_FILE = os.path.join(BASE_DIR, "data", "test_human_audited", "stress_set.jsonl")


def tokenize(text: str) -> Set[str]:
    """Simple whitespace + lowercase tokenization for Jaccard similarity."""
    return set(text.lower().strip().split())


def jaccard_similarity(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    """Computes Jaccard token overlap between two token sets."""
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a.intersection(tokens_b))
    union = len(tokens_a.union(tokens_b))
    return intersection / union if union > 0 else 0.0


def load_dataset_texts(fpath: str) -> List[Tuple[str, str]]:
    """Loads (text, source_file) pairs from a JSONL file."""
    if not os.path.exists(fpath):
        return []
    records = []
    fname = os.path.basename(fpath)
    with open(fpath, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                text = str(data.get("text", "") or "").strip()
                if text:
                    records.append((text, f"{fname}:line{idx}"))
            except json.JSONDecodeError:
                pass
    return records


def extract_replay_texts(target_path: str) -> List[Tuple[str, str]]:
    """Recursively finds and extracts comment texts from replay JSON/JSONL files."""
    texts: List[Tuple[str, str]] = []
    if os.path.isfile(target_path):
        candidates = [target_path]
    elif os.path.isdir(target_path):
        candidates = []
        for root, _, files in os.walk(target_path):
            for fname in files:
                if fname.endswith(".jsonl") or fname.endswith(".json"):
                    candidates.append(os.path.join(root, fname))
    else:
        print(f"Error: Path '{target_path}' does not exist.")
        return []

    for cpath in candidates:
        rel_path = os.path.relpath(cpath, BASE_DIR)
        with open(cpath, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    # Handle CommentEvent, NLPResult, or raw dict
                    text = str(obj.get("text") or obj.get("comment_text") or "").strip()
                    if text:
                        texts.append((text, f"{rel_path}:line{idx}"))
                except json.JSONDecodeError:
                    pass
    return texts


def check_replay_leakage(
    replay_path: str,
    near_dup_threshold: float = 0.85
) -> Dict[str, Any]:
    """
    Checks replay data against all NLP splits for exact & near duplicates.
    """
    # 1. Load all NLP reference datasets
    nlp_corpora: List[Tuple[str, str]] = []
    nlp_corpora.extend(load_dataset_texts(TRAIN_FILE))
    nlp_corpora.extend(load_dataset_texts(VAL_FILE))
    nlp_corpora.extend(load_dataset_texts(TEST_FILE))
    nlp_corpora.extend(load_dataset_texts(STRESS_FILE))

    print(f"Loaded {len(nlp_corpora)} reference NLP training/test samples across splits.")

    # Build reference lookup sets
    exact_nlp_lookup: Dict[str, str] = {t.lower(): loc for t, loc in nlp_corpora}
    tokenized_nlp: List[Tuple[str, Set[str], str]] = [(t, tokenize(t), loc) for t, loc in nlp_corpora]

    # 2. Extract replay texts
    replay_texts = extract_replay_texts(replay_path)
    print(f"Extracted {len(replay_texts)} candidate replay comment events from '{replay_path}'.")

    if not replay_texts:
        return {
            "status": "EMPTY",
            "total_replay_comments": 0,
            "exact_leaks": [],
            "near_leaks": [],
            "passed": True
        }

    exact_leaks = []
    near_leaks = []

    # 3. Check for overlap
    for rep_text, rep_loc in replay_texts:
        rep_clean = rep_text.lower()
        rep_tokens = tokenize(rep_text)

        # Exact check
        if rep_clean in exact_nlp_lookup:
            exact_leaks.append({
                "replay_location": rep_loc,
                "replay_text": rep_text,
                "nlp_location": exact_nlp_lookup[rep_clean],
                "reason": "EXACT_MATCH"
            })
            continue

        # Near-duplicate Jaccard check
        for nlp_text, nlp_tokens, nlp_loc in tokenized_nlp:
            score = jaccard_similarity(rep_tokens, nlp_tokens)
            if score >= near_dup_threshold:
                near_leaks.append({
                    "replay_location": rep_loc,
                    "replay_text": rep_text,
                    "nlp_location": nlp_loc,
                    "nlp_text": nlp_text,
                    "similarity": round(score, 4),
                    "reason": "NEAR_DUPLICATE"
                })
                break

    passed = (len(exact_leaks) == 0 and len(near_leaks) == 0)

    return {
        "status": "PASSED" if passed else "FAILED_LEAKAGE_DETECTED",
        "total_replay_comments": len(replay_texts),
        "total_reference_samples": len(nlp_corpora),
        "exact_leaks_count": len(exact_leaks),
        "near_leaks_count": len(near_leaks),
        "exact_leaks": exact_leaks,
        "near_leaks": near_leaks,
        "passed": passed
    }


def main():
    parser = argparse.ArgumentParser(description="Check replay comments for leakage against NLP training/test data.")
    parser.add_argument("target_path", nargs="?", default=os.path.join(BASE_DIR, "replay"),
                        help="Path to replay file or directory (default: ./replay)")
    parser.add_argument("--threshold", type=float, default=0.85, help="Jaccard similarity threshold for near-duplicates (default: 0.85)")
    args = parser.parse_args()

    print("================================================================")
    print("      AdFatigueRadar — NLP Replay Data Leakage Checker         ")
    print("================================================================")

    if not os.path.exists(args.target_path):
        print(f"\n[NOTE] Target replay path '{args.target_path}' does not exist yet.")
        print("When Person 3 generates replay comments, point this tool to their output directory.")
        print("================================================================\n")
        sys.exit(0)

    report = check_replay_leakage(args.target_path, near_dup_threshold=args.threshold)

    print("\n--- LEAKAGE AUDIT RESULTS ---")
    print(f"Status               : {report['status']}")
    print(f"Replay Comments Read : {report['total_replay_comments']}")
    print(f"Exact Matches        : {report['exact_leaks_count']}")
    print(f"Near Duplicates      : {report['near_leaks_count']}")

    if not report["passed"]:
        print("\n[!] LEAKAGE FOUND:")
        for leak in report["exact_leaks"][:5]:
            print(f"  - EXACT: {leak['replay_location']} matched {leak['nlp_location']}")
            print(f"    Text: {repr(leak['replay_text'])}")
        for leak in report["near_leaks"][:5]:
            print(f"  - NEAR ({leak['similarity']*100:.1f}%): {leak['replay_location']} matched {leak['nlp_location']}")
            print(f"    Replay: {repr(leak['replay_text'])}")
            print(f"    NLP   : {repr(leak['nlp_text'])}")
        print("\n================================================================\n")
        sys.exit(1)
    else:
        print("\n[OK] Zero leakage detected. Replay dataset is 100% disjoint from NLP training & test sets.")
        print("================================================================\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
