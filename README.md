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
                     ↘ dashboard board (tokens, $, latency, status)
```

Dogfood issues (local sandboxes, QuantForge/ChainVenue-shaped):

| Issue ID | Story |
|----------|--------|
| `qf-leakage-guard` | Look-ahead mid bug — multi retries, single fails |
| `cv-basis-bps` | Wrong basis sign — both modes can fix |

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

Docker: `docker compose up --build` then scale workers with `--scale worker=2`.

---

## API (Bearer `dev-token`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Liveness + queue depth |
| GET | `/api/jobs/issues` | Dogfood catalog |
| POST | `/api/jobs` | `{issue_id, mode, idempotency_key?}` |
| GET | `/api/jobs` | Board |
| POST | `/api/eval/run` | Multi vs single table |
| POST | `/api/analytics/events` | Batch ingest |
| GET | `/api/analytics/funnel` | Funnel + anomalies + insight |
| POST | `/api/analytics/consent` | Consent flag |
| DELETE | `/api/analytics/users/{id}` | Erase + block |

---

## Status vs placement plan

| Deliverable | Status |
|-------------|--------|
| Coordinator + workers + queue + verifier | Done (local/Redis) |
| Multi vs single eval | Done (`scripts/run_eval.py`) |
| Merge artifacts + human review checklist | Done |
| Cancel / retry / queue backpressure | Done |
| Observability metrics API | Done (`/api/metrics/overview`) |
| Analytics + privacy | Done (research journeys) |
| Operator telemetry + retention cohorts | Done |
| Horizontal scale story | Documented + compose `--scale worker=N` |
| Dogfood on QF/CV-shaped issues | Local sandboxes |
| Evidence pack / demo video | Docs ready; video user-owned |

Sibling status: [`docs/PORTFOLIO_STATUS.md`](docs/PORTFOLIO_STATUS.md)  
Docs: [`docs/EVIDENCE_PACK.md`](docs/EVIDENCE_PACK.md) · [`docs/THREAT_PRIVACY.md`](docs/THREAT_PRIVACY.md)

---

## Sibling projects

- [QuantForge](https://github.com/Wojtek-06/QuantForge) — C++ LOB MM lab (dogfood-shaped issue)
- [ChainVenue](https://github.com/Wojtek-06/ChainVenue) — Foundry CLOB–AMM lab (dogfood-shaped issue)
