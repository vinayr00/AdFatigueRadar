"""
Tests for P2 Early-Warning Logistic Regression Predictor
"""

import pytest
from backend.nlp.predictor import EarlyWarningPredictor, EarlyWarningPrediction


def test_predictor_healthy_step():
    predictor = EarlyWarningPredictor()
    # Healthy flat signals: zero differenced deltas
    pred = predictor.predict_step(
        step_idx=0,
        d_harmful_ratio=0.0,
        d_comment_acceleration=0.0,
        d_fatigue_mockery_share=0.0,
        sentiment_decay_velocity=0.0
    )
    assert isinstance(pred, EarlyWarningPrediction)
    assert pred.fatigue_probability < 0.50
    assert pred.early_warning_triggered is False


def test_predictor_surging_fatigue_step():
    predictor = EarlyWarningPredictor(threshold=0.65)
    # Rapid acceleration in fatigue + negative sentiment
    pred = predictor.predict_step(
        step_idx=24,
        d_harmful_ratio=0.35,
        d_comment_acceleration=0.40,
        d_fatigue_mockery_share=0.50,
        sentiment_decay_velocity=0.30
    )
    assert pred.fatigue_probability >= 0.65
    assert pred.early_warning_triggered is True
    assert pred.lead_time_hours_estimate > 0.0


def test_predictor_trajectory_evaluation():
    predictor = EarlyWarningPredictor()
    series = [
        {"d_harmful_ratio": 0.01 * i, "d_comment_acceleration": 0.02 * i, "d_fatigue_mockery_share": 0.02 * i, "sentiment_decay_velocity": 0.01 * i}
        for i in range(10)
    ]
    results = predictor.evaluate_trajectory(series)
    assert len(results) == 10
    # Probability should strictly increase as velocity rises
    assert results[-1].fatigue_probability > results[0].fatigue_probability
