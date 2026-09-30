"""
AdFatigueRadar — Confidence Calibration Module
=============================================
PERSON 1: AI / NLP Layer

Provides temperature scaling and probability calibration to ensure predicted
confidence scores reflect true empirical accuracy. Crucial for downstream
confidence-gated critical complaint triggers and Wilson score safety bounds.
"""

import math
from typing import List, Dict, Union, Tuple
import numpy as np


class TemperatureScaler:
    """
    Applies temperature scaling to raw classifier logits or probabilities.
    
    For logits z:
        p_i = exp(z_i / T) / sum_j exp(z_j / T)
        
    If raw probabilities p are passed, pseudo-logits are reconstructed:
        z_i = log(max(p_i, eps))
        and rescaled by T.
    """
    def __init__(self, temperature: float = 1.15, eps: float = 1e-7):
        if temperature <= 0.0:
            raise ValueError(f"Temperature must be strictly positive, got {temperature}")
        self.temperature = float(temperature)
        self.eps = eps

    def calibrate_logits(self, logits: List[float]) -> List[float]:
        """Calibrate raw logits via softmax with temperature scaling."""
        scaled = [z / self.temperature for z in logits]
        max_val = max(scaled)
        exp_vals = [math.exp(v - max_val) for v in scaled]
        sum_exp = sum(exp_vals)
        if sum_exp <= 0:
            return [1.0 / len(logits)] * len(logits)
        return [round(v / sum_exp, 6) for v in exp_vals]

    def calibrate_probabilities(self, probs: List[float]) -> List[float]:
        """Calibrate probabilities by converting to pseudo-logits and applying temperature."""
        if not probs:
            return []
        # Reconstruct pseudo-logits with numerical stability
        logits = [math.log(max(p, self.eps)) for p in probs]
        return self.calibrate_logits(logits)

    def calibrate_dict(self, prob_dict: Dict[str, float]) -> Dict[str, float]:
        """Calibrates a dictionary mapping {class_label: raw_probability}."""
        keys = list(prob_dict.keys())
        raw_vals = [prob_dict[k] for k in keys]
        calibrated_vals = self.calibrate_probabilities(raw_vals)
        return {k: v for k, v in zip(keys, calibrated_vals)}

    def calibrate_confidence(self, top_prob: float, num_classes: int = 8) -> float:
        """
        Calibrates a single top-1 confidence score against a uniform prior background.
        """
        top_prob = max(0.0, min(1.0, top_prob))
        if num_classes <= 1 or top_prob >= 0.999:
            return top_prob
        # Reconstruct pseudo-logit for binary or top-vs-rest
        other_prob = max(self.eps, (1.0 - top_prob) / (num_classes - 1))
        calibrated = self.calibrate_probabilities([top_prob] + [other_prob] * (num_classes - 1))
        return round(float(calibrated[0]), 4)


def compute_expected_calibration_error(
    confidences: List[float],
    accuracies: List[int],
    num_bins: int = 10
) -> float:
    """
    Computes Expected Calibration Error (ECE) for a set of predicted confidences
    and binary ground-truth correctness indicators (1 = correct, 0 = incorrect).
    """
    if not confidences or not accuracies or len(confidences) != len(accuracies):
        return 0.0

    n = len(confidences)
    bin_boundaries = np.linspace(0.0, 1.0, num_bins + 1)
    ece = 0.0

    for i in range(num_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        # Indices in bin
        if i == num_bins - 1:
            in_bin = [j for j, c in enumerate(confidences) if bin_lower <= c <= bin_upper]
        else:
            in_bin = [j for j, c in enumerate(confidences) if bin_lower <= c < bin_upper]
            
        bin_size = len(in_bin)
        if bin_size > 0:
            avg_confidence = sum(confidences[j] for j in in_bin) / bin_size
            avg_accuracy = sum(accuracies[j] for j in in_bin) / bin_size
            ece += (bin_size / n) * abs(avg_accuracy - avg_confidence)

    return round(float(ece), 4)


# Default global calibrated scaler instance
default_scaler = TemperatureScaler(temperature=1.12)
