from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from agentgrid.agents.catalog import ISSUES, list_issues
from agentgrid.api.deps import require_token
from agentgrid.db import get_db
from agentgrid.models import Job, JobStatus
from agentgrid.queue import get_broker
from agentgrid.schemas import IssueOut, JobCreate, JobOut

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
    return job


@router.get("", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db)) -> list[Job]:
    return list(db.execute(select(Job).order_by(Job.created_at.desc())).scalars())


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="not found")
    return job
