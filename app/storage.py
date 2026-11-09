from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any
from datetime import datetime, timezone

from app.config import LOG_DIR

_lock = Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(filename: str, record: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path: Path = LOG_DIR / filename
    with _lock:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
