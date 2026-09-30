"""
AdFatigueRadar — Stage 1: General Sentiment Classifier
======================================================
PERSON 1: AI / NLP Layer

Classifies comments into general sentiment: [positive, neutral, negative]
with calibrated probability score. Independent from custom 8-class taxonomy.
"""

import os
import re
from typing import Dict, Any, Tuple, Optional, List
import numpy as np

from .preprocessing import normalize_text
from .calibration import TemperatureScaler, default_scaler

# Sentiment Label Mapping
SENTIMENT_LABELS = ("negative", "neutral", "positive")

# Lexicons and semantic patterns for fast rule-assisted sentiment modeling & fallback
_POSITIVE_PATTERNS = [
    r"\b(love|great|awesome|best|amazing|fire|goat|super|good|solid|clean|worth it|recommend|obsessed|perfect|nice|cool|w|valid)\b",
    r"(❤️|🔥|😍|🙌|👍|✨|💯|👏)",
    r"\b(bought again|ordered again|purchased again|got mine|love mine|rizz|let him cook|he cookin|sigma|cinema)\b",
]

_NEGATIVE_PATTERNS = [
    r"\b(scam|trash|garbage|hate|horrible|terrible|awful|worst|broken|broke|fake|ruined|waste|useless|stolen|cheat|defective|disappointed)\b",
    r"\b(never again|stop showing|annoying|sick of|tired of|unfollow|overpriced|refund|ripoff|never received|still not received|ghosted)\b",
    r"\b(crypto|telegram|whatsapp me|dm me|free followers|make money fast|link in bio)\b",
    r"(😡|🤬|🤮|🤢|💩|👎|📉)",
]

_MOCKERY_PATTERNS = [
    r"\b(the acting|bro think he|who approved this|cringe|aint no way|npc behavior|clown show|delusional|acting is wild|budget ran out)\b",
    r"\b(who made this ad|voiceover is so bad|fake reaction|ai generated actor)\b",
    r"(🤡|💀|😭|🤣|🤦‍♂️|🤦‍♀️)",
]


class SentimentClassifier:
    """
    Stage 1 Sentiment Classifier.
    Employs an ultra-fast, deterministic semantic sentiment analyzer by default,
    with optional local HuggingFace Transformer loading (cardiffnlp/twitter-roberta-base-sentiment-latest)
    when use_transformer=True.
    """
    def __init__(
        self,
        model_dir: Optional[str] = None,
        scaler: Optional[TemperatureScaler] = None,
        use_transformer: bool = False
    ):
        self.scaler = scaler or default_scaler
        self.use_transformer = use_transformer or bool(os.environ.get("USE_TRANSFORMER_NLP", False))
        self.model_dir = model_dir
        self.pipeline = None
        self._initialized = False

    def _ensure_model_loaded(self):
        """Lazy load transformer pipeline only when enabled and required."""
        if self._initialized or not self.use_transformer:
            self._initialized = True
            return

        self._initialized = True
        candidates = []
        if self.model_dir:
            candidates.append(self.model_dir)
        
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        candidates.extend([
            os.path.join(base_dir, "data", "models", "twitter-roberta-base-sentiment-latest"),
            os.path.join(base_dir, "data", "models", "twitter-xlm-roberta-base-sentiment"),
        ])

        for path in candidates:
            if os.path.exists(path) and os.path.exists(os.path.join(path, "config.json")):
                try:
                    from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
                    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
                    model = AutoModelForSequenceClassification.from_pretrained(path, local_files_only=True)
                    self.pipeline = pipeline(
                        "text-classification",
                        model=model,
                        tokenizer=tokenizer,
                        top_k=None,
                        device=-1  # CPU safe
                    )
                    return
                except Exception:
                    continue

    def _fast_lexical_sentiment(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Deterministic, fast lexical & pattern-based sentiment inference.
        Ensures consistent, instant execution on CPU with zero cold-start delay.
        """
        clean = normalize_text(text)
        lower = clean.lower()
        
        pos_score = sum(len(re.findall(p, lower)) for p in _POSITIVE_PATTERNS)
        neg_score = sum(len(re.findall(p, lower)) for p in _NEGATIVE_PATTERNS)
        mock_score = sum(len(re.findall(p, lower)) for p in _MOCKERY_PATTERNS)
        
        # Specific positive overrides
        if "bought again" in lower or "ordered again" in lower:
            pos_score += 3
            neg_score = max(0, neg_score - 2)
            
        # Fatigue language is negative sentiment
        if "this ad again" in lower or "stop showing" in lower or "seen this 100 times" in lower:
            neg_score += 3

        # Convert to pseudo-logits
        logits = [
            0.5 + 1.2 * neg_score + 0.8 * mock_score,  # negative
            1.0,                                      # neutral baseline
            0.5 + 1.4 * pos_score                     # positive
        ]
        
        calibrated = self.scaler.calibrate_logits(logits)
        probs = {
            "negative": calibrated[0],
            "neutral": calibrated[1],
            "positive": calibrated[2]
        }
        
        top_label = max(probs, key=probs.get)
        top_score = probs[top_label]
        return top_label, top_score, probs

    def predict(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Predicts sentiment for a single comment.
        Returns: (label: str, confidence: float, class_probabilities: Dict[str, float])
        """
        clean = normalize_text(text)
        if not clean:
            return "neutral", 0.50, {"negative": 0.25, "neutral": 0.50, "positive": 0.25}

        self._ensure_model_loaded()

        if self.pipeline:
            try:
                # HF pipeline output format: [[{'label': 'negative', 'score': 0.9}, ...]]
                results = self.pipeline(clean[:512])[0]
                prob_dict = {}
                for item in results:
                    lbl = item["label"].lower()
                    if "neg" in lbl:
                        lbl = "negative"
                    elif "pos" in lbl:
                        lbl = "positive"
                    else:
                        lbl = "neutral"
                    prob_dict[lbl] = float(item["score"])
                    
                # Ensure all 3 classes exist
                for k in SENTIMENT_LABELS:
                    if k not in prob_dict:
                        prob_dict[k] = 1e-4
                        
                calibrated = self.scaler.calibrate_dict(prob_dict)
                top_label = max(calibrated, key=calibrated.get)
                return top_label, calibrated[top_label], calibrated
            except Exception:
                pass

        return self._fast_lexical_sentiment(clean)

    def predict_batch(self, texts: List[str]) -> List[Tuple[str, float, Dict[str, float]]]:
        """Batched sentiment inference."""
        return [self.predict(t) for t in texts]
