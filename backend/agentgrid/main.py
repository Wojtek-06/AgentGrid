from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agentgrid import __version__
from agentgrid.api import analytics, eval_api, jobs, metrics
from agentgrid.config import ROOT, settings
from agentgrid.db import init_db
from agentgrid.middleware.rate_limit import RateLimitMiddleware
from agentgrid.middleware.request_id import RequestIdMiddleware
from agentgrid.observability import configure_logging, get_logger
from agentgrid.queue import get_broker
from agentgrid.workers.heartbeat import list_alive

configure_logging()
log = get_logger("agentgrid.main")


def _redis_ok() -> bool | None:
    if not settings.use_redis:
        return None
    try:
        import redis

        client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        return bool(client.ping())
    except Exception:  # noqa: BLE001 — health probe
        return False


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    get_broker()
    if settings.api_token == "dev-token":
        log.warning(
            "action=startup_warn reason=default_api_token "
            "hint=set AGENTGRID_API_TOKEN for anything beyond local demo"
        )
    if not settings.use_redis:
        log.warning(
            "action=startup_warn reason=in_process_queue "
            "hint=set AGENTGRID_USE_REDIS=1 and start Redis for a separate worker process"
        )
    log.info("action=startup version=%s use_redis=%s", __version__, settings.use_redis)
    yield


app = FastAPI(
    title="AgentGrid",
    description="Horizontally scaled coding agents + trading/research behaviour analytics",
    version=__version__,
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIdMiddleware)

app.include_router(jobs.router)
app.include_router(analytics.router)
app.include_router(eval_api.router)
app.include_router(metrics.router)

frontend_dist = ROOT / "frontend" / "dist"
frontend_public = ROOT / "frontend" / "public"
if (frontend_dist / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")


@app.get("/api/health")
def health() -> dict:
    workers = list_alive()
    redis_ok = _redis_ok()
    use_redis = settings.use_redis
    queue_hint = None
    if not use_redis:
        queue_hint = (
            "in-process queue — start Redis and set AGENTGRID_USE_REDIS=1 "
            "before running a separate coding_worker process"
        )
    elif redis_ok is False:
        queue_hint = f"Redis unreachable at {settings.redis_url}"
    return {
        "ok": True,
        "version": __version__,
        "queue_depth": get_broker().depth(),
        "use_redis": use_redis,
        "redis_ok": redis_ok,
        "workers_alive": len(workers),
        "workers": workers,
        "default_token": settings.api_token == "dev-token",
        "queue_hint": queue_hint,
    }


@app.get("/")
def index() -> FileResponse:
    built = frontend_dist / "index.html"
    if built.is_file():
        return FileResponse(built)
    return FileResponse(frontend_public / "index.html")
