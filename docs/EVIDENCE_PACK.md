# AgentGrid evidence pack

## Generate artefacts

```powershell
cd C:\Projekty\Quant\AgentGrid
python -m pip install -r requirements.txt
$env:PYTHONPATH = "backend"
python -m pytest -q
python scripts\run_eval.py
python scripts\seed_analytics.py
```

Eval JSON: `data/eval_results.json` (multi vs single success rates).

### Sample published numbers (3 dogfood issues)

| Issue | Single | Multi |
|-------|--------|-------|
| `qf-leakage-guard` | fail | succeed (retry) |
| `qf-ewma-alpha` | fail | succeed (retry) |
| `cv-basis-bps` | succeed | succeed |
| **Rates** | **33%** | **100%** |

Regenerate after catalog changes; commit `data/eval_results.json` when rates change.

## Local demo

```powershell
# Terminal A — API
$env:PYTHONPATH = "backend"
python -m uvicorn agentgrid.main:app --reload --port 8000

# Terminal B — worker
$env:PYTHONPATH = "backend"
python -m agentgrid.workers.coding_worker
```

Open http://127.0.0.1:8000 — token `dev-token`.

1. Enqueue `qf-leakage-guard` or `qf-ewma-alpha` as **single** (fails) and **multi** (succeeds after retry).
2. Click **Run eval** — show success-rate table; note metrics strip (tokens / $ / latency).
3. Open succeeded job — show patch artifact path + `REVIEW_CHECKLIST.md` under `.artifacts/`.
4. Enqueue the same issue twice as multi — second job surfaces `merge_conflict_risk` in plan/error.
5. Seed analytics, Refresh — narrate grounded insight, day-1 retention, operator funnel.
6. Privacy: `DELETE /api/analytics/users/u1` then show event count 0.
7. Cancel a queued job / retry a failed one — operator recovery story.
8. Point at live board updates via SSE (`/api/jobs/stream`) and `X-Request-ID` on API responses.

## Docker

```bash
# Default: Redis + SQLite volume
docker compose up --build
docker compose up --scale worker=2

# Optional Postgres profile
docker compose --profile postgres up --build api-pg worker-pg postgres redis
```

## Interview claims (defendable)

- Coordinator + horizontal workers + durable queue + verifier gate
- Published multi- vs single-agent eval numbers on fixed dogfood issues (JSON + docs table)
- Research-journey analytics with consent/deletion
- Dogfood sandboxes shaped like QuantForge leakage/EWMA + ChainVenue basis bugs
- Merge conflict risk when re-patching the same sandbox file
- Request-ID structured logs + SSE board for ops story
