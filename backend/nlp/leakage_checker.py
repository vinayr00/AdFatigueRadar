#!/usr/bin/env python3
"""
AdFatigueRadar — NLP Replay & 4-Way Split Data Leakage & Provenance Checker
=========================================================================
PERSON 1: AI / NLP Layer (Phase 1 Remediation)

Utility to verify that:
1. Replay scenario comment streams have ZERO overlap with train, val, test, and stress sets.
2. Real-world 4-way splits (TRAIN, VAL, TEST, OOD) have ZERO pairwise leakage:
   - Exact text match = 0
   - Normalized text match = 0
   - Near-duplicate (Token Jaccard >= 0.85) = 0
   - Source record ID collision = 0

Usage:
    python -m backend.nlp.leakage_checker <path_to_replay_file_or_dir>
    python -m backend.nlp.leakage_checker --splits
"""

import sys
import os
import json
import argparse
import unicodedata
import re
from typing import Set, List, Dict, Tuple, Any, Optional

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TRAIN_FILE = os.path.join(BASE_DIR, "data", "training", "labels.jsonl")
VAL_FILE = os.path.join(BASE_DIR, "data", "training", "val_labels.jsonl")
TEST_FILE = os.path.join(BASE_DIR, "data", "test_human_audited", "labels.jsonl")
STRESS_FILE = os.path.join(BASE_DIR, "data", "test_human_audited", "stress_set.jsonl")

# Real-world splits
RW_TRAIN_FILE = os.path.join(BASE_DIR, "data", "splits", "real_world_train.jsonl")
RW_VAL_FILE = os.path.join(BASE_DIR, "data", "splits", "real_world_val.jsonl")
RW_TEST_FILE = os.path.join(BASE_DIR, "data", "splits", "real_world_test.jsonl")
RW_OOD_FILE = os.path.join(BASE_DIR, "data", "splits", "real_world_ood.jsonl")


def normalize_text_dedup(text: str) -> str:
    """Unicode NFKC normalization, lowercase, punctuation removed for leakage checking."""
    if not text:
        return ""
    norm = unicodedata.normalize("NFKC", text).lower()
    norm = re.sub(r"[^\w\s]", "", norm)
    return re.sub(r"\s+", " ", norm).strip()


def tokenize(text: str) -> Set[str]:
    """Token set for Jaccard similarity."""
    norm = normalize_text_dedup(text)
    return set(norm.split()) if norm else set()


def jaccard_similarity(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    """Computes Jaccard token overlap between two token sets."""
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a.intersection(tokens_b))
    union = len(tokens_a.union(tokens_b))
    return intersection / union if union > 0 else 0.0


def load_dataset_records(fpath: str) -> List[Dict[str, Any]]:
    """Loads records from a JSONL file."""
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
                data["_location"] = f"{fname}:line{idx}"
                records.append(data)
            except json.JSONDecodeError:
                pass
    return records


def load_dataset_texts(fpath: str) -> List[Tuple[str, str]]:
    """Loads (text, source_file) pairs from a JSONL file."""
    records = load_dataset_records(fpath)
    return [(str(r.get("text", "")).strip(), r["_location"]) for r in records if r.get("text")]


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
    Checks replay data against all reference NLP splits for exact & near duplicates.
    """
    nlp_corpora: List[Tuple[str, str]] = []
    nlp_corpora.extend(load_dataset_texts(TRAIN_FILE))
    nlp_corpora.extend(load_dataset_texts(VAL_FILE))
    nlp_corpora.extend(load_dataset_texts(TEST_FILE))
    nlp_corpora.extend(load_dataset_texts(STRESS_FILE))

    exact_nlp_lookup: Dict[str, str] = {t.lower(): loc for t, loc in nlp_corpora}
    tokenized_nlp: List[Tuple[str, Set[str], str]] = [(t, tokenize(t), loc) for t, loc in nlp_corpora]

    replay_texts = extract_replay_texts(replay_path)
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

    for rep_text, rep_loc in replay_texts:
        rep_clean = rep_text.lower()
        rep_tokens = tokenize(rep_text)

        if rep_clean in exact_nlp_lookup:
            exact_leaks.append({
                "replay_location": rep_loc,
                "replay_text": rep_text,
                "nlp_location": exact_nlp_lookup[rep_clean],
                "reason": "EXACT_MATCH"
            })
            continue

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


def check_4way_split_leakage(
    train_file: str = RW_TRAIN_FILE,
    val_file: str = RW_VAL_FILE,
    test_file: str = RW_TEST_FILE,
    ood_file: str = RW_OOD_FILE,
    near_dup_threshold: float = 0.85
) -> Dict[str, Any]:
    """
    Rigorously validates 4-way split independence across:
    TRAIN vs VAL, TRAIN vs TEST, TRAIN vs OOD,
    VAL vs TEST, VAL vs OOD, TEST vs OOD.
    """
    splits = {
        "TRAIN": load_dataset_records(train_file),
        "VAL": load_dataset_records(val_file),
        "TEST": load_dataset_records(test_file),
        "OOD": load_dataset_records(ood_file),
    }

    pairs = [
        ("TRAIN", "VAL"),
        ("TRAIN", "TEST"),
        ("TRAIN", "OOD"),
        ("VAL", "TEST"),
        ("VAL", "OOD"),
        ("TEST", "OOD"),
    ]

    pairwise_results = {}
    total_exact_leaks = 0
    total_norm_leaks = 0
    total_near_leaks = 0
    total_id_collisions = 0

    for name_a, name_b in pairs:
        recs_a = splits[name_a]
        recs_b = splits[name_b]

        pair_key = f"{name_a}_vs_{name_b}"
        exact_leaks = []
        norm_leaks = []
        near_leaks = []
        id_leaks = []

        seen_exact = {r.get("text", ""): r["_location"] for r in recs_a if r.get("text")}
        seen_norm = {normalize_text_dedup(r.get("text", "")): r["_location"] for r in recs_a if r.get("text")}
        seen_ids = {r.get("source_record_id") or r.get("comment_id"): r["_location"] for r in recs_a if r.get("comment_id")}

        tokenized_a = [(r.get("text", ""), tokenize(r.get("text", "")), r["_location"]) for r in recs_a if r.get("text")]

        for rb in recs_b:
            txt = rb.get("text", "")
            norm = normalize_text_dedup(txt)
            cid = rb.get("source_record_id") or rb.get("comment_id")
            tokens_b = tokenize(txt)

            # ID check
            if cid and cid in seen_ids:
                id_leaks.append({"id": cid, "loc_a": seen_ids[cid], "loc_b": rb["_location"]})

            # Exact text
            if txt in seen_exact:
                exact_leaks.append({"text": txt, "loc_a": seen_exact[txt], "loc_b": rb["_location"]})
                continue

            # Normalized text
            if norm in seen_norm:
                norm_leaks.append({"norm_text": norm, "loc_a": seen_norm[norm], "loc_b": rb["_location"]})
                continue

            # Near duplicate Jaccard
            for txt_a, tokens_a, loc_a in tokenized_a:
                sim = jaccard_similarity(tokens_a, tokens_b)
                if sim >= near_dup_threshold:
                    near_leaks.append({
                        "similarity": round(sim, 4),
                        "text_a": txt_a,
                        "loc_a": loc_a,
                        "text_b": txt,
                        "loc_b": rb["_location"]
                    })
                    break

        total_exact_leaks += len(exact_leaks)
        total_norm_leaks += len(norm_leaks)
        total_near_leaks += len(near_leaks)
        total_id_collisions += len(id_leaks)

        pairwise_results[pair_key] = {
            "exact_leaks_count": len(exact_leaks),
            "normalized_leaks_count": len(norm_leaks),
            "near_leaks_count": len(near_leaks),
            "id_collisions_count": len(id_leaks),
            "passed": (len(exact_leaks) == 0 and len(norm_leaks) == 0 and len(near_leaks) == 0 and len(id_leaks) == 0)
        }

    all_passed = (total_exact_leaks == 0 and total_norm_leaks == 0 and total_near_leaks == 0 and total_id_collisions == 0)

    return {
        "status": "PASSED" if all_passed else "FAILED_LEAKAGE_DETECTED",
        "passed": all_passed,
        "split_counts": {k: len(v) for k, v in splits.items()},
        "total_exact_leaks": total_exact_leaks,
        "total_normalized_leaks": total_norm_leaks,
        "total_near_leaks": total_near_leaks,
        "total_id_collisions": total_id_collisions,
        "pairwise_details": pairwise_results,
    }


def main():
    parser = argparse.ArgumentParser(description="Check NLP splits & replay comments for data leakage.")
    parser.add_argument("target_path", nargs="?", default=None, help="Path to replay file or directory")
    parser.add_argument("--splits", action="store_true", help="Run 4-way split independence leakage check (Train, Val, Test, OOD)")
    parser.add_argument("--threshold", type=float, default=0.85, help="Jaccard similarity threshold (default: 0.85)")
    args = parser.parse_args()

    print("================================================================")
    print("      AdFatigueRadar — Comprehensive Data Leakage Auditor      ")
    print("================================================================")

    if args.splits or not args.target_path:
        print("\n--- AUDITING 4-WAY SPLITS (TRAIN vs VAL vs TEST vs OOD) ---")
        split_report = check_4way_split_leakage(near_dup_threshold=args.threshold)
        print(f"Status: {split_report['status']}")
        for pair, res in split_report["pairwise_details"].items():
            status_str = "PASSED" if res["passed"] else "FAILED"
            print(f"  - {pair:18}: {status_str} (Exact: {res['exact_leaks_count']}, Norm: {res['normalized_leaks_count']}, Near: {res['near_leaks_count']}, IDs: {res['id_collisions_count']})")
        
        if not split_report["passed"]:
            print("\n[!] LEAKAGE DETECTED IN 4-WAY SPLITS!")
            sys.exit(1)
        else:
            print("\n[OK] Zero leakage across all 4 splits. Complete data isolation confirmed.")

    if args.target_path:
        print(f"\n--- AUDITING REPLAY STREAM: {args.target_path} ---")
        replay_report = check_replay_leakage(args.target_path, near_dup_threshold=args.threshold)
        print(f"Status: {replay_report['status']}")
        print(f"Exact Matches: {replay_report['exact_leaks_count']}, Near Duplicates: {replay_report['near_leaks_count']}")
        if not replay_report["passed"]:
            sys.exit(1)


if __name__ == "__main__":
    main()
