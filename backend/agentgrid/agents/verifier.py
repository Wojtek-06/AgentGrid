from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from agentgrid.config import settings


@dataclass
class VerifyResult:
    ok: bool
    log: str
    exit_code: int


def run_pytest(workspace: Path, timeout_s: float | None = None) -> VerifyResult:
    budget = float(timeout_s if timeout_s is not None else settings.verify_timeout_s)
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", str(workspace / "tests")],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=budget,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        log = (exc.stdout or "") + (exc.stderr or "")
        log = f"{log}\nverifier_timeout after {budget}s".strip()
        return VerifyResult(ok=False, log=log, exit_code=-1)
    log = (proc.stdout or "") + (proc.stderr or "")
    return VerifyResult(ok=proc.returncode == 0, log=log, exit_code=proc.returncode)
