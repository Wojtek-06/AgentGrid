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

Eval JSON: [`data/eval_results.json`](../data/eval_results.json) (multi vs single success rates).

### Sample published numbers (3 dogfood issues)

| Issue | Single | Multi |
|-------|--------|-------|
| `qf-leakage-guard` | fail | succeed (retry) |
| `qf-ewma-alpha` | fail | succeed (retry) |
| `cv-basis-bps` | succeed | succeed |
| **Rates** | **33%** | **100%** |

Regenerate after catalog changes; commit `data/eval_results.json` when rates change.

## Local demo (prep)

Separate API + worker need Redis (in-process queue is pytest-only).

```powershell
docker compose up -d redis
# Terminal A
.\scripts\run_api.ps1
# Terminal B
.\scripts\run_worker.ps1
```

Open http://127.0.0.1:8000 — token `dev-token`. Confirm SSE **live**, health shows `redis on · workers ≥ 1`.

---

## 5-minute interview script (exact clicks)

| Min | Click / say |
|-----|-------------|
| **0:00–0:45** | Open the board. Point at **AgentGrid** header + status board (counts) + metrics strip. Say: coordinator API, Redis/local queue, coding workers, verifier gate — no live LLM in CI. |
| **0:45–1:45** | Issue dropdown → `qf-leakage-guard`. Mode → **single**. Click **Enqueue**. Wait until status **failed**. Click the row → show verify log / error in the detail pane. |
| **1:45–2:45** | Same issue, mode → **multi**. Click **Enqueue**. Wait until **succeeded**. Click the row → show patch text + retry section in verify log. Call out status-board counts updating live (SSE **live**). |
| **2:45–3:30** | Click **Load published** (instant) or **Run eval**. Scroll to **Eval summary** — multi **100%** / single **~33%**. Point at committed [`data/eval_results.json`](../data/eval_results.json). |
| **3:30–4:15** | Click a succeeded row → mention `.artifacts/<job_id>/` patch + `REVIEW_CHECKLIST.md`. Optional: enqueue the same issue again as multi → note `merge_conflict_risk` in plan/error. |
| **4:15–5:00** | If seeded: **Refresh** → narrate research funnel insight + day-1 retention. Point at `req <id>` (X-Request-ID) and SSE reconnect hint if you toggle the network. Privacy one-liner: `DELETE /api/analytics/users/u1` erases + blocks. |

Skip cancel/retry / Docker scale unless asked — those are in the longer checklist below.

## Longer demo checklist (optional)

1. Enqueue `qf-ewma-alpha` single (fails) vs multi (succeeds).
2. Cancel a queued job / retry a failed one.
3. `docker compose up --build --scale worker=2` for horizontal scale.
4. Privacy: `DELETE /api/analytics/users/u1` then show event count 0.

## Docker

```bash
# Default: Redis + SQLite volume
docker compose up --build
docker compose up --scale worker=2

# Optional Postgres profile (do not mix with default api on :8000)
docker compose --profile postgres up --build api-pg worker-pg postgres redis
```

## Interview claims (defendable)

- Coordinator + horizontal workers + durable queue + verifier gate
- Published multi- vs single-agent eval numbers on fixed dogfood issues (JSON + docs table)
- Research-journey analytics with consent/deletion
- Dogfood sandboxes shaped like QuantForge leakage/EWMA + ChainVenue basis bugs
- Merge conflict risk when re-patching the same sandbox file
- Request-ID structured logs + SSE board for ops story
- Health: Redis probe + worker heartbeats; query token SSE-only
- Configurable job / verifier timeouts (`AGENTGRID_JOB_TIMEOUT_S`, `AGENTGRID_VERIFY_TIMEOUT_S`)
