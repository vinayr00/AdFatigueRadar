# AdFatigueRadar — Complete Production Reproducibility Guide

**Audit Date:** 2026-09-30  
**Target:** Engineering Handoff & Environment Re-creation  

---

## 1. System Requirements & Pinned Dependencies

```
OS: Windows 11 / Linux (x86_64)
Python: 3.12.3
CUDA: 11.8 (Supported on NVIDIA GeForce GTX 1650 4GB+)
PyTorch: 2.7.1+cu118
Transformers: 4.40.0
scikit-learn: 1.5.1
FastAPI: 0.111.0
Pydantic: 2.13.4
```

---

## 2. Step-by-Step Reproduction Workflow

### Step 1: Environment Setup
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install transformers scikit-learn fastapi uvicorn pydantic pytest requests
```

### Step 2: Verify GPU Acceleration
```powershell
python -c "import torch; print('CUDA Available:', torch.cuda.is_available(), 'Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

### Step 3: Run Full Regression Suite
```powershell
pytest -q
# Expected: 59 passed in ~45s
```

### Step 4: Evaluate Frozen Real-World Test Set
```powershell
python scripts/eval_real_world.py
# Expected Output: Accuracy: 65.55%, Macro-F1: 0.6200, ECE: 0.0626
```

### Step 5: Start Production API Server
```powershell
uvicorn backend.api.app:app --host 0.0.0.0 --port 8000
```

### Step 6: Test Health and Prediction Endpoints
```powershell
# Health check
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/ready

# Single comment prediction
curl -X POST http://localhost:8000/api/nlp/predict `
  -H "Content-Type: application/json" `
  -d '{\"text\": \"This ad keeps popping up every 5 minutes, so annoying!\"}'
```
