from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException

from agentgrid.api.deps import require_token
from agentgrid.config import ROOT
from agentgrid.eval.harness import run_eval
from agentgrid.schemas import EvalRequest

router = APIRouter(prefix="/api/eval", tags=["eval"], dependencies=[Depends(require_token)])

_EVAL_PATH = ROOT / "data" / "eval_results.json"


@router.get("/latest")
def eval_latest() -> dict:
    """Return committed/published eval JSON without re-running the harness."""
    if not _EVAL_PATH.is_file():
        raise HTTPException(status_code=404, detail="no eval results yet — run POST /api/eval/run")
    data = json.loads(_EVAL_PATH.read_text(encoding="utf-8"))
    data["source"] = str(_EVAL_PATH)
    return data


@router.post("/run")
def eval_run(body: EvalRequest) -> dict:
    return run_eval(body.issue_ids)
