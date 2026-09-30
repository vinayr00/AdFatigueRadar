"""Validate thresholds using the same runtime validator as the API."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
CONFIG_PATH = REPO_ROOT / "config" / "thresholds.yaml"
REQUIRED_PATHS = (
    "config_version", "compute.step_minutes", "compute.guard_window_minutes",
    "compute.ewma_alpha", "audience_gates.watch", "audience_gates.warning",
    "audience_gates.soft", "audience_gates.critical", "audience_gates.pause_audience",
    "economic.pause_gate", "economic.min_conversions_in_window", "persistence_hours.warning",
    "persistence_hours.soft", "persistence_hours.pause", "persistence_hours.emergency",
    "persistence_hours.recovery", "cooldown_minutes", "evidence.min_classified_comments",
    "evidence.min_distinct_authors", "evidence.min_classifier_confidence",
    "evidence.harmful_wilson_lb_min", "evidence.wilson_z", "audience_weights",
    "economic_weights", "normalization", "category_weights", "safe_bounds",
    "threshold_mutable_keys", "actions.soft_budget_multiplier",
    "critical_complaint.categories", "critical_complaint.min_confidence",
    "critical_complaint.rate_min", "anomaly.top_author_share_max",
    "anomaly.duplicate_cluster_share_max", "anomaly.per_author_max_comments_per_window",
    "staleness.stale_after_steps", "staleness.check_states", "staleness.paused_heartbeat",
    "baseline.method", "baseline.window_minutes", "baseline.warmup_steps",
    "accel_eps", "dup_min_chars", "readback_max_retries",
)
WILSON_GROUND_TRUTH = [
    (24,.25,.1200),(24,.50,.3143),(24,.75,.5510),
    (30,.25,.1298),(30,.50,.3315),(30,.75,.5730),
    (60,.25,.1578),(60,.50,.3773),(60,.75,.6277),
    (120,.25,.1811),(120,.50,.4119),(120,.75,.6656),
    (480,.25,.2134),(480,.50,.4554),(480,.75,.7094),
]


def _get(data: dict, dotted: str):
    for key in dotted.split("."):
        if not isinstance(data, dict) or key not in data:
            return None
        data = data[key]
    return data


def _worked_example(cfg: dict) -> list[str]:
    """Exercise production normalization and weighted score functions."""
    from backend.risk.audience_risk import compute_audience_risk
    from backend.risk.economic_risk import compute_economic_risk
    from backend.risk.features import SignalSet
    from backend.risk.normalization import normalize
    from backend.risk.wilson import wilson_lb

    n, k = 120, 56
    norm = cfg["normalization"]
    lb = wilson_lb(k, n)
    signals = SignalSet(
        harmful_negative_ratio=normalize(lb, **norm["harmful_negative_ratio"]),
        sentiment_decay=normalize(.14, **norm["sentiment_decay"]),
        fatigue_mockery=normalize(.30, **norm["fatigue_mockery"]),
        comment_acceleration=normalize(.08, **norm["comment_acceleration"]),
        ctr_frequency=(normalize(25, **norm["ctr_decay_pct"]) + normalize(55, **norm["frequency_increase_pct"])) / 2,
        critical_complaint_signal=normalize(.04, **norm["critical_complaint"]),
        cpa_cpm_signal=max(normalize(12, **norm["cpa_delta_pct"]), normalize(8, **norm["cpm_delta_pct"])),
        roas_conversion_signal=max(normalize(9.5, **norm["roas_drop_pct"]), normalize(6, **norm["conv_rate_drop_pct"])),
    )
    audience = compute_audience_risk(signals, cfg)
    economic = compute_economic_risk(signals, 25, cfg)
    errors = []
    if abs(audience - .781) > .05:
        errors.append(f"runtime audience worked example={audience:.4f}; expected approximately 0.781")
    if economic is None or abs(economic - .178) > .05:
        errors.append(f"runtime economic worked example={economic}; expected approximately 0.178")
    return errors


def main() -> int:
    if not CONFIG_PATH.exists():
        print(f"FAIL: missing {CONFIG_PATH}", file=sys.stderr)
        return 1
    try:
        cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"FAIL: invalid YAML: {exc}", file=sys.stderr)
        return 1
    missing = [path for path in REQUIRED_PATHS if _get(cfg, path) is None]
    if missing:
        print("MISSING_FROM_MASTER_SPEC: " + ", ".join(missing), file=sys.stderr)
        return 3

    from backend.api.threshold_validator import validate_config
    errors = validate_config(cfg)
    if errors:
        print("CONFIG INVALID:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1

    from backend.risk.wilson import wilson_lb
    for n, p, expected in WILSON_GROUND_TRUTH:
        if abs(wilson_lb(p * n, n) - expected) > 1e-4:
            print(f"FAIL: Wilson reference n={n}, p={p}", file=sys.stderr)
            return 1
    if wilson_lb(1, 0) != 0 or wilson_lb(-1, 12) != wilson_lb(0, 12) or wilson_lb(13, 12) != wilson_lb(12, 12):
        print("FAIL: Wilson guard/clamp behavior", file=sys.stderr)
        return 1
    errors = _worked_example(cfg)
    if errors:
        print("WORKED EXAMPLE FAILED:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print("Config validation, Wilson references, and runtime worked example passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
