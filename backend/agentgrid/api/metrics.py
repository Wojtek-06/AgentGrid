from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from agentgrid.api.deps import require_token
from agentgrid.db import get_db
from agentgrid.models import Job, JobStatus
from agentgrid.queue import get_broker

router = APIRouter(prefix="/api/metrics", tags=["metrics"], dependencies=[Depends(require_token)])


@router.get("/overview")
def overview(db: Session = Depends(get_db)) -> dict:
    jobs = list(db.execute(select(Job)).scalars())
    by_status = Counter(j.status.value for j in jobs)
    succeeded = [j for j in jobs if j.status == JobStatus.succeeded]
    failed = [j for j in jobs if j.status == JobStatus.failed]
    tokens = sum(j.tokens_used for j in jobs)
    cost = sum(j.cost_usd for j in jobs)
    latencies = [j.latency_ms for j in jobs if j.latency_ms > 0]
    return {
        "jobs_total": len(jobs),
        "by_status": dict(by_status),
        "success_rate": round(len(succeeded) / len(jobs), 4) if jobs else 0.0,
        "fail_rate": round(len(failed) / len(jobs), 4) if jobs else 0.0,
        "tokens_total": tokens,
        "cost_usd_total": round(cost, 6),
        "latency_ms_avg": round(sum(latencies) / len(latencies), 1) if latencies else 0,
        "queue_depth": get_broker().depth(),
        "active_workers_hint": by_status.get("coding", 0)
        + by_status.get("planning", 0)
        + by_status.get("verifying", 0),
    }
