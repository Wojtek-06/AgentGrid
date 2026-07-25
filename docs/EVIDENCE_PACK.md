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

1. Enqueue `qf-leakage-guard` as **single** (fails) and **multi** (succeeds after retry).
2. Click **Run eval** — show success-rate table; note metrics strip (tokens / $ / latency).
3. Open succeeded job — show patch artifact path + `REVIEW_CHECKLIST.md` under `.artifacts/`.
4. Seed analytics, Refresh — narrate grounded insight, day-1 retention, operator funnel.
5. Privacy: `DELETE /api/analytics/users/u1` then show event count 0.
6. Cancel a queued job / retry a failed one — operator recovery story.

## Docker

```bash
docker compose up --build
docker compose up --scale worker=2
```

## Interview claims (defendable)

- Coordinator + horizontal workers + durable queue + verifier gate
- Published multi- vs single-agent eval numbers on fixed dogfood issues
- Research-journey analytics with consent/deletion
- Dogfood sandboxes shaped like QuantForge leakage + ChainVenue basis bugs
