#!/usr/bin/env python3
"""
AdFatigueRadar — NLP Benchmark Script
=====================================
PERSON 1: AI / NLP Layer

Executes standalone latency, throughput, and accuracy benchmark.
Can be executed directly via: `python scripts/benchmark_nlp.py`
"""

import sys
import os
import json

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.nlp.classifier import CommentClassifier
from backend.nlp.benchmark import NLPLatencyBenchmark
from backend.nlp.baselines import SentimentOnlyBaseline


def main():
    print("================================================================")
    print("      AdFatigueRadar — Person 1: AI/NLP Benchmark Suite        ")
    print("================================================================")
    
    print("\n[1/3] Initializing CommentClassifier (bypassing cache for live run)...")
    classifier = CommentClassifier(use_cache=False)
    
    print("[2/3] Running Latency & Throughput Benchmark (100 samples)...")
    benchmark = NLPLatencyBenchmark(classifier=classifier)
    report = benchmark.run_benchmark(num_samples=100)
    
    print("\n--- BENCHMARK RESULTS ---")
    print(f"Total Comments Evaluated : {report.total_comments_evaluated}")
    print(f"Cold Start Latency       : {report.cold_start_ms:.2f} ms")
    print(f"Steady State Total Time  : {report.steady_state_total_ms:.2f} ms")
    print(f"Throughput               : {report.throughput_comments_per_sec:.2f} comments/sec")
    print(f"Latency p50 (Median)     : {report.latency_p50_ms:.2f} ms")
    print(f"Latency p95              : {report.latency_p95_ms:.2f} ms")
    print(f"Latency p99              : {report.latency_p99_ms:.2f} ms")
    print(f"Latency Max              : {report.latency_max_ms:.2f} ms")
    print(f"Sub-Minute Target Status : {'PASSED (Sub-millisecond / Sub-minute latency verified)' if report.sub_minute_target_passed else 'FAILED'}")
    
    print("\n[3/3] Validating Disambiguation & Taxonomy Guard Rules...")
    test_cases = [
        ("Bro this ad again 😂", "fatigue", "negative"),
        ("Bought again, love it!", "positive", "positive"),
        ("Ordered again, thank you!", "positive", "positive"),
        ("The product broke on day 2", "product_complaint", "negative"),
        ("Ordered 3 weeks ago still not received", "service_complaint", "negative"),
        ("The acting in this ad is killing me 💀", "mockery", "negative"),
        ("Bro got that unspoken rizz let him cook", "banter_meme", "positive"),
        ("Click link in bio for free crypto telegram", "spam", "negative"),
        ("What sizes are available in stock?", "neutral", "neutral"),
    ]
    
    all_passed = True
    for text, expected_cat, expected_sent in test_cases:
        res = classifier.classify_text(text)
        cat_match = res.category == expected_cat
        sent_match = res.sentiment == expected_sent
        status = "PASS" if (cat_match and sent_match) else "FAIL"
        if not (cat_match and sent_match):
            all_passed = False
        print(f"  [{status}] Text: \"{text}\"")
        print(f"      -> Category: {res.category} (expected: {expected_cat}) | Sentiment: {res.sentiment} | Conf: {res.confidence:.2f} | Critical: {res.critical_complaint}")

    print("\n================================================================")
    if all_passed and report.sub_minute_target_passed:
        print("  ALL PERSON 1 NLP BENCHMARKS AND CONTRACT CHECKS PASSED!  ")
    else:
        print("  SOME CHECKS REQUIRE ATTENTION (Review details above)     ")
    print("================================================================\n")


if __name__ == "__main__":
    main()
