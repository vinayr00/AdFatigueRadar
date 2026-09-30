"""
AdFatigueRadar — PII Sanitization Module
=======================================
PERSON 1: AI / NLP Layer (Phase 1 Remediation)

Deterministic PII sanitization for real-world comment ingestion.
Replaces personally identifiable tokens with standard semantic placeholders:
  - Emails: [email]
  - Phone Numbers: [phone]
  - Handles / User Mentions: [user]
  - URLs: [url]
  - IP Addresses: [ip]
  - Account / Payment IDs: [account_id]

Preserves:
  - Emojis (😂, 💀, 🤡, 🔥, 😡, etc.)
  - Punctuation & casing
  - Slang & Hinglish / Telugu transliterations
  - Typos & informal internet grammar
"""

import re
import json
import os
from typing import Tuple, Dict, Any, List, Optional

# Regex patterns for deterministic PII replacement
# Email
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

# Phone Numbers (International, US/India formats, e.g. +91 9876543210, (123) 456-7890, 123-456-7890)
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,5}[-.\s]?\d{3,5}\b"
)
# Filter out false positive numbers (e.g., single dates, small quantities, 2-4 digit numbers)
def _is_probable_phone(match_str: str) -> bool:
    digits = re.sub(r"\D", "", match_str)
    # Most valid phone numbers have 7 to 15 digits
    return 7 <= len(digits) <= 15

# IPv4 and IPv6
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_IPV6_RE = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b")

# URLs
_URL_RE = re.compile(r"https?://\S+|www\.\S+|t\.me/\S+|wa\.me/\S+")

# Usernames / Handles (@user, u/user, r/user)
_USER_HANDLE_RE = re.compile(r"(?<=^|(?<=\s))@[A-Za-z0-9_.-]+|(?<=^|(?<=\s))[ur]/[A-Za-z0-9_.-]+")

# Payment card numbers / Long account IDs (13-19 digits, possibly with dashes or spaces)
_ACCOUNT_ID_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


class PIISanitizer:
    """
    Deterministic PII Sanitizer and Auditor.
    """
    def __init__(self, version: str = "pii-sanitizer-v1.0"):
        self.version = version
        self.stats = {
            "email_count": 0,
            "phone_count": 0,
            "url_count": 0,
            "user_handle_count": 0,
            "ip_count": 0,
            "account_id_count": 0,
            "total_records_processed": 0,
            "records_with_pii": 0,
        }

    def sanitize(self, text: str) -> Tuple[str, Dict[str, int]]:
        """
        Sanitizes a single text string and returns (sanitized_text, match_counts).
        """
        if not text:
            return "", {}

        record_counts = {
            "email": 0,
            "phone": 0,
            "url": 0,
            "user_handle": 0,
            "ip": 0,
            "account_id": 0,
        }

        sanitized = text

        # 1. URLs
        urls = _URL_RE.findall(sanitized)
        if urls:
            record_counts["url"] += len(urls)
            sanitized = _URL_RE.sub("[url]", sanitized)

        # 2. Emails
        emails = _EMAIL_RE.findall(sanitized)
        if emails:
            record_counts["email"] += len(emails)
            sanitized = _EMAIL_RE.sub("[email]", sanitized)

        # 3. User Handles
        handles = _USER_HANDLE_RE.findall(sanitized)
        if handles:
            record_counts["user_handle"] += len(handles)
            sanitized = _USER_HANDLE_RE.sub("[user]", sanitized)

        # 4. IP Addresses
        ips = _IPV4_RE.findall(sanitized) + _IPV6_RE.findall(sanitized)
        if ips:
            record_counts["ip"] += len(ips)
            sanitized = _IPV4_RE.sub("[ip]", sanitized)
            sanitized = _IPV6_RE.sub("[ip]", sanitized)

        # 5. Account IDs / Cards
        account_matches = _ACCOUNT_ID_RE.findall(sanitized)
        valid_accounts = [m for m in account_matches if len(re.sub(r"\D", "", m)) >= 13]
        if valid_accounts:
            record_counts["account_id"] += len(valid_accounts)
            for acc in valid_accounts:
                sanitized = sanitized.replace(acc, "[account_id]")

        # 6. Phone Numbers (after URLs, emails, and account IDs are already stripped)
        phones = _PHONE_RE.findall(sanitized)
        valid_phones = [p for p in phones if _is_probable_phone(p)]
        if valid_phones:
            record_counts["phone"] += len(valid_phones)
            for phone in valid_phones:
                sanitized = sanitized.replace(phone, "[phone]")

        # Update running aggregate stats
        self.stats["total_records_processed"] += 1
        has_pii = any(v > 0 for v in record_counts.values())
        if has_pii:
            self.stats["records_with_pii"] += 1
            self.stats["email_count"] += record_counts["email"]
            self.stats["phone_count"] += record_counts["phone"]
            self.stats["url_count"] += record_counts["url"]
            self.stats["user_handle_count"] += record_counts["user_handle"]
            self.stats["ip_count"] += record_counts["ip"]
            self.stats["account_id_count"] += record_counts["account_id"]

        return sanitized, record_counts

    def generate_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates and optionally saves data/reports/pii_report.json.
        Never outputs raw PII strings.
        """
        report = {
            "pii_sanitizer_version": self.version,
            "summary": {
                "total_records_processed": self.stats["total_records_processed"],
                "records_with_pii": self.stats["records_with_pii"],
                "pii_detection_rate": round(
                    self.stats["records_with_pii"] / max(self.stats["total_records_processed"], 1), 4
                ),
            },
            "detections_by_category": {
                "email": self.stats["email_count"],
                "phone": self.stats["phone_count"],
                "url": self.stats["url_count"],
                "user_handle": self.stats["user_handle_count"],
                "ip": self.stats["ip_count"],
                "account_id": self.stats["account_id_count"],
            },
            "placeholders_used": {
                "email": "[email]",
                "phone": "[phone]",
                "url": "[url]",
                "user_handle": "[user]",
                "ip": "[ip]",
                "account_id": "[account_id]",
            }
        }
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
        return report
