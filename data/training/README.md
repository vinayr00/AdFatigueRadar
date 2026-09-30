# Training Dataset & Provenance
================================
**AdFatigueRadar — AI / NLP Training Data (Person 1)**

This directory contains pre-processed and curated training examples used for training/evaluating the Stage 1 Sentiment and Stage 2 Taxonomy classifiers.

### Data Provenance & Structure
- `labels.jsonl`: Curated training examples with ground truth labels across all 8 taxonomy categories and 3 sentiment classes.
- `source_manifest.json`: Metadata tracking source origins, class balance, preprocessing version, and strict train/test separation.

### Strict Isolation Guarantees
- Training examples are **completely disjoint** from `data/test_human_audited/` (held-out test set).
- Replay generation scripts use independent generative comment pools and do not leak into training sets.
