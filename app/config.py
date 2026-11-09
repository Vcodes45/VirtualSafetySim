from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = (ROOT / os.getenv("VIRTUAL_SAFETY_DATA_DIR", "data")).resolve()
MODEL_PATH = (ROOT / os.getenv("VIRTUAL_SAFETY_MODEL_PATH", "models/cognitive_load_model.joblib")).resolve()
LOG_DIR = DATA_DIR / "logs"
