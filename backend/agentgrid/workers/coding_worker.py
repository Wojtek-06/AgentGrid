from __future__ import annotations

import argparse
import socket
import traceback

from agentgrid.agents.merge import integrate_result
from agentgrid.agents.pipeline import run_pipeline
from agentgrid.config import settings
from agentgrid.db import SessionLocal, init_db
from agentgrid.models import Job, JobStatus
from agentgrid.queue import get_broker


def process_job(job_id: str, worker_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return
        if job.status == JobStatus.cancelled:
            return
        if job.status not in {JobStatus.queued, JobStatus.failed}:
            return

        job.status = JobStatus.planning
        job.worker_id = worker_id
        job.attempts += 1
        db.commit()

        # Re-check cancel between stages (idempotent recovery).
        db.refresh(job)
        if job.status == JobStatus.cancelled:
            return

        job.status = JobStatus.coding
        db.commit()

        result = run_pipeline(job.issue_id, job.mode, job_id=job.id)

        db.refresh(job)
        if job.status == JobStatus.cancelled:
            return

        job.plan_json = result.plan
        job.patch_text = result.patch_text
        job.verify_log = result.verify_log
        job.tokens_used = result.tokens_used
        job.cost_usd = result.cost_usd
        job.latency_ms = result.latency_ms
        job.status = JobStatus.verifying
        db.commit()

        if result.succeeded:
            job.status = JobStatus.integrating
            db.commit()
            integrate_result(db, job, result)
            job.status = JobStatus.succeeded
            if not (job.error and "merge_conflict" in job.error):
                job.error = None
        else:
            job.status = JobStatus.failed
            job.error = result.error
            integrate_result(db, job, result)

        db.commit()
    except Exception as exc:  # noqa: BLE001 — worker boundary
        db.rollback()
        job = db.get(Job, job_id)
        if job and job.status != JobStatus.cancelled:
            job.status = JobStatus.failed
            job.error = f"{exc}\n{traceback.format_exc()}"
            db.commit()
    finally:
        db.close()


def run_forever(worker_id: str | None = None) -> None:
    init_db()
    worker_id = worker_id or f"{socket.gethostname()}-{id(object())}"
    broker = get_broker()
    print(f"[worker {worker_id}] polling queue…", flush=True)
    while True:
        item = broker.dequeue(timeout_s=max(0.2, settings.worker_poll_ms / 1000))
        if not item:
            continue
        print(f"[worker {worker_id}] job={item['job_id']}", flush=True)
        process_job(item["job_id"], worker_id)


def main() -> None:
    p = argparse.ArgumentParser(description="AgentGrid coding worker")
    p.add_argument("--once", action="store_true", help="Process at most one job then exit")
    p.add_argument("--worker-id", default=None)
    args = p.parse_args()
    init_db()
    worker_id = args.worker_id or f"{socket.gethostname()}-once"
    if args.once:
        item = get_broker().dequeue(timeout_s=2.0)
        if item:
            process_job(item["job_id"], worker_id)
        return
    run_forever(worker_id)


if __name__ == "__main__":
    main()
