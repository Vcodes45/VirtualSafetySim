from __future__ import annotations

from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import MODEL_PATH
from app.engine import SimulationEngine
from app.load_estimator import CognitiveLoadEstimator
from app.scenarios import public_scenarios
from app.schemas import DecisionRequest, StartSessionRequest

BASE_DIR = Path(__file__).resolve().parent.parent
app = FastAPI(
    title="Virtual Safety — Adaptive Fire-Emergency Training Prototype",
    version="0.1.0",
    description="Interim simulator with scenario branching, decision logging, and a clearly-labelled demo adaptation path.",
)
estimator = CognitiveLoadEstimator(MODEL_PATH)
engine = SimulationEngine(estimator)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "app": "virtual-safety-interim",
        "trained_model_loaded": estimator.model_bundle is not None,
        "model_path": str(MODEL_PATH),
        "prototype_notice": "Browser presentation modes are not an actual Unity/OpenXR headset integration.",
    }


@app.get("/api/scenarios")
def scenarios() -> list[dict[str, Any]]:
    return public_scenarios()


@app.post("/api/sessions")
def start_session(request: StartSessionRequest) -> dict[str, Any]:
    try:
        return engine.start(request.scenario_id, request.condition, request.participant_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc).strip("'")) from exc


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    try:
        return engine.public_state(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc).strip("'")) from exc


@app.post("/api/sessions/{session_id}/decisions")
def submit_decision(session_id: str, request: DecisionRequest) -> dict[str, Any]:
    features = request.sensor_features.model_dump() if request.sensor_features else None
    try:
        return engine.decide(
            session_id=session_id,
            choice_id=request.choice_id,
            response_time_ms=request.response_time_ms,
            simulated_load=request.simulated_load,
            sensor_features=features,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc).strip("'")) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/sessions/{session_id}/export")
def export_session(session_id: str) -> dict[str, Any]:
    try:
        return engine.export_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc).strip("'")) from exc
