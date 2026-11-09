from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import joblib
import numpy as np

FEATURE_COLUMNS = [
    "pupil_diameter_mm",
    "fixation_count",
    "saccade_count",
    "blink_rate_per_min",
    "heart_rate_bpm",
    "rmssd_ms",
    "sdnn_ms",
]
LABELS = ["low", "medium", "high"]


@dataclass
class LoadPrediction:
    label: str
    confidence: float | None
    source: str
    note: str


class CognitiveLoadEstimator:
    """Interim estimator. A heuristic is not a validated cognitive-load model."""

    def __init__(self, model_path: Path | None = None):
        self.model_path = model_path
        self.model_bundle: dict[str, Any] | None = None
        if model_path and model_path.exists():
            try:
                bundle = joblib.load(model_path)
                if isinstance(bundle, dict) and "model" in bundle and "feature_columns" in bundle:
                    self.model_bundle = bundle
            except Exception:
                self.model_bundle = None

    def predict(self, features: dict[str, float | None] | None = None, simulated_label: str | None = None) -> LoadPrediction:
        if simulated_label in LABELS:
            return LoadPrediction(
                label=simulated_label,
                confidence=None,
                source="simulated_manual_demo",
                note="Manually selected demonstration input; not physiological sensor data.",
            )

        if features and self.model_bundle is not None:
            columns = self.model_bundle["feature_columns"]
            vector = np.array([[float(features.get(column) or 0.0) for column in columns]], dtype=float)
            model = self.model_bundle["model"]
            prediction = str(model.predict(vector)[0]).lower()
            confidence = None
            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba(vector)[0]
                confidence = float(max(probabilities))
            metadata = self.model_bundle.get("metadata", {})
            training_source = metadata.get("training_source", "unspecified")
            validity = "demo-only" if metadata.get("demo_only") else "trained model; validate externally before research use"
            return LoadPrediction(
                label=prediction if prediction in LABELS else "medium",
                confidence=confidence,
                source=f"trained_model:{training_source}",
                note=validity,
            )

        if features:
            return self._heuristic(features)

        return LoadPrediction(
            label="medium",
            confidence=None,
            source="neutral_fallback",
            note="No sensor features or trained model supplied; neutral baseline used.",
        )

    @staticmethod
    def _heuristic(features: dict[str, float | None]) -> LoadPrediction:
        """Conservative rule-based demo estimate, not a validated classifier."""
        score = 0
        observed = 0
        thresholds = {
            "pupil_diameter_mm": (4.5, 5.5, 1),
            "blink_rate_per_min": (10.0, 25.0, 1),
            "heart_rate_bpm": (85.0, 110.0, 1),
        }
        for name, (medium_cutoff, high_cutoff, weight) in thresholds.items():
            value = features.get(name)
            if value is None:
                continue
            observed += 1
            if float(value) >= high_cutoff:
                score += 2 * weight
            elif float(value) >= medium_cutoff:
                score += weight
        # A basic screen should not imply scientific validity; limited features return medium.
        if observed == 0:
            label = "medium"
        elif score >= 4:
            label = "high"
        elif score >= 2:
            label = "medium"
        else:
            label = "low"
        return LoadPrediction(
            label=label,
            confidence=None,
            source="unvalidated_heuristic",
            note="Rule-based placeholder only. Do not report this as a trained or validated cognitive-load model.",
        )
