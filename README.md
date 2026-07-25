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

Full write-up: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

```text
                    ┌─────────────────────────────────────┐
                    │         Dashboard (static UI)         │
                    │   board · metrics · funnel · SSE      │
                    └──────────────────┬──────────────────┘
                                       │ Bearer token
                                       ▼
┌──────────────┐   enqueue    ┌────────────────┐   dequeue   ┌─────────────────┐
│ FastAPI API  │─────────────►│ Queue (Redis   │────────────►│ Coding workers  │
│ jobs · eval  │              │  or in-proc)   │             │ plan→patch→test │
│ analytics    │◄─────────────│                │◄────────────│ + merge path    │
└──────┬───────┘   status     └────────────────┘   results   └────────┬────────┘
       │                                                              │
       │                              ┌───────────────────────────────┘
       ▼                              ▼
┌──────────────┐              ┌─────────────────┐
│ SQLite / PG  │              │ .artifacts/     │
│ jobs·events  │              │ patch + checklist│
└──────────────┘              └─────────────────┘
```

Dogfood issues (local sandboxes, QuantForge/ChainVenue-shaped):

| Issue ID | Story | Eval contrast |
|----------|--------|---------------|
| `qf-leakage-guard` | Look-ahead mid bug | multi retries, single fails |
| `qf-ewma-alpha` | EWMA weights swapped | multi retries, single fails |
| `cv-basis-bps` | Wrong basis sign | both modes can fix |

### Published eval numbers

Source of truth: [`data/eval_results.json`](data/eval_results.json) (regenerate with `python scripts/run_eval.py`).

| Mode | Success rate | Avg tokens |
|------|--------------|------------|
| Single-agent | **33%** (1/3) | ~200 |
| Multi-agent | **100%** (3/3) | ~287 |

Per-issue breakdown and interview script: [`docs/EVIDENCE_PACK.md`](docs/EVIDENCE_PACK.md).

---

## 60-second demo

```powershell
cd C:\Projekty\Quant\AgentGrid
python -m pip install -r requirements.txt
$env:PYTHONPATH = "$PWD\backend"
$env:AGENTGRID_API_TOKEN = "dev-token"

# Terminal A — API
python -m uvicorn agentgrid.main:app --reload --port 8000

# Terminal B — worker
python -m agentgrid.workers.coding_worker
```

1. Open http://127.0.0.1:8000 — token field should say `dev-token`.
2. Select issue `qf-leakage-guard`, mode **single** → **Enqueue** → status goes `failed`.
3. Same issue, mode **multi** → **Enqueue** → status goes `succeeded` (retry path).
4. Click **Run eval** → multi **100%** vs single **33%** (matches [`data/eval_results.json`](data/eval_results.json)).

Optional: `python scripts\seed_analytics.py` then **Refresh** for the research funnel.

Tests: `$env:PYTHONPATH="backend"; python -m pytest -q`

---

## Auth

Protected routes expect:

```http
Authorization: Bearer <AGENTGRID_API_TOKEN>
```

Default token is `dev-token` (see `.env.example`).  
SSE (`EventSource`) cannot set headers, so the live board uses `?token=` as an equivalent.  
Health (`GET /api/health`) is open; everything under `/api/jobs`, `/api/eval`, `/api/metrics`, `/api/analytics` requires the token.

---

## Quick start extras

```powershell
python scripts\run_eval.py          # refresh data/eval_results.json
python scripts\seed_analytics.py    # demo funnel + retention
```

**Docker (SQLite default):**

```bash
# API + Redis + one worker
docker compose up --build

# Horizontal scale story — extra workers share the Redis queue
docker compose up --build --scale worker=2
```

**Optional Postgres profile** (keeps SQLite for CI/default):

```bash
docker compose --profile postgres up --build api-pg worker-pg postgres redis
```

---

## API

All rows except health require `Authorization: Bearer <token>` (or `?token=` on SSE).

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/health` | — | Liveness + queue depth |
| GET | `/api/jobs/issues` | Bearer | Dogfood catalog |
| POST | `/api/jobs` | Bearer | `{issue_id, mode, idempotency_key?}` |
| GET | `/api/jobs` | Bearer | Board snapshot |
| GET | `/api/jobs/stream` | Bearer or `?token=` | SSE live board |
| GET | `/api/jobs/{id}` | Bearer | Job detail + patch/log |
| POST | `/api/jobs/{id}/cancel` | Bearer | Cancel queued/running |
| POST | `/api/jobs/{id}/retry` | Bearer | Re-enqueue failed/cancelled |
| POST | `/api/eval/run` | Bearer | Multi vs single summary |
| GET | `/api/metrics/overview` | Bearer | Tokens / $ / latency / queue |
| POST | `/api/analytics/events` | Bearer | Batch ingest |
| GET | `/api/analytics/funnel` | Bearer | Funnel + anomalies + insight |
| GET | `/api/analytics/retention` | Bearer | Day-1 retention cohorts |
| GET | `/api/analytics/operator-funnel` | Bearer | Operator telemetry funnel |
| POST | `/api/analytics/consent` | Bearer | Consent flag |
| DELETE | `/api/analytics/users/{id}` | Bearer | Erase + block |

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
