from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from agentgrid.agents.catalog import ISSUES, list_issues
from agentgrid.api.deps import require_token
from agentgrid.config import settings
from agentgrid.db import SessionLocal, get_db
from agentgrid.models import Job, JobStatus
from agentgrid.observability import get_logger
from agentgrid.queue import get_broker
from agentgrid.schemas import IssueOut, JobCreate, JobOut

log = get_logger("agentgrid.jobs")
router = APIRouter(prefix="/api/jobs", tags=["jobs"], dependencies=[Depends(require_token)])


@router.get("/issues", response_model=list[IssueOut])
def get_issues() -> list[IssueOut]:
    return [
        IssueOut(issue_id=i.issue_id, title=i.title, description=i.description)
        for i in list_issues()
    ]


@router.post("", response_model=JobOut)
def create_job(body: JobCreate, db: Session = Depends(get_db)) -> Job:
    if body.issue_id not in ISSUES:
        raise HTTPException(status_code=404, detail="unknown issue_id")

    if body.idempotency_key:
        existing = db.execute(
            select(Job).where(Job.idempotency_key == body.idempotency_key)
        ).scalar_one_or_none()
        if existing:
            return existing

    depth = get_broker().depth()
    if depth >= settings.max_queue_depth:
        raise HTTPException(
            status_code=429,
            detail=f"backpressure: queue_depth={depth} >= max={settings.max_queue_depth}",
        )

    spec = ISSUES[body.issue_id]
    job = Job(
        id=str(uuid.uuid4()),
        issue_id=body.issue_id,
        title=spec.title,
        mode=body.mode,
        status=JobStatus.queued,
        idempotency_key=body.idempotency_key,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    get_broker().enqueue(job.id)
    log.info("action=enqueue job_id=%s issue_id=%s mode=%s", job.id, job.issue_id, job.mode.value)
    return job


@router.get("", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db)) -> list[Job]:
    return list(db.execute(select(Job).order_by(Job.created_at.desc())).scalars())


def _job_snapshot(job: Job) -> dict:
    return {
        "id": job.id,
        "issue_id": job.issue_id,
        "mode": job.mode.value,
        "status": job.status.value,
        "tokens_used": job.tokens_used,
        "cost_usd": job.cost_usd,
        "latency_ms": job.latency_ms,
        "error": job.error,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


@router.get("/stream")
async def stream_jobs(
    request: Request,
    max_events: int | None = None,
) -> StreamingResponse:
    """SSE feed of job board snapshots (lightweight live status).

    `max_events` bounds the stream (useful for tests); omit for a live feed.
    """

    async def event_gen():
        last_sig = ""
        emitted = 0
        while True:
            if await request.is_disconnected():
                break
            if max_events is not None and emitted >= max_events:
                break
            db = SessionLocal()
            try:
                jobs = list(
                    db.execute(select(Job).order_by(Job.created_at.desc()).limit(50)).scalars()
                )
                payload = [_job_snapshot(j) for j in jobs]
                sig = json.dumps(
                    [(j["id"], j["status"], j["updated_at"]) for j in payload],
                    sort_keys=True,
                )
                if sig != last_sig:
                    last_sig = sig
                    yield f"event: jobs\ndata: {json.dumps(payload)}\n\n"
                else:
                    yield "event: ping\ndata: {}\n\n"
                emitted += 1
            finally:
                db.close()
            if max_events is not None and emitted >= max_events:
                break
            await asyncio.sleep(1.0)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="not found")
    return job


@router.post("/{job_id}/cancel", response_model=JobOut)
def cancel_job(job_id: str, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="not found")
    if job.status in {JobStatus.succeeded, JobStatus.cancelled}:
        return job
    job.status = JobStatus.cancelled
    job.error = (job.error + "\n" if job.error else "") + "cancelled_by_operator"
    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/retry", response_model=JobOut)
def retry_job(job_id: str, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="not found")
    if job.status not in {JobStatus.failed, JobStatus.cancelled}:
        raise HTTPException(status_code=400, detail="only failed/cancelled jobs can retry")
    depth = get_broker().depth()
    if depth >= settings.max_queue_depth:
        raise HTTPException(status_code=429, detail="backpressure: queue full")
    job.status = JobStatus.queued
    job.error = None
    db.commit()
    db.refresh(job)
    get_broker().enqueue(job.id)
    return job
