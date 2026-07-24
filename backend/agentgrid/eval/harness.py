from __future__ import annotations

import json
from pathlib import Path

from agentgrid.agents.catalog import ISSUES
from agentgrid.agents.pipeline import run_pipeline
from agentgrid.config import ROOT
from agentgrid.models import AgentMode


def run_eval(issue_ids: list[str] | None = None) -> dict:
    ids = issue_ids or list(ISSUES.keys())
    rows = []
    for issue_id in ids:
        single = run_pipeline(issue_id, AgentMode.single, job_id=f"eval-single-{issue_id}")
        multi = run_pipeline(issue_id, AgentMode.multi, job_id=f"eval-multi-{issue_id}")
        rows.append(
            {
                "issue_id": issue_id,
                "single": {
                    "succeeded": single.succeeded,
                    "tokens": single.tokens_used,
                    "cost_usd": single.cost_usd,
                    "latency_ms": single.latency_ms,
                },
                "multi": {
                    "succeeded": multi.succeeded,
                    "tokens": multi.tokens_used,
                    "cost_usd": multi.cost_usd,
                    "latency_ms": multi.latency_ms,
                },
            }
        )

    single_ok = sum(1 for r in rows if r["single"]["succeeded"])
    multi_ok = sum(1 for r in rows if r["multi"]["succeeded"])
    summary = {
        "n_issues": len(rows),
        "single_success_rate": round(single_ok / len(rows), 4) if rows else 0.0,
        "multi_success_rate": round(multi_ok / len(rows), 4) if rows else 0.0,
        "single_avg_tokens": round(
            sum(r["single"]["tokens"] for r in rows) / len(rows), 1
        )
        if rows
        else 0,
        "multi_avg_tokens": round(sum(r["multi"]["tokens"] for r in rows) / len(rows), 1)
        if rows
        else 0,
        "rows": rows,
    }

    out = ROOT / "data" / "eval_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    summary["wrote"] = str(out)
    return summary
