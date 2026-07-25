from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from agentgrid.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple per-IP sliding window for untrusted API clients."""

    def __init__(self, app):  # noqa: ANN001
        super().__init__(app)
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        if request.url.path in {"/api/health", "/api/jobs/stream"}:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = self._hits[ip]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= settings.rate_limit_per_minute:
            return JSONResponse({"detail": "rate_limited"}, status_code=429)
        window.append(now)
        return await call_next(request)
