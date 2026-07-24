from __future__ import annotations

from agentgrid.agents.catalog import ISSUES, IssueSpec


def plan_issue(issue_id: str) -> dict:
    spec = ISSUES[issue_id]
    return {
        "issue_id": spec.issue_id,
        "summary": spec.description,
        "steps": [
            {"id": "locate", "action": "open", "target": spec.broken_file},
            {"id": "patch", "action": "replace", "target": spec.broken_file},
            {"id": "verify", "action": "pytest", "target": "tests/"},
        ],
        "acceptance": "pytest exits 0",
        "tokens": 120,
    }


def get_spec(issue_id: str) -> IssueSpec:
    if issue_id not in ISSUES:
        raise KeyError(f"unknown issue: {issue_id}")
    return ISSUES[issue_id]
