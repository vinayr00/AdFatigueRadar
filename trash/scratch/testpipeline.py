from backend.nlp import CommentEvent, NLPResult
from backend.nlp.classifier import CommentClassifier

# 1. Initialize classifier once
classifier = CommentClassifier(use_cache=True)

# 2. Ingest comment event
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
