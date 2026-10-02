"""
AdFatigueRadar — Production Model Loader & Integrity Verifier (Phase 4)
=======================================================================
Enforces strict fail-closed artifact verification, SHA-256 integrity checks,
explicit device allocation (CUDA / CPU), and safe deserialization of frozen Phase 3 weights.
"""

import os
import sys
from pathlib import Path
import json
import hashlib
import joblib
from typing import Dict, Any, Tuple, Optional
import torch

from .constants import TAXONOMY_CATEGORIES, MODEL_VERSION, PREPROCESSING_VERSION
from .calibration import TemperatureScaler

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
CHECKSUMS_FILE = os.path.join(ARTIFACTS_DIR, "checksums.sha256")
PHASE3_MODEL_FILE = os.path.join(ARTIFACTS_DIR, "phase3_final_model.joblib")
PHASE3_SCALER_FILE = os.path.join(ARTIFACTS_DIR, "phase3_temperature_scaler.json")
PHASE3_CONFIG_FILE = os.path.join(ARTIFACTS_DIR, "phase3_config.json")
PHASE3_MAPPING_FILE = os.path.join(ARTIFACTS_DIR, "phase3_class_mapping.json")


def resolve_local_transformer_dir(path: str | os.PathLike[str]) -> str:
    """Resolve a local model directory before Transformers can parse it as a Hub ID."""
    candidate = Path(path).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise FileNotFoundError(f"Local transformer model directory does not exist: {candidate}") from exc
    if not resolved.is_dir():
        raise FileNotFoundError(f"Local transformer model path is not a directory: {resolved}")
    required = ("config.json",)
    missing = [name for name in required if not (resolved / name).is_file()]
    has_tokenizer = any(
        (resolved / name).is_file()
        for name in ("tokenizer.json", "vocab.json", "spiece.model", "sentencepiece.bpe.model")
    )
    weight_files = [name for name in ("model.safetensors", "pytorch_model.bin") if (resolved / name).is_file()]
    index_files = [resolved / name for name in ("model.safetensors.index.json", "pytorch_model.bin.index.json") if (resolved / name).is_file()]
    for index_file in index_files:
        try:
            index_data = json.loads(index_file.read_text(encoding="utf-8"))
            weight_files.extend(sorted(set(index_data.get("weight_map", {}).values())))
        except (OSError, ValueError, TypeError):
            missing.append(index_file.name + " with a valid weight_map")
    has_weights = bool(weight_files) and all((resolved / name).is_file() for name in weight_files)
    if not has_tokenizer:
        missing.append("tokenizer.json, vocab.json, or SentencePiece model")
    if not has_weights:
        missing.append("model.safetensors or pytorch_model.bin")
    if missing:
        raise FileNotFoundError(f"Local transformer model is incomplete at {resolved}; missing: {', '.join(missing)}")
    return str(resolved)


class ArtifactIntegrityError(RuntimeError):
    """Raised when artifact SHA-256 checksum fails or file is missing/tampered with."""
    pass


class ProductionModelBundle:
    """Encapsulates verified and loaded production NLP models and calibrators."""
    def __init__(
        self,
        classifier: Any,
        temperature: float,
        operational_threshold: float,
        class_mapping: Dict[str, int],
        device: torch.device,
        model_version: str,
        config: Dict[str, Any],
        checksums: Dict[str, str]
    ):
        self.classifier = classifier
        self.temperature = temperature
        self.scaler = TemperatureScaler(temperature=temperature)
        self.operational_threshold = operational_threshold
        self.class_mapping = class_mapping
        self.idx_to_class = {v: k for k, v in class_mapping.items()}
        self.device = device
        self.model_version = model_version
        self.config = config
        self.checksums = checksums


def verify_artifact_checksums() -> Dict[str, str]:
    """
    Verifies all production artifact SHA-256 checksums against checksums.sha256.
    Fails closed if any artifact is missing, unreadable, or modified.
    """
    if not os.path.exists(CHECKSUMS_FILE):
        raise ArtifactIntegrityError(f"Critical checksums manifest missing at: {CHECKSUMS_FILE}")
    
    verified_hashes = {}
    with open(CHECKSUMS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                expected_hash = parts[0].strip()
                filename = parts[1].strip()
                filepath = os.path.join(ARTIFACTS_DIR, filename)
                
                if not os.path.exists(filepath):
                    raise ArtifactIntegrityError(f"Required artifact '{filename}' missing at {filepath}")
                
                # Compute SHA-256
                hasher = hashlib.sha256()
                with open(filepath, "rb") as af:
                    while chunk := af.read(65536):
                        hasher.update(chunk)
                actual_hash = hasher.hexdigest()
                
                if actual_hash.lower() != expected_hash.lower():
                    raise ArtifactIntegrityError(
                        f"Integrity check FAILED for artifact '{filename}'!\n"
                        f"Expected SHA-256: {expected_hash}\n"
                        f"Actual SHA-256  : {actual_hash}"
                    )
                verified_hashes[filename] = actual_hash
                
    return verified_hashes


def load_production_model(device_mode: str = "auto") -> ProductionModelBundle:
    """
    Loads the frozen Phase 3 candidate model with full integrity verification.
    
    Args:
        device_mode (str): 'auto', 'cuda', or 'cpu'
        
    Returns:
        ProductionModelBundle: Verified model bundle ready for inference.
    """
    print("[ModelLoader] 1/4 Verifying SHA-256 artifact integrity...")
    verified_checksums = verify_artifact_checksums()
    print(f"  [OK] Verified {len(verified_checksums)} production artifacts via SHA-256.")

    print("[ModelLoader] 2/4 Initializing compute device...")
    if device_mode == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    elif device_mode == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was explicitly requested (device_mode='cuda') but is unavailable!")
        device = torch.device("cuda")
    elif device_mode == "cpu":
        device = torch.device("cpu")
    else:
        raise ValueError(f"Invalid device_mode '{device_mode}'. Must be 'auto', 'cuda', or 'cpu'.")

    device_name = torch.cuda.get_device_name(0) if device.type == "cuda" else "Host CPU"
    print(f"  [OK] Target compute device: {device} ({device_name})")

    print("[ModelLoader] 3/4 Loading Phase 3 model artifacts and configuration...")
    if not os.path.exists(PHASE3_MODEL_FILE):
        raise FileNotFoundError(f"Phase 3 model file missing at: {PHASE3_MODEL_FILE}")
        
    raw_bundle = joblib.load(PHASE3_MODEL_FILE)
    if isinstance(raw_bundle, dict):
        classifier = raw_bundle.get("model") or raw_bundle.get("classifier")
        temperature = float(raw_bundle.get("temperature", 1.0494))
        operational_threshold = float(raw_bundle.get("critical_threshold", 0.50))
        class_mapping = raw_bundle.get("class_mapping", {cat: i for i, cat in enumerate(TAXONOMY_CATEGORIES)})
    else:
        # Direct classifier object
        classifier = raw_bundle
        temperature = 1.0494
        operational_threshold = 0.50
        class_mapping = {cat: i for i, cat in enumerate(TAXONOMY_CATEGORIES)}

    # Load scaler JSON if present
    if os.path.exists(PHASE3_SCALER_FILE):
        with open(PHASE3_SCALER_FILE, "r", encoding="utf-8") as f:
            scaler_data = json.load(f)
            temperature = float(scaler_data.get("temperature", temperature))

    # Load config JSON if present
    config = {}
    if os.path.exists(PHASE3_CONFIG_FILE):
        with open(PHASE3_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            operational_threshold = float(config.get("critical_complaint_threshold", operational_threshold))

    bundle = ProductionModelBundle(
        classifier=classifier,
        temperature=temperature,
        operational_threshold=operational_threshold,
        class_mapping=class_mapping,
        device=device,
        model_version=MODEL_VERSION,
        config=config,
        checksums=verified_checksums
    )

    print("[ModelLoader] 4/4 Running startup sanity check...")
    # Verify classifier has predict_proba or decision_function
    assert hasattr(bundle.classifier, "predict_proba") or hasattr(bundle.classifier, "decision_function"), \
        "Loaded model does not have expected scikit-learn classification methods!"
    
    print(f"  [OK] Model Loaded Successfully: {bundle.model_version} (T={bundle.temperature:.4f}, tau={bundle.operational_threshold:.2f})")
    return bundle
