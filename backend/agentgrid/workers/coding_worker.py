from __future__ import annotations

import argparse
import socket
import traceback
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

from agentgrid.agents.merge import integrate_result
from agentgrid.agents.pipeline import run_pipeline
from agentgrid.config import settings
from agentgrid.db import SessionLocal, init_db
from agentgrid.models import Job, JobStatus
from agentgrid.observability import configure_logging, get_logger, new_request_id, request_id_ctx
from agentgrid.queue import get_broker
from agentgrid.workers.heartbeat import beat

configure_logging()
log = get_logger("agentgrid.worker")


def process_job(job_id: str, worker_id: str) -> None:
    rid = new_request_id()
    token = request_id_ctx.set(rid)
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            log.warning("action=skip job_id=%s reason=missing", job_id)
            return
        if job.status == JobStatus.cancelled:
            log.info("action=skip job_id=%s reason=cancelled", job_id)
            return
        if job.status not in {JobStatus.queued, JobStatus.failed}:
            log.info(
                "action=skip job_id=%s reason=bad_status status=%s",
                job_id,
                job.status.value,
            )
            return

        job.status = JobStatus.planning
        job.worker_id = worker_id
        job.attempts += 1
        db.commit()
        beat(worker_id, status="planning")
        log.info(
            "action=planning job_id=%s issue_id=%s mode=%s worker_id=%s attempt=%s timeout_s=%s",
            job_id,
            job.issue_id,
            job.mode.value,
            worker_id,
            job.attempts,
            settings.job_timeout_s,
        )

        # Re-check cancel between stages (idempotent recovery).
        db.refresh(job)
        if job.status == JobStatus.cancelled:
            log.info("action=skip job_id=%s reason=cancelled_mid_plan", job_id)
            return

        job.status = JobStatus.coding
        db.commit()
        beat(worker_id, status="coding")
        log.info("action=coding job_id=%s issue_id=%s", job_id, job.issue_id)

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(run_pipeline, job.issue_id, job.mode, job.id)
            try:
                result = future.result(timeout=settings.job_timeout_s)
            except FuturesTimeout:
                future.cancel()
                db.refresh(job)
                if job.status != JobStatus.cancelled:
                    job.status = JobStatus.failed
                    job.error = f"job_timeout after {settings.job_timeout_s}s"
                    db.commit()
                log.error(
                    "action=timeout job_id=%s timeout_s=%s",
                    job_id,
                    settings.job_timeout_s,
                )
                return

        db.refresh(job)
        if job.status == JobStatus.cancelled:
            log.info("action=skip job_id=%s reason=cancelled_after_pipeline", job_id)
            return

        job.plan_json = result.plan
        job.patch_text = result.patch_text
        job.verify_log = result.verify_log
        job.tokens_used = result.tokens_used
        job.cost_usd = result.cost_usd
        job.latency_ms = result.latency_ms
        job.status = JobStatus.verifying
        db.commit()
        log.info(
            "action=verifying job_id=%s succeeded=%s tokens=%s",
            job_id,
            result.succeeded,
            result.tokens_used,
        )

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
        log.info(
            "action=finish job_id=%s status=%s tokens=%s cost_usd=%s latency_ms=%s",
            job_id,
            job.status.value,
            job.tokens_used,
            job.cost_usd,
            job.latency_ms,
        )
    except Exception as exc:  # noqa: BLE001 — worker boundary
        db.rollback()
        job = db.get(Job, job_id)
        if job and job.status != JobStatus.cancelled:
            job.status = JobStatus.failed
            job.error = f"{exc}\n{traceback.format_exc()}"
            db.commit()
        log.exception("action=error job_id=%s err=%s", job_id, exc)
    finally:
        db.close()
        request_id_ctx.reset(token)


def run_forever(worker_id: str | None = None) -> None:
    init_db()
    worker_id = worker_id or f"{socket.gethostname()}-{id(object())}"
    broker = get_broker()
    if not settings.use_redis:
        log.warning(
            "action=poll_warn reason=in_process_queue worker_id=%s "
            "hint=API and worker must share Redis (AGENTGRID_USE_REDIS=1)",
            worker_id,
        )
    log.info(
        "action=poll_start worker_id=%s use_redis=%s poll_ms=%s job_timeout_s=%s",
        worker_id,
        settings.use_redis,
        settings.worker_poll_ms,
        settings.job_timeout_s,
    )
    while True:
        beat(worker_id, status="idle")
        item = broker.dequeue(timeout_s=max(0.2, settings.worker_poll_ms / 1000))
        if not item:
            continue
        log.info("action=dequeue job_id=%s worker_id=%s", item["job_id"], worker_id)
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
        else:
            log.info("action=idle reason=no_job")
        return
    run_forever(worker_id)


if __name__ == "__main__":
    main()
