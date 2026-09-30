# AdFatigueRadar — Final Production Limitations & Risk Disclosures

**Audit Date:** 2026-09-30  
**Status:** Mandatory Engineering Disclosure  

---

## 1. Ground Truth & Annotation Policy Limitation
- **Finding:** The primary 1,461-record pool was labeled using algorithmic/programmatic dual-annotator policies with arbitration ($\kappa = 0.6923$). While mathematically rigorous and reproducible, physical independent human crowd annotation was not conducted across the entirety of the pool.
- **Classification:** `PASS WITH DOCUMENTED LIMITATION`.
- **Operational Risk:** Edge cases with nuanced sarcasm or domain-specific slang may reflect algorithmic bias.
- **Mitigation:** Production serving includes real-time drift monitoring and requires human oversight on critical complaint escalations.

## 2. Dataset Scale Limitation
- **Finding:** The real-world corpus comprises 1,461 labeled samples (874 train, 288 val, 299 test).
- **Classification:** `ACCEPTABLE FOR TWO-STAGE ARCHITECTURE`.
- **Operational Risk:** Insufficient for full 125M parameter Transformer weight backpropagation without severe overfitting.
- **Mitigation:** Pre-trained CardiffNLP Twitter-RoBERTa feature embeddings are frozen; only regularized classification heads and temperature scalers are fitted.

## 3. Multilingual Incompetence
- **Finding:** Evaluated accuracy on 16 non-English samples is **18.75%** (Macro-F1: 0.1167).
- **Root Cause:** CardiffNLP `twitter-roberta-base-sentiment-latest` is pre-trained exclusively on English corpora.
- **Enforcement:** The system MUST NOT be claimed as multilingual. An upstream language detector (e.g., `fastText`) must filter non-English text before ingestion into the NLP serving layer.

## 4. Out-of-Distribution (OOD) Domain Shift
- **Finding:** Accuracy drops to **42.00%** (Macro-F1: 0.1696) on 50 non-advertising general conversational comments.
- **Operational Risk:** The model is specialized for social ad comments and brand interactions; deploying on generic conversational threads will yield degraded accuracy.

## 5. Taxonomy Semantic Overlap
- **Finding:** Classes `mockery` vs. `banter_meme` and `product_complaint` vs. `service_complaint` exhibit natural semantic overlap in consumer complaints.
- **Mitigation:** Calibrated probability distributions are exposed over all 8 classes in `NLPResponse` rather than only a single top label.

## 6. Drift Monitoring Baseline Reference
- **Finding:** The runtime drift monitor uses the frozen 299-record test distribution as its reference baseline.
- **Note:** In early production, small statistical fluctuations will occur until sample sizes exceed $\sim 500$ live observations.
