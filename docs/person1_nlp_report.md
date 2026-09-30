# AdFatigueRadar — Person 1 (AI / NLP Layer) Engineering Handoff Report
**CODEBEGUN HACKZEN 2026 · Topic #15 | Production-Grade NLP Layer Handoff**

---

### 1. Executive Summary & Verification Matrix

> **Core Provenance & Data Disclosure**: All evaluation data in `data/test_human_audited/` and `data/training/` is synthetically engineered and scripted. The directory name `test_human_audited/` is fixed by the project specification and does **not** imply third-party human annotation. No third-party human audit, inter-annotator agreement (IAA) score, or real-world accuracy is claimed. `sample_audit_50.jsonl` is provided as an unblinded review scaffold for manual evaluator audit.

| Dimension | Specification Requirement | Delivered Result | Status |
| :--- | :--- | :--- | :---: |
| **Component Scope** | Person 1 AI / NLP Layer only (`backend/nlp/`, `data/`, `tests/nlp/`) | Strict boundary preserved; 0 out-of-scope files modified | **PASSED** |
| **Input Contract** | `CommentEvent` (JSON / dict / dataclass) | Supported via `CommentEvent` & `CommentClassifier.classify()` | **PASSED** |
| **Output Contract** | Frozen `NLPResult` schema (`comment_id`, `sentiment`, `sentiment_score`, `category`, `confidence`, `critical_complaint`) | Emitted deterministically matching frozen JSON contract exactly (6 fields) | **PASSED** |
| **Stage 1 Sentiment** | Local RoBERTa sequence classification on CPU | Loaded once locally (`twitter-roberta-base-sentiment-latest`), `local_files_only=True` | **PASSED** |
| **Stage 2 Taxonomy** | Real 8-class taxonomy ML classifier (no regex scoring) | Sentence-embeddings (768-dim) + Logistic Regression + Fitted Temperature Scaling | **PASSED** |
| **Held-Out Test Accuracy** | Measured on 320 held-out synthetic samples | **95.00% Accuracy (304 / 320 correct)**, **0.9499 Macro-F1** | **PASSED** |
| **Synthetic Stress Accuracy** | Measured on 64 synthetic edge-case samples | **95.31% Accuracy (61 / 64 correct)**, **0.9530 Macro-F1** | **PASSED** |
| **Disambiguation** | "Bro this ad again" $\rightarrow$ `fatigue`; "Bought again" $\rightarrow$ `positive` | Domain guard rules verified: fatigue (conf=0.9950), positive (conf=0.9920) | **PASSED** |
| **Critical Complaint** | `category` in `{product, service}_complaint` $\wedge$ `confidence >= 0.85` | Confidence-gated flag; keyword alone in banter/deals strictly rejected | **PASSED** |
| **Calibration** | Temperature Scaling ($T=0.5467$) fitted on Validation split | **ECE reduced from 0.0239 to 0.0162 (Val)** / **0.0163 (Test)** | **PASSED** |
| **Latency Benchmark** | Sub-minute classification latency requirement | **p50 = 56.57 ms**, **p95 = 63.34 ms** (199.29 batched comments/sec on CPU) | **PASSED** |
| **Replay Cache** | Keyed by `sha256(comment_id + model_ver + preproc_ver)` | SQLite + Memory `NLPCache`; invalidates on version change; bypassable | **PASSED** |
| **Data Leakage** | 0 overlap across train/val/test/stress | 0 exact and 0 near-duplicate matches (token Jaccard >= 0.85) | **PASSED** |
| **Test Suite** | Comprehensive unit and integration test suite | **37 / 37 pytest tests passed** | **PASSED** |

---

### 2. Verified Held-Out Test Evaluation Metrics (320 Samples)

Evaluated on the 320-sample held-out synthetic test split (`data/test_human_audited/labels.jsonl`, exactly 40 samples per class):

- **Overall Accuracy**: **95.00%** (304 / 320 correct)
- **Macro-F1 Score**: **0.9499**
- **Expected Calibration Error (ECE)**: **0.0163**

#### Per-Class Performance Table:
| Category | Support | Precision | Recall | F1-Score | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `product_complaint` | 40 | 0.9070 | 0.9750 | 0.9398 | High Recall |
| `service_complaint` | 40 | 0.9737 | 0.9250 | 0.9487 | High Precision |
| `fatigue` | 40 | 0.9070 | 0.9750 | 0.9398 | Reliable Ad Fatigue Detection |
| `mockery` | 40 | 0.9231 | 0.9000 | 0.9114 | High Accuracy on Cringe Ads |
| `spam` | 40 | 1.0000 | 0.9750 | 0.9873 | Near-Perfect Discrimination |
| `banter_meme` | 40 | 0.9211 | 0.8750 | 0.8974 | Protected from Complaint Bleed ($w=0.00$) |
| `neutral` | 40 | 1.0000 | 0.9750 | 0.9873 | Zero False Neutral Complaints |
| `positive` | 40 | 0.9756 | 1.0000 | 0.9877 | Perfect Recall |

#### Confusion Matrix (Rows = Ground Truth, Columns = Predicted):
```
True \ Pred            prod   serv   fati   mock   spam   bant   neut   posi
----------------------------------------------------------------------------
product_complaint        39      0      1      0      0      0      0      0
service_complaint         2     37      1      0      0      0      0      0
fatigue                   0      0     39      1      0      0      0      0
mockery                   1      0      0     36      0      3      0      0
spam                      0      0      0      0     39      0      0      1
banter_meme               1      1      1      2      0     35      0      0
neutral                   0      0      1      0      0      0     39      0
positive                  0      0      0      0      0      0      0     40
```

---

### 3. Synthetic Stress Test Evaluation (64 Samples)

Evaluated on `data/test_human_audited/stress_set.jsonl`: **small synthetic stress set authored by the same pipeline (64 samples, 8 per class); not independent evidence**.

- **Stress Set Accuracy**: **95.31%** (61 / 64 correct)
- **Stress Set Macro-F1**: **0.9530**

#### Stress Set Confusion Matrix:
```
True \ Pred             prod   serv   fati   mock   spam   bant   neut   posi
-----------------------------------------------------------------------------
product_complaint         7      1      0      0      0      0      0      0
service_complaint         0      8      0      0      0      0      0      0
fatigue                   0      0      7      1      0      0      0      0
mockery                   0      0      0      7      0      1      0      0
spam                      0      0      0      0      8      0      0      0
banter_meme               0      0      0      0      0      8      0      0
neutral                   0      0      0      0      0      0      8      0
positive                  0      0      0      0      0      0      0      8
```

#### Known Failure Cases & Mitigations:
1. *Mixed Complaints*: `"Bhai parcel khula hua aaya aur andar ka product poora toota hua tha"` $\rightarrow$ Predicted `service_complaint` (conf: 0.6414) instead of `product_complaint`. Both map to high risk ($w=1.00$).
2. *Technical Slang*: `"Bro the targeting algorithm is glitched, seen this 10x in one hour"` $\rightarrow$ Predicted `mockery` (conf: 0.4957) instead of `fatigue`.
3. *Meme Sarcasm*: `"Bro really hit the sigma male walk after using a vacuum cleaner 🤡😭"` $\rightarrow$ Predicted `banter_meme` (conf: 0.6596) instead of `mockery`.

---

### 4. Stage 1 Sentiment Alignment & Proxy Calibration

- **Pre-Trained Backbone**: Stage 1 utilizes `cardiffnlp/twitter-roberta-base-sentiment-latest` loaded locally on CPU.
- **Dataset Context**: Ground-truth datasets (`labels.jsonl`) were annotated strictly for the custom 8-class taxonomy; no independent 3-way sentiment labeling was conducted.
- **Proxy Calibration Numbers**:
  - Unambiguous validation subset (80 samples: `positive`, `neutral`, `product_complaint`, `service_complaint` mapped to pos/neu/neg).
  - ECE Before ($T=1.0$): **0.1156**
  - Fitted Temperature $T$: **1.3109** (via bounded NLL loss optimization)
  - ECE After ($T=1.3109$): **0.1357**
- **Plain Truth on Application**:
  - This fitted temperature ($T = 1.3109$) is **documented as an exploratory proxy study only and is NOT applied in `sentiment.py`**.
  - `sentiment.py` executes direct softmax ($T = 1.0$) over RoBERTa logits.
  - **Optimistic Limitation**: Because this proxy set excludes `fatigue` and `mockery`, the proxy ECE estimate is inherently optimistic.
  - `sentiment_score` in `NLPResult` outputs the normalized softmax probability (with domain repeat-purchase and ad-fatigue guards). The frozen `NLPResult` contract remains unchanged.

---

### 5. CPU Latency & Throughput Benchmark

- **Hardware Environment**: Local CPU execution on **AMD Ryzen 5 5600H with Radeon Graphics** (6 Cores / 12 Threads, x86_64, Windows).
- **Execution Mode**: CPU execution using PyTorch and HuggingFace Transformers (CUDA bypassed to verify CPU SLA).
- **Cache Status**: Replay cache strictly **BYPASSED** (`bypass_cache=True`).
- **Cold-Start Model Load Time**: **3,332.43 ms**
- **Steady-State Total Time (Single sequential)**: **11,417.84 ms** (11.42 s for 200 items)
- **Batched Total Time (Batch Size = 32)**: **1,003.59 ms** (1.00 s for 200 items)
- **Single-Item Throughput**: **17.43 comments/sec**
- **Batched (32) Throughput**: **199.29 comments/sec**
- **Latency p50**: **56.57 ms**
- **Latency p95**: **63.34 ms**
- **Latency p99**: **73.30 ms**
- **Latency Max**: **79.41 ms**
- **Sub-Minute SLA Target**: **PASSED** (1.00s batched / 11.42s single for 200 comments $\ll$ 60.0s)

---

### 6. Clean Checkout & Reproducibility Guide

#### A. Deterministic Retraining from Scratch
To reproduce the Stage 2 taxonomy model and calibration parameters deterministically:
```bash
python backend/nlp/train_models.py
```
- **Seeding**: Uses `torch.manual_seed(42)` and `random_state=42`.
- **Execution Time**: ~12 seconds on AMD Ryzen 5 5600H CPU.
- **Artifact Location**: Saves to `backend/nlp/artifacts/taxonomy_model.joblib`.
- **Startup Protection**: `TaxonomyClassifier` includes an explicit check that fails fast with `FileNotFoundError: Trained taxonomy artifact not found at '...'. Run 'python backend/nlp/train_models.py' from the repository root to generate it deterministically.`

#### B. Model Weight Pre-Caching for Offline Hackathon Demos
Pre-trained RoBERTa weights are stored locally in the **git-ignored weight cache**:
`data/models/twitter-roberta-base-sentiment-latest/`
All models load with `local_files_only=True` to guarantee 100% offline functionality without network access during live demos.

#### C. Exact Package Dependencies for Person 2 & Person 3
Person 1 does not modify shared environment files. The team's dependency owner should add the following exact packages:
| Package Name | Tested Version | Minimum Required | Role in NLP Pipeline |
| :--- | :--- | :--- | :--- |
| `torch` | `2.5.1` | `>= 2.0.0` | RoBERTa inference on CPU |
| `transformers` | `4.40.0` | `>= 4.35.0` | Model loading & tokenization |
| `scikit-learn` | `1.5.1` | `>= 1.3.0` | Stage 2 Linear classifier & metrics |
| `joblib` | `1.4.2` | `>= 1.3.0` | Fast artifact serialization |
| `numpy` | `1.26.4` | `>= 1.24.0` | Array & vector transformations |
| `scipy` | `1.14.0` | `>= 1.10.0` | NLL temperature optimization |
| `pytest` | `9.1.1` | `>= 7.0.0` | Test runner & contract assertions |

#### D. Proposed `.gitignore` Adjustments (Report Recommendation Only)
Currently `.gitignore` correctly ignores `*.joblib`, `*.db`, `*.sqlite`, and `data/models/`. No manual `.gitignore` edits were made.


---

### 7. Data Leakage & Test Suite Realities

- **Leakage Guarantee**: **0 exact and 0 near-duplicate matches (token Jaccard >= 0.85)** across `train`, `val`, `test`, and `stress` splits.
- **Automated Verification**: Run `python -m backend.nlp.leakage_checker <path_to_replay_files>` to check any replay stream against NLP corpora.
- **Note on `test_no_replay_overlap`**: In the automated test suite, `test_no_replay_overlap` is a structural safety test that is currently vacuous because Person 3 has not yet committed replay scenario files. `backend.nlp.leakage_checker` is the operational verification tool for Person 3 handoff.

---

### 8. Real-World Evaluation (Pending)

To evaluate on authentic hand-written comments provided by judges or evaluators:
1. Populate [data/test_human_audited/real_world_set.jsonl](file:///d:/kaladharroyal/projects/AdFatigue/data/test_human_audited/real_world_set.jsonl) with records in schema format:
   ```json
   {"text": "Sample real-world comment text", "category": "product_complaint"}
   ```
2. Execute the evaluation script:
   ```bash
   python scripts/eval_real_world.py data/test_human_audited/real_world_set.jsonl
   ```
3. The script outputs Accuracy, Macro-F1, per-class breakdown, confusion matrix, and complete error listings.

---

### 9. Inventory of Person 1 Files & Helper Utilities

#### Core Spec Files:
- `backend/nlp/__init__.py`: Package exports, `CommentEvent`, `NLPResult`.
- `backend/nlp/preprocessing.py`: Text & Unicode normalization routines.
- `backend/nlp/sentiment.py`: Stage 1 3-way RoBERTa classifier.
- `backend/nlp/taxonomy.py`: Stage 2 8-class taxonomy classifier with domain guards.
- `backend/nlp/classifier.py`: Unified `CommentClassifier` orchestrator.
- `backend/nlp/calibration.py`: `TemperatureScaler` & ECE computation.
- `backend/nlp/inference.py`: `StreamCommentProcessor` for streaming/batching.
- `backend/nlp/cache.py`: `NLPCache` SQLite/Memory cache.
- `backend/nlp/baselines.py`: `SentimentOnlyBaseline` (P1 baseline).
- `backend/nlp/benchmark.py`: Core latency & throughput benchmark engine.
- `data/training/`: `labels.jsonl`, `val_labels.jsonl`, `source_manifest.json`, `README.md`.
- `data/test_human_audited/`: `labels.jsonl`, `audit_manifest.json`, `sample_audit_50.jsonl`, `README.md`.
- `backend/tests/nlp/`: 9 unit test files covering all Sec 20 items (37 passing tests).
- `scripts/benchmark_nlp.py`: Standalone CLI benchmark script.
- `docs/person1_nlp_report.md`: Engineering handoff report.

#### Additional NLP Helpers Created:
- `backend/nlp/constants.py`: Centralized versions, category tuples, and threshold constants.
- `backend/nlp/train_models.py`: Deterministic retraining script for Stage 2.
- `backend/nlp/leakage_checker.py`: CLI tool for Person 3 replay leakage verification.
- `data/test_human_audited/stress_set.jsonl`: 64-sample synthetic stress dataset.
- `data/test_human_audited/real_world_set.jsonl`: Scaffold for incoming authentic comments.
- `scripts/eval_real_world.py`: Evaluation CLI for scoring `real_world_set.jsonl`.
- `scripts/eval_nlp_test_set.py`: Detailed evaluation script for held-out test splits.

---

### 10. Integration Guide for Person 2 & Person 3

```python
from backend.nlp import CommentEvent, NLPResult
from backend.nlp.classifier import CommentClassifier

# Initialize classifier once (loads models into memory on CPU)
classifier = CommentClassifier(use_cache=True)

# 1. Single Comment Ingestion (Live Stream)
event = CommentEvent(
    event_id="comment_0001",
    timestamp="2026-09-30T12:00:00Z",
    campaign_id="campaign_01",
    ad_id="ad_07",
    author_id="author_184",
    text="Bro this ad again 😂"
)
result: NLPResult = classifier.classify(event)
print(result.to_dict())
# {
#   "comment_id": "comment_0001",
#   "sentiment": "negative",
#   "sentiment_score": 0.9200,
#   "category": "fatigue",
#   "confidence": 0.9950,
#   "critical_complaint": false
# }

# 2. Batched Ingestion (Replay Simulation)
results = classifier.classify_batch([event1, event2, event3])
```
