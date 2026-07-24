from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from agentgrid.models import AgentMode, JobStatus


class JobCreate(BaseModel):
    issue_id: str
    mode: AgentMode = AgentMode.multi
    idempotency_key: str | None = None


class JobOut(BaseModel):
    id: str
    issue_id: str
    title: str
    mode: AgentMode
    status: JobStatus
    tokens_used: int
    cost_usd: float
    latency_ms: int
    attempts: int
    worker_id: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime
    plan_json: dict[str, Any] | None = None
    patch_text: str | None = None
    verify_log: str | None = None

    model_config = {"from_attributes": True}


class IssueOut(BaseModel):
    issue_id: str
    title: str
    description: str


class EventIn(BaseModel):
    event_id: str
    user_id: str
    session_id: str
    name: str
    ts: datetime | None = None
    props: dict[str, Any] | None = None
    consent: bool = True


class EventBatchIn(BaseModel):
    events: list[EventIn] = Field(min_length=1)


class ConsentIn(BaseModel):
    user_id: str
    consent_analytics: bool


class EvalRequest(BaseModel):
    issue_ids: list[str] | None = None
