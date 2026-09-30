"""
AdFatigueRadar — Confidence Calibration Module
=============================================
PERSON 1: AI / NLP Layer

Provides temperature scaling and probability calibration to ensure predicted
confidence scores reflect true empirical accuracy.
Fitted on the VALIDATION split only via Negative Log-Likelihood optimization.
"""

import math
from typing import List, Dict, Union, Tuple, Optional
import numpy as np
from scipy.optimize import minimize_scalar


class TemperatureScaler:
    """
    Applies temperature scaling to raw classifier logits or probabilities.
    
    For logits z:
        p_i = exp(z_i / T) / sum_j exp(z_j / T)
    """
    def __init__(self, temperature: float = 1.0, eps: float = 1e-7):
        if temperature <= 0.0:
            raise ValueError(f"Temperature must be strictly positive, got {temperature}")
        self.temperature = float(temperature)
        self.eps = eps

    def fit(self, logits: np.ndarray, labels: np.ndarray) -> float:
        """
        Fits optimal temperature T on the validation split by minimizing NLL loss.
        
        Args:
            logits: np.ndarray of shape (N, num_classes)
            labels: np.ndarray of integer class indices of shape (N,)
            
        Returns:
            optimal_temperature (float)
        """
        logits = np.asarray(logits, dtype=np.float64)
        labels = np.asarray(labels, dtype=np.int64)
        
        def nll_loss(t: float) -> float:
            if t <= 1e-3:
                return 1e9
            scaled_logits = logits / t
            # Log-sum-exp trick for numerical stability
            max_logits = np.max(scaled_logits, axis=1, keepdims=True)
            log_sum_exp = max_logits + np.log(np.sum(np.exp(scaled_logits - max_logits), axis=1, keepdims=True))
            log_probs = scaled_logits - log_sum_exp
            n = logits.shape[0]
            nll = -np.sum(log_probs[np.arange(n), labels]) / n
            return float(nll)

        res = minimize_scalar(nll_loss, bounds=(0.05, 10.0), method="bounded")
        if res.success:
            self.temperature = round(float(res.x), 4)
        return self.temperature

    def calibrate_logits(self, logits: Union[List[float], np.ndarray]) -> List[float]:
        """Calibrate raw logits via softmax with temperature scaling."""
        z = np.asarray(logits, dtype=np.float64) / self.temperature
        max_val = np.max(z)
        exp_vals = np.exp(z - max_val)
        sum_exp = np.sum(exp_vals)
        if sum_exp <= 0:
            return [1.0 / len(logits)] * len(logits)
        probs = exp_vals / sum_exp
        return [round(float(v), 6) for v in probs]

    def calibrate_probabilities(self, probs: Union[List[float], np.ndarray]) -> List[float]:
        """Calibrate probabilities by reconstructing pseudo-logits and applying temperature."""
        if not len(probs):
            return []
        p = np.asarray(probs, dtype=np.float64)
        logits = np.log(np.maximum(p, self.eps))
        return self.calibrate_logits(logits)

    def calibrate_dict(self, prob_dict: Dict[str, float]) -> Dict[str, float]:
        """Calibrates a dictionary mapping {class_label: raw_probability}."""
        keys = list(prob_dict.keys())
        raw_vals = [prob_dict[k] for k in keys]
        calibrated_vals = self.calibrate_probabilities(raw_vals)
        return {k: v for k, v in zip(keys, calibrated_vals)}


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


# Default global calibrated scaler instance (will be updated with fitted temperature)
default_scaler = TemperatureScaler(temperature=1.0)
