from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agentgrid import __version__
from agentgrid.api import analytics, eval_api, jobs
from agentgrid.config import ROOT, settings
from agentgrid.db import init_db
from agentgrid.queue import get_broker


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    get_broker()
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

app.include_router(jobs.router)
app.include_router(analytics.router)
app.include_router(eval_api.router)

frontend_dist = ROOT / "frontend" / "dist"
frontend_public = ROOT / "frontend" / "public"
if (frontend_dist / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "version": __version__,
        "queue_depth": get_broker().depth(),
        "use_redis": settings.use_redis,
    }


@app.get("/")
def index() -> FileResponse:
    built = frontend_dist / "index.html"
    if built.is_file():
        return FileResponse(built)
    return FileResponse(frontend_public / "index.html")
