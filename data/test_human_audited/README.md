# AdFatigueRadar — Held-Out Evaluation Dataset
================================================
PERSON 1: AI / NLP Layer

> **Important Disclosure**: All data in this folder is synthetically generated; the folder name is fixed by the project specification and does not imply third-party human annotation.

---

## 1. Overview
This directory contains the held-out evaluation datasets used for reporting test metrics and diagnosing edge-case performance.

## 2. Dataset Files & Provenance
- **`labels.jsonl` (Held-Out Evaluation Split)**: 320 records (exactly 40 per category across all 8 classes).
  - Synthetically authored and strictly held out from training and validation.
  - Leakage guarantee: 0 exact and 0 near-duplicate matches (token Jaccard >= 0.85) across train/val/test/stress splits.
  - No human audit, inter-annotator agreement (IAA) score, or real-world accuracy is claimed for this synthetic set.
- **`stress_set.jsonl` (Synthetic Stress Test Set)**: Small synthetic stress set authored by the same pipeline (64 samples, 8 per class); not independent evidence. Contains heavy typos, Hinglish, Telugu transliterations, emojis, sarcastic roasts, and complex boundary cases.
- **`sample_audit_50.jsonl` (Audit Template Scaffold)**: 50 unblinded samples drawn from the held-out test split with schema fields (`human_auditor_verified`, `human_agreed_category`, `notes`) provided as an audit scaffold for evaluators to manually inspect. No third-party panel has completed this review.
- **`real_world_set.jsonl` (Real-World Evaluation - Pending)**: Scaffold file reserved for authentic human-authored comment streams to be evaluated independently without training leakage.

## 3. Disjointness Guarantee
- 0 exact and 0 near-duplicate matches (token Jaccard >= 0.85) across train/val/test/stress splits.
