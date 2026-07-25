from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from agentgrid.observability import get_logger, new_request_id, request_id_ctx

log = get_logger("agentgrid.http")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        rid = request.headers.get("x-request-id") or new_request_id()
        token = request_id_ctx.set(rid)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            if request.url.path.startswith("/api/"):
                log.info(
                    "method=%s path=%s status=%s",
                    request.method,
                    request.url.path,
                    response.status_code,
                )
            return response
        finally:
            request_id_ctx.reset(token)
