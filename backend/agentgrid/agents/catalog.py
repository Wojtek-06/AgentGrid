from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentgrid.config import settings


@dataclass(frozen=True)
class IssueSpec:
    issue_id: str
    title: str
    sandbox_rel: str
    broken_file: str
    broken_snippet: str
    fixed_snippet: str
    description: str
    # Single-agent is clumsier: may apply a wrong first attempt on hard issues.
    single_agent_fail_first: bool = False


ISSUES: dict[str, IssueSpec] = {
    "qf-leakage-guard": IssueSpec(
        issue_id="qf-leakage-guard",
        title="Fix mid-as-of look-ahead guard (QuantForge-shaped)",
        sandbox_rel="dogfood_qf_leakage",
        broken_file="research_mid.py",
        broken_snippet="return series[-1]  # BUG: uses future bar",
        fixed_snippet="return series[i]  # as-of: only current index",
        description="Naïve mid uses the last bar (look-ahead). Should return series[i].",
        single_agent_fail_first=True,
    ),
    "cv-basis-bps": IssueSpec(
        issue_id="cv-basis-bps",
        title="Fix basis bps sign for hedge side (ChainVenue-shaped)",
        sandbox_rel="dogfood_cv_basis",
        broken_file="basis.py",
        broken_snippet="return int((amm_mid - clob_mid) / clob_mid * 10_000)",
        fixed_snippet="return int((clob_mid - amm_mid) / clob_mid * 10_000)",
        description="Basis should be CLOB − AMM in bps so positive means CLOB rich.",
        single_agent_fail_first=False,
    ),
    "qf-ewma-alpha": IssueSpec(
        issue_id="qf-ewma-alpha",
        title="Fix EWMA weight order (QuantForge-shaped)",
        sandbox_rel="dogfood_qf_ewma",
        broken_file="ewma.py",
        broken_snippet="return (1.0 - alpha) * observation + alpha * prev",
        fixed_snippet="return alpha * observation + (1.0 - alpha) * prev",
        description="EWMA must weight the new observation by alpha, not (1-alpha).",
        single_agent_fail_first=True,
    ),
}


def issue_sandbox_path(issue_id: str) -> Path:
    spec = ISSUES[issue_id]
    return settings.sandbox_root / spec.sandbox_rel


def list_issues() -> list[IssueSpec]:
    return list(ISSUES.values())
