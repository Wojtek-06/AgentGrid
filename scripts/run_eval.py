#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from agentgrid.eval.harness import run_eval  # noqa: E402


def main() -> None:
    summary = run_eval()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
