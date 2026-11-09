from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCENARIO_FILE = Path(__file__).resolve().parent.parent / "data" / "scenarios.json"


def load_scenarios() -> dict[str, dict[str, Any]]:
    with SCENARIO_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


SCENARIOS = load_scenarios()


def public_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "id": scenario_id,
            "title": scenario["title"],
            "description": scenario["description"],
            "environment": scenario["environment"],
            "decision_count": len(scenario["decisions"]),
        }
        for scenario_id, scenario in SCENARIOS.items()
    ]
