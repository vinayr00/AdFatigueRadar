"""
backend/risk/aggregation.py
----------------------------
Rolling window aggregation, SimClock, HMAC ingestion, anomaly detection,
per-author cap, and deduplication.

Design:
- SimClock drives all gate/persistence/staleness evaluation via tick().
  The replay runner calls tick() once per 5-min step, even with no events.
- HMAC author ID replacement happens at the ingestion boundary.
  Raw author_id is never stored, logged, or returned after this point.
- Anomaly detection runs on PRE-CAP counts.
- Per-author cap (3) keeps earliest by (timestamp, event_id); excess flagged
  excluded_from_scoring=True (never deleted).
- Wilson n and all rates use POST-CAP counts.

Authority: SPEC §§7,9,12, Execution Prompt items 2,3,4,5,7, Plan v3 §P-02,P-07,P-09.
"""
from __future__ import annotations

import hashlib
import hmac
import math
import os
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterator, Protocol, runtime_checkable

from backend.models.backend_models import CommentEvent, NLPResult, ReasonCode, TelemetryEvent
from backend.risk.config_loader import get_config

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CANONICAL_CATEGORIES = frozenset({
    "product_complaint", "service_complaint", "fatigue",
    "mockery", "spam", "banter_meme", "neutral", "positive",
})

_STRIP_RE = re.compile(r"[^\w\s]", re.UNICODE)


@runtime_checkable
class NLPResultSource(Protocol):
    """Typed boundary accepted from the Person 1 NLP producer."""
    comment_id: str
    sentiment: str
    sentiment_score: float
    category: str
    confidence: float
    critical_complaint: bool


# ---------------------------------------------------------------------------
# HMAC helper — applied at ingestion boundary only
# ---------------------------------------------------------------------------

def _hmac_author_id(raw_id: str) -> str:
    """HMAC-SHA256 of raw author_id with ADFR_HMAC_SECRET, truncated hex (16 chars).
    Fails closed if ADFR_HMAC_SECRET is not set.
    """
    secret = os.environ.get("ADFR_HMAC_SECRET", "")
    if not secret:
        raise RuntimeError("ADFR_HMAC_SECRET not set — cannot derive author HMAC")
    return hmac.new(
        secret.encode(),
        raw_id.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Text normalization for duplicate detection (P-07)
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    """Lowercase, strip punctuation/emoji/whitespace — for duplicate detection only."""
    # Remove emoji via unicode category
    text = "".join(
        c for c in text
        if unicodedata.category(c)[0] not in ("S", "P") or c.isalpha()
    )
    text = _STRIP_RE.sub("", text.lower())
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Stored enriched comment record
# ---------------------------------------------------------------------------

@dataclass(order=False)
class EnrichedComment:
    """A comment after HMAC replacement, joined with NLPResult."""
    event_id: str
    timestamp: datetime
    hmac_author_id: str          # never the raw author_id
    text: str
    reactions: int
    replies: int
    campaign_id: str
    ad_id: str
    # NLP fields — None if NLPResult not yet received
    sentiment: str | None = None
    sentiment_score: float | None = None
    category: str | None = None
    confidence: float | None = None
    critical_complaint: bool = False
    # Derived
    excluded_from_scoring: bool = False   # True after per-author cap
    unknown_category: bool = False        # True if category not in canonical set
    unknown_category_name: str | None = None
    normalized_text: str = ""            # for duplicate detection


@dataclass
class TelemetryRecord:
    event_id: str
    timestamp: datetime
    campaign_id: str
    spend: float
    impressions: float
    reach: float
    clicks: float
    conversions: float
    roas: float | None


# ---------------------------------------------------------------------------
# SimClock — drives all gate/persistence/staleness evaluation
# ---------------------------------------------------------------------------

class SimClock:
    """Injectable simulated clock for a single campaign.

    The replay runner calls tick(sim_time) once per 5-minute step.
    No datetime.now() is ever called in risk/gate/state logic.
    """

    def __init__(self) -> None:
        self._current: datetime | None = None
        self._step_count: int = 0

    @property
    def current(self) -> datetime | None:
        return self._current

    @property
    def step_count(self) -> int:
        return self._step_count

    def tick(self, sim_time: datetime) -> datetime:
        """Advance clock to sim_time. Returns sim_time."""
        if sim_time.tzinfo is None or sim_time.utcoffset() != timedelta(0):
            raise ValueError("sim_time must be UTC timezone-aware")
        if int(sim_time.timestamp() // 60) % 5:
            raise ValueError("sim_time must fall on a 5-minute boundary")
        if self._current is not None and sim_time < self._current:
            raise ValueError("SimClock cannot move backwards")
        self._current = sim_time
        self._step_count += 1
        return sim_time

    def reset(self) -> None:
        self._current = None
        self._step_count = 0


# ---------------------------------------------------------------------------
# Per-campaign window aggregator
# ---------------------------------------------------------------------------

class CampaignAggregator:
    """Manages the rolling window of comments and telemetry for one campaign.

    Thread safety: external lock (one per-campaign lock) expected from caller.
    """

    def __init__(self, campaign_id: str, cfg: dict | None = None) -> None:
        self.campaign_id = campaign_id
        self._cfg = cfg or get_config()
        self._guard_window_minutes: int = self._cfg["compute"]["guard_window_minutes"]
        self._per_author_cap: int = self._cfg["anomaly"]["per_author_max_comments_per_window"]
        self._dup_min_chars: int = self._cfg.get("dup_min_chars", 3)

        # Storage — keyed by event_id for O(1) dedup
        self._comments: dict[str, EnrichedComment] = {}
        self._nlp_pending: dict[str, NLPResultSource] = {}    # typed NLP boundary, waiting for join
        self.late_nlp_dropped = 0
        self._telemetry: list[TelemetryRecord] = []
        self._dedup_ids: set[str] = set()                # all event_ids ever seen (for idempotency)
        self._nlp_dedup: set[str] = set()
        self._telemetry_dedup: set[str] = set()

        # Audit state (unknown category per distinct category string)
        self._unknown_categories_seen: set[str] = set()

        self.clock = SimClock()

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest_comment(self, event: CommentEvent) -> tuple[bool, list[ReasonCode]]:
        """Ingest a CommentEvent. Returns (is_new, reason_codes_for_audit).

        HMAC replacement happens here. Raw author_id never leaves this method.
        """
        # 1. Dedup
        if event.event_id in self._dedup_ids:
            return False, []
        self._dedup_ids.add(event.event_id)

        # 2. HMAC author ID at boundary
        hmac_id = _hmac_author_id(event.author_id)

        # 3. Construct enriched record
        rec = EnrichedComment(
            event_id=event.event_id,
            timestamp=event.timestamp,
            hmac_author_id=hmac_id,
            text=event.text,
            reactions=event.reactions,
            replies=event.replies,
            campaign_id=event.campaign_id,
            ad_id=event.ad_id,
            normalized_text=_normalize_text(event.text),
        )

        # 4. Check for pending NLPResult
        if event.event_id in self._nlp_pending:
            if self._inside_window(event.timestamp):
                self._apply_nlp(rec, self._nlp_pending.pop(event.event_id))
            else:
                self._nlp_pending.pop(event.event_id, None)
                self.late_nlp_dropped += 1

        self._comments[event.event_id] = rec

        # 5. Check unknown category after NLP join
        audit_codes: list[ReasonCode] = []
        if rec.unknown_category:
            unknown_name = rec.unknown_category_name or ""
            if unknown_name not in self._unknown_categories_seen:
                self._unknown_categories_seen.add(unknown_name)
                audit_codes.append(ReasonCode.UNKNOWN_CATEGORY)

        return True, audit_codes

    def ingest_nlp(self, result: NLPResultSource) -> tuple[bool, list[ReasonCode]]:
        """Ingest an NLPResult. Joins to existing comment if present."""
        if result.comment_id in self._nlp_dedup:
            return False, []
        self._nlp_dedup.add(result.comment_id)
        if result.comment_id in self._comments:
            rec = self._comments[result.comment_id]
            if not self._inside_window(rec.timestamp):
                self.late_nlp_dropped += 1
                return False, []
            self._apply_nlp(rec, result)
            audit_codes: list[ReasonCode] = []
            unknown_name = rec.unknown_category_name or ""
            if rec.unknown_category and unknown_name not in self._unknown_categories_seen:
                self._unknown_categories_seen.add(unknown_name)
                audit_codes.append(ReasonCode.UNKNOWN_CATEGORY)
            return True, audit_codes
        else:
            # Store for later join
            self._nlp_pending[result.comment_id] = result
            return False, []

    def _apply_nlp(self, rec: EnrichedComment, nlp: NLPResultSource) -> None:
        """Attach NLPResult fields to an EnrichedComment."""
        rec.sentiment = nlp.sentiment
        rec.sentiment_score = nlp.sentiment_score
        rec.confidence = nlp.confidence
        rec.critical_complaint = nlp.critical_complaint
        # Validate category
        cat = nlp.category
        if cat not in _CANONICAL_CATEGORIES:
            rec.category = "neutral"
            rec.unknown_category = True
            rec.unknown_category_name = cat
        else:
            rec.category = cat

    def _inside_window(self, timestamp: datetime) -> bool:
        start = self._window_start()
        return start is None or timestamp >= start

    def ingest_telemetry(self, event: TelemetryEvent) -> bool:
        """Ingest a TelemetryEvent. Returns True if new."""
        if event.event_id in self._telemetry_dedup:
            return False
        self._telemetry_dedup.add(event.event_id)
        roas = event.roas
        self._telemetry.append(TelemetryRecord(
            event_id=event.event_id,
            timestamp=event.timestamp,
            campaign_id=event.campaign_id,
            spend=event.spend,
            impressions=event.impressions,
            reach=event.reach,
            clicks=event.clicks,
            conversions=event.conversions,
            roas=roas,
        ))
        return True

    # ------------------------------------------------------------------
    # Window queries — always computed against current sim clock time
    # ------------------------------------------------------------------

    def _window_start(self) -> datetime | None:
        if self.clock.current is None:
            return None
        return self.clock.current - timedelta(minutes=self._guard_window_minutes)

    def get_window_comments(self) -> list[EnrichedComment]:
        """All comments in the rolling guard window, sorted by timestamp."""
        ws = self._window_start()
        if ws is None:
            return []
        return sorted(
            [c for c in self._comments.values() if ws <= c.timestamp <= self.clock.current],
            key=lambda c: (c.timestamp, c.event_id),
        )

    def get_window_telemetry(self) -> list[TelemetryRecord]:
        """All telemetry in the rolling guard window, sorted by timestamp."""
        ws = self._window_start()
        if ws is None:
            return []
        return sorted(
            [t for t in self._telemetry if ws <= t.timestamp <= self.clock.current],
            key=lambda t: t.timestamp,
        )

    def compute_anomaly_and_cap(
        self,
    ) -> tuple[bool, float, float, list[EnrichedComment]]:
        """Compute anomaly flags on PRE-CAP counts, then apply per-author cap.

        Returns:
            (anomaly, top_author_share, dup_cluster_share, post_cap_comments)

        post_cap_comments: scored (not excluded) comments for risk computation.
        All excess comments are marked excluded_from_scoring=True but retained.
        """
        window = self.get_window_comments()
        total = len(window)
        if total == 0:
            return False, 0.0, 0.0, []

        # --- PRE-CAP anomaly detection ---

        # top_author_share
        author_counts: dict[str, int] = defaultdict(int)
        for c in window:
            author_counts[c.hmac_author_id] += 1
        max_author_count = max(author_counts.values()) if author_counts else 0
        top_author_share = max_author_count / total

        # duplicate_cluster_share (P-07: exclude texts shorter than dup_min_chars)
        cluster_counts: dict[str, int] = defaultdict(int)
        for c in window:
            nt = c.normalized_text
            if len(nt) >= self._dup_min_chars:
                cluster_key = hashlib.sha256(nt.encode("utf-8")).hexdigest()
                cluster_counts[cluster_key] += 1
        max_cluster = max(cluster_counts.values()) if cluster_counts else 0
        dup_cluster_share = max_cluster / total

        cfg_anomaly = self._cfg["anomaly"]
        anomaly = (
            top_author_share > cfg_anomaly["top_author_share_max"]
            or dup_cluster_share > cfg_anomaly["duplicate_cluster_share_max"]
        )

        # --- Per-author cap (POST-anomaly detection) ---
        # Keep earliest 3 by (timestamp, event_id); mark rest excluded
        author_kept: dict[str, int] = defaultdict(int)
        cap = self._per_author_cap
        post_cap: list[EnrichedComment] = []

        for c in window:  # already sorted by (timestamp, event_id)
            if author_kept[c.hmac_author_id] < cap:
                author_kept[c.hmac_author_id] += 1
                c.excluded_from_scoring = False
                post_cap.append(c)
            else:
                c.excluded_from_scoring = True  # flagged, never deleted

        return anomaly, top_author_share, dup_cluster_share, post_cap

    def get_telemetry_window_sums(self) -> dict[str, float | None]:
        """Return window telemetry sums. CPA/CPM/ROAS recomputed from sums.

        All ratios recomputed from extensive sums (never averaged per-event ratios).
        Division by zero → None, never inf.
        """
        recs = self.get_window_telemetry()
        if not recs:
            return {
                "spend": 0.0, "impressions": 0.0, "reach": 0.0,
                "clicks": 0.0, "conversions": 0.0,
                "ctr": None, "frequency": None,
                "cpa": None, "cpm": None, "cpc": None, "roas": None,
                "revenue": 0.0,
            }

        spend = sum(r.spend for r in recs)
        impressions = sum(r.impressions for r in recs)
        reach = sum(r.reach for r in recs)
        clicks = sum(r.clicks for r in recs)
        conversions = sum(r.conversions for r in recs)
        # revenue = roas × spend per record (roas may be null)
        revenue = sum(
            r.roas * r.spend for r in recs if r.roas is not None
        )

        def _safe_div(a: float, b: float) -> float | None:
            if not math.isfinite(a) or not math.isfinite(b) or b == 0.0:
                return None
            value = a / b
            return value if math.isfinite(value) else None

        sums = (spend, impressions, reach, clicks, conversions, revenue)
        if not all(math.isfinite(value) for value in sums):
            raise ValueError("telemetry window total is not finite")

        raw_cpm = _safe_div(spend, impressions)
        cpm = raw_cpm * 1000 if raw_cpm is not None and math.isfinite(raw_cpm * 1000) else None

        return {
            "spend": spend,
            "impressions": impressions,
            "reach": reach,
            "clicks": clicks,
            "conversions": conversions,
            "revenue": revenue,
            "ctr": _safe_div(clicks, impressions),      # clicks/impressions
            "frequency": _safe_div(impressions, reach), # impressions/reach
            "cpa": _safe_div(spend, conversions),       # null when conversions=0
            "cpm": cpm,
            "cpc": _safe_div(spend, clicks),
            "roas": _safe_div(revenue, spend),
        }

    def get_comment_rate_history(self) -> list[tuple[datetime, float]]:
        """Return (step_boundary, comments_per_step) for comment acceleration.

        Groups post-cap comments by 5-min step boundaries.
        """
        step_min = self._cfg["compute"]["step_minutes"]
        ws = self._window_start()
        if ws is None or self.clock.current is None:
            return []
        _, _, _, post_cap = self.compute_anomaly_and_cap()
        buckets: dict[int, int] = defaultdict(int)
        for c in post_cap:
            # which step bucket (0 = oldest)
            delta = (c.timestamp - ws).total_seconds() / 60.0
            bucket_idx = int(delta // step_min)
            buckets[bucket_idx] += 1
        n_steps = int(self._guard_window_minutes // step_min)
        result = []
        t = ws
        for i in range(n_steps):
            result.append((t, float(buckets.get(i, 0))))
            t += timedelta(minutes=step_min)
        return result

    def get_step_count(self) -> int:
        """Number of ticks since last telemetry (for staleness)."""
        return self.clock.step_count

    def has_telemetry_in_last_n_steps(self, n: int) -> bool:
        """True if any telemetry arrived within the last n steps."""
        if self.clock.current is None:
            return False
        step_min = self._cfg["compute"]["step_minutes"]
        cutoff = self.clock.current - timedelta(minutes=step_min * n)
        return any(t.timestamp >= cutoff for t in self._telemetry)

    # ------------------------------------------------------------------
    # Reset (for replay/reset — P-03)
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Clear all window state. Preserves nothing (audit log is external)."""
        self._comments.clear()
        self._nlp_pending.clear()
        self._nlp_dedup.clear()
        self.late_nlp_dropped = 0
        self._telemetry.clear()
        self._dedup_ids.clear()
        self._telemetry_dedup.clear()
        self._unknown_categories_seen.clear()
        self.clock.reset()
