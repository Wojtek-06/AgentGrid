from __future__ import annotations

from fastapi import APIRouter, Depends

from agentgrid.api.deps import require_token
from agentgrid.eval.harness import run_eval
from agentgrid.schemas import EvalRequest

router = APIRouter(prefix="/api/eval", tags=["eval"], dependencies=[Depends(require_token)])


@router.post("/run")
def eval_run(body: EvalRequest) -> dict:
    return run_eval(body.issue_ids)
