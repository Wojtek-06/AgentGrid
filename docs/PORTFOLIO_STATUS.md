# Portfolio status (three flagships)

Last updated: 2026-07-25

| Project | Repo | Latest ship | Status |
|---------|------|-------------|--------|
| **1 — QuantForge** | https://github.com/Wojtek-06/QuantForge | `8ecc7ee` | **Done for sprint** — LOB/MM/backtest, stops, signals, stress configs, Docker, evidence scripts. Your job: run evidence + optional demo video. |
| **2 — ChainVenue** | https://github.com/Wojtek-06/ChainVenue | `4c8cfb9` | **Done for sprint** — EVM lab, CPAMM, hedge path, adversarial tests, dashboard ledger, threat/latency docs. Your job: Anvil demo + optional video. |
| **3 — AgentGrid** | https://github.com/Wojtek-06/AgentGrid | in progress | **MVP + ops slice** — agents/eval/analytics shipped; continuing merge/cancel/metrics/retention. |

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

## AgentGrid — current vs remaining

| Slice | State |
|-------|--------|
| Coordinator + workers + queue + verifier | Done |
| Multi vs single eval (dogfood QF/CV-shaped) | Done |
| Research-journey analytics + privacy | Done |
| Merge artifacts + review checklist | This slice |
| Cancel / retry / backpressure | This slice |
| Metrics overview + dashboard board | This slice |
| Operator funnel + retention cohorts | This slice |
| Real LLM planner (optional) | Later |
| User demo video | You |
