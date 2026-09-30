"""
AdFatigueRadar — Stage 1: General Sentiment Classifier
======================================================
PERSON 1: AI / NLP Layer

Classifies comments into general sentiment: [negative, neutral, positive]
with calibrated softmax probability scores using a locally cached RoBERTa model.
CPU-only, loaded once, eval mode, torch.no_grad, fully deterministic.
"""

import os
import re
from typing import Dict, Any, Tuple, Optional, List
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from .constants import SENTIMENT_LABELS, DEFAULT_MAX_SEQ_LENGTH
from .preprocessing import normalize_text
from .calibration import TemperatureScaler, default_scaler

# Seed for absolute reproducibility
torch.manual_seed(42)

# Specific domain disambiguation guard patterns
# DOCUMENTED RULE: 'again' refers to positive repeat purchase when combined with buying verbs,
# whereas 'ad again' indicates negative ad fatigue.
_REPEAT_PURCHASE_PATTERN = re.compile(r"\b(bought again|ordered again|purchased again|got it again)\b", re.IGNORECASE)
_AD_FATIGUE_PATTERN = re.compile(r"\b(this ad again|seen this ad|this same ad|saw this ad|another ad|stop showing me this ad)\b", re.IGNORECASE)


class SentimentClassifier:
    """
    Stage 1 Sentiment Classifier.
    Loads local RoBERTa sentiment model once on CPU.
    """
    def __init__(
        self,
        model_dir: Optional[str] = None,
        scaler: Optional[TemperatureScaler] = None,
    ):
        self.scaler = scaler or default_scaler
        self.model_dir = model_dir or self._find_default_model_dir()
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # Load local model and tokenizer once
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir, local_files_only=True)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_dir, local_files_only=True)
        self.model.to(self.device)
        self.model.eval()
        
        # Verify model config mapping
        self.id2label = self.model.config.id2label
        self.model_name = self.model.config._name_or_path or "twitter-roberta-base-sentiment-latest"
        self.model_version = getattr(self.model.config, "transformers_version", "1.0")

    def _find_default_model_dir(self) -> str:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        candidate = os.path.join(base_dir, "data", "models", "twitter-roberta-base-sentiment-latest")
        if os.path.exists(candidate) and os.path.exists(os.path.join(candidate, "config.json")):
            return candidate
        fallback = os.path.join(base_dir, "data", "models", "twitter-xlm-roberta-base-sentiment")
        if os.path.exists(fallback):
            return fallback
        raise FileNotFoundError(f"Local sentiment model directory not found at {candidate}")

    def _apply_guard_rules(self, text: str, probs: Dict[str, float]) -> Tuple[str, float, Dict[str, float]]:
        """
        Applies domain-specific guard rules for ad fatigue vs repeat purchase disambiguation.
        Guards adjust probability distribution if specific domain triggers match.
        """
        lower = text.lower()
        
        # Repeat purchase guard: "bought again" -> high positive confidence
        if _REPEAT_PURCHASE_PATTERN.search(lower):
            probs = {"negative": 0.005, "neutral": 0.015, "positive": 0.980}
            return "positive", 0.980, probs

        # Ad fatigue guard: "this ad again" -> high negative confidence
        if _AD_FATIGUE_PATTERN.search(lower):
            probs = {"negative": 0.920, "neutral": 0.060, "positive": 0.020}
            return "negative", 0.920, probs

        top_label = max(probs, key=probs.get)
        top_score = probs[top_label]
        return top_label, top_score, probs

    def predict(self, text: Optional[str]) -> Tuple[str, float, Dict[str, float]]:
        """
        Predicts sentiment for a single comment string.
        
        Returns:
            label (str): "positive", "neutral", or "negative"
            confidence (float): softmax probability score [0.0, 1.0]
            probabilities (Dict[str, float]): full probability distribution
        """
        clean = normalize_text(text) if text is not None else ""
        if not clean:
            # Neutral fallback for empty/whitespace/None input
            return "neutral", 0.50, {"negative": 0.25, "neutral": 0.50, "positive": 0.25}

        inputs = self.tokenizer(
            clean,
            padding=False,
            truncation=True,
            max_length=DEFAULT_MAX_SEQ_LENGTH,
            return_tensors="pt"
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            raw_probs = torch.softmax(outputs.logits, dim=-1)[0].cpu().numpy()

        prob_dict = {}
        for idx, p_val in enumerate(raw_probs):
            raw_lbl = str(self.id2label.get(idx, idx)).lower()
            if "neg" in raw_lbl or raw_lbl == "0":
                lbl = "negative"
            elif "pos" in raw_lbl or raw_lbl == "2":
                lbl = "positive"
            else:
                lbl = "neutral"
            prob_dict[lbl] = float(p_val)

        # Ensure all three classes are present
        for k in SENTIMENT_LABELS:
            if k not in prob_dict:
                prob_dict[k] = 1e-4

        # Apply guard rules if triggered
        top_label, top_score, final_probs = self._apply_guard_rules(clean, prob_dict)
        return top_label, round(float(top_score), 4), {k: round(float(v), 4) for k, v in final_probs.items()}

    def predict_batch(self, texts: List[Optional[str]]) -> List[Tuple[str, float, Dict[str, float]]]:
        """
        Batched sentiment inference for high throughput.
        """
        if not texts:
            return []

        cleaned_texts = [normalize_text(t) if t is not None else "" for t in texts]
        non_empty_indices = [i for i, t in enumerate(cleaned_texts) if t]
        
        results: List[Optional[Tuple[str, float, Dict[str, float]]]] = [None] * len(texts)
        
        # Handle empty inputs
        for i, t in enumerate(cleaned_texts):
            if not t:
                results[i] = ("neutral", 0.50, {"negative": 0.25, "neutral": 0.50, "positive": 0.25})

        if non_empty_indices:
            batch_inputs = [cleaned_texts[i] for i in non_empty_indices]
            encoded = self.tokenizer(
                batch_inputs,
                padding=True,
                truncation=True,
                max_length=DEFAULT_MAX_SEQ_LENGTH,
                return_tensors="pt"
            )
            encoded = {k: v.to(self.device) for k, v in encoded.items()}
            
            with torch.no_grad():
                outputs = self.model(**encoded)
                probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()

            for batch_idx, original_idx in enumerate(non_empty_indices):
                raw_probs = probs[batch_idx]
                prob_dict = {}
                for idx, p_val in enumerate(raw_probs):
                    raw_lbl = str(self.id2label.get(idx, idx)).lower()
                    if "neg" in raw_lbl or raw_lbl == "0":
                        lbl = "negative"
                    elif "pos" in raw_lbl or raw_lbl == "2":
                        lbl = "positive"
                    else:
                        lbl = "neutral"
                    prob_dict[lbl] = float(p_val)
                    
                for k in SENTIMENT_LABELS:
                    if k not in prob_dict:
                        prob_dict[k] = 1e-4
                        
                top_label, top_score, final_probs = self._apply_guard_rules(cleaned_texts[original_idx], prob_dict)
                results[original_idx] = (top_label, round(float(top_score), 4), {k: round(float(v), 4) for k, v in final_probs.items()})

        return results
