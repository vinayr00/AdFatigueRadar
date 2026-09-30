# AdFatigueRadar — Reproducibility & Environment Report

**Audit Date:** 2026-09-30  
**Audit Scope:** Environment, Pipeline, and Artifact Determinism Verification  

---

## 1. Operating Environment Specifications

| Component | Audited Environment Value | Verification Method |
| :--- | :--- | :--- |
| **Operating System** | Windows 11 Home / Pro (64-bit AMD64) | `sys.platform`, `platform.version()` |
| **Python Version** | 3.12.3 (v3.12.3:f6650f9) | `sys.version` |
| **PyTorch Version** | 2.7.1+cu118 (CUDA 11.8 Enabled) | `torch.__version__`, `torch.version.cuda` |
| **Primary GPU** | NVIDIA GeForce GTX 1650 (4 GB VRAM) | `torch.cuda.get_device_name(0)` |
| **Transformers** | 4.40.0 | `transformers.__version__` |
| **scikit-learn** | 1.5.1 | `sklearn.__version__` |
| **FastAPI** | 0.111.0 | `fastapi.__version__` |
| **Pydantic** | 2.13.4 | `pydantic.__version__` |
| **Git Commit** | `dbf6b4206f4c99dec3b8324bdcbc28ad75c926d0` | `git rev-parse HEAD` |
| **Git Branch** | `NlpPipeline` | `git branch --show-current` |

---

## 2. Cryptographic Integrity Checklist

All production model weights, temperature calibration parameters, taxonomy configurations, and frozen evaluation datasets have verified SHA-256 digests:

```
# Production Model Artifacts (backend/nlp/artifacts/checksums.sha256)
3e4b8fdbc39394ead9b1b8161c3afe5f5001114e2ee848c519523da0151dbee1  phase3_final_model.joblib
c75a6fbf7fa347e044705a95b8a7e9300510574478e91e7c5b5058dc38481fd6  phase3_temperature_scaler.json
b17644c5243b0bd8d1e0e8e20572bfc06231caf1791b845867bd057fe9d9a847  phase3_class_mapping.json
c1b059c2bc3b251e3afc603e376a21bfa6816824c2a1972b7aa13b7aa27ab5fb  phase3_config.json
64191b728eb7f9c2866bd9a622740ae2f12140070759ee9c14dffa634f25c4d6  taxonomy_model.joblib

# Frozen Real-World Test Dataset (data/real_world/test/test.jsonl)
82dacabc48ba6d5ae57df9b647d6928e1d743a6d45f4f46a297920786cfba7e9  test.jsonl (299 records)
```

---

## 3. End-to-End Pipeline Execution Verification

1. **Test Set Evaluation (`scripts/eval_real_world.py`):**
   - Re-evaluating the frozen test set (`data/real_world/test/test.jsonl`) deterministically outputs:
     - Accuracy: **65.55%**
     - Macro-F1: **0.6200**
     - Weighted-F1: **0.6472**
     - ECE: **0.0626**
2. **Regression Test Suite (`pytest -q`):**
   - Executing `pytest -q` runs 59 unit, integration, and security tests:
     - Output: `59 passed in ~42s` (0 failures, 0 errors).
3. **Production Server Launch (`backend/api/app.py`):**
   - Command: `uvicorn backend.api.app:app --host 0.0.0.0 --port 8000`
   - Initializes on `cuda:0`, passes SHA-256 verification, and serves `/health` and `/ready` probes.
