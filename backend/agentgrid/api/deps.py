from __future__ import annotations

from fastapi import Header, HTTPException, Query

from agentgrid.config import settings


def require_token(
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None, description="Bearer alternative for SSE"),
) -> None:
    if not settings.api_token:
        return
    expected = f"Bearer {settings.api_token}"
    if authorization == expected:
        return
    if token == settings.api_token:
        return
    raise HTTPException(status_code=401, detail="unauthorized")
