# Threat model & privacy

## Trust boundaries

| Zone | Trust |
|------|--------|
| API clients | Untrusted; bearer token required (`secrets.compare_digest`) |
| Coding workers | Trusted compute; still treat issue text as untrusted input |
| Sandbox workspaces | Isolated copies under `.artifacts/`; no host git mutation |
| Analytics store | Contains synthetic demo IDs only in seed data |

**Token handling:** `Authorization: Bearer` on all protected routes. Query `?token=` is accepted **only** on `/api/jobs/stream` (EventSource cannot set headers) so tokens are not encouraged on arbitrary URLs/logs. Empty `AGENTGRID_API_TOKEN` fails closed (503). Default `dev-token` is for local demos; startup logs a warning.

## Coding-agent threats

| Threat | Mitigation |
|--------|------------|
| Prompt injection / malicious issue text | Deterministic catalog today; future LLM path must sandbox tools + allowlist |
| Untrusted code execution | Verifier runs pytest only inside copied sandbox |
| Queue poison / duplicate submits | Idempotency keys; status machine ignores non-queued jobs |
| Secret exfiltration via patches | No network tools in worker; artifacts local |

## Analytics privacy

| Control | Implementation |
|---------|----------------|
| Consent | `POST /api/analytics/consent`; ingest checks consent |
| Minimization | Funnel API returns aggregates; user event endpoint returns **count only** |
| Deletion | `DELETE /api/analytics/users/{id}` erases events + blocks re-ingest |
| Retention | Demo uses ephemeral SQLite; production would add TTL jobs |

## Explicit non-goals

- Live LLM calls in CI (offline deterministic agents)
- Fitness / gym domain
- Mutating QuantForge/ChainVenue remotes automatically (dogfood sandboxes are local copies)
