from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, Query, Request

from agentgrid.config import settings


def _token_ok(got: str | None, expected: str) -> bool:
    if got is None:
        return False
    try:
        return secrets.compare_digest(got, expected)
    except (TypeError, ValueError):
        return False


def require_token(
    request: Request,
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None, description="SSE-only Bearer alternative"),
) -> None:
    expected = settings.api_token
    if not expected:
        raise HTTPException(status_code=503, detail="api_token_not_configured")

    if authorization and authorization.startswith("Bearer "):
        if _token_ok(authorization.removeprefix("Bearer "), expected):
            return

    # EventSource cannot set Authorization; allow ?token= only on the SSE stream.
    if token is not None:
        if request.url.path.rstrip("/").endswith("/jobs/stream") and _token_ok(token, expected):
            return
        raise HTTPException(
            status_code=401,
            detail="unauthorized: query token is only accepted on /api/jobs/stream",
        )

    raise HTTPException(status_code=401, detail="unauthorized")
