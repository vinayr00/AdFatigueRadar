"""
AdFatigueRadar — CardiffNLP Auxiliary Signal Extractors
======================================================
PERSON 1: AI / NLP Layer (Phase 1 Remediation)

Provides isolated, standalone wrappers for the three CardiffNLP pretrained models:
1. twitter-roberta-base-sentiment-latest (English 3-class sentiment: negative, neutral, positive)
2. twitter-roberta-base-irony (English 2-class irony: non_irony, irony)
3. twitter-xlm-roberta-base-sentiment (Multilingual 3-class sentiment: negative, neutral, positive)

IMPORTANT ARCHITECTURAL CONSTRAINTS:
- These models provide AUXILIARY signals and evaluation benchmarks.
- They do NOT replace or overwrite the primary 8-class AdFatigue taxonomy.
- The irony model is NOT an 8-class taxonomy classifier.
- English sentiment is not assumed to support low-resource/regional dialects without experimental testing.
- XLM-R multilingual sentiment was fine-tuned on 8 languages (ar, en, fr, de, hi, it, es, pt);
  its accuracy on Hindi, Telugu transliterations, and code-switched Hinglish is evaluated empirically.
"""

import os
import re
from typing import Dict, Any, Optional, List, Tuple
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Standard CardiffNLP Twitter text preprocessing placeholder helper
def preprocess_for_twitter_roberta(text: str) -> str:
    """
    Applies standard Twitter model preprocessing expected by CardiffNLP RoBERTa:
    - User mentions -> @user
    - Web links/URLs -> http
    Preserves emojis, punctuation, casing, and word tokens.
    """
    if not text:
        return ""
    new_text = []
    for t in text.split(" "):
        t = "@user" if t.startswith("@") and len(t) > 1 else t
        t = "http" if t.startswith("http://") or t.startswith("https://") else t
        new_text.append(t)
    return " ".join(new_text).strip()


class CardiffNLPSignals:
    """
    Unified manager for CardiffNLP auxiliary models.
    Loads models on CPU in eval mode with torch.no_grad().
    """
    def __init__(
        self,
        sentiment_dir: Optional[str] = None,
        irony_dir: Optional[str] = None,
        multilingual_dir: Optional[str] = None,
        device: Optional[str] = None,
    ):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        models_root = os.path.join(base_dir, "data", "models")
        
        self.sentiment_dir = sentiment_dir or os.path.join(models_root, "twitter-roberta-base-sentiment-latest")
        self.irony_dir = irony_dir or os.path.join(models_root, "twitter-roberta-base-irony")
        self.multilingual_dir = multilingual_dir or os.path.join(models_root, "twitter-xlm-roberta-base-sentiment")
        
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        
        self._sentiment_tokenizer = None
        self._sentiment_model = None
        self._irony_tokenizer = None
        self._irony_model = None
        self._multilingual_tokenizer = None
        self._multilingual_model = None

    # Lazy loading to optimize memory and startup latency
    @property
    def sentiment_model(self):
        if self._sentiment_model is None:
            self._sentiment_tokenizer = AutoTokenizer.from_pretrained(self.sentiment_dir, local_files_only=True)
            self._sentiment_model = AutoModelForSequenceClassification.from_pretrained(self.sentiment_dir, local_files_only=True)
            self._sentiment_model.to(self.device)
            self._sentiment_model.eval()
        return self._sentiment_model

    @property
    def sentiment_tokenizer(self):
        if self._sentiment_tokenizer is None:
            _ = self.sentiment_model
        return self._sentiment_tokenizer

    @property
    def irony_model(self):
        if self._irony_model is None:
            self._irony_tokenizer = AutoTokenizer.from_pretrained(self.irony_dir, local_files_only=True)
            self._irony_model = AutoModelForSequenceClassification.from_pretrained(self.irony_dir, local_files_only=True)
            self._irony_model.to(self.device)
            self._irony_model.eval()
        return self._irony_model

    @property
    def irony_tokenizer(self):
        if self._irony_tokenizer is None:
            _ = self.irony_model
        return self._irony_tokenizer

    @property
    def multilingual_model(self):
        if self._multilingual_model is None:
            self._multilingual_tokenizer = AutoTokenizer.from_pretrained(self.multilingual_dir, local_files_only=True)
            self._multilingual_model = AutoModelForSequenceClassification.from_pretrained(self.multilingual_dir, local_files_only=True)
            self._multilingual_model.to(self.device)
            self._multilingual_model.eval()
        return self._multilingual_model

    @property
    def multilingual_tokenizer(self):
        if self._multilingual_tokenizer is None:
            _ = self.multilingual_model
        return self._multilingual_tokenizer

    def predict_sentiment_en(self, text: str) -> Dict[str, Any]:
        """
        English Twitter RoBERTa Sentiment Classification.
        Returns: { 'label': 'negative'|'neutral'|'positive', 'score': float, 'probabilities': dict }
        """
        prep_text = preprocess_for_twitter_roberta(text)
        if not prep_text:
            return {"label": "neutral", "score": 0.333, "probabilities": {"negative": 0.333, "neutral": 0.334, "positive": 0.333}}
        
        inputs = self.sentiment_tokenizer(prep_text, return_tensors="pt", truncation=True, max_length=128)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.sentiment_model(**inputs)
            scores = torch.softmax(outputs.logits, dim=1)[0].cpu().tolist()
            
        id2label = self.sentiment_model.config.id2label
        # Standard CardiffNLP mapping: 0 -> negative, 1 -> neutral, 2 -> positive
        label_probs = {id2label.get(i, f"class_{i}").lower(): score for i, score in enumerate(scores)}
        top_idx = int(torch.argmax(outputs.logits, dim=1)[0].cpu().item())
        top_label = id2label.get(top_idx, "neutral").lower()
        top_score = round(scores[top_idx], 4)
        
        return {
            "label": top_label,
            "score": top_score,
            "probabilities": {k: round(v, 4) for k, v in label_probs.items()}
        }

    def predict_irony(self, text: str) -> Dict[str, Any]:
        """
        English Twitter RoBERTa Irony Classification.
        Returns: { 'label': 'irony'|'non_irony', 'score': float, 'probabilities': dict }
        """
        prep_text = preprocess_for_twitter_roberta(text)
        if not prep_text:
            return {"label": "non_irony", "score": 0.5, "probabilities": {"non_irony": 0.5, "irony": 0.5}}
        
        inputs = self.irony_tokenizer(prep_text, return_tensors="pt", truncation=True, max_length=128)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.irony_model(**inputs)
            scores = torch.softmax(outputs.logits, dim=1)[0].cpu().tolist()
            
        id2label = self.irony_model.config.id2label
        # Standard: 0 -> non_irony, 1 -> irony
        label_map = {0: "non_irony", 1: "irony"}
        label_probs = {label_map.get(i, id2label.get(i, f"class_{i}")): score for i, score in enumerate(scores)}
        top_idx = int(torch.argmax(outputs.logits, dim=1)[0].cpu().item())
        top_label = label_map.get(top_idx, id2label.get(top_idx, "non_irony"))
        top_score = round(scores[top_idx], 4)
        
        return {
            "label": top_label,
            "score": top_score,
            "probabilities": {k: round(v, 4) for k, v in label_probs.items()}
        }

    def predict_multilingual_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Multilingual Twitter XLM-RoBERTa Sentiment Classification.
        Returns: { 'label': 'negative'|'neutral'|'positive', 'score': float, 'probabilities': dict }
        """
        prep_text = preprocess_for_twitter_roberta(text)
        if not prep_text:
            return {"label": "neutral", "score": 0.333, "probabilities": {"negative": 0.333, "neutral": 0.334, "positive": 0.333}}
        
        inputs = self.multilingual_tokenizer(prep_text, return_tensors="pt", truncation=True, max_length=128)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.multilingual_model(**inputs)
            scores = torch.softmax(outputs.logits, dim=1)[0].cpu().tolist()
            
        id2label = self.multilingual_model.config.id2label
        # Standard XLM-R: 0 -> negative, 1 -> neutral, 2 -> positive
        label_probs = {id2label.get(i, f"class_{i}").lower(): score for i, score in enumerate(scores)}
        top_idx = int(torch.argmax(outputs.logits, dim=1)[0].cpu().item())
        top_label = id2label.get(top_idx, "neutral").lower()
        top_score = round(scores[top_idx], 4)
        
        return {
            "label": top_label,
            "score": top_score,
            "probabilities": {k: round(v, 4) for k, v in label_probs.items()}
        }

    def extract_auxiliary_signals(self, text: str) -> Dict[str, Any]:
        """
        Extracts all auxiliary NLP signals for an input comment.
        """
        sent_en = self.predict_sentiment_en(text)
        irony = self.predict_irony(text)
        sent_multi = self.predict_multilingual_sentiment(text)
        
        return {
            "sentiment_en_label": sent_en["label"],
            "sentiment_en_score": sent_en["score"],
            "irony_label": irony["label"],
            "irony_score": irony["score"],
            "sentiment_multilingual_label": sent_multi["label"],
            "sentiment_multilingual_score": sent_multi["score"],
        }
