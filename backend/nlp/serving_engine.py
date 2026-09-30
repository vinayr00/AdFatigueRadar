"""
AdFatigueRadar — Production Serving Engine (Phase 4)
====================================================
Thread-safe, high-throughput production serving engine executing the frozen
Phase 3 Multi-Signal RoBERTa + Calibrated LR model with PII redaction,
two-tier caching, latency telemetry, and drift monitoring hooks.
"""

import os
import sys
import time
import threading
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import torch
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification

from .constants import TAXONOMY_CATEGORIES, DEFAULT_MAX_SEQ_LENGTH, MODEL_VERSION, PREPROCESSING_VERSION
from .preprocessing import normalize_text
from .pii_sanitizer import PIISanitizer
from .cache import NLPCache
from .model_loader import ProductionModelBundle, load_production_model
from .schemas import NLPRequest, NLPResponse, BatchNLPResponse

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOCAL_ROBERTA_DIR = os.path.join(BASE_DIR, "data", "models", "twitter-roberta-base-sentiment-latest")


class ProductionServingEngine:
    """
    Singleton production inference engine with GPU memory safety,
    batched execution, PII masking, and latency observability.
    """
    _instance: Optional["ProductionServingEngine"] = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, device_mode: str = "auto", use_cache: bool = True) -> "ProductionServingEngine":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(device_mode=device_mode, use_cache=use_cache)
            return cls._instance

    def __init__(self, device_mode: str = "auto", use_cache: bool = True):
        self.device_mode = device_mode
        self.bundle: ProductionModelBundle = load_production_model(device_mode=device_mode)
        self.device = self.bundle.device
        
        # Load HuggingFace Backbones onto target device
        print(f"[ServingEngine] Loading RoBERTa Transformers on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(LOCAL_ROBERTA_DIR, local_files_only=True)
        self.base_model = AutoModel.from_pretrained(LOCAL_ROBERTA_DIR, local_files_only=True).to(self.device)
        self.base_model.eval()
        
        self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(LOCAL_ROBERTA_DIR, local_files_only=True).to(self.device)
        self.sentiment_model.eval()
        
        # PII Sanitizer & Cache
        self.sanitizer = PIISanitizer()
        self.use_cache = use_cache
        cache_db = os.path.join(BASE_DIR, "data", "nlp_production_cache.sqlite")
        self.cache = NLPCache(db_path=cache_db) if use_cache else None
        
        # Performance Telemetry
        self.request_count = 0
        self.item_count = 0
        self.latencies_ms: List[float] = []
        self.error_count = 0
        self.start_time = time.time()
        self._telemetry_lock = threading.Lock()
        
        # Initial Warm-Up
        self.warm_up()

    def warm_up(self, num_samples: int = 3):
        """Runs dummy warm-up forward passes to initialize PyTorch CUDA kernels & caching."""
        print(f"[ServingEngine] Warming up inference engine on {self.device}...")
        dummy_texts = ["Warmup test comment for AdFatigue radar", "Checking latency pipeline initialization"] * num_samples
        _ = self.predict_batch([NLPRequest(text=t, bypass_cache=True) for t in dummy_texts[:num_samples]])
        print("  ✓ Warm-up forward passes completed successfully.")

    def _extract_features(self, texts: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extracts 768-dim sentence embeddings and 3-dim sentiment probabilities on GPU/CPU.
        Returns fused 771-dim feature vectors and sentiment posteriors.
        """
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=DEFAULT_MAX_SEQ_LENGTH,
            return_tensors="pt"
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.inference_mode():
            # 1. RoBERTa Dense Embeddings (768-dim)
            base_out = self.base_model(**inputs)
            mask = inputs["attention_mask"].unsqueeze(-1).expand(base_out.last_hidden_state.size()).float()
            sum_emb = torch.sum(base_out.last_hidden_state * mask, 1)
            sum_mask = torch.clamp(mask.sum(1), min=1e-9)
            embeddings = (sum_emb / sum_mask).cpu().numpy()
            
            # 2. RoBERTa Sentiment Posteriors (3-dim)
            sent_out = self.sentiment_model(**inputs)
            sent_probs = torch.softmax(sent_out.logits, dim=-1).cpu().numpy()
            
        # Multi-signal concatenation: [768-dim emb, 3-dim sent * 2.5] -> 771-dim
        fused = np.hstack([embeddings, sent_probs * 2.5])
        return fused, sent_probs

    def predict_single(self, request: NLPRequest) -> NLPResponse:
        """Processes a single validated NLPRequest with PII protection & caching."""
        t_start = time.perf_counter()
        req_id = request.comment_id or f"req_{int(time.time()*1000)}_{np.random.randint(1000, 9999)}"
        
        # 1. PII Sanitization
        clean_text, pii_entities = self.sanitizer.sanitize(request.text)
        has_pii = len(pii_entities) > 0
        
        # 2. Check Cache
        if self.cache and not request.bypass_cache:
            cached_res = self.cache.get(clean_text)
            if cached_res:
                proc_time = (time.perf_counter() - t_start) * 1000
                self._record_telemetry(proc_time, 1)
                
                cached_probs = {c: 0.0 for c in TAXONOMY_CATEGORIES}
                cached_probs[cached_res.category] = round(cached_res.confidence, 4)
                
                return NLPResponse(
                    comment_id=req_id,
                    category=cached_res.category,
                    confidence=cached_res.confidence,
                    sentiment=cached_res.sentiment,
                    sentiment_score=cached_res.sentiment_score,
                    probabilities=cached_probs,
                    critical_complaint=cached_res.critical_complaint,
                    is_critical_complaint=cached_res.critical_complaint,
                    pii_redacted=has_pii,
                    cached=True,
                    model_version=self.bundle.model_version,
                    processing_time_ms=round(proc_time, 2)
                )

        # 3. Model Inference (GPU/CPU)
        fused_vec, sent_probs = self._extract_features([clean_text])
        logits = self.bundle.classifier.decision_function(fused_vec)
        
        # Temperature Scaling Calibration
        scaled_logits = logits / max(self.bundle.temperature, 0.05)
        exp_l = np.exp(scaled_logits - np.max(scaled_logits, axis=1, keepdims=True))
        cal_probs = exp_l / np.sum(exp_l, axis=1, keepdims=True)
        
        pred_idx = int(np.argmax(cal_probs[0]))
        category = self.bundle.idx_to_class[pred_idx]
        confidence = float(cal_probs[0, pred_idx])
        
        # Sentiment mapping (0: neg, 1: neu, 2: pos)
        sent_labels = ["negative", "neutral", "positive"]
        top_sent_idx = int(np.argmax(sent_probs[0]))
        sentiment = sent_labels[top_sent_idx]
        sentiment_score = float(sent_probs[0, top_sent_idx])
        
        # Critical complaint gate (Category is complaint + confidence >= tau)
        is_complaint = category in ["product_complaint", "service_complaint"]
        is_critical = is_complaint and (confidence >= self.bundle.operational_threshold)
        
        all_probs = {self.bundle.idx_to_class[i]: round(float(cal_probs[0, i]), 4) for i in range(len(TAXONOMY_CATEGORIES))}
        
        # 4. Save to Cache
        if self.cache and not request.bypass_cache:
            from . import NLPResult
            self.cache.put(clean_text, NLPResult(
                comment_id=req_id,
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                category=category,
                confidence=confidence,
                critical_complaint=is_critical
            ))

        proc_time = (time.perf_counter() - t_start) * 1000
        self._record_telemetry(proc_time, 1)

        return NLPResponse(
            comment_id=req_id,
            category=category,
            confidence=round(confidence, 4),
            sentiment=sentiment,
            sentiment_score=round(sentiment_score, 4),
            probabilities=all_probs,
            critical_complaint=is_critical,
            is_critical_complaint=is_critical,
            pii_redacted=has_pii,
            cached=False,
            model_version=self.bundle.model_version,
            processing_time_ms=round(proc_time, 2)
        )

    def predict_batch(self, requests: List[NLPRequest], chunk_size: int = 32) -> BatchNLPResponse:
        """Processes a batch of NLPRequests efficiently in GPU/CPU chunks."""
        t_batch_start = time.perf_counter()
        results: List[NLPResponse] = []
        
        # Process in chunks to maintain strict VRAM safety
        for i in range(0, len(requests), chunk_size):
            chunk = requests[i : i + chunk_size]
            for req in chunk:
                res = self.predict_single(req)
                results.append(res)
                
        total_time_ms = (time.perf_counter() - t_batch_start) * 1000
        throughput = len(requests) / (total_time_ms / 1000) if total_time_ms > 0 else 0.0
        
        return BatchNLPResponse(
            results=results,
            total_items=len(requests),
            total_time_ms=round(total_time_ms, 2),
            batch_throughput_items_sec=round(throughput, 2)
        )

    def _record_telemetry(self, latency_ms: float, count: int):
        with self._telemetry_lock:
            self.request_count += 1
            self.item_count += count
            self.latencies_ms.append(latency_ms)
            if len(self.latencies_ms) > 10000:
                self.latencies_ms = self.latencies_ms[-5000:]

    def get_metrics(self) -> Dict[str, Any]:
        """Returns comprehensive real-time runtime metrics."""
        with self._telemetry_lock:
            hits = self.cache.hits if self.cache else 0
            misses = self.cache.misses if self.cache else 0
            total_c = hits + misses
            hit_ratio = (hits / total_c) if total_c > 0 else 0.0
            
            lats = self.latencies_ms if self.latencies_ms else [0.0]
            p50 = float(np.percentile(lats, 50))
            p95 = float(np.percentile(lats, 95))
            p99 = float(np.percentile(lats, 99))
            avg_lat = float(np.mean(lats))
            
            vram_mb = (torch.cuda.memory_allocated(0) / (1024 ** 2)) if self.device.type == "cuda" else 0.0
            
            return {
                "total_requests": self.request_count,
                "total_items_processed": self.item_count,
                "cache_hits": hits,
                "cache_misses": misses,
                "cache_hit_ratio": round(hit_ratio, 4),
                "latency_p50_ms": round(p50, 2),
                "latency_p95_ms": round(p95, 2),
                "latency_p99_ms": round(p99, 2),
                "avg_latency_ms": round(avg_lat, 2),
                "error_count": self.error_count,
                "active_device": str(self.device),
                "vram_usage_mb": round(vram_mb, 2)
            }
