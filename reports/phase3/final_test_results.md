# Phase 3 Final Real-World Test Evaluation Report

**Evaluation Timestamp (UTC):** 2026-09-30T15:26:03Z  
**Dataset:** `data/real_world/test/test.jsonl` (299 records, Frozen SHA-256: `82dacabc7b54812ce7455e68cf66cbdb6402228bab9fb5ccb35f197846e67112`)  
**Winning Model Candidate:** `PHASE3_FINAL_FUSED_ROBERTA_LR`  
**Architecture:** RoBERTa Dense Embeddings (768-dim) + RoBERTa Sentiment Posteriors (3-dim) + Calibrated Logistic Regression  

---

## 1. Baseline vs. Phase 3 Comparison

| Metric | Phase 2 Real-World Baseline | Phase 3 Final Candidate | Delta ($\Delta$) |
| :--- | :---: | :---: | :---: |
| **Accuracy** | 28.09% | **65.55%** | **+37.46%** |
| **Macro Precision** | 0.3623 | **0.6531** | **+0.2908** |
| **Macro Recall** | 0.2816 | **0.6135** | **+0.3319** |
| **Macro F1** | 0.2711 | **0.6200** | **+0.3489** |
| **Weighted Precision** | 0.2780 | **0.6698** | **+0.3918** |
| **Weighted Recall** | 0.2809 | **0.6555** | **+0.3746** |
| **Weighted F1** | 0.2685 | **0.6472** | **+0.3787** |
| **Calibration ECE** | 0.1357 | **0.0626** | **-0.0731** |
| **Brier Score** | 0.8421 | **0.4798** | **-0.3623** |

---

## 2. Per-Class Performance Breakdown (299 Test Records)

| Category | Support | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: |
| `product_complaint` | 42 | 0.6250 | 0.5952 | **0.6098** |
| `service_complaint` | 20 | 0.6364 | 0.7000 | **0.6667** |
| `fatigue` | 21 | 0.5789 | 0.5238 | **0.5500** |
| `mockery` | 41 | 0.5957 | 0.6829 | **0.6364** |
| `spam` | 13 | 0.8333 | 0.3846 | **0.5263** |
| `banter_meme` | 40 | 0.5000 | 0.3750 | **0.4286** |
| `neutral` | 81 | 0.7209 | 0.7654 | **0.7425** |
| `positive` | 41 | 0.7347 | 0.8780 | **0.8000** |

---

## 3. Generalization & Challenge Set Results

| Split | Sample Count | Accuracy | Macro-F1 |
| :--- | :---: | :---: | :---: |
| **Out-Of-Distribution (`data/real_world/ood/ood.jsonl`)** | 50 | 42.00% | 0.1696 |
| **Multilingual (`data/splits/multilingual_test.jsonl`)** | 16 | 18.75% | 0.1167 |
| **Stress / Challenge (`data/test_human_audited/stress_set.jsonl`)** | 64 | 60.94% | 0.6296 |
