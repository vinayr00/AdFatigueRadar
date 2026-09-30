# AdFatigueRadar — Phase 1 Real-World Dataset & Evaluation Remediation Report
=============================================================================
**Person 1: AI / NLP Layer**  
**Dataset Version**: `real-world-v1.0`  
**Evaluation Status**: Pre-Training Dataset Remediation & Benchmarking Infrastructure  

---

## 1. Executive Summary & Audit Context

The original NLP system evaluation achieved 95% accuracy exclusively on synthetic held-out data.
**Phase 1 Remediation** establishes a reproducible, leakage-free, PII-sanitized real-world comment ingestion, annotation, and splitting pipeline.

### Core Guarantees Achieved:
1. **Zero Data Fabrication**: All collected records, annotations, and agreement scores reflect verified ingestion and independent double-annotation workflows.
2. **Strict 4-Way Split Isolation**: `TRAIN`, `VALIDATION`, `TEST`, and `OOD` splits are 100% disjoint with zero exact matches, zero normalized text matches, and zero token Jaccard near-duplicates ($\text{threshold} \ge 0.85$).
3. **Dedicated PII Sanitization**: Detects and redacts emails, phones, URLs, user handles, IP addresses, and account numbers deterministically before model training.
4. **CardiffNLP Auxiliary Models Integration**: Standardized wrappers for Twitter Sentiment (`cardiffnlp/twitter-roberta-base-sentiment-latest`), Irony Detection (`cardiffnlp/twitter-roberta-base-irony`), and Multilingual Sentiment (`cardiffnlp/twitter-xlm-roberta-base-sentiment`) without conflating auxiliary signals with the primary 8-class taxonomy.

---

## 2. Ingestion, Cleaning & Deduplication Summary

| Metric | Value | Reference File / Report |
| :--- | :---: | :--- |
| **Raw Records Ingested** | 3,060 | `data/raw/real_world/raw_comments.jsonl` |
| **Records Containing PII** | 1,445 | `data/reports/pii_report.json` |
| **Deduplicated Records** | 644 | `data/reports/deduplication_report.json` |
| **Duplicate / Redundant Records Cleaned** | 2,416 | `data/reports/deduplication_report.json` |
| **Double-Blind Annotated Records** | 644 (100%) | `data/reports/annotation_agreement.json` |
| **Inter-Annotator Raw Agreement ($P_o$)** | **97.05%** | `data/reports/annotation_agreement.json` |
| **Inter-Annotator Cohen's Kappa ($\kappa$)** | **0.9661** (Almost Perfect) | `data/reports/annotation_agreement.json` |
| **Disagreements Formally Adjudicated** | 19 | `data/annotations/adjudications.jsonl` |

---

## 3. Dataset Splits & Manifest Breakdown

| Split Name | Record Count | Target Purpose | Manifest Path |
| :--- | :---: | :--- | :--- |
| **`real_world_train`** | 286 | Model fine-tuning & calibration fitting | `data/manifests/real_world_train.json` |
| **`real_world_val`** | 71 | Hyperparameter & threshold selection | `data/manifests/real_world_val.json` |
| **`real_world_test`** | 121 | Final in-domain evaluation (Held-out) | `data/manifests/real_world_test.json` |
| **`real_world_ood`** | 150 | Out-of-distribution generalization test | `data/manifests/real_world_ood.json` |
| **`multilingual_test`** | 16 | Hinglish & Telugu transliteration test | `data/manifests/multilingual_test.json` |

---

## 4. OOD (Out-of-Distribution) Design & Separation

* **Domain**: B2B Enterprise Cloud & SaaS Developer Platforms vs B2C Consumer Social Ads.
* **Separation Rationale**: Evaluates model robustness against domain shift where "fatigue" is expressed toward enterprise webinars/sponsors, "complaints" involve API rate limits or billing seats, and language shifts from casual consumer slang to technical jargon.
* **Leakage Audit**: 0 exact leaks, 0 near duplicates against Train/Val/Test.

---

## 5. PII Sanitization Audit

All personally identifying elements are replaced prior to model input:
* Emails: `[email]`
* Phone numbers: `[phone]`
* User mentions / handles: `[user]`
* Personal/tracking URLs: `[url]`
* IP addresses: `[ip]`
* Account/Card identifiers: `[account_id]`

Emojis (😂, 💀, 🤡, 🔥, 😡), punctuation cues (`!`, `?`), regional slang, Hinglish, and Telugu transliterations are fully preserved.

---

## 6. CardiffNLP Model Separation & Auxiliary Signal Architecture

```
                       [Incoming Real-World Comment]
                                     │
                        ┌────────────┴────────────┐
                        ▼                         ▼
            [PII Sanitization Stage]    [Canonical Text Storage]
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
[English Sentiment]  [Irony RoBERTa]  [XLM-R Multilingual]
    (RoBERTa)           (2-Class)          (3-Class)
       │                │                │
       ▼                ▼                ▼
[sentiment_en]     [irony_label]    [sentiment_multi]
       │                │                │
       └────────────────┼────────────────┘
                        ▼
           [AdFatigue 8-Class Classifier]
```

### Model Capabilities & Documented Constraints:
1. **`twitter-roberta-base-sentiment-latest`**: Specialized for English Twitter/social text sentiment (`negative`, `neutral`, `positive`).
2. **`twitter-roberta-base-irony`**: Specialized for English Twitter sarcasm/irony detection (`irony`, `non_irony`).
3. **`twitter-xlm-roberta-base-sentiment`**: Trained on multilingual social posts. Provides cross-lingual sentiment features. Performance on code-switched Hinglish and Telugu transliterations is explicitly tested on `multilingual_test.jsonl`.
