"""
Tests for NLP Latency & Throughput Benchmark Suite
"""

import pytest
from backend.nlp.benchmark import NLPLatencyBenchmark, LatencyBenchmarkReport


def test_latency_benchmark_execution():
    benchmark = NLPLatencyBenchmark()
    report = benchmark.run_benchmark(num_samples=25, batch_size=8)

    assert isinstance(report, LatencyBenchmarkReport)
    assert report.total_comments_evaluated == 25
    assert report.cold_start_ms >= 0.0
    assert report.steady_state_total_ms >= 0.0
    assert report.latency_p50_ms >= 0.0
    assert report.latency_p95_ms >= report.latency_p50_ms
    assert report.sub_minute_target_passed is True

    # Test dictionary serialization
    d = report.to_dict()
    assert "latency_p95_ms" in d
    assert "throughput_comments_per_sec" in d
