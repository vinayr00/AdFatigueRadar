# AdFatigueRadar — AI & NLP Module (Person 1)
==============================================

## 1. Overview
The `backend/nlp/` package provides the complete, isolated AI/NLP layer for AdFatigueRadar. It processes raw social ad comments into calibrated sentiment and an 8-class ad-fatigue taxonomy, emits the frozen `NLPResult` contract, and provides replay caching and baseline metrics.

## 2. Frozen Input and Output Contracts

### Input: `CommentEvent`
```json
{
  "event_id": "comment_0001",
  "timestamp": "2026-09-30T12:00:00Z",
  "campaign_id": "campaign_01",
  "ad_id": "ad_07",
  "author_id": "author_184",
  "text": "Bro this ad again 😂",
  "reactions": 12,
  "replies": 3
}
```

### Output: `NLPResult`
```json
{
  "comment_id": "comment_0001",
  "sentiment": "negative",
  "sentiment_score": 0.91,
  "category": "fatigue",
  "confidence": 0.94,
  "critical_complaint": false
}
```

## 3. The Frozen 8-Class Taxonomy
1. `product_complaint`: Defect, malfunction, or poor build quality.
2. `service_complaint`: Shipping delay, missing order, refused refund, or support failure.
3. `fatigue`: Repetitive exposure to the advertisement (*"Bro this ad again"*).
4. `mockery`: Ad-directed ridicule, roasting actors/script/cringe factor.
5. `spam`: Low quality bot promos, crypto, telegram links, follower spam.
6. `banter_meme`: Non-harmful humor, memes, slang (*"bro got that rizz"*). Excluded from harmful ratio ($w = 0.00$).
7. `neutral`: Inquiries, questions on price/specs/shipping, friend tags.
8. `positive`: Praise, satisfaction, repeat purchase (*"bought again, love it"*).

## 4. Key Components
- `preprocessing.py`: Deterministic text & Unicode normalization, feature extraction.
- `sentiment.py`: Stage 1 3-class sentiment classifier (Negative / Neutral / Positive).
- `taxonomy.py`: Stage 2 8-class taxonomy classifier with 'again' disambiguation and mockery vs banter separation.
- `calibration.py`: Temperature scaling calibration ($T = 1.12$) & ECE evaluation.
- `classifier.py`: `CommentClassifier` unifying the two-stage pipeline.
- `cache.py`: `NLPCache` deterministic replay cache keyed by `hash(comment_id + model_ver + preproc_ver)`.
- `inference.py`: `StreamCommentProcessor` for streaming and batched execution.
- `benchmark.py`: Latency, throughput, and sub-minute guarantee verification (bypasses cache).
- `baselines.py`: P1 `SentimentOnlyBaseline` (Baseline C) for negative-control benchmarking against banter storms.

## 5. Usage Example (For Person 2 & Person 3)
```python
from backend.nlp import CommentEvent, NLPResult
from backend.nlp.classifier import CommentClassifier

classifier = CommentClassifier(use_cache=True)

event = CommentEvent(
    event_id="comment_0001",
    timestamp="2026-09-30T12:00:00Z",
    campaign_id="campaign_01",
    ad_id="ad_07",
    author_id="author_184",
    text="Bro this ad again 😂"
)

result: NLPResult = classifier.classify(event)
print(result.to_dict())
# {
#   "comment_id": "comment_0001",
#   "sentiment": "negative",
#   "sentiment_score": 0.8954,
#   "category": "fatigue",
#   "confidence": 0.9231,
#   "critical_complaint": false
# }
```
