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
    assert client.get("/api/health").json()["ok"] is True


def test_jobs_require_bearer_token(client):
    r = client.get("/api/jobs")
    assert r.status_code == 401
    assert r.json()["detail"] == "unauthorized"


def test_jobs_accept_query_token_for_sse_style(client):
    r = client.get("/api/jobs", params={"token": "test-token"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)
