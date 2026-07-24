from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VerifyResult:
    ok: bool
    log: str
    exit_code: int


def run_pytest(workspace: Path, timeout_s: float = 30.0) -> VerifyResult:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(workspace / "tests")],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    log = (proc.stdout or "") + (proc.stderr or "")
    return VerifyResult(ok=proc.returncode == 0, log=log, exit_code=proc.returncode)
