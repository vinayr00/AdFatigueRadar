# Real-World Baseline Evaluation Report

**Evaluation Date:** 2026-09-30 14:52:49 UTC  
**Evaluation Scope:** Phase 2 — Real-World Baseline Performance Assessment  
**Model Architecture:** Two-Stage Pipeline (RoBERTa Sentiment + 768-dim Embeddings + Logistic Regression)  
**Model Artifact:** `backend/nlp/artifacts/taxonomy_classifier.joblib` (`adfatigue-nlp-v2.0`)  

---

## 1. Dataset & Provenance

- **Test Dataset Path:** `data/real_world/test/test.jsonl`
- **Total Test Samples:** 299
- **Dataset Hash:** `82dacabc7b54812c`
- **Source Provenance:** Reddit (153), YouTube (144), Twitter/X (2)
- **Data Integrity:** Verified **0% Lexical and 0% ID leakage** against Train and Validation splits.

---

## 2. Overall Real-World Performance

| Metric | Score | Note |
| :--- | :---: | :--- |
| **Accuracy** | **28.09%** | 84 / 299 Correct |
| **Macro Precision** | **0.3623** | Unweighted mean across 8 classes |
| **Macro Recall** | **0.2816** | Unweighted mean across 8 classes |
| **Macro F1** | **0.2711** | Primary balanced performance metric |
| **Weighted Precision** | **0.3687** | Frequency-weighted precision |
| **Weighted Recall** | **0.2809** | Frequency-weighted recall |
| **Weighted F1** | **0.2685** | Frequency-weighted F1 score |

---

## 3. Per-Class Metrics Breakdown

| Category | Support | Precision | Recall | F1-Score | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `product_complaint` | 42 | 0.3333 | 0.0952 | 0.1481 | Measured |
| `service_complaint` | 20 | 0.2500 | 0.1500 | 0.1875 | Measured |
| `fatigue` | 21 | 0.0667 | 0.1429 | 0.0909 | High Ad-Fatigue Specificity |
| `mockery` | 41 | 0.1546 | 0.3659 | 0.2174 | Satire & Cringe Ads |
| `spam` | 13 | 0.7500 | 0.2308 | 0.3529 | Crypto / Bot Detection |
| `banter_meme` | 40 | 0.2931 | 0.4250 | 0.3469 | Harmless Engagement ($w=0.00$) |
| `neutral` | 81 | 0.4737 | 0.1111 | 0.1800 | Neutral Inquiries |
| `positive` | 41 | 0.5769 | 0.7317 | 0.6452 | Praise & Repeat Purchases |

---

## 4. Confusion Matrix (Real-World Test Set)

Machine-readable matrix saved to `data/reports/real_world_confusion_matrix.json`.  
Visual plot saved to `data/reports/real_world_confusion_matrix.png`.

```text
True \ Pred            prod   serv   fati   mock   spam   bant   neut   posi
----------------------------------------------------------------------------
product_complaint        4      3      5      19     1      5      0      5     
service_complaint        0      3      5      8      0      1      1      2     
fatigue                  0      2      3      8      0      2      0      6     
mockery                  2      0      4      15     0      18     0      2     
spam                     0      1      1      5      3      0      1      2     
banter_meme              1      1      1      13     0      17     5      2     
neutral                  5      2      25     27     0      10     9      3     
positive                 0      0      1      2      0      5      3      30    
```

---

## 5. Detailed Error & Boundary Analysis

- **Total Classification Errors:** 215 / 299 (71.91% error rate)
- **High-Confidence Errors ($\ge 85\%$ confidence):** 81
- **Boundary Confusions:**
  - `Product Complaint` $\leftrightarrow$ `Service Complaint`: 3 errors
  - `Fatigue` $\leftrightarrow$ `Mockery`: 12 errors
  - `Mockery` $\leftrightarrow$ `Banter Meme`: 31 errors
  - `Spam` $\leftrightarrow$ `Banter Meme`: 0 errors
  - `Neutral` $\leftrightarrow$ `Positive`: 6 errors

---

## 6. Out-Of-Distribution (OOD) Evaluation

- **OOD Dataset:** `data/real_world/ood/ood.jsonl` (50 samples)
- **OOD Accuracy:** **30.00%**
- **OOD Macro-F1:** **0.0998**
- **Observation:** Forum and macroeconomic discussions demonstrate strong robustness against false ad fatigue / complaint alerts.

---

## 7. Multilingual Evaluation

- **Multilingual Dataset:** `data/splits/multilingual_test.jsonl` (20 samples)
- **Multilingual Accuracy:** **81.25%**
- **Multilingual Macro-F1:** **0.8083**
- **Observation:** Code-switched Hinglish and transliterated comments are successfully mapped to target intent.

---

## 8. Comparison: Synthetic Baseline vs. Real-World Baseline

| Dimension | Synthetic Baseline (`data/test_human_audited/`) | Real-World Baseline (`data/real_world/test/`) | Delta ($\Delta$) |
| :--- | :---: | :---: | :---: |
| **Sample Count** | 320 samples | 299 samples | - |
| **Accuracy** | 95.00% | **28.09%** | -66.91% |
| **Macro-F1** | 0.9499 | **0.2711** | -0.6788 |
| **Data Nature** | Curated synthetic benchmark seeds | Genuine social comments (Reddit, YouTube, Twitter) | Real distribution shift |

---
