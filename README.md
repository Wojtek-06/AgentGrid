# AgentGrid

[![CI](https://github.com/Wojtek-06/AgentGrid/actions/workflows/ci.yml/badge.svg)](https://github.com/Wojtek-06/AgentGrid/actions/workflows/ci.yml)

Greenfield **horizontally scaled AI platform** with two verticals on shared infra:

1. **Autonomous coding agents** — plan → isolated workspace → patch → pytest verifier → merge status (multi-agent retry vs single-agent baseline).
2. **Behaviour analytics** — synthetic **trading/research** product journeys (funnels, anomalies, evidence-grounded NL insights) with consent + deletion.

> Placement pitch: *I can ship distributed agent systems with evals and a real analytics product surface—not a chat demo.*

**Repo:** https://github.com/Wojtek-06/AgentGrid  
**Non-goals:** Fitness-App code/domain; live extractive agents against private remotes; LLM network calls in CI.

---

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

```
API (FastAPI) → queue (Redis or local) → coding workers + verifier
                     ↘ analytics ingest → funnel / privacy / insights
                     ↘ dashboard board (tokens, $, latency, status + SSE)
```

Dogfood issues (local sandboxes, QuantForge/ChainVenue-shaped):

| Issue ID | Story |
|----------|--------|
| `qf-leakage-guard` | Look-ahead mid bug — multi retries, single fails |
| `qf-ewma-alpha` | EWMA weights swapped — multi retries, single fails |
| `cv-basis-bps` | Wrong basis sign — both modes can fix |

### Published eval (sample)

From `data/eval_results.json` (regenerate with `python scripts/run_eval.py`):

| Mode | Success rate | Avg tokens |
|------|--------------|------------|
| Single-agent | 33% (1/3) | ~200 |
| Multi-agent | 100% (3/3) | ~287 |

---

## Quick start (Windows)

```powershell
cd C:\Projekty\Quant\AgentGrid
python -m pip install -r requirements.txt
$env:PYTHONPATH = "$PWD\backend"
$env:AGENTGRID_API_TOKEN = "dev-token"

# Terminal A
python -m uvicorn agentgrid.main:app --reload --port 8000

# Terminal B
python -m agentgrid.workers.coding_worker
```

Open http://127.0.0.1:8000

```powershell
# Eval numbers
python scripts\run_eval.py

# Analytics demo data
python scripts\seed_analytics.py
```

Tests: `python -m pytest -q` (with `PYTHONPATH=backend`).

Docker (SQLite default): `docker compose up --build` then scale workers with `--scale worker=2`.

Optional Postgres profile (keeps SQLite for CI/default):

```bash
docker compose --profile postgres up --build api-pg worker-pg postgres redis
```

---

## API (Bearer `dev-token`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Liveness + queue depth |
| GET | `/api/jobs/issues` | Dogfood catalog |
| POST | `/api/jobs` | `{issue_id, mode, idempotency_key?}` |
| GET | `/api/jobs` | Board |
| GET | `/api/jobs/stream` | SSE live board (`?token=` for EventSource) |
| POST | `/api/jobs/{id}/cancel` | Cancel queued/running |
| POST | `/api/jobs/{id}/retry` | Re-enqueue failed/cancelled |
| POST | `/api/eval/run` | Multi vs single table |
| GET | `/api/metrics/overview` | Tokens / $ / latency / queue |
| POST | `/api/analytics/events` | Batch ingest |
| GET | `/api/analytics/funnel` | Funnel + anomalies + insight |
| POST | `/api/analytics/consent` | Consent flag |
| DELETE | `/api/analytics/users/{id}` | Erase + block |

Responses include `X-Request-ID` (echo client header or generate). API + worker logs use structured `request_id=…` fields.

---

## Status vs placement plan

| Deliverable | Status |
|-------------|--------|
| Coordinator + workers + queue + verifier | Done (local/Redis) |
| Multi vs single eval | Done (`scripts/run_eval.py` → `data/eval_results.json`) |
| Merge artifacts + human review checklist | Done |
| Merge conflict risk surfacing + tests | Done |
| Cancel / retry / queue backpressure | Done |
| Observability metrics + request IDs / structured logs | Done |
| SSE live job board | Done |
| Analytics + privacy | Done (research journeys) |
| Operator telemetry + retention cohorts | Done |
| Optional Postgres compose profile | Done (SQLite remains CI default) |
| Horizontal scale story | Documented + compose `--scale worker=N` |
| Dogfood on QF/CV-shaped issues | 3 local sandboxes |
| Evidence pack / demo video | Docs ready; video user-owned |

Sibling status: [`docs/PORTFOLIO_STATUS.md`](docs/PORTFOLIO_STATUS.md)  
Docs: [`docs/EVIDENCE_PACK.md`](docs/EVIDENCE_PACK.md) · [`docs/THREAT_PRIVACY.md`](docs/THREAT_PRIVACY.md)

---

## Sibling projects

- [QuantForge](https://github.com/Wojtek-06/QuantForge) — C++ LOB MM lab (dogfood-shaped issues)
- [ChainVenue](https://github.com/Wojtek-06/ChainVenue) — Foundry CLOB–AMM lab (dogfood-shaped issue)
