"""
backend/risk/config_loader.py
------------------------------
Loads and caches thresholds.yaml. Single point of access for all risk modules.
Never hardcodes numeric values.

Per-campaign runtime overrides are layered on top of the base YAML at request time.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import yaml

_LOCK = threading.Lock()
_BASE_CONFIG: dict[str, Any] | None = None

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "thresholds.yaml"


def _load_base() -> dict[str, Any]:
    global _BASE_CONFIG
    with _LOCK:
        if _BASE_CONFIG is None:
            path = _DEFAULT_CONFIG_PATH
            if not path.exists():
                raise FileNotFoundError(f"thresholds.yaml not found: {path}")
            with path.open() as f:
                _BASE_CONFIG = yaml.safe_load(f)
    return _BASE_CONFIG  # type: ignore[return-value]


def get_config() -> dict[str, Any]:
    """Return the base (YAML) config. Immutable — never write to this dict."""
    return _load_base()


def _reload_for_tests() -> None:
    """Reset cached config — for use in tests only."""
    global _BASE_CONFIG
    with _LOCK:
        _BASE_CONFIG = None
