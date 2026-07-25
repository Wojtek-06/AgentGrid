from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentgrid.agents.catalog import ISSUES
from agentgrid.agents.pipeline import RunResult
from agentgrid.config import settings
from agentgrid.models import Artifact, Job, JobStatus


REVIEW_CHECKLIST = """# Human review checklist (dogfood acceptance)

- [ ] Verifier (pytest) green in isolated workspace
- [ ] Patch touches only the intended file
- [ ] No secrets / network calls introduced
- [ ] Multi-agent retry path documented in verify log (if hard issue)
- [ ] Ready to cherry-pick into QuantForge / ChainVenue manually

Issue: {issue_id}
Job: {job_id}
Mode: {mode}
"""


def detect_file_conflict(db: Session, job: Job) -> str | None:
    """Flag if another succeeded job already patched the same sandbox file recently."""
    spec = ISSUES.get(job.issue_id)
    if not spec:
        return None
    others = db.execute(
        select(Job).where(
            Job.issue_id == job.issue_id,
            Job.status == JobStatus.succeeded,
            Job.id != job.id,
        )
    ).scalars().all()
    if not others:
        return None
    return (
        f"merge_conflict_risk: {len(others)} prior succeeded job(s) already patched "
        f"{spec.broken_file} for {job.issue_id}"
    )


def integrate_result(db: Session, job: Job, result: RunResult) -> None:
    """Write patch + checklist artifacts and finalize merge status."""
    art_dir = settings.artifact_dir / job.id
    art_dir.mkdir(parents=True, exist_ok=True)

    patch_path = art_dir / "change.patch"
    patch_path.write_text(result.patch_text or "", encoding="utf-8")
    db.add(
        Artifact(
            job_id=job.id,
            kind="patch",
            path=str(patch_path),
            meta_json={"bytes": patch_path.stat().st_size},
        )
    )

    checklist = REVIEW_CHECKLIST.format(
        issue_id=job.issue_id, job_id=job.id, mode=job.mode.value
    )
    check_path = art_dir / "REVIEW_CHECKLIST.md"
    check_path.write_text(checklist, encoding="utf-8")
    db.add(
        Artifact(
            job_id=job.id,
            kind="review_checklist",
            path=str(check_path),
            meta_json={"acceptance": "human_review"},
        )
    )

    db.add(
        Artifact(
            job_id=job.id,
            kind="workspace",
            path=str(result.workspace),
            meta_json={"succeeded": result.succeeded},
        )
    )

    conflict = detect_file_conflict(db, job) if result.succeeded else None
    if conflict:
        job.error = (job.error + "\n" if job.error else "") + conflict
        # Still succeed verification, but surface conflict for operator.
        job.plan_json = {
            **(job.plan_json or {}),
            "merge_warning": conflict,
        }
