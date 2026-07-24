from __future__ import annotations

from agentgrid.agents.pipeline import run_multi_agent, run_single_agent
from agentgrid.models import AgentMode


def test_multi_fixes_hard_leakage_issue():
    result = run_multi_agent("qf-leakage-guard", job_id="t-multi-qf")
    assert result.succeeded
    assert "retry" in result.verify_log or result.patch_text


def test_single_fails_hard_leakage_issue():
    result = run_single_agent("qf-leakage-guard", job_id="t-single-qf")
    assert not result.succeeded


def test_both_modes_fix_basis_issue():
    s = run_single_agent("cv-basis-bps", job_id="t-single-cv")
    m = run_multi_agent("cv-basis-bps", job_id="t-multi-cv")
    assert s.succeeded
    assert m.succeeded
