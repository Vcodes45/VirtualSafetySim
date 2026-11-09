from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.adaptive import adaptation_for
from app.load_estimator import CognitiveLoadEstimator, LoadPrediction
from app.scenarios import SCENARIOS
from app.storage import append_jsonl, utc_now


class SimulationEngine:
    def __init__(self, estimator: CognitiveLoadEstimator):
        self.estimator = estimator
        self.sessions: dict[str, dict[str, Any]] = {}

    def start(self, scenario_id: str, condition: str, participant_code: str | None) -> dict[str, Any]:
        if scenario_id not in SCENARIOS:
            raise KeyError("Unknown scenario")
        scenario = SCENARIOS[scenario_id]
        session_id = str(uuid4())
        code = participant_code or f"demo-{session_id[:8]}"
        neutral = LoadPrediction("medium", None, "neutral_fallback", "No sensor signal supplied at session start.")
        state = {
            "session_id": session_id,
            "participant_code": code,
            "scenario_id": scenario_id,
            "condition": condition,
            "started_at": utc_now(),
            "status": "active",
            "current_decision_id": scenario["start"],
            "decision_count": 0,
            "correct_count": 0,
            "score": 0,
            "response_times_ms": [],
            "decision_events": [],
            "current_adaptation": adaptation_for(condition, neutral),
        }
        self.sessions[session_id] = state
        append_jsonl("sessions.jsonl", {
            "event": "session_started", "timestamp": state["started_at"],
            "session_id": session_id, "participant_code": code,
            "scenario_id": scenario_id, "condition": condition,
            "is_demo": code.startswith("demo-"),
        })
        return self.public_state(session_id)

    def decide(
        self,
        session_id: str,
        choice_id: str,
        response_time_ms: float | None,
        simulated_load: str | None,
        sensor_features: dict[str, float | None] | None,
    ) -> dict[str, Any]:
        session = self._session(session_id)
        if session["status"] != "active":
            raise ValueError("This session has already finished")

        scenario = SCENARIOS[session["scenario_id"]]
        decision_id = session["current_decision_id"]
        decision = scenario["decisions"][decision_id]
        option = next((item for item in decision["options"] if item["id"] == choice_id), None)
        if option is None:
            raise ValueError("Invalid choice for the current decision")

        prediction = self.estimator.predict(sensor_features, simulated_load)
        adaptation = adaptation_for(session["condition"], prediction)
        response_ms = float(response_time_ms if response_time_ms is not None else 0.0)
        event = {
            "timestamp": utc_now(),
            "session_id": session_id,
            "participant_code": session["participant_code"],
            "scenario_id": session["scenario_id"],
            "condition": session["condition"],
            "decision_id": decision_id,
            "choice_id": choice_id,
            "decision_score": int(option["score"]),
            "safety_correct": int(option["score"]) >= 2,
            "response_time_ms": response_ms,
            "load_label": prediction.label,
            "load_source": prediction.source,
            "load_confidence": prediction.confidence,
            "sensor_features": sensor_features if sensor_features and prediction.source != "simulated_manual_demo" else None,
            "simulated_load": simulated_load,
            "adaptation": adaptation,
        }
        session["decision_count"] += 1
        session["correct_count"] += int(event["safety_correct"])
        session["score"] += int(option["score"])
        session["response_times_ms"].append(response_ms)
        session["decision_events"].append(event)
        session["current_adaptation"] = adaptation
        append_jsonl("decision_events.jsonl", event)

        next_id = option.get("next")
        session["last_feedback"] = option["feedback"]
        session["last_decision_id"] = decision_id
        if next_id is None:
            session["status"] = "completed"
            session["completed_at"] = utc_now()
            append_jsonl("sessions.jsonl", {
                "event": "session_completed", "timestamp": session["completed_at"],
                "session_id": session_id, "participant_code": session["participant_code"],
                "scenario_id": session["scenario_id"], "condition": session["condition"],
                "decision_count": session["decision_count"], "correct_count": session["correct_count"],
                "score": session["score"], "decision_accuracy": self._accuracy(session),
                "mean_response_time_ms": self._mean_response_time(session), "is_demo": True,
            })
        else:
            session["current_decision_id"] = next_id

        return {
            "feedback": option["feedback"],
            "decision_score": option["score"],
            "safety_correct": event["safety_correct"],
            "load": {"label": prediction.label, "source": prediction.source, "confidence": prediction.confidence, "note": prediction.note},
            "adaptation": adaptation,
            "state": self.public_state(session_id),
        }

    def public_state(self, session_id: str) -> dict[str, Any]:
        session = self._session(session_id)
        scenario = SCENARIOS[session["scenario_id"]]
        state: dict[str, Any] = {
            "session_id": session_id,
            "scenario_id": session["scenario_id"],
            "scenario_title": scenario["title"],
            "scenario_description": scenario["description"],
            "learning_note": scenario["learning_note"],
            "condition": session["condition"],
            "status": session["status"],
            "decision_count": session["decision_count"],
            "correct_count": session["correct_count"],
            "score": session["score"],
            "last_feedback": session.get("last_feedback"),
            "last_decision_id": session.get("last_decision_id"),
            "adaptation": session["current_adaptation"],
        }
        if session["status"] == "completed":
            state["summary"] = self._summary(session)
            return state

        decision_id = session["current_decision_id"]
        decision = scenario["decisions"][decision_id]
        adaptation = session["current_adaptation"]
        show_hint = session["condition"] in ("desktop", "fixed_vr") or adaptation.get("guidance_level") == "high"
        state["current_decision"] = {
            "id": decision_id,
            "number": session["decision_count"] + 1,
            "title": decision["title"],
            "prompt": decision["prompt"],
            "hint": decision["hint"] if show_hint else None,
            "options": [{"id": o["id"], "label": o["label"]} for o in decision["options"]],
        }
        return state

    def export_session(self, session_id: str) -> dict[str, Any]:
        session = self._session(session_id)
        return {
            "session_id": session_id,
            "participant_code": session["participant_code"],
            "scenario_id": session["scenario_id"],
            "condition": session["condition"],
            "status": session["status"],
            "started_at": session["started_at"],
            "completed_at": session.get("completed_at"),
            "decisions": session["decision_events"],
            "summary": self._summary(session) if session["status"] == "completed" else None,
        }

    def _session(self, session_id: str) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if session is None:
            raise KeyError("Session not found. Sessions remain in memory while the server is running.")
        return session

    @staticmethod
    def _accuracy(session: dict[str, Any]) -> float:
        count = session["decision_count"]
        return round(session["correct_count"] / count, 4) if count else 0.0

    @staticmethod
    def _mean_response_time(session: dict[str, Any]) -> float:
        values = [value for value in session["response_times_ms"] if value > 0]
        return round(sum(values) / len(values), 2) if values else 0.0

    def _summary(self, session: dict[str, Any]) -> dict[str, Any]:
        count = session["decision_count"]
        return {
            "decision_count": count,
            "correct_decisions": session["correct_count"],
            "decision_accuracy": self._accuracy(session),
            "score": session["score"],
            "maximum_possible_score_for_path": 2 * count,
            "score_percentage_clamped": round(max(0, min(100, session["score"] / (2 * count) * 100)), 2) if count else 0.0,
            "mean_response_time_ms": self._mean_response_time(session),
            "duration_seconds": round((datetime.fromisoformat(session.get("completed_at", utc_now())) - datetime.fromisoformat(session["started_at"])).total_seconds(), 2),
            "condition": session["condition"],
            "scenario_id": session["scenario_id"],
            "is_research_result": False,
            "note": "Prototype session metrics only. Do not present as a controlled user-study result.",
        }
