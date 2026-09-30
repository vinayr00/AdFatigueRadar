# AdFatigueRadar — Formal System Limitations & Risk Assessment

**Report Version:** Phase 5 Final Assessment  
**Classification:** Transparent Technical Disclosure  

---

## 1. Ground Truth & Annotation Policy Limitation
- **Nature of Ground Truth:** The 1,461-record labeled pool across training, validation, and testing was generated using rigorous programmatic dual-annotator policies with algorithmic adjudication rather than an independent physical team of human domain experts.
- **Impact:** While Cohen's kappa ($\kappa = 0.6923$) demonstrates high consistency, systemic biases inherent in rule-based or heuristic annotators may persist in edge cases.
- **Mitigation:** Active prediction drift monitoring in production with manual human review for critical complaint escalations.

## 2. Labeled Dataset Scale
- **Dataset Size:** 1,461 total records (876 train, 286 validation, 299 test).
- **Impact:** The sample volume is sufficient to fit regularized linear classification heads on top of frozen RoBERTa embeddings (768 dimensions), but insufficient for full end-to-end backpropagation fine-tuning of all 125M Transformer parameters without catastrophic overfitting.
- **Mitigation:** Two-stage multi-signal architecture leveraging pre-trained CardiffNLP Twitter-RoBERTa feature representations.

## 3. Multilingual Incompetence
- **Diagnostic Result:** 18.75% accuracy and 0.1167 Macro-F1 on a 16-sample multilingual benchmark (Spanish, German, Hindi, French).
- **Root Cause:** CardiffNLP `twitter-roberta-base-sentiment-latest` is an English-only checkpoint.
- **Operational Requirement:** A language identification gate (e.g., `fastText` or `langdetect`) MUST filter non-English comments prior to NLP serving. Non-English text must not be routed to this model.

## 4. Out-of-Distribution (OOD) Degradation
- **Diagnostic Result:** 42.00% accuracy and 0.1696 Macro-F1 on 50 non-advertising conversational Reddit/YouTube comments.
- **Impact:** The model performs well on ad-fatigue and brand mockery contexts, but misclassifies ambiguous conversational banter when divorced from advertising context.
- **Mitigation:** Model should only be deployed on verified ad post comment streams.

## 5. Critical Complaint Precision/Recall Trade-Off
- **Threshold Setting:** $\tau = 0.50$ yields **79.41% Precision** and **45.76% Recall** ($F_1 = 0.5806$).
- **Trade-off:** High precision minimizes false alarms for brand safety teams, but approximately 54% of subtler complaints fall below the conservative threshold and must be captured via aggregate category scoring rather than instant critical alerting.

## 6. Hardware & Concurrency Boundaries
- **Target GPU:** Single NVIDIA GeForce GTX 1650 (4 GB VRAM).
- **Throughput Bounds:** Steady-state single-stream throughput is $\sim 18.3\text{ items/sec}$; concurrent load scales up to $\sim 197\text{ req/sec}$ before GPU queue saturation.
- **Mitigation:** High-volume multi-million comment pipelines require horizontal scaling across multiple GPU worker nodes with Redis distributed caching.
