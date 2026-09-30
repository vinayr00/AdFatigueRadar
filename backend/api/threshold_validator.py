"""Single authoritative validation for base configuration and runtime overrides."""
from __future__ import annotations

from copy import deepcopy
import math
from typing import Any


class ThresholdValidationError(ValueError):
    pass


def _get_nested(data: dict[str, Any], key: str) -> Any:
    cur: Any = data
    for part in key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise ThresholdValidationError(f"unknown threshold key: {key}")
        cur = cur[part]
    return cur


def validate_config(cfg: dict[str, Any]) -> list[str]:
    """Return configuration errors. Used by checker and API override validation."""
    errors: list[str] = []
    mutable = cfg.get("threshold_mutable_keys", [])
    bounds = cfg.get("safe_bounds", {})
    if not isinstance(mutable, list) or len(mutable) != len(set(mutable)):
        errors.append("threshold_mutable_keys must be a unique list")
        mutable = []
    if not isinstance(bounds, dict):
        errors.append("safe_bounds must be a mapping")
        bounds = {}
    if set(bounds) != set(mutable):
        errors.append("safe_bounds keys must equal threshold_mutable_keys exactly")
    allowed_paths = {
        "audience_gates.warning", "audience_gates.soft", "audience_gates.pause_audience",
        "economic.pause_gate", "cooldown_minutes", "actions.soft_budget_multiplier",
    }
    unknown_paths = set(mutable) - allowed_paths
    if unknown_paths:
        errors.append("threshold_mutable_keys contains forbidden paths: " + ", ".join(sorted(unknown_paths)))
    if cfg.get("config_version") != "thresholds_v4":
        errors.append("config_version must be thresholds_v4")
    compute = cfg.get("compute", {})
    if compute.get("step_minutes") != 5 or compute.get("guard_window_minutes") != 60:
        errors.append("compute step/window must match thresholds_v4 (5/60 minutes)")
    if compute.get("ewma_alpha") != 0.30:
        errors.append("compute.ewma_alpha must match thresholds_v4 (0.30)")
    if cfg.get("evidence", {}).get("wilson_z") != 1.96:
        errors.append("evidence.wilson_z must equal 1.96")
    if cfg.get("accel_eps", 0) <= 0:
        errors.append("accel_eps must be > 0")
    for key in ("dup_min_chars", "readback_max_retries"):
        if not isinstance(cfg.get(key), int) or isinstance(cfg.get(key), bool) or cfg[key] <= 0:
            errors.append(f"{key} must be a positive integer")
    anomaly = cfg.get("anomaly", {})
    if not isinstance(anomaly.get("per_author_max_comments_per_window"), int) or anomaly.get("per_author_max_comments_per_window") != 3:
        errors.append("per-author comment cap must equal 3")
    if cfg.get("staleness", {}).get("stale_after_steps") != 2:
        errors.append("staleness.stale_after_steps must equal 2")
    for key in mutable:
        bound = bounds.get(key)
        try:
            value = _get_nested(cfg, key)
        except ThresholdValidationError as exc:
            errors.append(str(exc))
            continue
        if not isinstance(bound, dict) or set(bound) != {"min", "max"}:
            errors.append(f"safe_bounds.{key} must contain min and max")
            continue
        lo, hi = bound["min"], bound["max"]
        if (isinstance(lo, bool) or isinstance(hi, bool)
                or not isinstance(lo, (int, float)) or not isinstance(hi, (int, float))
                or not math.isfinite(lo) or not math.isfinite(hi) or lo > hi):
            errors.append(f"safe_bounds.{key} has invalid bounds")
        elif not isinstance(value, (int, float)) or isinstance(value, bool) or not lo <= value <= hi:
            errors.append(f"configured value for {key} is outside safe_bounds")

    for weights_path in ("audience_weights", "economic_weights"):
        weights = cfg.get(weights_path, {})
        if (not isinstance(weights, dict)
                or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in weights.values())
                or abs(sum(weights.values()) - 1.0) > 1e-9):
            errors.append(f"{weights_path} must sum to 1")
    expected_weights = {
        "audience_weights": {"harmful_negative_ratio": .30, "sentiment_decay": .25,
            "fatigue_mockery": .20, "comment_acceleration": .10, "ctr_frequency": .10,
            "critical_complaint": .05},
        "economic_weights": {"cpa_cpm": .55, "roas_conversion": .45},
    }
    for key, expected in expected_weights.items():
        if cfg.get(key) != expected:
            errors.append(f"{key} are immutable and must match thresholds_v4")
    ag = cfg.get("audience_gates", {})
    ordered = [ag.get(k) for k in ("watch", "warning", "soft", "critical")]
    if any(not isinstance(v, (int, float)) for v in ordered) or not all(a < b for a, b in zip(ordered, ordered[1:])):
        errors.append("audience gates must satisfy watch < warning < soft < critical")
    if ag.get("soft") is not None and ag.get("pause_audience") is not None and ag["soft"] > ag["pause_audience"]:
        errors.append("soft must be <= pause_audience")
    rec = cfg.get("recovery", {})
    warning_recovery = rec.get("warning_threshold", ag.get("warning_recovery"))
    soft_recovery = rec.get("soft_threshold", ag.get("soft_recovery"))
    if warning_recovery is not None and soft_recovery is not None and warning_recovery >= soft_recovery:
        errors.append("recovery.warning_threshold must be < recovery.soft_threshold")
    if ag.get("warning_recovery") is not None and ag.get("warning") is not None and ag["warning_recovery"] >= ag["warning"]:
        errors.append("warning recovery must be below warning entry")
    if ag.get("soft_recovery") is not None and ag.get("soft") is not None and ag["soft_recovery"] >= ag["soft"]:
        errors.append("soft recovery must be below soft entry")
    persistence = cfg.get("persistence_hours", cfg.get("persistence", {}))
    if not isinstance(persistence, dict) or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in persistence.values()):
        errors.append("all persistence values must be > 0")
    if isinstance(cfg.get("cooldown_minutes"), bool) or not isinstance(cfg.get("cooldown_minutes"), (int, float)) or cfg["cooldown_minutes"] <= 0:
        errors.append("cooldown_minutes must be > 0")
    multiplier = cfg.get("actions", {}).get("soft_budget_multiplier", cfg.get("soft_budget_multiplier"))
    if isinstance(multiplier, bool) or not isinstance(multiplier, (int, float)) or not 0 < multiplier <= 1:
        errors.append("soft_budget_multiplier must be in (0, 1]")
    cats = cfg.get("category_weights", {})
    if cats.get("banter_meme") != 0:
        errors.append("category_weights.banter_meme must equal 0")
    expected_categories = {
        "product_complaint": 1.0, "service_complaint": 1.0, "fatigue": .8,
        "mockery": .75, "spam": .6, "banter_meme": 0.0, "neutral": 0.0, "positive": 0.0,
    }
    if cats != expected_categories:
        errors.append("category_weights are immutable and must match the master specification")
    return errors


def validate_overrides(overrides: dict[str, float], cfg: dict[str, Any] | None = None) -> list[str]:
    """Validate and cross-check an override against the base config."""
    from backend.risk.config_loader import get_config

    base = deepcopy(cfg if cfg is not None else get_config())
    errors: list[str] = []
    if not overrides:
        return ["at least one threshold override is required"]
    mutable = set(base.get("threshold_mutable_keys", []))
    bounds = base.get("safe_bounds", {})
    for key, value in overrides.items():
        if key not in mutable:
            errors.append(f"immutable or unknown threshold key: {key}")
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"threshold {key} must be numeric")
            continue
        bound = bounds.get(key, {})
        if not bound or not bound["min"] <= value <= bound["max"]:
            errors.append(f"threshold {key} is outside safe bounds")
            continue
        _set_nested(base, key, value)
    errors.extend(validate_config(base))
    return list(dict.fromkeys(errors))


def _set_nested(data: dict[str, Any], dotted_key: str, value: Any) -> None:
    keys = dotted_key.split(".")
    cur = data
    for part in keys[:-1]:
        cur = cur[part]
    cur[keys[-1]] = value
