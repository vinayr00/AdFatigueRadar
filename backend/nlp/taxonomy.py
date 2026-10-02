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

Uses RoBERTa sentence embeddings + LogisticRegression head + fitted TemperatureScaler.
Preserves explicit 'again' disambiguation guard rules.
Protects against low-confidence / unknown / non-English input tie-break bugs with neutral fallback.
"""

import os
import re
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
import torch
import joblib
from transformers import AutoModel, AutoTokenizer

from .constants import (
    TAXONOMY_CATEGORIES,
    CRITICAL_COMPLAINT_CATEGORIES,
    CRITICAL_COMPLAINT_CONFIDENCE_THRESHOLD,
    LOW_CONFIDENCE_FALLBACK_THRESHOLD,
    DEFAULT_MAX_SEQ_LENGTH,
)
from .preprocessing import normalize_text
from .calibration import TemperatureScaler, default_scaler
from .model_loader import resolve_local_transformer_dir

# Seed for deterministic evaluation
torch.manual_seed(42)

# Specific domain disambiguation guard patterns
_REPEAT_PURCHASE_PATTERN = re.compile(r"\b(bought again|ordered again|purchased again|got it again|reordered)\b", re.IGNORECASE)
_AD_FATIGUE_PATTERN = re.compile(r"\b(this ad again|seen this ad|this same ad|saw this ad|another ad|stop showing me this ad|on my feed again)\b", re.IGNORECASE)


class TaxonomyClassifier:
    """
    Stage 2 Custom Ad-Fatigue Taxonomy Classifier.
    Integrates local RoBERTa embedding backbone with a trained, temperature-calibrated linear head.
    """
    def __init__(
        self,
        model_dir: Optional[str] = None,
        artifact_path: Optional[str] = None,
        scaler: Optional[TemperatureScaler] = None,
    ):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.model_dir = model_dir or os.path.join(base_dir, "data", "models", "twitter-roberta-base-sentiment-latest")
        self.artifact_path = artifact_path or os.path.join(os.path.dirname(__file__), "artifacts", "taxonomy_model.joblib")
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # Load embedding backbone
        self.model_dir = resolve_local_transformer_dir(self.model_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir, local_files_only=True)
        self.model = AutoModel.from_pretrained(self.model_dir, local_files_only=True)
        self.model.to(self.device)
        self.model.eval()

        if not os.path.exists(self.artifact_path):
            raise FileNotFoundError(
                f"Trained taxonomy artifact not found at '{self.artifact_path}'. "
                f"Run 'python backend/nlp/train_models.py' from the repository root to generate it deterministically."
            )
            
        artifact = joblib.load(self.artifact_path)
        self.clf = artifact["classifier"]
        fitted_temperature = float(artifact.get("temperature", 1.0))
        self.scaler = scaler or TemperatureScaler(temperature=fitted_temperature)
        self.categories = list(TAXONOMY_CATEGORIES)
        self.cat_to_idx = {cat: i for i, cat in enumerate(self.categories)}

    def _embed_texts(self, texts: List[str]) -> np.ndarray:
        """Extract mean-pooled embeddings across non-masked token representations."""
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=DEFAULT_MAX_SEQ_LENGTH,
            return_tensors="pt"
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            out = self.model(**inputs)
            mask = inputs["attention_mask"].unsqueeze(-1).expand(out.last_hidden_state.size()).float()
            sum_emb = torch.sum(out.last_hidden_state * mask, 1)
            sum_mask = torch.clamp(mask.sum(1), min=1e-9)
            embeddings = (sum_emb / sum_mask).cpu().numpy()
        return embeddings

    def _apply_guard_rules(
        self,
        clean_text: str,
        probs: Dict[str, float]
    ) -> Tuple[str, float, bool, Dict[str, float]]:
        """
        Applies documented domain guard rules:
        - 'bought again' / 'ordered again' -> positive repeat purchase
        - 'this ad again' -> ad fatigue
        - Low confidence fallback -> neutral
        """
        lower = clean_text.lower()

        # Repeat purchase guard: overrides to positive
        if _REPEAT_PURCHASE_PATTERN.search(lower):
            probs = {cat: 0.001 for cat in self.categories}
            probs["positive"] = 0.992
            return "positive", 0.992, False, probs

        # Ad fatigue guard: overrides to fatigue
        if _AD_FATIGUE_PATTERN.search(lower):
            probs = {cat: 0.001 for cat in self.categories}
            probs["fatigue"] = 0.995
            return "fatigue", 0.995, False, probs

        top_cat = max(probs, key=probs.get)
        confidence = probs[top_cat]

        # Low-confidence / uncertainty fallback: if top prediction is below threshold, fallback to neutral
        if confidence < LOW_CONFIDENCE_FALLBACK_THRESHOLD:
            top_cat = "neutral"

        is_critical = (
            top_cat in CRITICAL_COMPLAINT_CATEGORIES
            and confidence >= CRITICAL_COMPLAINT_CONFIDENCE_THRESHOLD
        )
        return top_cat, round(confidence, 4), is_critical, probs

    def classify(
        self,
        text: Optional[str],
        sentiment_hint: Optional[str] = None
    ) -> Tuple[str, float, bool, Dict[str, float]]:
        """
        Classifies comment text into one of the 8 taxonomy classes.
        
        Returns:
            category (str): Top predicted taxonomy category.
            confidence (float): Calibrated confidence score [0.0, 1.0].
            critical_complaint (bool): True iff category in {product, service}_complaint AND confidence >= 0.85.
            probabilities (Dict[str, float]): Full calibrated probability distribution.
        """
        clean = normalize_text(text) if text is not None else ""
        if not clean:
            # Deterministic uniform prior with neutral fallback for empty/whitespace/None
            uniform = round(1.0 / len(self.categories), 4)
            probs = {cat: uniform for cat in self.categories}
            return "neutral", uniform, False, probs

        emb = self._embed_texts([clean])
        logits = self.clf.decision_function(emb)[0]
        calibrated_probs = self.scaler.calibrate_logits(logits)
        
        prob_dict = {cat: float(p) for cat, p in zip(self.categories, calibrated_probs)}
        return self._apply_guard_rules(clean, prob_dict)

    def classify_batch(
        self,
        texts: List[Optional[str]]
    ) -> List[Tuple[str, float, bool, Dict[str, float]]]:
        """
        Batched taxonomy classification for high throughput.
        """
        if not texts:
            return []

        cleaned_texts = [normalize_text(t) if t is not None else "" for t in texts]
        non_empty_indices = [i for i, t in enumerate(cleaned_texts) if t]
        
        results: List[Optional[Tuple[str, float, bool, Dict[str, float]]]] = [None] * len(texts)
        uniform = round(1.0 / len(self.categories), 4)
        
        for i, t in enumerate(cleaned_texts):
            if not t:
                results[i] = ("neutral", uniform, False, {cat: uniform for cat in self.categories})

        if non_empty_indices:
            batch_texts = [cleaned_texts[i] for i in non_empty_indices]
            embeddings = self._embed_texts(batch_texts)
            all_logits = self.clf.decision_function(embeddings)
            
            for batch_idx, original_idx in enumerate(non_empty_indices):
                logits = all_logits[batch_idx]
                calibrated_probs = self.scaler.calibrate_logits(logits)
                prob_dict = {cat: float(p) for cat, p in zip(self.categories, calibrated_probs)}
                results[original_idx] = self._apply_guard_rules(cleaned_texts[original_idx], prob_dict)

        return results
