from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, field_validator

Condition = Literal["desktop", "fixed_vr", "adaptive_vr"]
LoadBand = Literal["low", "medium", "high"]


class StartSessionRequest(BaseModel):
    scenario_id: str
    condition: Condition = "adaptive_vr"
    participant_code: str | None = Field(default=None, max_length=40)

    @field_validator("participant_code")
    @classmethod
    def clean_participant_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = "".join(c for c in value.strip() if c.isalnum() or c in "-_" )
        return cleaned[:40] or None


class SensorFeatures(BaseModel):
    pupil_diameter_mm: float | None = Field(default=None, ge=0, le=15)
    fixation_count: float | None = Field(default=None, ge=0, le=10000)
    saccade_count: float | None = Field(default=None, ge=0, le=10000)
    blink_rate_per_min: float | None = Field(default=None, ge=0, le=300)
    heart_rate_bpm: float | None = Field(default=None, ge=25, le=240)
    rmssd_ms: float | None = Field(default=None, ge=0, le=1000)
    sdnn_ms: float | None = Field(default=None, ge=0, le=1000)


class DecisionRequest(BaseModel):
    choice_id: str = Field(min_length=1, max_length=80)
    response_time_ms: float | None = Field(default=None, ge=0, le=3600000)
    simulated_load: LoadBand | None = None
    sensor_features: SensorFeatures | None = None
