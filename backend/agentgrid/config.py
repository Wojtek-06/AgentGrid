from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AGENTGRID_",
        env_file=".env",
        extra="ignore",
    )

    database_url: str = f"sqlite:///{ROOT / 'data' / 'agentgrid.db'}"
    redis_url: str = "redis://localhost:6379/0"
    artifact_dir: Path = ROOT / ".artifacts"
    sandbox_root: Path = ROOT / "sandbox"
    api_token: str = "dev-token"
    worker_poll_ms: int = 500
    use_redis: bool = False
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000"


settings = Settings()
settings.artifact_dir.mkdir(parents=True, exist_ok=True)
(ROOT / "data").mkdir(parents=True, exist_ok=True)
