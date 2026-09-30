# AdFatigueRadar - Data Directory Structure

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
