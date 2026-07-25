from __future__ import annotations

import json
import re
import time
from pathlib import Path

from agentgrid.config import settings

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")
DEFAULT_MAX_AGE_S = 20.0


def _dir() -> Path:
    # Under artifact_dir so Docker api/worker share heartbeats via the data volume.
    path = Path(settings.artifact_dir) / "heartbeats"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _path(worker_id: str) -> Path:
    safe = _SAFE.sub("_", worker_id)[:80] or "worker"
    return _dir() / f"{safe}.json"


def beat(worker_id: str, *, status: str = "idle") -> None:
    """Write a cross-process heartbeat the API can read (works without Redis)."""
    payload = {
        "worker_id": worker_id,
        "status": status,
        "ts": time.time(),
        "artifact_dir": str(settings.artifact_dir),
    }
    path = _path(worker_id)
    path.write_text(json.dumps(payload), encoding="utf-8")


def list_alive(max_age_s: float = DEFAULT_MAX_AGE_S) -> list[dict]:
    now = time.time()
    alive: list[dict] = []
    for path in _dir().glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            ts = float(data.get("ts", 0))
            if now - ts <= max_age_s:
                alive.append(
                    {
                        "worker_id": data.get("worker_id") or path.stem,
                        "status": data.get("status") or "idle",
                        "age_s": round(now - ts, 1),
                    }
                )
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    alive.sort(key=lambda w: w["worker_id"])
    return alive
