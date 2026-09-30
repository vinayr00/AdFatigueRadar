"""
AdFatigueRadar — Stage 2: 8-Class Ad-Fatigue Taxonomy Classifier
================================================================
PERSON 1: AI / NLP Layer

Classifies comments into the frozen 8-class taxonomy:
  - product_complaint
  - service_complaint
  - fatigue
  - mockery
  - spam
  - banter_meme
  - neutral
  - positive

Implements the critical 'again' disambiguation rule, mockery vs banter separation,
and confidence-gated critical complaint identification.
"""

import re
from typing import Dict, Any, Tuple, List, Optional

from . import (
    TAXONOMY_CATEGORIES,
    CRITICAL_COMPLAINT_CATEGORIES,
    CRITICAL_COMPLAINT_CONFIDENCE_THRESHOLD,
)
from .preprocessing import normalize_text, extract_features_meta
from .calibration import TemperatureScaler, default_scaler


# Pattern rules for category scoring and disambiguation
_FATIGUE_PATTERNS = [
    r"\b(this ad again|seen this ad|this same ad|saw this ad|another ad|stop showing|every 5 mins|tired of seeing|why is this on my feed|fyp again|haunting my feed|5th time seeing|again and again and again|unskippable ad|every single day|sick of this commercial)\b",
    r"\b(bro this ad|ad again|stop giving me this ad|seen this 100 times|blocking this ad|report this ad)\b",
]

_PRODUCT_COMPLAINT_PATTERNS = [
    r"\b(broke on day|doesn't work|cheap plastic|terrible quality|poor quality|fell apart|stopped working|fake product|defective|ruined|horrible material|waste of money|completely broken|malfunction|does not work|broke immediately|scam product)\b",
    r"\b(burnt out|smells bad|leaking|damaged item|doesnt turn on|useless product|horrible design|snapped in half|poor steel|battery expanded)\b",
]

_SERVICE_COMPLAINT_PATTERNS = [
    r"\b(never arrived|still haven't received|waiting 3 weeks|shipping took|lost package|tracking not updating|customer support won't reply|no response from support|charged twice|refused refund|where is my order|never got mine|no refund|stole my money|billing issue|scammed me)\b",
    r"\b(support is useless|unauthorized charge|cant track order|delivery failed|never delivered|support refuses|issue a refund|refund or reply|ordered 3 weeks ago|still waiting on my refund|sent the wrong item|overcharged|ghosted my)\b",
    r"\b(customer support|customer service|shipping delay|delivery took|package was marked|double charged|refuses to issue)\b",
]

_MOCKERY_PATTERNS = [
    r"\b(the acting|bro think he|who approved this|cringe|aint no way|npc behavior|clown show|delusional|acting is wild|budget ran out|bro tried so hard|what is this commercial|roast|who made this ad|voiceover is so bad|fake reaction|ai generated actor)\b",
    r"(🤡|💀|😭|🤣|🤦‍♂️|🤦‍♀️)",
]

_SPAM_PATTERNS = [
    r"\b(check out my profile|click link in bio|crypto|forex|free followers|follow for follow|dm me to earn|telegram|whatsapp|promo code in bio|make money fast|whatsapp me|invest with|dm @)\b",
    r"(t\.me/|bit\.ly/|wa\.me/)",
]

_BANTER_MEME_PATTERNS = [
    r"\b(bro got that|rizz|skibidi|fr fr|nah he cookin|let him cook|bro really said|me at 3am|the design is very human|broski|main character|emotional damage|real|sigma|valid|caught in 4k)\b",
    r"\b(bro took it personally|bro think|i can't even|blud|bro is living in)\b",
]

_POSITIVE_PATTERNS = [
    r"\b(bought again|ordered again|purchased again|love it|amazing|best purchase|obsessed|10/10|worth every penny|so good|super fast delivery|great quality|highly recommend|just ordered|cant wait to get mine|got mine yesterday)\b",
    r"(❤️|🔥|😍|🙌|✨|💯)",
]

_NEUTRAL_INQUIRY_PATTERNS = [
    r"\b(how much|where can i buy|is this available|international shipping|what sizes|link please|price\?|does this come in|compatible with|restock date)\b",
    r"^@\w+(\s+@\w+)*$",  # Friend tagging only
]


class TaxonomyClassifier:
    """
    Stage 2 Custom Ad-Fatigue Taxonomy Classifier.
    Evaluates contextual signals, handles nuanced edge-cases, calibrates probabilities,
    and determines critical complaint candidacy.
    """
    def __init__(self, scaler: Optional[TemperatureScaler] = None):
        self.scaler = scaler or default_scaler

    def _score_patterns(self, text: str, lower: str, meta: Dict[str, Any]) -> Dict[str, float]:
        """Calculates raw evidence scores for each of the 8 taxonomy classes."""
        scores = {cat: 0.10 for cat in TAXONOMY_CATEGORIES}  # Base prior
        
        # 1. Product Complaints
        for pat in _PRODUCT_COMPLAINT_PATTERNS:
            if re.search(pat, lower):
                scores["product_complaint"] += 3.5

        # 2. Service Complaints
        for pat in _SERVICE_COMPLAINT_PATTERNS:
            if re.search(pat, lower):
                scores["service_complaint"] += 3.5

        # 3. Ad Fatigue vs Repeat Purchase Disambiguation
        # Rule: 'again' means fatigue ONLY when repeated ad exposure is indicated.
        if meta.get("has_again"):
            # Check if repeat purchase/satisfaction
            if any(re.search(p, lower) for p in [r"\bbought again\b", r"\bordered again\b", r"\bpurchased again\b", r"\bgot it again\b"]):
                scores["positive"] += 4.0
                scores["fatigue"] = 0.01
            elif any(re.search(p, lower) for p in [r"\b(this|the|same|another)\s+ad\s+again\b", r"\bbro\s+(this\s+)?ad\s+again\b", r"\bon\s+my\s+feed\s+again\b"]):
                scores["fatigue"] += 4.5
            elif meta.get("has_ad_reference"):
                scores["fatigue"] += 3.0
            else:
                # Ambiguous 'again' without ad context - bias to neutral/fatigue depending on tone
                if "love" in lower or "good" in lower:
                    scores["positive"] += 2.5
                else:
                    scores["fatigue"] += 1.5

        for pat in _FATIGUE_PATTERNS:
            if re.search(pat, lower):
                scores["fatigue"] += 3.0

        # 4. Mockery vs Banter
        for pat in _MOCKERY_PATTERNS:
            if re.search(pat, lower):
                scores["mockery"] += 2.8

        for pat in _BANTER_MEME_PATTERNS:
            if re.search(pat, lower):
                scores["banter_meme"] += 3.0

        # Disambiguate mockery vs banter:
        # If joke is specifically attacking the actor/script/company ad = mockery
        if meta.get("has_ad_reference") and ("acting" in lower or "commercial" in lower or "clown" in lower or "cringe" in lower):
            scores["mockery"] += 2.0
            scores["banter_meme"] = max(0.1, scores["banter_meme"] - 1.5)

        # 5. Spam
        for pat in _SPAM_PATTERNS:
            if re.search(pat, lower):
                scores["spam"] += 4.0

        # 6. Positive
        for pat in _POSITIVE_PATTERNS:
            if re.search(pat, lower):
                scores["positive"] += 2.5

        # 7. Neutral / Inquiries
        for pat in _NEUTRAL_INQUIRY_PATTERNS:
            if re.search(pat, lower):
                scores["neutral"] += 2.5
                
        if meta.get("has_question") and scores["product_complaint"] < 1.0 and scores["service_complaint"] < 1.0:
            scores["neutral"] += 1.5

        return scores

    def classify(self, text: str, sentiment_hint: Optional[str] = None) -> Tuple[str, float, bool, Dict[str, float]]:
        """
        Classifies comment text into one of the 8 taxonomy classes.
        
        Returns:
            category (str): Top predicted category.
            confidence (float): Calibrated confidence score [0.0, 1.0].
            critical_complaint (bool): Whether this satisfies critical complaint threshold.
            probabilities (Dict[str, float]): Calibrated probability distribution over all 8 classes.
        """
        clean = normalize_text(text)
        if not clean:
            probs = {cat: 1.0 / len(TAXONOMY_CATEGORIES) for cat in TAXONOMY_CATEGORIES}
            return "neutral", round(probs["neutral"], 4), False, probs

        lower = clean.lower()
        meta = extract_features_meta(clean)
        raw_scores = self._score_patterns(clean, lower, meta)

        # Apply sentiment hint alignment
        if sentiment_hint == "positive" and raw_scores["positive"] > 0.5:
            raw_scores["positive"] += 1.0
        elif sentiment_hint == "negative":
            # Negative hint boosts complaint, fatigue, or mockery
            if raw_scores["fatigue"] > 1.0:
                raw_scores["fatigue"] += 1.0
            if raw_scores["product_complaint"] > 1.0:
                raw_scores["product_complaint"] += 1.0
            if raw_scores["service_complaint"] > 1.0:
                raw_scores["service_complaint"] += 1.0

        # Convert scores to pseudo-logits and calibrate
        logits = [raw_scores[cat] for cat in TAXONOMY_CATEGORIES]
        calibrated_probs = self.scaler.calibrate_logits(logits)
        prob_dict = {cat: prob for cat, prob in zip(TAXONOMY_CATEGORIES, calibrated_probs)}

        # Find top class
        top_cat = max(prob_dict, key=prob_dict.get)
        confidence = prob_dict[top_cat]

        # Critical Complaint Verification
        # Eligible: product_complaint or service_complaint WITH confidence >= 0.85
        # Keyword alone without meeting the calibrated confidence threshold is NOT critical.
        is_critical = (
            top_cat in CRITICAL_COMPLAINT_CATEGORIES
            and confidence >= CRITICAL_COMPLAINT_CONFIDENCE_THRESHOLD
        )

        return top_cat, round(confidence, 4), is_critical, prob_dict
