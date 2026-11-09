from __future__ import annotations

import json
from fastapi.testclient import TestClient

import app.storage as storage
from app.main import app

client = TestClient(app)


def test_health_and_scenarios():
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    scenarios = client.get("/api/scenarios")
    assert scenarios.status_code == 200
    assert {item["id"] for item in scenarios.json()} == {"office_fire", "blocked_exit", "smoke_stairwell"}


def test_start_decision_adaptation_and_export(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "LOG_DIR", tmp_path)
    response = client.post("/api/sessions", json={"scenario_id": "office_fire", "condition": "adaptive_vr", "participant_code": "P-TEST"})
    assert response.status_code == 200
    state = response.json()
    session_id = state["session_id"]
    assert state["status"] == "active"

    result = client.post(f"/api/sessions/{session_id}/decisions", json={
        "choice_id": "evacuate", "response_time_ms": 900, "simulated_load": "high"
    })
    assert result.status_code == 200
    payload = result.json()
    assert payload["load"]["source"] == "simulated_manual_demo"
    assert payload["adaptation"]["guidance_level"] == "high"
    assert payload["state"]["current_decision"]["hint"]

    export = client.get(f"/api/sessions/{session_id}/export")
    assert export.status_code == 200
    assert len(export.json()["decisions"]) == 1
    assert (tmp_path / "decision_events.jsonl").exists()
    record = json.loads((tmp_path / "decision_events.jsonl").read_text().splitlines()[0])
    assert record["condition"] == "adaptive_vr"
    assert record["response_time_ms"] == 900


def test_complete_blocked_exit_session(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "LOG_DIR", tmp_path)
    response = client.post("/api/sessions", json={"scenario_id": "blocked_exit", "condition": "desktop"})
    assert response.status_code == 200
    state = response.json()
    session_id = state["session_id"]
    loops = 0
    while state["status"] == "active":
        choice_id = state["current_decision"]["options"][0]["id"]
        result = client.post(f"/api/sessions/{session_id}/decisions", json={
            "choice_id": choice_id, "response_time_ms": 1200, "simulated_load": "medium"
        })
        assert result.status_code == 200
        state = result.json()["state"]
        loops += 1
        assert loops <= 8
    assert state["status"] == "completed"
    assert state["summary"]["decision_count"] == 6
    assert state["summary"]["is_research_result"] is False


def test_invalid_scenario_and_choice():
    bad = client.post("/api/sessions", json={"scenario_id": "not-real", "condition": "desktop"})
    assert bad.status_code == 404
    start = client.post("/api/sessions", json={"scenario_id": "smoke_stairwell", "condition": "fixed_vr"})
    sid = start.json()["session_id"]
    invalid = client.post(f"/api/sessions/{sid}/decisions", json={"choice_id": "not-an-option"})
    assert invalid.status_code == 400
