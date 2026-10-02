"""
demo_live_campaign.py
=====================
Interactive, campaign-scoped live demonstration simulator for AdFatigueRadar.

Lifecycle & Rules:
- Demo JSON files reside strictly in demo_data/campaigns/<campaign_id>.json.
- Campaign JSON files are ONLY created when "+ Create Campaign" is clicked in the UI.
- Never creates a campaign automatically on startup.
- Automatically selects the campaign if exactly 1 exists, prompts if multiple,
  or uses --campaign-id.
- Continuously accepts real-world comments interactively, executes the CardiffNLP
  model pipeline, computes score impact, updates the isolated JSON, and returns
  to prompt without exiting.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Suppress HuggingFace / PyTorch initialization warnings for clean presentation
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent
DEMO_DIR = BASE_DIR / "demo_data" / "campaigns"

# ANSI color codes for rich terminal display (matching demo_live.py)
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

CATEGORY_WEIGHTS = {
    "product_complaint": (1.00, RED, "Product defect / functional issue"),
    "service_complaint": (1.00, RED, "Customer support / logistics / billing"),
    "fatigue": (0.80, YELLOW, "Repeated ad exposure / creative burnout"),
    "mockery": (0.75, MAGENTA, "Satire / ad ridicule / cringe roast"),
    "spam": (0.60, YELLOW, "Crypto / bot / promotional solicitation"),
    "banter_meme": (0.00, CYAN, "Harmless humor / banter / pop meme (0.00 harm)"),
    "neutral": (0.00, DIM, "Informational query / neutral observation"),
    "positive": (0.00, GREEN, "Praise / repeat purchase ('bought again')"),
}

# Score impacts per category
CATEGORY_IMPACT = {
    "positive": +5,
    "fatigue": -8,
    "mockery": -10,
    "product_complaint": -12,
    "service_complaint": -15,
    "spam": -6,
    "banter_meme": 0,
    "neutral": 0,
}

_classifier = None
_sanitizer = None


def _get_nlp():
    global _classifier, _sanitizer
    if _classifier is None:
        try:
            sys.path.insert(0, str(BASE_DIR))
            from backend.nlp.classifier import CommentClassifier
            from backend.nlp.pii_sanitizer import PIISanitizer
            _sanitizer = PIISanitizer()
            _classifier = CommentClassifier()
        except Exception:
            _sanitizer = None
            _classifier = None
    return _classifier, _sanitizer


def _classify_comment_heuristic(text: str) -> tuple[str, str, float]:
    """Fallback sentiment and category classification using keyword heuristics."""
    t = text.lower()
    if any(w in t for w in ["stop", "again", "tired", "seen this", "too many times", "over and over", "annoying"]):
        return "negative", "fatigue", 0.80
    if any(w in t for w in ["clown", "worst", "cringe", "joke", "trash", "terrible", "awful", "lmao", "fake"]):
        return "negative", "mockery", 0.75
    if any(w in t for w in ["scam", "refund", "charged", "stole", "never received", "support", "broken"]):
        return "negative", "service_complaint", 1.00
    if any(w in t for w in ["freeze", "crash", "bug", "defect", "fail", "poor quality"]):
        return "negative", "product_complaint", 1.00
    if any(w in t for w in ["crypto", "telegram", "whatsapp", "dm me", "returns", "free money"]):
        return "neutral", "spam", 0.60
    if any(w in t for w in ["love", "great", "bought again", "awesome", "perfect", "good", "fast delivery", "recommend"]):
        return "positive", "positive", 0.00
    if any(w in t for w in ["haha", "lol", "me at 3am"]):
        return "neutral", "banter_meme", 0.00
    return "neutral", "neutral", 0.00


def classify_text(text: str) -> dict[str, Any]:
    """Classify comment text using CardiffNLP model or fallback heuristic."""
    classifier, sanitizer = _get_nlp()
    if classifier is not None and sanitizer is not None:
        try:
            clean_text, _ = sanitizer.sanitize(text)
            result = classifier.classify_text(clean_text)
            return {
                "sentiment": result.sentiment,
                "category": result.category,
                "sentiment_score": float(result.sentiment_score),
                "confidence": float(result.confidence),
                "critical_complaint": bool(result.critical_complaint),
            }
        except Exception:
            pass

    sentiment, category, weight = _classify_comment_heuristic(text)
    return {
        "sentiment": sentiment,
        "category": category,
        "sentiment_score": 0.85 if sentiment == "negative" else (0.15 if sentiment == "positive" else 0.50),
        "confidence": 0.90,
        "critical_complaint": category in {"service_complaint", "product_complaint"},
    }


def get_campaign_path(campaign_id: str) -> Path:
    return DEMO_DIR / f"{campaign_id}.json"


def campaign_exists(campaign_id: str) -> bool:
    return get_campaign_path(campaign_id).is_file()


def list_existing_campaigns() -> list[tuple[str, str]]:
    """Return list of (campaign_id, campaign_name) for initialized demo campaigns, newest first."""
    if not DEMO_DIR.is_dir():
        return []
    campaigns = []
    active_cid = None
    active_path = BASE_DIR / "demo_data" / "active_campaign.txt"
    if active_path.is_file():
        try:
            active_cid = active_path.read_text(encoding="utf-8").strip()
        except Exception:
            pass

    files = sorted(DEMO_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files:
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                campaigns.append((p.stem, data.get("name", p.stem)))
        except Exception:
            campaigns.append((p.stem, p.stem))

    if active_cid:
        match_idx = next((i for i, (cid, _) in enumerate(campaigns) if cid == active_cid), None)
        if match_idx is not None and match_idx > 0:
            campaigns.insert(0, campaigns.pop(match_idx))

    return campaigns


def init_demo_campaign(campaign_id: str, name: str) -> dict[str, Any]:
    """Initialize a demo campaign JSON file.
    
    ONLY called after successful '+ Create Campaign' flow.
    """
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    target = get_campaign_path(campaign_id)
    
    now = datetime.now(timezone.utc).isoformat()
    data: dict[str, Any] = {
        "campaign_id": campaign_id,
        "name": name,
        "status": "ACTIVE",
        "severity": "HEALTHY",
        "health_score": 100,
        "risk_score": 0.0,
        "economic_risk": 0.05,
        "cpa": 1050.0,
        "metrics": {
            "total_comments": 0,
            "positive_comments": 0,
            "negative_comments": 0,
            "neutral_comments": 0,
            "fatigue_comments": 0,
            "complaint_comments": 0,
            "mockery_comments": 0,
            "negative_ratio": 0.0,
            "recent_negative_ratio": 0.0,
        },
        "recent_window": {
            "size": 20,
            "events": [],
            "negative": 0,
            "positive": 0,
            "neutral": 0,
        },
        "comments": [],
        "events": [
            {
                "event_id": "evt_1",
                "event_type": "CAMPAIGN_INITIALIZED",
                "description": f"Campaign '{name}' initialized with 100% health score.",
                "timestamp": now,
            }
        ],
        "created_at": now,
        "updated_at": now,
    }
    
    with open(target, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    active_path = BASE_DIR / "demo_data" / "active_campaign.txt"
    try:
        active_path.write_text(campaign_id, encoding="utf-8")
    except Exception:
        pass

    return data


def load_demo_campaign(campaign_id: str) -> dict[str, Any]:
    """Load existing campaign JSON. Raises FileNotFoundError if missing."""
    target = get_campaign_path(campaign_id)
    if not target.is_file():
        raise FileNotFoundError("demo campaign not initialized")
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Ensure required simulation fields exist for backwards compatibility
    if "metrics" not in data:
        comments = data.get("comments", [])
        total_c = len(comments)
        neg_c = sum(1 for c in comments if c.get("sentiment") == "negative")
        pos_c = sum(1 for c in comments if c.get("sentiment") == "positive")
        neu_c = sum(1 for c in comments if c.get("sentiment") == "neutral")
        data["metrics"] = {
            "total_comments": total_c,
            "positive_comments": pos_c,
            "negative_comments": neg_c,
            "neutral_comments": neu_c,
            "fatigue_comments": sum(1 for c in comments if c.get("category") == "fatigue"),
            "complaint_comments": sum(1 for c in comments if "complaint" in c.get("category", "")),
            "mockery_comments": sum(1 for c in comments if c.get("category") == "mockery"),
            "negative_ratio": round(neg_c / max(total_c, 1), 2),
            "recent_negative_ratio": 0.0,
        }
    if "recent_window" not in data:
        recent_comments = data.get("comments", [])[-20:]
        recent_events = [
            {
                "comment_id": c.get("comment_id", f"c_{i}"),
                "sentiment": c.get("sentiment", "neutral"),
                "category": c.get("category", "neutral"),
                "timestamp": c.get("timestamp", ""),
            }
            for i, c in enumerate(recent_comments)
        ]
        r_neg = sum(1 for e in recent_events if e.get("sentiment") == "negative")
        r_pos = sum(1 for e in recent_events if e.get("sentiment") == "positive")
        r_neu = sum(1 for e in recent_events if e.get("sentiment") == "neutral")
        data["recent_window"] = {
            "size": 20,
            "events": recent_events,
            "negative": r_neg,
            "positive": r_pos,
            "neutral": r_neu,
        }
        data["metrics"]["recent_negative_ratio"] = round(r_neg / max(len(recent_events), 1), 2)
    if "severity" not in data:
        h = data.get("health_score", 100)
        data["severity"] = "HEALTHY" if h >= 80 else ("WATCH" if h >= 60 else ("WARNING" if h >= 40 else "CRITICAL"))
    if "economic_risk" not in data:
        r = float(data.get("risk_score", 0.0))
        data["economic_risk"] = round(r * 0.82, 2) if r > 0 else 0.05
        data["cpa"] = round(1050.0 * (1.0 + data["economic_risk"] * 0.60), 2)

    return data


def save_demo_campaign(campaign_id: str, data: dict[str, Any]) -> None:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    target = get_campaign_path(campaign_id)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(target, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def process_demo_comment(
    campaign_id: str,
    comment_text: str,
    author: str = "Demo User",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Process a comment submission for an existing demo campaign.
    
    Returns (updated_campaign_state, processed_comment_details).
    """
    campaign = load_demo_campaign(campaign_id)

    classified = classify_text(comment_text)
    sentiment = classified["sentiment"]
    category = classified["category"]
    confidence = classified["confidence"]
    sentiment_score = classified.get("sentiment_score", 0.50)

    # 1. Update cumulative metrics
    metrics = campaign.setdefault("metrics", {})
    metrics["total_comments"] = metrics.get("total_comments", 0) + 1
    if sentiment == "positive":
        metrics["positive_comments"] = metrics.get("positive_comments", 0) + 1
    elif sentiment == "negative":
        metrics["negative_comments"] = metrics.get("negative_comments", 0) + 1
    else:
        metrics["neutral_comments"] = metrics.get("neutral_comments", 0) + 1

    if "complaint" in category:
        metrics["complaint_comments"] = metrics.get("complaint_comments", 0) + 1
    if category == "fatigue":
        metrics["fatigue_comments"] = metrics.get("fatigue_comments", 0) + 1
    if category == "mockery":
        metrics["mockery_comments"] = metrics.get("mockery_comments", 0) + 1

    total_comments = metrics["total_comments"]
    negative_comments = metrics["negative_comments"]
    metrics["negative_ratio"] = round(negative_comments / max(total_comments, 1), 2)

    now = datetime.now(timezone.utc).isoformat()
    comment_id = f"comment_{len(campaign.get('comments', [])) + 1:04d}"

    # 2. Update recent sliding window (size 20)
    rw = campaign.setdefault("recent_window", {"size": 20, "events": []})
    events_list = rw.setdefault("events", [])
    events_list.append({
        "comment_id": comment_id,
        "sentiment": sentiment,
        "category": category,
        "timestamp": now,
    })
    events_list = events_list[-20:]
    rw["events"] = events_list
    rw["size"] = 20

    recent_neg = sum(1 for e in events_list if e.get("sentiment") == "negative")
    recent_pos = sum(1 for e in events_list if e.get("sentiment") == "positive")
    recent_neu = sum(1 for e in events_list if e.get("sentiment") == "neutral")
    rw["negative"] = recent_neg
    rw["positive"] = recent_pos
    rw["neutral"] = recent_neu

    recent_negative_ratio = round(recent_neg / max(len(events_list), 1), 2)
    metrics["recent_negative_ratio"] = recent_negative_ratio

    # 3. Dynamic cumulative health score calculation
    old_health = campaign.get("health_score", 100)
    base_deltas = {
        "product_complaint": -13,
        "service_complaint": -14,
        "mockery": -11,
        "fatigue": -9,
        "spam": -6,
    }

    if sentiment == "negative":
        base_pressure = base_deltas.get(category, -8)
        accum_pressure = round(recent_negative_ratio * 4)
        impact = base_pressure - accum_pressure
        new_health = max(0, min(100, old_health + impact))
    elif sentiment == "positive":
        # Gradual recovery damped by accumulated negative pressure
        damping = max(0.25, 1.0 - 0.65 * recent_negative_ratio)
        impact = max(1, round(5 * damping))
        new_health = max(0, min(100, old_health + impact))
    else:
        impact = 0
        new_health = old_health

    new_risk = round((100 - new_health) / 100.0, 2)

    # 4. Severity derivation
    if new_health >= 80:
        new_severity = "HEALTHY"
    elif new_health >= 60:
        new_severity = "WATCH"
    elif new_health >= 40:
        new_severity = "WARNING"
    else:
        new_severity = "CRITICAL"

    # 5. Status derivation (ACTIVE, SOFT_REDUCED, PAUSED, BLOCKED)
    if new_health >= 50:
        new_status = "ACTIVE"
    elif new_health >= 25:
        new_status = "SOFT_REDUCED"
    else:
        new_status = "PAUSED"

    comment_entry = {
        "comment_id": comment_id,
        "timestamp": now,
        "author": author,
        "text": comment_text,
        "sentiment": sentiment,
        "sentiment_score": round(sentiment_score, 4),
        "category": category,
        "confidence": round(confidence, 4),
        "impact": impact,
        "health_score_after": new_health,
    }
    campaign.setdefault("comments", []).append(comment_entry)

    event_entry = {
        "event_id": f"evt_{len(campaign.get('events', [])) + 1}",
        "event_type": "COMMENT_INGESTED",
        "description": f"Processed {category.upper()} comment ({sentiment}). Health: {old_health} -> {new_health}",
        "previous_health": old_health,
        "new_health": new_health,
        "impact": impact,
        "previous_risk": campaign.get("risk_score", 0.0),
        "new_risk": new_risk,
        "severity": new_severity,
        "status": new_status,
        "timestamp": now,
    }
    campaign.setdefault("events", []).append(event_entry)

    new_econ_risk = round(min(0.95, new_risk * 0.82 + recent_negative_ratio * 0.12), 2) if new_risk > 0 else 0.05
    simulated_cpa = round(1050.0 * (1.0 + new_econ_risk * 0.60), 2)

    campaign["health_score"] = new_health
    campaign["risk_score"] = new_risk
    campaign["economic_risk"] = new_econ_risk
    campaign["cpa"] = simulated_cpa
    campaign["severity"] = new_severity
    campaign["status"] = new_status

    save_demo_campaign(campaign_id, campaign)

    return campaign, comment_entry


def print_banner(campaign_id: str, campaign_name: str = ""):
    sep = "=" * 80
    print(f"\n{BOLD}{CYAN}{sep}")
    print("   ADFATIGUERADAR — CAMPAIGN LIVE SIMULATION")
    name_suffix = f" ({campaign_name})" if campaign_name else ""
    print(f"   Campaign: {campaign_id}{name_suffix}")
    print(f"{sep}{RESET}\n")


def print_campaign_state(camp: dict[str, Any]):
    m = camp.get("metrics", {})
    status_color = GREEN if camp.get("status") == "ACTIVE" else (YELLOW if camp.get("status") == "SOFT_REDUCED" else RED)
    sev = camp.get("severity", "HEALTHY")
    sev_color = GREEN if sev == "HEALTHY" else (YELLOW if sev in ("WATCH", "WARNING") else RED)
    neg_ratio_pct = int(round(m.get("negative_ratio", 0.0) * 100))

    print(f"\n{BOLD}Campaign Metrics:{RESET}")
    print(f"  {BOLD}Total Comments:{RESET}       {m.get('total_comments', 0)}")
    print(f"  {BOLD}Negative Comments:{RESET}    {m.get('negative_comments', 0)}")
    print(f"  {BOLD}Positive Comments:{RESET}    {m.get('positive_comments', 0)}")
    print(f"  {BOLD}Negative Ratio:{RESET}       {neg_ratio_pct}%\n")
    print(f"{BOLD}Campaign State:{RESET}")
    print(f"  {BOLD}Health Score:{RESET} {camp.get('health_score')}")
    print(f"  {BOLD}Risk Score:{RESET}   {camp.get('risk_score'):.2f}")
    print(f"  {BOLD}Severity:{RESET}     {sev_color}{sev}{RESET}")
    print(f"  {BOLD}Status:{RESET}       {status_color}{camp.get('status')}{RESET}\n")


def interactive_loop(campaign_id: str):
    camp = load_demo_campaign(campaign_id)
    print_banner(campaign_id, camp.get("name", ""))

    print(f"{DIM}Loading weights...{RESET}")
    _get_nlp()
    print(f"{GREEN}[OK] Model loaded successfully.{RESET}\n")

    print_campaign_state(camp)

    print(f"{BOLD}Commands:{RESET}")
    print(f"  - Type or paste {BOLD}any real-world comment{RESET} and press Enter")
    print(f"  - Type {YELLOW}'status'{RESET} to display the current campaign state")
    print(f"  - Type {RED}'exit'{RESET} or {RED}'quit'{RESET} to exit\n")

    while True:
        try:
            prompt_str = f"{BOLD}[Campaign: {CYAN}{campaign_id}{RESET}{BOLD}] Enter comment > {RESET}"
            user_input = input(prompt_str).strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print(f"\n{CYAN}Exiting simulator. Goodbye!{RESET}\n")
                break

            if user_input.lower() == "status":
                current_camp = load_demo_campaign(campaign_id)
                print_campaign_state(current_camp)
                continue

            # Process comment
            updated_camp, comment_meta = process_demo_comment(campaign_id, user_input)

            sentiment = comment_meta["sentiment"]
            category = comment_meta["category"]
            confidence = comment_meta["confidence"]

            sent_color = GREEN if sentiment == "positive" else (RED if sentiment == "negative" else CYAN)
            _, cat_color, _ = CATEGORY_WEIGHTS.get(category, (0.0, RESET, ""))

            m = updated_camp.get("metrics", {})
            neg_ratio_pct = int(round(m.get("negative_ratio", 0.0) * 100))

            sev = updated_camp.get("severity", "HEALTHY")
            sev_color = GREEN if sev == "HEALTHY" else (YELLOW if sev in ("WATCH", "WARNING") else RED)
            st_color = GREEN if updated_camp["status"] == "ACTIVE" else (YELLOW if updated_camp["status"] == "SOFT_REDUCED" else RED)

            print(f"\n{BOLD}Comment:{RESET}")
            print(f"{user_input}\n")

            print(f"{BOLD}Sentiment:{RESET}  {sent_color}{sentiment}{RESET}")
            print(f"{BOLD}Category:{RESET}   {cat_color}{category}{RESET}")
            print(f"{BOLD}Confidence:{RESET} {confidence:.2f}\n")

            print(f"{BOLD}Campaign Metrics:{RESET}")
            print(f"  {BOLD}Total Comments:{RESET}       {m.get('total_comments', 0)}")
            print(f"  {BOLD}Negative Comments:{RESET}    {m.get('negative_comments', 0)}")
            print(f"  {BOLD}Positive Comments:{RESET}    {m.get('positive_comments', 0)}")
            print(f"  {BOLD}Negative Ratio:{RESET}       {neg_ratio_pct}%\n")

            print(f"{BOLD}Campaign State:{RESET}")
            print(f"  {BOLD}Health Score:{RESET} {updated_camp['health_score']}")
            print(f"  {BOLD}Audience Risk:{RESET} {updated_camp['risk_score']:.2f}")
            print(f"  {BOLD}Economic Risk:{RESET} {updated_camp.get('economic_risk', 0.05):.2f}")
            print(f"  {BOLD}Simulated CPA:{RESET} ₹{updated_camp.get('cpa', 1050.0):.0f}")
            print(f"  {BOLD}Severity:{RESET}     {sev_color}{sev}{RESET}")
            print(f"  {BOLD}Status:{RESET}       {st_color}{updated_camp['status']}{RESET}\n")

        except (KeyboardInterrupt, EOFError):
            print(f"\n{CYAN}Exiting simulator. Goodbye!{RESET}\n")
            break


def main():
    parser = argparse.ArgumentParser(description="AdFatigueRadar Demo Campaign Simulator")
    parser.add_argument("--campaign-id", required=False, default=None, help="Campaign ID to inspect or simulate")
    parser.add_argument("--comment", help="Comment text to submit in non-interactive batch mode")
    parser.add_argument("--author", default="Demo User", help="Comment author")
    parser.add_argument("--status", action="store_true", help="Print current campaign status JSON and exit")

    args = parser.parse_args()

    selected_campaign_id = args.campaign_id

    # If campaign-id was explicitly provided, verify it exists
    if selected_campaign_id:
        if not campaign_exists(selected_campaign_id):
            print(f"Error: demo campaign '{selected_campaign_id}' not initialized.", file=sys.stderr)
            sys.exit(1)
    else:
        # Check existing initialized campaigns in demo_data/campaigns/
        existing = list_existing_campaigns()

        if len(existing) == 0:
            print("AdFatigueRadar Demo Campaign Simulator")
            print("Waiting for a campaign...")
            print('Campaigns are initialized only when "+ Create Campaign" is clicked.')
            sys.exit(0)
        elif len(existing) == 1:
            selected_campaign_id = existing[0][0]
        else:
            print(f"{BOLD}{CYAN}AdFatigueRadar Demo Campaign Simulator{RESET}")
            print(f"{BOLD}Multiple initialized campaigns found:{RESET}")
            for idx, (cid, cname) in enumerate(existing, start=1):
                print(f"  [{idx}] {CYAN}{cid}{RESET} ({cname})")

            try:
                choice = input(f"\nSelect a campaign (1-{len(existing)} or ID): ").strip()
                if not choice:
                    selected_campaign_id = existing[0][0]
                elif choice.isdigit() and 1 <= int(choice) <= len(existing):
                    selected_campaign_id = existing[int(choice) - 1][0]
                elif campaign_exists(choice):
                    selected_campaign_id = choice
                else:
                    print(f"Error: Unknown campaign selection '{choice}'.", file=sys.stderr)
                    sys.exit(1)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                sys.exit(0)

    active_path = BASE_DIR / "demo_data" / "active_campaign.txt"
    try:
        active_path.write_text(selected_campaign_id, encoding="utf-8")
    except Exception:
        pass

    # If --comment was supplied via CLI argument, process once and exit
    if args.comment:
        updated, _ = process_demo_comment(selected_campaign_id, args.comment, args.author)
        print(f"\n[Updated Demo Campaign State: {selected_campaign_id}]")
        print(json.dumps(updated, indent=2))
        sys.exit(0)

    # If --status was supplied via CLI argument, print status and exit
    if args.status:
        camp = load_demo_campaign(selected_campaign_id)
        print(json.dumps(camp, indent=2))
        sys.exit(0)

    # Primary experience: Interactive REPL loop
    interactive_loop(selected_campaign_id)


if __name__ == "__main__":
    main()
