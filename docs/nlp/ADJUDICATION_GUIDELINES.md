# AdFatigueRadar — Adjudication & Inter-Annotator Agreement Guidelines
=====================================================================
**Version**: `v2.0-real-world`  
**Applicability**: Double-Annotation Verification & Disagreement Resolution  

---

## 1. Dual-Annotation Architecture & Protocol

To establish a gold-standard benchmark, at least **20%** of all real-world comments must be independently double-annotated by two distinct annotators (`Annotator_A` and `Annotator_B`).

### Strict Double-Blind Protocol:
1. `Annotator_B` is never shown `Annotator_A`'s assigned label, confidence, or notes prior to submitting their own annotation.
2. Annotators do not see model-predicted outputs as pre-filled defaults.
3. Every annotation record is uniquely identified and timestamped:
```json
{
  "comment_id": "comm_rw_0042",
  "label": "mockery",
  "annotator_id": "annotator_01",
  "annotation_timestamp": "2026-09-30T14:00:00Z",
  "guideline_version": "v2.0-real-world",
  "confidence": 1.0,
  "notes": "Roasting actor accent without complaining about product defect"
}
```

---

## 2. Disagreement Resolution Workflow

```
       ┌────────────────────────┐        ┌────────────────────────┐
       │      Annotator A       │        │      Annotator B       │
       │    (Independent)       │        │    (Independent)       │
       └───────────┬────────────┘        └───────────┬────────────┘
                   │                                 │
                   └────────────────┬────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Label Match?      │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │ YES                           │ NO
                    ▼                               ▼
       ┌────────────────────────┐      ┌─────────────────────────┐
       │      Final Label       │      │       Adjudication      │
       │    (Auto-Approved)     │      │   (Lead Domain Auditor) │
       └────────────────────────┘      └────────────┬────────────┘
                                                    │
                                                    ▼
                                       ┌─────────────────────────┐
                                       │ Final Adjudicated Label │
                                       │   + Logged Rationale    │
                                       └─────────────────────────┘
```

1. **Exact Match (`Label_A == Label_B`)**: The agreed label is confirmed as the canonical ground truth.
2. **Disagreement (`Label_A != Label_B`)**:
   - The sample is flagged and routed to the **Lead Domain Adjudicator**.
   - The adjudicator reviews the comment text against [`ANNOTATION_GUIDELINES.md`](./ANNOTATION_GUIDELINES.md).
   - The adjudicator records the final label, rationale, and underlying root cause of the ambiguity.
   - Disagreement patterns are reviewed weekly to update guidelines or clarify confusing terminology.

---

## 3. Mathematical Inter-Annotator Agreement Formulas

### A. Raw Agreement ($P_o$)
$$P_o = \frac{\sum_{i=1}^{K} n_{ii}}{N}$$
Where $n_{ii}$ is the count of samples where both annotators agreed on class $i$, and $N$ is the total double-annotated samples.

### B. Cohen's Kappa ($\kappa$)
$$\kappa = \frac{P_o - P_e}{1 - P_e}$$
Where $P_e$ is the hypothetical probability of chance agreement:
$$P_e = \sum_{i=1}^{K} \left( \frac{n_{i\cdot}}{N} \times \frac{n_{\cdot i}}{N} \right)$$
* Interpretation scale:
  - $\kappa \ge 0.81$: Almost Perfect Agreement
  - $0.61 \le \kappa \le 0.80$: Substantial Agreement (Minimum acceptable threshold for production NLP ground-truth)
  - $0.41 \le \kappa \le 0.60$: Moderate Agreement (Triggers mandatory guideline clarification for confusing classes)
  - $\kappa < 0.40$: Poor Agreement (Invalidates dataset split until re-annotated)

---

## 4. Adjudication Log Schema

When a disagreement is adjudicated, an entry is appended to `data/annotations/adjudications.jsonl`:
```json
{
  "comment_id": "comm_rw_0189",
  "text": "Bro really dropped a 3 minute documentary for socks 😂",
  "annotator_a_id": "ann_01",
  "annotator_a_label": "mockery",
  "annotator_b_id": "ann_02",
  "annotator_b_label": "banter_meme",
  "adjudicator_id": "lead_adjudicator",
  "final_label": "banter_meme",
  "adjudication_timestamp": "2026-09-30T14:30:00Z",
  "rationale": "Humorous light teasing without attacking brand quality or product legitimacy.",
  "confusion_pair": "mockery_vs_banter_meme"
}
```
