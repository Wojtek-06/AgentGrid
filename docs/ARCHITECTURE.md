# AgentGrid architecture

```
 Issues / analytics events
            │
            ▼
     ┌──────────────┐
     │  FastAPI API │  auth token · idempotent job create · event ingest
     └──────┬───────┘
            │
     durable queue (Redis or in-process) + SQLite/Postgres artifacts
            │
   ┌────────┼────────┐
   ▼        ▼        ▼
coding   verifier  analytics
workers  (pytest)  (funnel / privacy)
   │
   └────► integration status on job row
            │
            ▼
     Observability dashboard (task board, cost, funnel insight)
```

## Coding vertical

1. `POST /api/jobs` enqueues an issue (`qf-leakage-guard` / `qf-ewma-alpha` / `cv-basis-bps` dogfood sandboxes).
2. Worker dequeues → **plan** → isolated workspace copy → **patch** → **pytest verifier**.
3. **Multi-agent:** verifier failure triggers retry with corrected patch.
4. **Single-agent:** one-shot; fails hard QF issues on purpose for eval contrast.
5. Metrics: tokens (simulated), cost USD, latency ms, attempts.
6. Merge path writes patch + `REVIEW_CHECKLIST.md`; flags `merge_conflict_risk` if the same sandbox file already succeeded.
7. `GET /api/jobs/stream` (SSE) + `X-Request-ID` structured logs for live ops.

## Analytics vertical

Trading/research product journeys (not fitness):

`page_view_research → load_data → configure_experiment → run_backtest → open_report`

- Session funnel + drop-off anomalies
- Grounded NL insight citing **aggregates only**
- Consent + delete (right-to-be-forgotten) blocks further ingest

## Horizontal scale

- Add workers: second process / `docker compose up --scale worker=2`
- Redis queue for multi-process; local deque for CI/dev
- Idempotency keys on job create; retries counted on job row
