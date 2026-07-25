from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get("-")
        return True


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if getattr(root, "_agentgrid_configured", False):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s level=%(levelname)s logger=%(name)s "
            "request_id=%(request_id)s %(message)s"
        )
    )
    handler.addFilter(RequestIdFilter())
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
    root._agentgrid_configured = True  # type: ignore[attr-defined]


def new_request_id() -> str:
    return uuid.uuid4().hex[:16]


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
