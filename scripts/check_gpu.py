"""
AdFatigueRadar — GPU Diagnostic & CUDA Verification Script
==========================================================
Verifies NVIDIA CUDA hardware, driver, PyTorch CUDA build, VRAM, and executes
tensor matmul, transformer inference, and embedding smoke tests on the GPU.
"""

import sys
import os

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import torch

def run_gpu_diagnostic():
    print("=" * 70)
    print("       ADFATIGUERADAR -- GPU & CUDA DIAGNOSTIC REPORT")
    print("=" * 70)
    
    python_ver = sys.version.replace('\n', ' ')
    torch_ver = torch.__version__
    cuda_runtime = torch.version.cuda
    cuda_available = torch.cuda.is_available()
    cudnn_available = torch.backends.cudnn.is_available()
    cudnn_version = torch.backends.cudnn.version() if cudnn_available else "N/A"
    
    print(f"  - Python Version         : {python_ver}")
    print(f"  - PyTorch Version        : {torch_ver}")
    print(f"  - PyTorch CUDA Runtime   : {cuda_runtime}")
    print(f"  - CUDA Available         : {cuda_available}")
    print(f"  - cuDNN Available        : {cudnn_available} (v{cudnn_version})")
    
    if not cuda_available:
        print("\n[FAIL] CRITICAL: CUDA is NOT available to PyTorch!")
        print("       Cannot proceed with GPU-accelerated training/inference.")
        sys.exit(1)
        
    device_count = torch.cuda.device_count()
    device_name = torch.cuda.get_device_name(0)
    device_props = torch.cuda.get_device_properties(0)
    total_memory_mb = device_props.total_memory / (1024 ** 2)
    
    print(f"  - GPU Device Count       : {device_count}")
    print(f"  - Primary GPU Name       : {device_name}")
    print(f"  - Total VRAM             : {total_memory_mb:.2f} MiB ({total_memory_mb/1024:.2f} GB)")
    print(f"  - Compute Capability     : {device_props.major}.{device_props.minor}")
    
    # 1. Tensor Matrix Multiplication Test
    print("\n[Test 1] Executing GPU Tensor Matrix Multiplication (2048 x 2048)...")
    torch.cuda.empty_cache()
    init_allocated = torch.cuda.memory_allocated(0) / (1024 ** 2)
    init_reserved = torch.cuda.memory_reserved(0) / (1024 ** 2)
    
    x = torch.randn(2048, 2048, device="cuda", dtype=torch.float32)
    y = x @ x
    torch.cuda.synchronize()
    
    post_allocated = torch.cuda.memory_allocated(0) / (1024 ** 2)
    post_reserved = torch.cuda.memory_reserved(0) / (1024 ** 2)
    print(f"  [PASS] Matmul Success! Shape: {tuple(y.shape)}, Device: {y.device}")
    print(f"  - Memory Allocated       : {post_allocated:.2f} MiB (Delta: +{post_allocated - init_allocated:.2f} MiB)")
    print(f"  - Memory Reserved        : {post_reserved:.2f} MiB")
    
    del x, y
    torch.cuda.empty_cache()

    # 2. Hugging Face Transformer Inference Test on GPU
    print("\n[Test 2] Loading RoBERTa Sentiment Model onto GPU...")
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModel
    
    model_path = os.path.join(os.path.dirname(__file__), "..", "data", "models", "twitter-roberta-base-sentiment-latest")
    if not os.path.exists(model_path):
        print(f"  [WARN] Local model path not found at {model_path}. Skipping transformer test.")
        return
        
    device = torch.device("cuda")
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    sent_model = AutoModelForSequenceClassification.from_pretrained(model_path, local_files_only=True).to(device)
    sent_model.eval()
    
    sample_text = ["This ad is so exhausting, stop showing it every 2 minutes!"]
    inputs = tokenizer(sample_text, padding=True, truncation=True, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        out = sent_model(**inputs)
        probs = torch.softmax(out.logits, dim=-1).cpu().numpy()
        
    trans_allocated = torch.cuda.memory_allocated(0) / (1024 ** 2)
    print(f"  [PASS] Transformer Forward Pass Success!")
    print(f"  - Model Device           : {next(sent_model.parameters()).device}")
    print(f"  - Input Tensor Device    : {inputs['input_ids'].device}")
    print(f"  - Output Probs (3-class) : {probs[0]}")
    print(f"  - GPU VRAM Allocated     : {trans_allocated:.2f} MiB")

    # 3. Dense Embedding Extraction Test on GPU
    print("\n[Test 3] Loading RoBERTa Backbone for Embedding Generation on GPU...")
    base_model = AutoModel.from_pretrained(model_path, local_files_only=True).to(device)
    base_model.eval()
    
    with torch.no_grad():
        base_out = base_model(**inputs)
        mask = inputs["attention_mask"].unsqueeze(-1).expand(base_out.last_hidden_state.size()).float()
        sum_emb = torch.sum(base_out.last_hidden_state * mask, 1)
        sum_mask = torch.clamp(mask.sum(1), min=1e-9)
        emb = (sum_emb / sum_mask).cpu().numpy()
        
    print(f"  [PASS] Embedding Generation Success!")
    print(f"  - Embedding Shape        : {emb.shape} (768-dim)")
    print(f"  - Total VRAM In Use      : {torch.cuda.memory_allocated(0)/(1024**2):.2f} MiB")
    
    del sent_model, base_model, inputs, out, base_out
    torch.cuda.empty_cache()
    
    print("\n" + "=" * 70)
    print("✅ GPU HARDWARE & CUDA ENVIRONMENT VERIFICATION: ALL TESTS PASSED")
    print("=" * 70)

if __name__ == "__main__":
    run_gpu_diagnostic()
