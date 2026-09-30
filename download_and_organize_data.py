"""
Data Download and Organization Script for AdFatigue Project
Downloads and organizes:
1. mteb/banking77 (Intent Classification Dataset)
2. cardiffnlp/tweeteval (Tweet Evaluation Benchmark Datasets: irony, sentiment, emotion, hate, offensive, stance, emoji)
3. cardiffnlp/twitter-roberta-base-irony (Model & Tokenizer)
4. cardiffnlp/twitter-roberta-base-sentiment-latest (Model & Tokenizer)
5. cardiffnlp/twitter-xlm-roberta-base-sentiment (Multilingual Model & Tokenizer)
"""

import os
import sys
import json
import zipfile
import io
import urllib.request
import pandas as pd
from huggingface_hub import snapshot_download

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def log(msg):
    print(f"[INFO] {msg}", flush=True)

def download_banking77():
    log("=== Downloading Banking77 Dataset ===")
    banking77_dir = os.path.join(DATA_DIR, "banking77")
    os.makedirs(banking77_dir, exist_ok=True)
    
    # Download dataset files from huggingface hub
    snapshot_download(
        repo_id="mteb/banking77",
        repo_type="dataset",
        local_dir=banking77_dir,
        ignore_patterns=[".git*"]
    )
    
    # Convert parquet to clean CSV and JSONL if present
    parquet_train = os.path.join(banking77_dir, "data", "train-00000-of-00001.parquet")
    parquet_test = os.path.join(banking77_dir, "data", "test-00000-of-00001.parquet")
    
    if os.path.exists(parquet_train) and os.path.exists(parquet_test):
        df_train = pd.read_parquet(parquet_train)
        df_test = pd.read_parquet(parquet_test)
        
        csv_dir = os.path.join(banking77_dir, "csv")
        os.makedirs(csv_dir, exist_ok=True)
        df_train.to_csv(os.path.join(csv_dir, "train.csv"), index=False)
        df_test.to_csv(os.path.join(csv_dir, "test.csv"), index=False)
        
        log(f"Banking77 processed: Train samples={len(df_train)}, Test samples={len(df_test)}")
    log("Banking77 download completed.")

def download_tweeteval():
    log("=== Downloading CardiffNLP TweetEval Dataset ===")
    tweeteval_dir = os.path.join(DATA_DIR, "tweeteval")
    os.makedirs(tweeteval_dir, exist_ok=True)
    
    url = "https://github.com/cardiffnlp/tweeteval/archive/refs/heads/main.zip"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    log(f"Fetching {url}...")
    with urllib.request.urlopen(req) as resp:
        zip_bytes = resp.read()
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for member in z.infolist():
            # Extract only contents inside tweeteval-main/
            if member.filename.startswith("tweeteval-main/"):
                rel_path = member.filename[len("tweeteval-main/"):]
                if not rel_path:
                    continue
                dest_path = os.path.join(tweeteval_dir, rel_path)
                if member.is_dir():
                    os.makedirs(dest_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    with z.open(member) as src_file, open(dest_path, "wb") as dst_file:
                        dst_file.write(src_file.read())
                        
    log("TweetEval GitHub repository unpacked.")
    
    # Process text + label files into convenient unified CSV/JSONL for key tasks: irony, sentiment, emotion, offensive, hate
    datasets_base = os.path.join(tweeteval_dir, "datasets")
    if os.path.exists(datasets_base):
        for task in os.listdir(datasets_base):
            task_path = os.path.join(datasets_base, task)
            if not os.path.isdir(task_path):
                continue
            
            mapping_file = os.path.join(task_path, "mapping.txt")
            mapping = {}
            if os.path.exists(mapping_file):
                with open(mapping_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        parts = line.strip().split("\t")
                        if len(parts) == 2:
                            mapping[int(parts[0])] = parts[1]
            
            for split in ["train", "val", "test"]:
                text_file = os.path.join(task_path, f"{split}_text.txt")
                labels_file = os.path.join(task_path, f"{split}_labels.txt")
                
                if os.path.exists(text_file) and os.path.exists(labels_file):
                    with open(text_file, "r", encoding="utf-8", errors="ignore") as ft:
                        texts = [l.strip() for l in ft.readlines()]
                    with open(labels_file, "r", encoding="utf-8", errors="ignore") as fl:
                        labels = [int(l.strip()) for l in fl.readlines() if l.strip()]
                    
                    if len(texts) == len(labels):
                        label_names = [mapping.get(lbl, str(lbl)) for lbl in labels]
                        df = pd.DataFrame({"text": texts, "label": labels, "label_name": label_names})
                        df.to_csv(os.path.join(task_path, f"{split}.csv"), index=False)
                        df.to_parquet(os.path.join(task_path, f"{split}.parquet"), index=False)
        log("TweetEval sub-tasks converted to unified tabular formats (CSV & Parquet).")

def download_models():
    models = [
        ("twitter-roberta-base-irony", "cardiffnlp/twitter-roberta-base-irony"),
        ("twitter-roberta-base-sentiment-latest", "cardiffnlp/twitter-roberta-base-sentiment-latest"),
        ("twitter-xlm-roberta-base-sentiment", "cardiffnlp/twitter-xlm-roberta-base-sentiment"),
    ]
    
    models_base_dir = os.path.join(DATA_DIR, "models")
    os.makedirs(models_base_dir, exist_ok=True)
    
    for folder_name, repo_id in models:
        log(f"=== Downloading Model: {repo_id} ===")
        target_dir = os.path.join(models_base_dir, folder_name)
        os.makedirs(target_dir, exist_ok=True)
        snapshot_download(
            repo_id=repo_id,
            repo_type="model",
            local_dir=target_dir,
            ignore_patterns=[".git*", "tf_model.h5", "flax_model.msgpack"] # prioritize PyTorch weights and configs
        )
        log(f"Model {repo_id} saved to {target_dir}")

def generate_catalog():
    log("=== Generating Data Catalog and Structure README ===")
    catalog = {
        "project": "AdFatigueRadar",
        "datasets": {
            "banking77": {
                "description": "77-category customer intent classification dataset for banking and transactional complaints",
                "source": "https://huggingface.co/datasets/mteb/banking77",
                "location": "data/banking77",
                "formats": ["parquet", "jsonl", "csv"]
            },
            "tweeteval": {
                "description": "CardiffNLP TweetEval benchmark datasets (Irony, Sentiment, Emotion, Hate, Offensive, Stance, Emoji)",
                "source": "https://github.com/cardiffnlp/tweeteval.git",
                "location": "data/tweeteval/datasets",
                "formats": ["raw txt", "csv", "parquet"]
            },
            "models": {
                "twitter-roberta-base-irony": {
                    "description": "CardiffNLP Twitter RoBERTa model fine-tuned for irony detection",
                    "source": "https://huggingface.co/cardiffnlp/twitter-roberta-base-irony",
                    "location": "data/models/twitter-roberta-base-irony"
                },
                "twitter-roberta-base-sentiment-latest": {
                    "description": "CardiffNLP Twitter RoBERTa model fine-tuned for 3-way sentiment classification (positive, neutral, negative)",
                    "source": "https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest",
                    "location": "data/models/twitter-roberta-base-sentiment-latest"
                },
                "twitter-xlm-roberta-base-sentiment": {
                    "description": "CardiffNLP multilingual XLM-RoBERTa sentiment classification model",
                    "source": "https://huggingface.co/cardiffnlp/twitter-xlm-roberta-base-sentiment",
                    "location": "data/models/twitter-xlm-roberta-base-sentiment"
                }
            }
        }
    }
    
    with open(os.path.join(DATA_DIR, "catalog.json"), "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)
        
    readme_content = """# AdFatigueRadar - Data Directory Structure

This folder contains the organized datasets and pretrained model assets for sentiment analysis, irony/mockery detection, intent/complaint classification, and ad fatigue monitoring.

---

## 1. Directory Structure

```text
data/
├── banking77/                             # Banking77 customer intent & complaint dataset
│   ├── data/                              # Original Parquet files (train, test)
│   ├── csv/                               # Cleaned CSV files (train.csv, test.csv)
│   ├── train.jsonl & test.jsonl           # JSON Lines format
│   └── README.md                          # Dataset card & label definitions
│
├── tweeteval/                             # CardiffNLP TweetEval Benchmark Suite
│   ├── datasets/
│   │   ├── irony/                         # Irony & sarcasm detection (crucial for ad mockery)
│   │   │   ├── train.csv, val.csv, test.csv
│   │   │   ├── train.parquet, val.parquet, test.parquet
│   │   │   ├── train_text.txt, train_labels.txt ...
│   │   │   └── mapping.txt                # 0: non_irony, 1: irony
│   │   ├── sentiment/                     # 3-class sentiment (positive, neutral, negative)
│   │   │   ├── train.csv, val.csv, test.csv
│   │   │   ├── train.parquet, val.parquet, test.parquet
│   │   │   ├── train_text.txt, train_labels.txt ...
│   │   │   └── mapping.txt                # 0: negative, 1: neutral, 2: positive
│   │   ├── emotion/                       # 4-class emotion (anger, joy, optimism, sadness)
│   │   ├── offensive/                     # Offensive language identification
│   │   ├── hate/                          # Hate speech detection
│   │   ├── stance/                        # Multi-domain stance detection
│   │   └── emoji/                         # 20-class emoji prediction
│   ├── evaluation_marMo.py                # Evaluation scripts
│   └── README.md
│
├── models/                                # CardiffNLP Pretrained NLP Models & Tokenizers
│   ├── twitter-roberta-base-irony/        # Irony Classifier (PyTorch model, config, vocab, merges)
│   ├── twitter-roberta-base-sentiment-latest/ # Sentiment Classifier (PyTorch model, config, vocab, merges)
│   └── twitter-xlm-roberta-base-sentiment/    # Multilingual Sentiment Classifier (PyTorch model, sentencepiece model)
│
└── catalog.json                           # Machine-readable metadata catalog
```

---

## 2. Usage Guide

### Loading Sentiment / Irony Datasets (Pandas)
```python
import pandas as pd

# Load TweetEval Irony
df_irony_train = pd.read_parquet("data/tweeteval/datasets/irony/train.parquet")
print(df_irony_train.head())

# Load TweetEval Sentiment
df_sentiment_train = pd.read_parquet("data/tweeteval/datasets/sentiment/train.parquet")
print(df_sentiment_train.head())
```

### Loading Banking77 Intent Classification
```python
import pandas as pd

df_banking_train = pd.read_parquet("data/banking77/data/train-00000-of-00001.parquet")
print(df_banking_train.head())
```

### Loading CardiffNLP Pretrained Models with Transformers
```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Load Irony Model
irony_tokenizer = AutoTokenizer.from_pretrained("data/models/twitter-roberta-base-irony")
irony_model = AutoModelForSequenceClassification.from_pretrained("data/models/twitter-roberta-base-irony")

# Load Latest Sentiment Model
sentiment_tokenizer = AutoTokenizer.from_pretrained("data/models/twitter-roberta-base-sentiment-latest")
sentiment_model = AutoModelForSequenceClassification.from_pretrained("data/models/twitter-roberta-base-sentiment-latest")
```
"""
    with open(os.path.join(DATA_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    log("Catalog and README created successfully.")

if __name__ == "__main__":
    download_banking77()
    download_tweeteval()
    download_models()
    generate_catalog()
    log("=== All Datasets and Models Successfully Downloaded & Organized ===")
