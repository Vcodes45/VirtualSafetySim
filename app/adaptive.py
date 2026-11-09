from __future__ import annotations

from app.load_estimator import LoadPrediction


def adaptation_for(condition: str, prediction: LoadPrediction) -> dict:
    if condition != "adaptive_vr":
        return {
            "enabled": False,
            "load_label": prediction.label,
            "load_source": prediction.source,
            "guidance_level": "fixed",
            "cue_salience": "fixed",
            "time_pressure": "fixed",
            "message": "This condition uses fixed guidance; no adaptation was applied.",
        }

    if prediction.label == "high":
        return {
            "enabled": True,
            "load_label": prediction.label,
            "load_source": prediction.source,
            "guidance_level": "high",
            "cue_salience": "high",
            "time_pressure": "reduced",
            "message": "Demo adaptation: provide a clearer safety hint, emphasize the safe-route cue and reduce time pressure.",
        }
    if prediction.label == "low":
        return {
            "enabled": True,
            "load_label": prediction.label,
            "load_source": prediction.source,
            "guidance_level": "standard",
            "cue_salience": "standard",
            "time_pressure": "normal",
            "message": "Demo adaptation: maintain clear safety-critical cues; offer standard guidance with an optional reflection prompt.",
        }
    return {
        "enabled": True,
        "load_label": prediction.label,
        "load_source": prediction.source,
        "guidance_level": "standard",
        "cue_salience": "enhanced",
        "time_pressure": "normal",
        "message": "Demo adaptation: preserve normal time pressure and make key safety cues easy to notice.",
    }
