from __future__ import annotations

AUTH = {"Authorization": "Bearer test-token"}


def test_create_and_process_job(client):
    from agentgrid.workers.coding_worker import process_job

    r = client.post(
        "/api/jobs",
        json={"issue_id": "cv-basis-bps", "mode": "multi", "idempotency_key": "k1"},
        headers=AUTH,
    )
    assert r.status_code == 200
    job = r.json()
    assert job["status"] == "queued"

    # Idempotent
    r2 = client.post(
        "/api/jobs",
        json={"issue_id": "cv-basis-bps", "mode": "multi", "idempotency_key": "k1"},
        headers=AUTH,
    )
    assert r2.json()["id"] == job["id"]

    process_job(job["id"], "test-worker")
    got = client.get(f"/api/jobs/{job['id']}", headers=AUTH).json()
    assert got["status"] == "succeeded"
    assert got["tokens_used"] > 0


def test_health(client):
    body = client.get("/api/health").json()
    assert body["ok"] is True
    assert "workers_alive" in body
    assert "queue_hint" in body
    assert body["use_redis"] is False
    assert body["redis_ok"] is None


def test_jobs_require_bearer_token(client):
    r = client.get("/api/jobs")
    assert r.status_code == 401
    assert r.json()["detail"] == "unauthorized"


def test_query_token_rejected_outside_sse(client):
    r = client.get("/api/jobs", params={"token": "test-token"})
    assert r.status_code == 401
    assert "SSE" in r.json()["detail"] or "stream" in r.json()["detail"]
