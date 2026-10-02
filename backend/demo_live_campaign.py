"""
backend/demo_live_campaign.py
=============================
Bridge exporting simulation functions from root demo_live_campaign.
"""
from __future__ import annotations
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from demo_live_campaign import (
    init_demo_campaign,
    load_demo_campaign,
    save_demo_campaign,
    process_demo_comment,
    campaign_exists,
    classify_text,
)

__all__ = [
    "init_demo_campaign",
    "load_demo_campaign",
    "save_demo_campaign",
    "process_demo_comment",
    "campaign_exists",
    "classify_text",
]
