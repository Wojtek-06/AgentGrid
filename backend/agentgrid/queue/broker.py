from __future__ import annotations

import json
import threading
import time
from collections import deque
from typing import Any

from agentgrid.config import settings

QUEUE_KEY = "agentgrid:jobs"


class JobBroker:
    """Durable-enough job queue: Redis when enabled, else process-local deque."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._local: deque[str] = deque()
        self._redis = None
        if settings.use_redis:
            import redis

            self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    def enqueue(self, job_id: str, payload: dict[str, Any] | None = None) -> None:
        body = json.dumps({"job_id": job_id, "payload": payload or {}})
        if self._redis is not None:
            self._redis.lpush(QUEUE_KEY, body)
            return
        with self._lock:
            self._local.appendleft(body)

    def dequeue(self, timeout_s: float = 1.0) -> dict[str, Any] | None:
        if self._redis is not None:
            item = self._redis.brpop(QUEUE_KEY, timeout=max(1, int(timeout_s)))
            if not item:
                return None
            return json.loads(item[1])

        deadline = time.time() + timeout_s
        while time.time() < deadline:
            with self._lock:
                if self._local:
                    return json.loads(self._local.pop())
            time.sleep(0.05)
        return None

    def depth(self) -> int:
        if self._redis is not None:
            return int(self._redis.llen(QUEUE_KEY))
        with self._lock:
            return len(self._local)


_broker: JobBroker | None = None


def get_broker() -> JobBroker:
    global _broker
    if _broker is None:
        _broker = JobBroker()
    return _broker
