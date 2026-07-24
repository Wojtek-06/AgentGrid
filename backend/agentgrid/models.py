from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from agentgrid.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobStatus(str, enum.Enum):
    queued = "queued"
    planning = "planning"
    coding = "coding"
    verifying = "verifying"
    integrating = "integrating"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class AgentMode(str, enum.Enum):
    single = "single"
    multi = "multi"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    issue_id: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(256))
    mode: Mapped[AgentMode] = mapped_column(
        Enum(AgentMode, native_enum=False), default=AgentMode.multi
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False), default=JobStatus.queued, index=True
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    plan_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    patch_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    verify_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    worker_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(36), index=True)
    kind: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(String(512))
    meta_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    props: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    consent: Mapped[bool] = mapped_column(Boolean, default=True)


class UserPrivacy(Base):
    __tablename__ = "user_privacy"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    consent_analytics: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
