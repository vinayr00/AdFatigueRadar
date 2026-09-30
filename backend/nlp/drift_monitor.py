"""
AdFatigueRadar — Prediction Drift Monitor & Background Daemon (Phase 4)
=======================================================================
Implements Population Stability Index (PSI) & Jensen-Shannon Divergence
tracking against the Phase 3 Real-World reference distribution.
Emits structured alerts (NORMAL / WARNING / CRITICAL) and persists drift metrics.
"""

import os
import json
import time
import threading
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from collections import Counter

from .constants import TAXONOMY_CATEGORIES
from .schemas import DriftStatusResponse

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REPORTS_PHASE4_DIR = os.path.join(BASE_DIR, "reports", "phase4")
os.makedirs(REPORTS_PHASE4_DIR, exist_ok=True)

# Documented Phase 3 Real-World Reference Baseline Distribution (299 held-out test samples)
PHASE3_BASELINE_DISTRIBUTION = {
    "product_complaint": 42 / 299,
    "service_complaint": 20 / 299,
    "fatigue": 21 / 299,
    "mockery": 41 / 299,
    "spam": 13 / 299,
    "banter_meme": 40 / 299,
    "neutral": 81 / 299,
    "positive": 41 / 299,
}


def calculate_psi(expected: Dict[str, float], actual: Dict[str, float], epsilon: float = 1e-4) -> float:
    """
    Computes Population Stability Index (PSI) between reference and observed category distributions.
    
    PSI < 0.10  -> NORMAL (No significant shift)
    0.10 - 0.25 -> WARNING (Moderate distribution shift)
    PSI >= 0.25 -> CRITICAL (Severe population drift)
    """
    psi = 0.0
    for cat in TAXONOMY_CATEGORIES:
        e = max(expected.get(cat, 0.0), epsilon)
        a = max(actual.get(cat, 0.0), epsilon)
        psi += (a - e) * np.log(a / e)
    return float(psi)


def calculate_js_divergence(p: np.ndarray, q: np.ndarray, epsilon: float = 1e-9) -> float:
    """Computes symmetric Jensen-Shannon divergence in [0.0, 1.0]."""
    p = np.clip(p, epsilon, 1.0)
    p = p / np.sum(p)
    q = np.clip(q, epsilon, 1.0)
    q = q / np.sum(q)
    m = 0.5 * (p + q)
    kl_pm = np.sum(p * np.log(p / m))
    kl_qm = np.sum(q * np.log(q / m))
    return float(0.5 * kl_pm + 0.5 * kl_qm)


class PredictionDriftMonitor:
    """
    Thread-safe drift monitor tracking live predictions and evaluating
    divergence at configurable intervals.
    """
    _instance: Optional["PredictionDriftMonitor"] = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, window_size: int = 500) -> "PredictionDriftMonitor":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(window_size=window_size)
            return cls._instance

    def __init__(self, window_size: int = 500, baseline_dist: Optional[Dict[str, float]] = None):
        self.window_size = window_size
        self.baseline_dist = baseline_dist or PHASE3_BASELINE_DISTRIBUTION
        self.observations: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []
        self._obs_lock = threading.Lock()
        self._daemon_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.last_status: Optional[DriftStatusResponse] = None
        self.last_evaluated_utc = datetime.now(timezone.utc).isoformat()

    def record_prediction(self, category: str, confidence: float, is_critical: bool):
        """Records a live prediction observation into the rolling window."""
        with self._obs_lock:
            self.observations.append({
                "category": category,
                "confidence": confidence,
                "is_critical": is_critical,
                "timestamp": time.time()
            })
            if len(self.observations) > self.window_size:
                self.observations = self.observations[-self.window_size:]

    def evaluate_drift(self, min_samples: int = 20) -> DriftStatusResponse:
        """Evaluates PSI, JS divergence, and confidence shifts across the active observation window."""
        with self._obs_lock:
            total_obs = len(self.observations)
            if total_obs < min_samples:
                return DriftStatusResponse(
                    status="INSUFFICIENT_DATA",
                    psi_score=0.0,
                    js_divergence=0.0,
                    sample_window_size=total_obs,
                    critical_complaint_rate=0.0,
                    avg_confidence=0.0,
                    low_confidence_rate=0.0,
                    baseline_distribution=self.baseline_dist,
                    current_distribution={cat: 0.0 for cat in TAXONOMY_CATEGORIES},
                    last_evaluated_utc=datetime.now(timezone.utc).isoformat()
                )

            counts = Counter(o["category"] for o in self.observations)
            current_dist = {cat: counts.get(cat, 0) / total_obs for cat in TAXONOMY_CATEGORIES}
            
            confs = [o["confidence"] for o in self.observations]
            avg_conf = float(np.mean(confs))
            low_conf_rate = float(np.mean([1 if c < 0.40 else 0 for c in confs]))
            crit_rate = float(np.mean([1 if o["is_critical"] else 0 for o in self.observations]))

        # Calculate metrics
        psi = calculate_psi(self.baseline_dist, current_dist)
        
        base_arr = np.array([self.baseline_dist.get(c, 0.0) for c in TAXONOMY_CATEGORIES])
        curr_arr = np.array([current_dist.get(c, 0.0) for c in TAXONOMY_CATEGORIES])
        js_div = calculate_js_divergence(base_arr, curr_arr)

        if psi >= 0.25 or js_div >= 0.20:
            status = "CRITICAL"
        elif psi >= 0.10 or js_div >= 0.08 or low_conf_rate > 0.25:
            status = "WARNING"
        else:
            status = "NORMAL"

        eval_utc = datetime.now(timezone.utc).isoformat()
        status_resp = DriftStatusResponse(
            status=status,
            psi_score=round(psi, 4),
            js_divergence=round(js_div, 4),
            sample_window_size=total_obs,
            critical_complaint_rate=round(crit_rate, 4),
            avg_confidence=round(avg_conf, 4),
            low_confidence_rate=round(low_conf_rate, 4),
            baseline_distribution={k: round(v, 4) for k, v in self.baseline_dist.items()},
            current_distribution={k: round(v, 4) for k, v in current_dist.items()},
            last_evaluated_utc=eval_utc
        )
        self.last_status = status_resp
        self.last_evaluated_utc = eval_utc
        
        if status in ["WARNING", "CRITICAL"]:
            self.alerts.append({
                "timestamp_utc": eval_utc,
                "severity": status,
                "psi_score": round(psi, 4),
                "js_divergence": round(js_div, 4),
                "sample_count": total_obs
            })

        self.persist_drift_report()
        return status_resp

    def persist_drift_report(self):
        """Persists drift evaluation report to reports/phase4/drift_report.json."""
        if not self.last_status:
            return
        rep_path = os.path.join(REPORTS_PHASE4_DIR, "drift_report.json")
        with open(rep_path, "w", encoding="utf-8") as f:
            json.dump({
                "drift_status": self.last_status.dict(),
                "active_alerts_count": len(self.alerts),
                "recent_alerts": self.alerts[-10:],
                "evaluation_policy": {
                    "psi_warning_threshold": 0.10,
                    "psi_critical_threshold": 0.25,
                    "js_warning_threshold": 0.08,
                    "js_critical_threshold": 0.20,
                    "min_sample_size": 20
                }
            }, f, indent=2)

    def start_background_daemon(self, interval_seconds: int = 60):
        """Starts background periodic drift evaluation daemon."""
        if self._daemon_thread and self._daemon_thread.is_alive():
            return

        def _daemon_loop():
            while not self._stop_event.is_set():
                try:
                    self.evaluate_drift()
                except Exception as e:
                    print(f"[DriftDaemon] Evaluation error: {e}")
                self._stop_event.wait(interval_seconds)

        self._stop_event.clear()
        self._daemon_thread = threading.Thread(target=_daemon_loop, daemon=True, name="DriftDaemon")
        self._daemon_thread.start()

    def stop_background_daemon(self):
        """Stops background daemon cleanly."""
        self._stop_event.set()
        if self._daemon_thread:
            self._daemon_thread.join(timeout=2)
