"""
Tests for Temperature Scaling & Confidence Calibration
"""

import pytest
import math
from backend.nlp.calibration import TemperatureScaler, compute_expected_calibration_error


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
    # Temperature > 1.0 should soften overconfident probabilities
    scaler = TemperatureScaler(temperature=1.5)
    raw_probs = [0.90, 0.05, 0.05]
    calibrated = scaler.calibrate_probabilities(raw_probs)
    
    assert calibrated[0] < 0.90  # Softened
    assert calibrated[1] > 0.05
    assert calibrated[2] > 0.05


def test_compute_expected_calibration_error():
    # Perfectly calibrated case: confidences match accuracies
    confs = [0.1, 0.2, 0.5, 0.8, 0.9]
    accs = [0, 0, 1, 1, 1]
    ece = compute_expected_calibration_error(confs, accs, num_bins=5)
    assert 0.0 <= ece <= 1.0
