from __future__ import annotations

import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from agentgrid.agents.catalog import issue_sandbox_path
from agentgrid.agents.coder import apply_fix_patch
from agentgrid.agents.planner import get_spec, plan_issue
from agentgrid.agents.verifier import run_pytest
from agentgrid.config import settings
from agentgrid.models import AgentMode


@dataclass
class RunResult:
    succeeded: bool
    plan: dict
    patch_text: str
    verify_log: str
    tokens_used: int
    cost_usd: float
    latency_ms: int
    error: str | None
    workspace: Path


def _isolate(issue_id: str, job_id: str) -> Path:
    src = issue_sandbox_path(issue_id)
    if not src.is_dir():
        raise FileNotFoundError(f"sandbox missing: {src}")
    dest = settings.artifact_dir / job_id / "workspace"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    return dest


def run_single_agent(issue_id: str, job_id: str | None = None) -> RunResult:
    """One-shot: plan+code without verifier feedback loop (weaker on hard issues)."""
    t0 = time.perf_counter()
    job_id = job_id or str(uuid.uuid4())
    spec = get_spec(issue_id)
    plan = plan_issue(issue_id)
    tokens = plan["tokens"] + 80
    workspace = _isolate(issue_id, job_id)

    # Hard issues: single agent applies a wrong first (and only) attempt.
    wrong = spec.single_agent_fail_first
    patch = apply_fix_patch(workspace, spec, wrong=wrong)
    if wrong:
        # Still "edits" nothing useful — leave file broken.
        verify = run_pytest(workspace)
        ms = int((time.perf_counter() - t0) * 1000)
        return RunResult(
            succeeded=False,
            plan=plan,
            patch_text=patch,
            verify_log=verify.log,
            tokens_used=tokens,
            cost_usd=round(tokens * 0.00002, 6),
            latency_ms=ms,
            error="single-agent patch failed verification",
            workspace=workspace,
        )

    verify = run_pytest(workspace)
    ms = int((time.perf_counter() - t0) * 1000)
    return RunResult(
        succeeded=verify.ok,
        plan=plan,
        patch_text=patch,
        verify_log=verify.log,
        tokens_used=tokens,
        cost_usd=round(tokens * 0.00002, 6),
        latency_ms=ms,
        error=None if verify.ok else "verifier failed",
        workspace=workspace,
    )


def run_multi_agent(issue_id: str, job_id: str | None = None) -> RunResult:
    """Plan → code → verify → retry with correct patch (verifier feedback)."""
    t0 = time.perf_counter()
    job_id = job_id or str(uuid.uuid4())
    spec = get_spec(issue_id)
    plan = plan_issue(issue_id)
    tokens = plan["tokens"]
    workspace = _isolate(issue_id, job_id)

    # Attempt 1 may be wrong on hard issues; verifier forces retry.
    if spec.single_agent_fail_first:
        apply_fix_patch(workspace, spec, wrong=True)
        tokens += 90
        first = run_pytest(workspace)
        if not first.ok:
            # Reset workspace and apply correct patch (integration agent).
            shutil.rmtree(workspace)
            workspace = _isolate(issue_id, job_id)
            patch = apply_fix_patch(workspace, spec, wrong=False)
            tokens += 110
            verify = run_pytest(workspace)
            ms = int((time.perf_counter() - t0) * 1000)
            return RunResult(
                succeeded=verify.ok,
                plan=plan,
                patch_text=patch,
                verify_log=first.log + "\n--- retry ---\n" + verify.log,
                tokens_used=tokens,
                cost_usd=round(tokens * 0.00002, 6),
                latency_ms=ms,
                error=None if verify.ok else "verifier failed after retry",
                workspace=workspace,
            )

    patch = apply_fix_patch(workspace, spec, wrong=False)
    tokens += 100
    verify = run_pytest(workspace)
    ms = int((time.perf_counter() - t0) * 1000)
    return RunResult(
        succeeded=verify.ok,
        plan=plan,
        patch_text=patch,
        verify_log=verify.log,
        tokens_used=tokens,
        cost_usd=round(tokens * 0.00002, 6),
        latency_ms=ms,
        error=None if verify.ok else "verifier failed",
        workspace=workspace,
    )


def run_pipeline(issue_id: str, mode: AgentMode, job_id: str | None = None) -> RunResult:
    if mode == AgentMode.single:
        return run_single_agent(issue_id, job_id)
    return run_multi_agent(issue_id, job_id)
