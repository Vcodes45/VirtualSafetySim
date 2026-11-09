from app.load_estimator import CognitiveLoadEstimator


def test_manual_demo_load_is_not_misrepresented_as_sensor_data():
    result = CognitiveLoadEstimator().predict(simulated_label="high")
    assert result.label == "high"
    assert result.source == "simulated_manual_demo"
    assert "not physiological sensor data" in result.note


def test_no_features_returns_neutral_fallback():
    result = CognitiveLoadEstimator().predict()
    assert result.label == "medium"
    assert result.source == "neutral_fallback"


def test_heuristic_is_explicitly_unvalidated():
    result = CognitiveLoadEstimator().predict({
        "pupil_diameter_mm": 6.0,
        "blink_rate_per_min": 30.0,
        "heart_rate_bpm": 120.0,
    })
    assert result.label == "high"
    assert result.source == "unvalidated_heuristic"
