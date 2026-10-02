from pathlib import Path

import pytest

from backend.nlp.model_loader import resolve_local_transformer_dir
from backend.nlp.sentiment import SentimentClassifier


def test_local_transformer_path_is_resolved_before_loading(monkeypatch):
    monkeypatch.setattr(Path, "resolve", lambda self, strict=False: self)
    monkeypatch.setattr(Path, "is_dir", lambda self: True)
    monkeypatch.setattr(Path, "is_file", lambda self: self.name in {"config.json", "tokenizer.json", "model.safetensors"})
    candidate = Path.cwd() / "local-model"
    result = Path(resolve_local_transformer_dir(str(candidate)))
    assert result.is_absolute()
    assert result == candidate


def test_incomplete_local_model_fails_before_transformers_hub_resolution(monkeypatch):
    monkeypatch.setattr(Path, "resolve", lambda self, strict=False: self)
    monkeypatch.setattr(Path, "is_dir", lambda self: True)
    monkeypatch.setattr(Path, "is_file", lambda self: self.name == "config.json")
    with pytest.raises(FileNotFoundError, match="incomplete"):
        resolve_local_transformer_dir(str(Path.cwd() / "incomplete-model"))


def test_sentencepiece_bpe_model_is_a_valid_local_tokenizer(monkeypatch):
    monkeypatch.setattr(Path, "resolve", lambda self, strict=False: self)
    monkeypatch.setattr(Path, "is_dir", lambda self: True)
    monkeypatch.setattr(
        Path,
        "is_file",
        lambda self: self.name in {"config.json", "sentencepiece.bpe.model", "pytorch_model.bin"},
    )
    candidate = Path.cwd() / "xlm-local-model"
    assert Path(resolve_local_transformer_dir(str(candidate))) == candidate


def test_default_sentiment_path_does_not_fall_back_to_another_model(monkeypatch):
    monkeypatch.setattr(
        Path,
        "is_dir",
        lambda self: self.name == "twitter-xlm-roberta-base-sentiment",
    )
    classifier = SentimentClassifier.__new__(SentimentClassifier)
    with pytest.raises(FileNotFoundError, match="twitter-roberta-base-sentiment-latest"):
        classifier._find_default_model_dir()
