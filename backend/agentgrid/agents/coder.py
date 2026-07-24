from __future__ import annotations

from pathlib import Path

from agentgrid.agents.catalog import IssueSpec


def apply_fix_patch(workspace: Path, spec: IssueSpec, *, wrong: bool = False) -> str:
    """Apply a deterministic patch inside an isolated workspace copy."""
    target = workspace / spec.broken_file
    text = target.read_text(encoding="utf-8")
    if wrong:
        # Deliberately bad "fix" for single-agent first attempt on hard issues.
        bad = spec.broken_snippet.replace("BUG", "STILL_BUG")
        if spec.broken_snippet not in text:
            raise FileNotFoundError(f"broken snippet missing in {target}")
        # Leave broken code intact — simulates a failed single-shot edit.
        patch = (
            f"--- a/{spec.broken_file}\n+++ b/{spec.broken_file}\n"
            f"# no-op wrong attempt\n"
        )
        _ = bad
        return patch

    if spec.broken_snippet not in text:
        raise FileNotFoundError(f"broken snippet missing in {target}")
    new_text = text.replace(spec.broken_snippet, spec.fixed_snippet, 1)
    target.write_text(new_text, encoding="utf-8")
    return (
        f"--- a/{spec.broken_file}\n+++ b/{spec.broken_file}\n"
        f"-{spec.broken_snippet}\n+{spec.fixed_snippet}\n"
    )
