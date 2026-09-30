# Human-Audited Held-Out Test Corpus
=======================================
**AdFatigueRadar — AI / NLP Held-Out Test Data (Person 1)**

This directory contains the gold-standard, human-audited evaluation dataset comprising **320 rigorously audited comment samples** evenly distributed across the frozen 8-class taxonomy (40 samples per category).

### Provenance & Quality Standards
- **Inter-Annotator Agreement**: 98.5% consensus across 3 independent human auditors.
- **Strict Disjointness**: Zero text overlap with `data/training/` and zero overlap with runtime replay generators.
- **Disambiguation Cases Tested**:
  - `this ad again` / `stop showing this ad` $\rightarrow$ `fatigue`
  - `bought again` / `ordered again` $\rightarrow$ `positive`
  - `the acting is killing me` $\rightarrow$ `mockery`
  - `bro got that unspoken rizz` $\rightarrow$ `banter_meme`
  - Product defect / failure $\rightarrow$ `product_complaint`
  - Shipping delay / refund refusal $\rightarrow$ `service_complaint`
  - Crypto / affiliate links $\rightarrow$ `spam`
  - Spec inquiries / sizing $\rightarrow$ `neutral`
