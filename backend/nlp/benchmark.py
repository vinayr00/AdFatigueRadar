"""
AdFatigueRadar — NLP Latency & Throughput Benchmark Suite
=========================================================
PERSON 1: AI / NLP Layer

Profiles end-to-end CPU latency, batched throughput, and cold-start overhead.
Enforces sub-minute classification latency verification.

NOTE: All live latency benchmarks explicitly BYPASS the replay cache.
"""

import time
import statistics
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from . import CommentEvent, NLPResult
from .classifier import CommentClassifier


@dataclass
class LatencyBenchmarkReport:
    """Benchmark performance report."""
    total_comments_evaluated: int
    batch_size: int
    cold_start_ms: float
    steady_state_total_ms: float
    throughput_comments_per_sec: float
    throughput_batched_comments_per_sec: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    latency_max_ms: float
    batched_total_time_ms: float
    sub_minute_target_passed: bool
    hardware_note: str = "Local CPU Execution"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NLPLatencyBenchmark:
    """
    Executes rigorous latency profiling on cold and steady-state inference.
    """
    def __init__(self, classifier: Optional[CommentClassifier] = None):
        self.classifier = classifier or CommentClassifier(use_cache=False)

    def run_benchmark(
        self,
        test_texts: Optional[List[str]] = None,
        num_samples: int = 200,
        batch_size: int = 32
    ) -> LatencyBenchmarkReport:
        """
        Runs comprehensive latency benchmark over >= 200 comments.
        Bypasses replay cache to measure actual live CPU computation time.
        """
        sample_pool = test_texts or [
            "Bro this ad again 😂 I see it on my feed every 5 minutes",
            "Bought again, absolute best quality item, highly recommend!",
            "Ordered 3 weeks ago and still haven't received it! Terrible customer support.",
            "The product broke on day 2, complete waste of money",
            "The acting in this commercial is making my teeth hurt from cringe 💀",
            "Click the link in my bio for guaranteed 100x crypto signals daily 🚀",
            "Bro got that unspoken rizz let him cook 🔥",
            "What is the current retail price including local sales taxes?",
            "Stop showing me this ad, I am so tired of seeing it",
            "Awesome product, arrived super fast and works great ❤️",
            "Tracking status has been stuck at label created for eighteen days",
            "Motor started making a loud grinding sound and then shut down completely",
            "Nah he cookin let him cook fr fr 👨‍🍳",
            "Is there an iOS application available on the Apple App Store?",
            "Join t.me/free_crypto for 10x gains link in bio",
            "The voiceover sounds like an AI robot that gave up on life",
        ]

        # Generate evaluation dataset
        comments = []
        for i in range(num_samples):
            text = sample_pool[i % len(sample_pool)]
            comments.append(CommentEvent(
                event_id=f"bench_comment_{i:04d}",
                timestamp="2026-09-30T12:00:00Z",
                campaign_id="bench_camp",
                ad_id="bench_ad",
                author_id=f"author_{i % 20}",
                text=text,
            ))

        # 1. Cold start measurement (first single inference, model warm-up)
        t_cold_start = time.perf_counter()
        _ = self.classifier.classify(comments[0], bypass_cache=True)
        t_cold_end = time.perf_counter()
        cold_start_ms = (t_cold_end - t_cold_start) * 1000.0

        # 2. Per-comment latency measurements across steady-state
        individual_latencies_ms = []
        t_steady_start = time.perf_counter()

        for comment in comments[1:]:
            t0 = time.perf_counter()
            _ = self.classifier.classify(comment, bypass_cache=True)
            t1 = time.perf_counter()
            individual_latencies_ms.append((t1 - t0) * 1000.0)

        t_steady_end = time.perf_counter()
        steady_state_total_ms = (t_steady_end - t_steady_start) * 1000.0

        # 3. Batched throughput measurement
        t_batch_start = time.perf_counter()
        for i in range(0, len(comments), batch_size):
            chunk = comments[i : i + batch_size]
            _ = self.classifier.classify_batch(chunk, bypass_cache=True)
        t_batch_end = time.perf_counter()
        batched_total_ms = (t_batch_end - t_batch_start) * 1000.0

        # 4. Compute Percentiles
        sorted_latencies = sorted(individual_latencies_ms)
        n = len(sorted_latencies)
        p50 = statistics.median(sorted_latencies) if n > 0 else 0.0
        p95 = sorted_latencies[int(0.95 * n)] if n > 0 else 0.0
        p99 = sorted_latencies[int(0.99 * n)] if n > 0 else 0.0
        max_lat = max(sorted_latencies) if n > 0 else 0.0
        
        total_single_time_sec = (steady_state_total_ms / 1000.0)
        throughput_single = (len(comments) - 1) / total_single_time_sec if total_single_time_sec > 0 else 0.0
        
        total_batched_time_sec = (batched_total_ms / 1000.0)
        throughput_batched = len(comments) / total_batched_time_sec if total_batched_time_sec > 0 else 0.0

        # Sub-minute check (total processing time for 200 items must be < 60,000 ms)
        passed = (steady_state_total_ms < 60000.0) and (batched_total_ms < 60000.0)

        return LatencyBenchmarkReport(
            total_comments_evaluated=num_samples,
            batch_size=batch_size,
            cold_start_ms=round(cold_start_ms, 2),
            steady_state_total_ms=round(steady_state_total_ms, 2),
            throughput_comments_per_sec=round(throughput_single, 2),
            throughput_batched_comments_per_sec=round(throughput_batched, 2),
            latency_p50_ms=round(p50, 2),
            latency_p95_ms=round(p95, 2),
            latency_p99_ms=round(p99, 2),
            latency_max_ms=round(max_lat, 2),
            batched_total_time_ms=round(batched_total_ms, 2),
            sub_minute_target_passed=passed,
            hardware_note="Local CPU Execution (PyTorch + RoBERTa)",
        )
