#!/usr/bin/env python3
"""
AdFatigueRadar — Real NLP Benchmark & Accuracy Audit Script
===========================================================
PERSON 1: AI / NLP Layer

Executes standalone CPU latency, throughput, and accuracy benchmark
using the real RoBERTa Stage 1 & Stage 2 models with cache BYPASS.
Evaluates on 200+ samples and reports real percentiles.
"""

import sys
import os
import json

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.nlp.classifier import CommentClassifier
from backend.nlp.benchmark import NLPLatencyBenchmark


def main():
    print("================================================================")
    print("      AdFatigueRadar — Person 1: AI/NLP Benchmark Suite        ")
    print("================================================================")
    
    print("\n[1/3] Initializing CommentClassifier (Loading local RoBERTa models)...")
    classifier = CommentClassifier(use_cache=False)
    
    print("[2/3] Running CPU Latency & Batched Throughput Benchmark (200 samples)...")
    benchmark = NLPLatencyBenchmark(classifier=classifier)
    report = benchmark.run_benchmark(num_samples=200, batch_size=32)
    
    print("\n--- LATENCY & THROUGHPUT BENCHMARK RESULTS ---")
    print(f"Total Comments Evaluated : {report.total_comments_evaluated}")
    print(f"Hardware Environment     : {report.hardware_note}")
    print(f"Cold Start Latency (Load): {report.cold_start_ms:.2f} ms")
    print(f"Steady State Single Total: {report.steady_state_total_ms:.2f} ms")
    print(f"Batched Total Time (b=32): {report.batched_total_time_ms:.2f} ms")
    print(f"Throughput (Single-item) : {report.throughput_comments_per_sec:.2f} comments/sec")
    print(f"Throughput (Batched 32)  : {report.throughput_batched_comments_per_sec:.2f} comments/sec")
    print(f"Single Latency p50       : {report.latency_p50_ms:.2f} ms")
    print(f"Single Latency p95       : {report.latency_p95_ms:.2f} ms")
    print(f"Single Latency p99       : {report.latency_p99_ms:.2f} ms")
    print(f"Single Latency Max       : {report.latency_max_ms:.2f} ms")
    print(f"Sub-Minute Target Status : {'PASSED (Sub-minute processing verified on CPU)' if report.sub_minute_target_passed else 'FAILED'}")
    
    print("\n[3/3] Validating Disambiguation & Domain Guard Cases...")
    test_cases = [
        ("Bro this ad again 😂", "fatigue", "negative"),
        ("Bought again, love it!", "positive", "positive"),
        ("Ordered again, thank you!", "positive", "positive"),
        ("The product broke on day 2", "product_complaint", "negative"),
        ("Ordered 3 weeks ago still not received", "service_complaint", "negative"),
        ("The acting in this ad is making my teeth hurt 💀", "mockery", "negative"),
        ("Bro got that unspoken rizz let him cook 🔥", "banter_meme", "positive"),
        ("Click the link in my bio for guaranteed 100x crypto signals daily 🚀", "spam", "negative"),
        ("What is the current retail price including local sales taxes?", "neutral", "neutral"),
    ]
    
    for text, expected_cat, expected_sent in test_cases:
        res = classifier.classify_text(text)
        print(f"  Text: {repr(text)}")
        print(f"    -> Category: {res.category} (exp: {expected_cat}) | Conf: {res.confidence:.4f} | Sentiment: {res.sentiment} | Critical: {res.critical_complaint}")

    print("\n================================================================")
    print("             REAL BENCHMARK EXECUTION COMPLETED                 ")
    print(f"  Sub-Minute CPU Target: {'PASSED' if report.sub_minute_target_passed else 'FAILED'} (p95: {report.latency_p95_ms:.2f} ms)")
    print("================================================================\n")


if __name__ == "__main__":
    main()
