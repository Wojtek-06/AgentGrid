from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = str(ROOT / "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


def _purge_agentgrid() -> None:
    for name in list(sys.modules):
        if name == "agentgrid" or name.startswith("agentgrid."):
            del sys.modules[name]


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "t.db"
    art = tmp_path / "artifacts"
    art.mkdir()
    monkeypatch.setenv("AGENTGRID_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AGENTGRID_ARTIFACT_DIR", str(art))
    monkeypatch.setenv("AGENTGRID_USE_REDIS", "0")
    monkeypatch.setenv("AGENTGRID_API_TOKEN", "test-token")
    monkeypatch.setenv("AGENTGRID_SANDBOX_ROOT", str(ROOT / "sandbox"))

    _purge_agentgrid()

    from agentgrid.db import init_db
    from agentgrid.main import app

    init_db()

    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c
