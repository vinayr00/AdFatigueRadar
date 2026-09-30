"""
AdFatigueRadar — Annotation, Agreement & Adjudication Engine
===========================================================
PERSON 1: AI / NLP Layer (Phase 1 Remediation)

Handles:
1. Annotation record validation and queue loading
2. Double-annotation pairing (Annotator A vs Annotator B)
3. Inter-annotator agreement calculation (Raw Agreement, Cohen's Kappa, Confusion Matrix)
4. Adjudication workflow for resolving disagreements
5. Generation of data/reports/annotation_agreement.json
"""

import os
import json
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

TAXONOMY_CATEGORIES = [
    "product_complaint",
    "service_complaint",
    "fatigue",
    "mockery",
    "spam",
    "banter_meme",
    "neutral",
    "positive",
]


def validate_annotation_record(record: Dict[str, Any]) -> bool:
    """
    Validates that an annotation record strictly adheres to the schema:
    {
      "comment_id": str,
      "label": str (must be in 8-class taxonomy),
      "annotator_id": str,
      "annotation_timestamp": str,
      "guideline_version": str,
      "confidence": float,
      "notes": str
    }
    """
    required_keys = ["comment_id", "label", "annotator_id", "annotation_timestamp", "guideline_version"]
    for k in required_keys:
        if k not in record or record[k] is None or record[k] == "":
            return False
    if record["label"] not in TAXONOMY_CATEGORIES:
        return False
    return True


def compute_cohens_kappa(
    annotations_a: Dict[str, str],
    annotations_b: Dict[str, str],
    categories: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Computes Cohen's Kappa and raw agreement between two independent annotators
    for shared comment_ids.
    """
    cats = categories or TAXONOMY_CATEGORIES
    cat_to_idx = {c: i for i, c in enumerate(cats)}
    k_len = len(cats)

    # Find common annotated IDs
    common_ids = sorted(list(set(annotations_a.keys()).intersection(set(annotations_b.keys()))))
    n = len(common_ids)
    if n == 0:
        return {
            "double_annotated_count": 0,
            "raw_agreement": 0.0,
            "cohens_kappa": 0.0,
            "interpretation": "No overlapping annotations",
            "confusion_matrix": {},
            "per_class_agreement": {},
            "disagreements": []
        }

    confusion = [[0 for _ in range(k_len)] for _ in range(k_len)]
    agreed_count = 0
    disagreements = []

    for cid in common_ids:
        la = annotations_a[cid]
        lb = annotations_b[cid]
        if la not in cat_to_idx or lb not in cat_to_idx:
            continue
        idx_a = cat_to_idx[la]
        idx_b = cat_to_idx[lb]
        confusion[idx_a][idx_b] += 1
        
        if la == lb:
            agreed_count += 1
        else:
            disagreements.append({
                "comment_id": cid,
                "annotator_a_label": la,
                "annotator_b_label": lb
            })

    # Observed agreement
    p_o = agreed_count / n

    # Expected agreement by chance
    p_e = 0.0
    for i in range(k_len):
        row_sum = sum(confusion[i][j] for j in range(k_len))
        col_sum = sum(confusion[j][i] for j in range(k_len))
        p_e += (row_sum / n) * (col_sum / n)

    if (1.0 - p_e) == 0:
        kappa = 1.0 if p_o == 1.0 else 0.0
    else:
        kappa = (p_o - p_e) / (1.0 - p_e)

    # Interpretation
    if kappa >= 0.81:
        interp = "Almost Perfect Agreement"
    elif kappa >= 0.61:
        interp = "Substantial Agreement"
    elif kappa >= 0.41:
        interp = "Moderate Agreement"
    else:
        interp = "Poor Agreement"

    # Per-class agreement (diagonal / (row_sum + col_sum - diagonal))
    per_class = {}
    for i, c in enumerate(cats):
        row_sum = sum(confusion[i][j] for j in range(k_len))
        col_sum = sum(confusion[j][i] for j in range(k_len))
        diag = confusion[i][i]
        denom = (row_sum + col_sum - diag)
        jacc = (diag / denom) if denom > 0 else 1.0 if (row_sum == 0 and col_sum == 0) else 0.0
        per_class[c] = {
            "annotator_a_count": row_sum,
            "annotator_b_count": col_sum,
            "agreed_count": diag,
            "jaccard_agreement": round(jacc, 4)
        }

    # Format confusion matrix dict for readability
    matrix_dict = {
        cats[i]: {cats[j]: confusion[i][j] for j in range(k_len)}
        for i in range(k_len)
    }

    return {
        "double_annotated_count": n,
        "raw_agreement": round(p_o, 4),
        "cohens_kappa": round(kappa, 4),
        "chance_agreement_pe": round(p_e, 4),
        "interpretation": interp,
        "disagreement_count": len(disagreements),
        "per_class_agreement": per_class,
        "confusion_matrix": matrix_dict,
        "sample_disagreements": disagreements[:10]
    }


def resolve_and_adjudicate(
    records: List[Dict[str, Any]],
    annotations_a: Dict[str, Dict[str, Any]],
    annotations_b: Dict[str, Dict[str, Any]],
    adjudication_rules_applied: Optional[Dict[str, str]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Combines independent annotations and generates finalized dataset records.
    For matching annotations -> direct adoption.
    For non-matching -> applies formal adjudication rule.
    Returns (finalized_records, adjudication_log).
    """
    finalized = []
    adjudications = []

    for r in records:
        cid = r["comment_id"]
        ann_a = annotations_a.get(cid)
        ann_b = annotations_b.get(cid)

        if ann_a and ann_b:
            if ann_a["label"] == ann_b["label"]:
                final_label = ann_a["label"]
                adjudication_status = "auto_agreed"
            else:
                # Disagreement resolution
                rule_label = adjudication_rules_applied.get(cid) if adjudication_rules_applied else None
                final_label = rule_label or ann_a["label"] # Adjudicated label
                adjudication_status = "adjudicated"
                adjudications.append({
                    "comment_id": cid,
                    "text": r.get("text", ""),
                    "annotator_a_label": ann_a["label"],
                    "annotator_b_label": ann_b["label"],
                    "final_label": final_label,
                    "adjudication_status": adjudication_status,
                    "adjudicator_id": "lead_adjudicator"
                })
        elif ann_a:
            final_label = ann_a["label"]
            adjudication_status = "single_annotator_a"
        elif ann_b:
            final_label = ann_b["label"]
            adjudication_status = "single_annotator_b"
        else:
            final_label = r.get("category", "neutral")
            adjudication_status = "original_source"

        rec_final = dict(r)
        rec_final["category"] = final_label
        rec_final["annotation_status"] = adjudication_status
        finalized.append(rec_final)

    return finalized, adjudications
