"""
AdFatigueRadar — Live Model Demonstration & Real-World Text Reviewer
===================================================================
Interactive live reviewer tool to demonstrate the NLP model on any real-world comment.

Usage:
  1. Interactive REPL (Recommended for Live Reviews):
     python demo_live.py

  2. Direct CLI Input:
     python demo_live.py "Bro this ad again 😂 make it stop"

  3. Run Built-In Benchmark Demo Suite:
     python demo_live.py --demo-suite
"""

import sys
import os
import time
import json
import warnings
from datetime import datetime, timezone

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Suppress HuggingFace / PyTorch initialization warnings for clean presentation
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
warnings.filterwarnings("ignore")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

from backend.nlp.classifier import CommentClassifier
from backend.nlp.pii_sanitizer import PIISanitizer

# ANSI color codes for rich terminal display
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

CATEGORY_WEIGHTS = {
    "product_complaint": (1.00, RED, "Product defect / functional issue"),
    "service_complaint": (1.00, RED, "Customer support / logistics / billing"),
    "fatigue": (0.80, YELLOW, "Repeated ad exposure / creative burnout"),
    "mockery": (0.75, MAGENTA, "Satire / ad ridicule / cringe roast"),
    "spam": (0.60, YELLOW, "Crypto / bot / promotional solicitation"),
    "banter_meme": (0.00, CYAN, "Harmless humor / banter / pop meme (0.00 harm)"),
    "neutral": (0.00, DIM, "Informational query / neutral observation"),
    "positive": (0.00, GREEN, "Praise / repeat purchase ('bought again')")
}

DEMO_TEST_SUITE = [
    ("⚡ Ad Fatigue (Repeated Exposure)", "Bro this ad again 😂 please make it stop! 4th time seeing it today"),
    ("⚡ The 'Again' Rule (Positive Purchase)", "Bought again, love this product so much! Fast delivery too"),
    ("⚡ Mockery & Sarcasm (Ad Ridicule)", "Whoever approved this commercial deserves a clown award 🤡 worst acting ever"),
    ("⚡ Banter / Meme (Harmless Engagement)", "literally me at 3am staring into the void lmao"),
    ("⚡ Critical Service Complaint (Emergency Trigger)", "You charged my card twice and support stopped replying, absolute scam refund me!"),
    ("⚡ Product Complaint (Defect)", "The app keeps freezing and crashing whenever I try to checkout, totally broken"),
    ("⚡ Bot Spam / Phishing", "Dm me on Telegram @fastcrypto for 500% guaranteed weekly returns!"),
    ("⚡ Neutral Inquiry", "Does this model come in blue or is it only available in black?")
]

def format_banner():
    sep = "=" * 80
    print(f"\n{BOLD}{CYAN}{sep}")
    print("   ADFATIGUERADAR — LIVE REAL-WORLD NLP CLASSIFIER DEMO")
    print("   Two-Stage Model: RoBERTa Sentiment + 8-Class Ad-Fatigue Taxonomy")
    print(f"{sep}{RESET}\n")

def run_classification(text: str, classifier: CommentClassifier, sanitizer: PIISanitizer, comment_id: str = "demo_comment"):
    print(f"\n{BOLD}{'─' * 80}{RESET}")
    print(f"{BOLD}📥 INPUT COMMENT:{RESET} {CYAN}\"{text}\"{RESET}")
    
    # 1. PII Sanitization
    t_start = time.perf_counter()
    clean_text, pii_meta = sanitizer.sanitize(text)
    
    # 2. Model Inference
    result = classifier.classify_text(clean_text, comment_id=comment_id)
    t_elapsed_ms = (time.perf_counter() - t_start) * 1000
    
    cat = result.category
    weight, color, desc = CATEGORY_WEIGHTS.get(cat, (0.0, RESET, "Unknown"))
    
    sentiment_color = GREEN if result.sentiment == "positive" else (RED if result.sentiment == "negative" else CYAN)
    crit_badge = f"{BOLD}{RED}[CRITICAL COMPLAINT: YES]{RESET}" if result.critical_complaint else f"{DIM}[Critical: No]{RESET}"
    
    print(f"\n{BOLD}🔍 LIVE MODEL OUTPUT & RISK SIGNALS:{RESET}")
    print(f"  ├─ {BOLD}Normalized Text:{RESET}      \"{clean_text}\"")
    if pii_meta.get("scrubbed_count", 0) > 0:
        print(f"  ├─ {YELLOW}PII Scrubbed:{RESET}          {pii_meta}")
        
    print(f"  ├─ {BOLD}Stage 1 (Sentiment):{RESET}   {sentiment_color}{result.sentiment.upper()}{RESET} (Calibrated Score: {result.sentiment_score:.2f})")
    print(f"  ├─ {BOLD}Stage 2 (Taxonomy):{RESET}    {color}{BOLD}{cat.upper()}{RESET} ({desc})")
    print(f"  ├─ {BOLD}Confidence:{RESET}            {color}{result.confidence:.1%}{RESET}")
    print(f"  ├─ {BOLD}Risk Engine Weight:{RESET}    {BOLD}{weight:.2f}{RESET} / 1.00 (Harmful Share Contribution)")
    print(f"  ├─ {BOLD}Emergency Flag:{RESET}        {crit_badge}")
    print(f"  └─ {BOLD}Inference Latency:{RESET}     {GREEN}{t_elapsed_ms:.2f} ms{RESET} (CPU)")
    
    # Output frozen JSON Schema
    print(f"\n{DIM}📦 Frozen JSON Output Contract (consumed by Backend Risk Engine):{RESET}")
    contract_json = {
        "comment_id": result.comment_id,
        "sentiment": result.sentiment,
        "sentiment_score": round(result.sentiment_score, 4),
        "category": result.category,
        "confidence": round(result.confidence, 4),
        "critical_complaint": result.critical_complaint,
        "harmful_weight": weight,
        "latency_ms": round(t_elapsed_ms, 2)
    }
    print(f"{CYAN}{json.dumps(contract_json, indent=2)}{RESET}")
    print(f"{BOLD}{'─' * 80}{RESET}")

def run_interactive_mode(classifier: CommentClassifier, sanitizer: PIISanitizer):
    format_banner()
    print(f"{BOLD}Commands:{RESET}")
    print(f"  • Type or paste {BOLD}any real-world comment{RESET} and press Enter")
    print(f"  • Type {YELLOW}'demo'{RESET} or {YELLOW}'suite'{RESET} to run the 8 curated taxonomy benchmark cases")
    print(f"  • Type {YELLOW}'1'..'8'{RESET} to run a specific test case immediately")
    print(f"  • Type {RED}'exit'{RESET} or {RED}'quit'{RESET} to exit\n")
    
    count = 1
    while True:
        try:
            user_input = input(f"\n{BOLD}{GREEN}[AdFatigueRadar] Enter comment > {RESET}").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print(f"\n{CYAN}Exiting demo. Goodbye!{RESET}\n")
                break
            elif user_input.lower() in ["demo", "suite", "test", "all"]:
                print(f"\n{BOLD}{YELLOW}Running Curated 8-Class Benchmark Test Suite...{RESET}")
                for title, text in DEMO_TEST_SUITE:
                    print(f"\n{BOLD}{MAGENTA}─── {title} ───{RESET}")
                    run_classification(text, classifier, sanitizer, comment_id=f"demo_suite_{count}")
                    count += 1
            elif user_input.isdigit() and 1 <= int(user_input) <= len(DEMO_TEST_SUITE):
                idx = int(user_input) - 1
                title, text = DEMO_TEST_SUITE[idx]
                print(f"\n{BOLD}{MAGENTA}─── {title} ───{RESET}")
                run_classification(text, classifier, sanitizer, comment_id=f"demo_{idx+1}")
                count += 1
            else:
                run_classification(user_input, classifier, sanitizer, comment_id=f"live_{count}")
                count += 1
        except KeyboardInterrupt:
            print(f"\n\n{CYAN}Session ended.{RESET}\n")
            break
        except Exception as e:
            print(f"\n{RED}Error during classification: {e}{RESET}")

def main():
    print(f"{DIM}Initializing AdFatigueRadar NLP engine and loading weights...{RESET}", end="", flush=True)
    classifier = CommentClassifier(use_cache=False)
    sanitizer = PIISanitizer()
    print(f"\r{GREEN}✓ Model loaded successfully. Ready for evaluation.{RESET}\n")
    
    if len(sys.argv) > 1:
        arg = " ".join(sys.argv[1:]).strip()
        if arg in ["--demo-suite", "--suite", "-s"]:
            format_banner()
            for title, text in DEMO_TEST_SUITE:
                print(f"\n{BOLD}{MAGENTA}─── {title} ───{RESET}")
                run_classification(text, classifier, sanitizer)
        else:
            format_banner()
            run_classification(arg, classifier, sanitizer)
    else:
        run_interactive_mode(classifier, sanitizer)

if __name__ == "__main__":
    main()
