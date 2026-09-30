"""
backend/replay/file_source.py
------------------------------
Default ReplaySource that reads events from replay/generated/{campaign_id}/.
Files are read READ-ONLY.

If replay/generated/ has no data for a campaign, yields nothing.
Format: JSONL files — one event per line with a "type" discriminator field.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from backend.models.backend_models import CommentEvent, NLPResult, TelemetryEvent
from backend.replay.runner import ReplaySource


class FileReplaySource:
    """Reads events from replay/generated/{campaign_id}/ READ-ONLY."""

    def __init__(self, campaign_id: str) -> None:
        self._campaign_id = campaign_id
        repo_root = Path(__file__).resolve().parent.parent.parent
        self._source_dir = repo_root / "replay" / "generated" / campaign_id

    def events(self) -> Iterator[CommentEvent | NLPResult | TelemetryEvent]:
        if not self._source_dir.exists():
            return  # no data — yield nothing

        for jsonl_file in sorted(self._source_dir.glob("*.jsonl")):
            with jsonl_file.open() as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        event_type = data.get("type", "")
                        if event_type == "comment":
                            yield CommentEvent(**{k: v for k, v in data.items() if k != "type"})
                        elif event_type == "nlp":
                            yield NLPResult(**{k: v for k, v in data.items() if k != "type"})
                        elif event_type == "telemetry":
                            yield TelemetryEvent(**{k: v for k, v in data.items() if k != "type"})
                    except Exception:
                        continue  # skip malformed lines
