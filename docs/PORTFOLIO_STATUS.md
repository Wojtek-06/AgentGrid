# Portfolio status (three flagships)

Last updated: 2026-08-30

| Project | Repo | Latest ship | Status |
|---------|------|-------------|--------|
| **1 — QuantForge** | https://github.com/Wojtek-06/QuantForge | `8ecc7ee` | **Done for sprint** — LOB/MM/backtest, stops, signals, stress configs, Docker, evidence scripts. Your job: run evidence + optional demo video. |
| **2 — ChainVenue** | https://github.com/Wojtek-06/ChainVenue | `4c8cfb9` | **Done for sprint** — EVM lab, CPAMM, hedge path, adversarial tests, dashboard ledger, threat/latency docs. Your job: Anvil demo + optional video. |
| **3 — AgentGrid** | https://github.com/Wojtek-06/AgentGrid | `81a4da4` | **Public-ready** — MIT, recruiter README, secret-clean, CI badge. Eval board, SSE, Redis demo scripts, evidence pack. Your job: optional screenshot + demo video. |

## QuantForge — what “done” means

- C++20 LOB: market/limit/**stop**, IOC/FOK, fees, queue position, cancel latency races  
- Strategies: no-trade / symmetric / Avellaneda–Stoikov with EWMA vol + blended toxicity  
- Walk-forward, leakage tests, risk kill-switch, research UI  
- Evidence: `scripts/generate_evidence.ps1` → `build/reports/` + replay JSON  
- Tests: **65/65** last local run  

## ChainVenue — what “done” means

- Foundry EVM lab + CPAMM + Python differential  
- Cross-venue adapter with guards; DemoHedge + `e2e_hedge.py`  
- Adversarial suite; `web/dashboard` metrics ledger  
- Docs: threat model, latency/fee regimes, evidence pack  
- Forge + **pytest 27** last local run  

## AgentGrid — public-ready checklist

| Slice | State |
|-------|--------|
| Coordinator + workers + queue + verifier | Done |
| Multi vs single eval (dogfood QF/CV-shaped) | Done (3 issues; published JSON) |
| Research-journey analytics + privacy | Done |
| Merge artifacts + review checklist | Done |
| Merge conflict risk + tests | Done |
| Cancel / retry / backpressure | Done |
| Metrics overview + dashboard board | Done |
| SSE live job status + reconnect hint | Done |
| Structured logs + request IDs (UI + API) | Done |
| Worker heartbeats + Redis health on `/api/health` | Done |
| SSE-only query token + constant-time compare | Done |
| Published eval load (no re-run) + dashboard table | Done |
| Job / verifier timeout config | Done |
| Operator funnel + retention cohorts | Done |
| Optional Postgres compose profile | Done |
| Evidence pack (5-min interview script) | Done |
| MIT LICENSE + public GitHub | Done |
| Recruiter README (no 3P API keys) | Done |
| Real LLM planner (optional) | Later — offline stubs only |
| Dashboard screenshot | You (`docs/images/`) |
| User demo video | You |
