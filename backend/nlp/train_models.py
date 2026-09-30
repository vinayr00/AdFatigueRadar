"""
AdFatigueRadar — Model Training & Calibration Script
===================================================
PERSON 1: AI / NLP Layer

Trains the Stage 2 Taxonomy Classifier using local RoBERTa sentence embeddings
+ scikit-learn LogisticRegression on the TRAIN split only.
Fits TemperatureScaler on the VALIDATION split only.
Saves the artifact with joblib for zero-cold-start inference.
"""

import os
import sys
import json
import joblib
import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

# Ensure local imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.nlp.constants import (
    MODEL_VERSION,
    PREPROCESSING_VERSION,
    TAXONOMY_CATEGORIES,
    DEFAULT_MAX_SEQ_LENGTH,
)
from backend.nlp.preprocessing import normalize_text
from backend.nlp.calibration import TemperatureScaler, compute_expected_calibration_error


def train_and_calibrate():
    print("================================================================")
    print("       AdFatigueRadar — Training Stage 2 Taxonomy Model        ")
    print("================================================================")

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    train_path = os.path.join(base_dir, "data", "training", "labels.jsonl")
    val_path = os.path.join(base_dir, "data", "training", "val_labels.jsonl")
    model_dir = os.path.join(base_dir, "data", "models", "twitter-roberta-base-sentiment-latest")
    artifact_dir = os.path.join(os.path.dirname(__file__), "artifacts")
    os.makedirs(artifact_dir, exist_ok=True)
    artifact_path = os.path.join(artifact_dir, "taxonomy_model.joblib")

    # 1. Load Data
    print(f"\n[1/5] Loading training and validation splits...")
    train_data = [json.loads(l) for l in open(train_path, encoding="utf-8")]
    val_data = [json.loads(l) for l in open(val_path, encoding="utf-8")]
    print(f"  - Train samples: {len(train_data)} (80 per class)")
    print(f"  - Val samples  : {len(val_data)} (20 per class)")

    # 2. Load Local Embedding Model with GPU Acceleration if Available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n[2/5] Loading local embedding backbone from {model_dir} (Device: {device})...")
    tok = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    mod = AutoModel.from_pretrained(model_dir, local_files_only=True)
    mod.to(device)
    mod.eval()

    def get_embeddings(texts, batch_size=32):
        cleaned = [normalize_text(t) for t in texts]
        all_emb = []
        for i in range(0, len(cleaned), batch_size):
            batch = cleaned[i : i + batch_size]
            inputs = tok(
                batch,
                padding=True,
                truncation=True,
                max_length=DEFAULT_MAX_SEQ_LENGTH,
                return_tensors="pt"
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
            with torch.no_grad():
                out = mod(**inputs)
                mask = inputs["attention_mask"].unsqueeze(-1).expand(out.last_hidden_state.size()).float()
                sum_emb = torch.sum(out.last_hidden_state * mask, 1)
                sum_mask = torch.clamp(mask.sum(1), min=1e-9)
                emb = (sum_emb / sum_mask).cpu().numpy()
                all_emb.append(emb)
        return np.vstack(all_emb)

    # 3. Extract Features
    print(f"\n[3/5] Extracting sentence embeddings for train and val splits...")
    X_train = get_embeddings([d["text"] for d in train_data])
    y_train = [d["category"] for d in train_data]

    X_val = get_embeddings([d["text"] for d in val_data])
    y_val = [d["category"] for d in val_data]

    # Map categories to integer indices matching TAXONOMY_CATEGORIES
    cat_to_idx = {cat: i for i, cat in enumerate(TAXONOMY_CATEGORIES)}
    y_train_idx = np.array([cat_to_idx[cat] for cat in y_train])
    y_val_idx = np.array([cat_to_idx[cat] for cat in y_val])

    # 4. Train Logistic Regression Classifier on Train Split Only
    print(f"\n[4/5] Training multi-class Logistic Regression on train split (C=2.5)...")
    clf = LogisticRegression(
        max_iter=1000,
        C=2.5,
        solver="lbfgs",
        random_state=42
    )
    clf.fit(X_train, y_train_idx)

    # 5. Fit Temperature Scaling on Validation Split Only
    print(f"\n[5/5] Fitting Temperature Scaler on VALIDATION split only...")
    val_logits = clf.decision_function(X_val)
    val_preds_uncal = np.argmax(val_logits, axis=1)
    val_conf_uncal = np.max(np.exp(val_logits) / np.sum(np.exp(val_logits), axis=1, keepdims=True), axis=1)
    acc_indicator = (val_preds_uncal == y_val_idx).astype(int)

    ece_before = compute_expected_calibration_error(val_conf_uncal.tolist(), acc_indicator.tolist())

    scaler = TemperatureScaler()
    fitted_t = scaler.fit(val_logits, y_val_idx)

    calibrated_val_probs = np.array([scaler.calibrate_logits(row) for row in val_logits])
    val_conf_cal = np.max(calibrated_val_probs, axis=1)
    val_preds_cal = np.argmax(calibrated_val_probs, axis=1)

    ece_after = compute_expected_calibration_error(val_conf_cal.tolist(), acc_indicator.tolist())

    val_acc = accuracy_score(y_val_idx, val_preds_cal)
    val_macro_f1 = f1_score(y_val_idx, val_preds_cal, average="macro")

    print("\n--- VALIDATION METRICS (Held-out from training) ---")
    print(f"Validation Accuracy     : {val_acc:.4f} ({val_acc*100:.2f}%)")
    print(f"Validation Macro-F1     : {val_macro_f1:.4f}")
    print(f"Fitted Temperature (T)  : {fitted_t:.4f}")
    print(f"ECE (Before Calibration): {ece_before:.4f}")
    print(f"ECE (After Calibration) : {ece_after:.4f}")

    # Save artifact
    artifact = {
        "model_version": MODEL_VERSION,
        "preprocessing_version": PREPROCESSING_VERSION,
        "taxonomy_categories": TAXONOMY_CATEGORIES,
        "classifier": clf,
        "temperature": fitted_t,
        "val_accuracy": val_acc,
        "val_macro_f1": val_macro_f1,
        "ece_before": ece_before,
        "ece_after": ece_after,
    }
    joblib.dump(artifact, artifact_path)
    print(f"\nSuccessfully saved trained artifact to: {artifact_path}")
    print("================================================================\n")


if __name__ == "__main__":
    train_and_calibrate()
