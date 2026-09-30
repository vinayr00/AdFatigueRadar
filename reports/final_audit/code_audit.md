# AdFatigueRadar — Comprehensive Codebase & Architecture Audit

**Audit Date:** 2026-09-30  
**Scope:** Backend, NLP Pipelines, Serving Engine, APIs, Test Suite, Dead Code Analysis  

---

## 1. Architectural Architecture & Component Trace

1. **`backend/nlp/schemas.py`**:
   - Pydantic v2 data models: `NLPRequest`, `BatchNLPRequest`, `NLPResponse`, `BatchNLPResponse`, `HealthResponse`, `ReadinessResponse`, `MetricsResponse`, `DriftStatusResponse`, and `ErrorResponse`.
   - Payload length gating: $1 \le \text{length} \le 4000$ characters. Batch size limit: $\le 128$.
2. **`backend/nlp/model_loader.py`**:
   - Centralized singleton loader. Cryptographically validates SHA-256 hashes of all 5 artifacts in `checksums.sha256` before invoking joblib deserialization. Fails closed (`ArtifactIntegrityError`) on mismatch.
3. **`backend/nlp/serving_engine.py`**:
   - Thread-safe singleton orchestrator managing CardiffNLP RoBERTa feature extractors and Logistic Regression classifier heads.
   - Enforces `torch.inference_mode()`, batch chunking (32 items), automated PII redaction, two-tier cache lookup, and real-time latency percentile telemetry.
4. **`backend/nlp/cache.py`**:
   - Two-tier cache (L1 In-Memory + L2 SQLite).
   - Deterministic cache key: $\text{SHA-256}(\text{normalized\_text} + \text{model\_version} + \text{preprocessing\_version})$.
   - Handles corrupted SQLite databases gracefully by operating in memory-only fallback mode.
5. **`backend/nlp/drift_monitor.py`**:
   - In-memory rolling prediction stream monitor with background asynchronous daemon.
   - Computes Population Stability Index (PSI) and Jensen-Shannon (JS) divergence against the baseline distribution.
6. **`backend/api/app.py`**:
   - Production FastAPI application with endpoints:
     - `POST /api/nlp/predict`
     - `POST /api/nlp/predict/batch`
     - `GET /health`
     - `GET /ready`
     - `GET /api/nlp/metrics`
     - `GET /api/nlp/drift`
     - `POST /api/nlp/drift/check`
   - Exception masking middleware redacting raw internal tracebacks and filesystem paths.

---

## 2. Dead Code & Duplicate Implementation Analysis

- **`backend/nlp/artifacts/taxonomy_model.joblib`**: Retained for Phase 0 baseline evaluation and regression comparison (Intentional).
- **`backend/nlp/signals.py` vs `build_real_world_pipeline.py`**: `signals.py` provides runtime CardiffNLP inference; `build_real_world_pipeline.py` contains offline batch preprocessing utilities. No runtime collision detected.
- **Unused Exploratory Files**: Exploratory files (`realdata/`, `testpipeline.py`, `demo_live.py`) exist in workspace root as scratch scripts and are strictly excluded from the production API serving path.

---

## 3. Test Coverage & Robustness
- 59 automated test cases in `backend/tests/`:
  - 48 Phase 0/1/2 regression and contract tests.
  - 11 Phase 4 production serving, API, cache, PII, and drift tests.
- Execution status: 59 passed in 45.27s with zero failures.
