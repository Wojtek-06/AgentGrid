from __future__ import annotations

from agentgrid.eval.harness import run_eval


def test_eval_multi_beats_or_ties_single():
    summary = run_eval()
    assert summary["n_issues"] == 2
    assert summary["multi_success_rate"] >= summary["single_success_rate"]
    assert summary["multi_success_rate"] == 1.0
    assert summary["single_success_rate"] < 1.0
