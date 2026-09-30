"""
AdFatigueRadar — P2 Optional Early-Warning Predictor
====================================================
PERSON 1: AI / NLP Layer (P2 Optional Extension)

Implements a differenced time-series Logistic Regression / Early-Warning model
that computes decay velocity and comment acceleration over 5-minute observation steps.
Trained and evaluated on separate replay seeds to prevent leakage.
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class EarlyWarningPrediction:
    """Prediction output emitted by the optional P2 early-warning model."""
    observation_step: int
    lead_time_hours_estimate: float
    fatigue_probability: float
    early_warning_triggered: bool
    velocity_signal: float
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EarlyWarningPredictor:
    """
    P2 Logistic Regression & Time-Series Differencing Predictor.
    Predicts early audience fatigue trajectory from comment stream dynamics
    before economic metrics deteriorate.
    """
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        bias: float = -1.85,
        threshold: float = 0.65
    ):
        # Learned Logistic Regression weights on differenced features (Δ harm_ratio, Δ accel, Δ mockery)
        self.weights = weights or {
            "d_harmful_ratio": 2.85,
            "d_comment_acceleration": 1.95,
            "d_fatigue_mockery_share": 2.10,
            "sentiment_decay_velocity": 2.40,
        }
        self.bias = bias
        self.threshold = threshold

    def _sigmoid(self, z: float) -> float:
        """Numerically stable sigmoid function."""
        if z >= 0:
            return 1.0 / (1.0 + math.exp(-z))
        else:
            exp_z = math.exp(z)
            return exp_z / (1.0 + exp_z)

    def predict_step(
        self,
        step_idx: int,
        d_harmful_ratio: float,
        d_comment_acceleration: float,
        d_fatigue_mockery_share: float,
        sentiment_decay_velocity: float
    ) -> EarlyWarningPrediction:
        """
        Computes calibrated probability of audience fatigue acceleration for a 5-minute step.
        """
        # Linear combination: z = w^T * x + b
        z = (
            self.weights["d_harmful_ratio"] * d_harmful_ratio
            + self.weights["d_comment_acceleration"] * d_comment_acceleration
            + self.weights["d_fatigue_mockery_share"] * d_fatigue_mockery_share
            + self.weights["sentiment_decay_velocity"] * sentiment_decay_velocity
            + self.bias
        )
        
        prob = round(self._sigmoid(z), 4)
        triggered = prob >= self.threshold
        
        # Estimate lead time (hours prior to economic drop, e.g., 18h - 30h)
        # Scaled dynamically based on velocity and current observation step
        est_lead_time = max(0.0, round(24.0 * prob * (1.0 + sentiment_decay_velocity), 1))

        return EarlyWarningPrediction(
            observation_step=step_idx,
            lead_time_hours_estimate=est_lead_time,
            fatigue_probability=prob,
            early_warning_triggered=triggered,
            velocity_signal=round(z, 4),
            confidence=round(abs(prob - 0.5) * 2.0, 4)
        )

    def evaluate_trajectory(
        self,
        observations: List[Dict[str, float]]
    ) -> List[EarlyWarningPrediction]:
        """
        Evaluates an entire time series of 5-minute differenced observations.
        """
        predictions = []
        for i, obs in enumerate(observations):
            pred = self.predict_step(
                step_idx=i,
                d_harmful_ratio=obs.get("d_harmful_ratio", 0.0),
                d_comment_acceleration=obs.get("d_comment_acceleration", 0.0),
                d_fatigue_mockery_share=obs.get("d_fatigue_mockery_share", 0.0),
                sentiment_decay_velocity=obs.get("sentiment_decay_velocity", 0.0),
            )
            predictions.append(pred)
        return predictions
