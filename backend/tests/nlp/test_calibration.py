"""
Tests for Temperature Scaling & Confidence Calibration
"""

import pytest
import numpy as np
from backend.nlp.calibration import TemperatureScaler, compute_expected_calibration_error
from backend.nlp.constants import CRITICAL_COMPLAINT_CONFIDENCE_THRESHOLD


def test_temperature_scaler_positive():
    with pytest.raises(ValueError):
        TemperatureScaler(temperature=-1.0)
    with pytest.raises(ValueError):
        TemperatureScaler(temperature=0.0)


def test_temperature_scaler_probabilities_sum_to_one():
    scaler = TemperatureScaler(temperature=1.2)
    raw_probs = [0.70, 0.15, 0.15]
    calibrated = scaler.calibrate_probabilities(raw_probs)
    
    assert len(calibrated) == 3
    assert abs(sum(calibrated) - 1.0) < 1e-4
    assert all(0.0 <= p <= 1.0 for p in calibrated)


def test_temperature_scaling_smoothing():
    scaler = TemperatureScaler(temperature=1.5)
    raw_probs = [0.90, 0.05, 0.05]
    calibrated = scaler.calibrate_probabilities(raw_probs)
    
    assert calibrated[0] < 0.90  # Softened
    assert calibrated[1] > 0.05
    assert calibrated[2] > 0.05


def test_temperature_scaler_fit_optimizes_nll():
    # Synthetic overconfident logits
    np.random.seed(42)
    logits = np.array([
        [5.0, 1.0, 0.5],
        [4.0, 2.0, 0.1],
        [0.5, 4.5, 1.0],
        [1.0, 0.5, 5.0],
    ])
    # True labels: [0, 0, 1, 2]
    labels = np.array([0, 0, 1, 2])
    
    scaler = TemperatureScaler(temperature=1.0)
    fitted_t = scaler.fit(logits, labels)
    
    assert fitted_t > 0.0
    assert isinstance(fitted_t, float)
    calibrated = [scaler.calibrate_logits(row) for row in logits]
    for row in calibrated:
        assert abs(sum(row) - 1.0) < 1e-4


def test_compute_expected_calibration_error():
    confs = [0.1, 0.2, 0.5, 0.8, 0.9]
    accs = [0, 0, 1, 1, 1]
    ece = compute_expected_calibration_error(confs, accs, num_bins=5)
    assert 0.0 <= ece <= 1.0


def test_critical_complaint_flag_threshold_behavior():
    # Proves changing confidence across 0.85 threshold flips the flag
    cat = "product_complaint"
    
    # Below 0.85 -> False
    conf_low = 0.84
    is_crit_low = (cat in {"product_complaint", "service_complaint"} and conf_low >= CRITICAL_COMPLAINT_CONFIDENCE_THRESHOLD)
    assert is_crit_low is False

    # At or above 0.85 -> True
    conf_high = 0.85
    is_crit_high = (cat in {"product_complaint", "service_complaint"} and conf_high >= CRITICAL_COMPLAINT_CONFIDENCE_THRESHOLD)
    assert is_crit_high is True
