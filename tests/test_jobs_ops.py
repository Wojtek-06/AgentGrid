from __future__ import annotations

AUTH = {"Authorization": "Bearer test-token"}


def test_cancel_and_retry(client):
    from agentgrid.workers.coding_worker import process_job

    r = client.post(
        "/api/jobs",
        json={"issue_id": "cv-basis-bps", "mode": "multi"},
        headers=AUTH,
    )
    job_id = r.json()["id"]

    cancelled = client.post(f"/api/jobs/{job_id}/cancel", headers=AUTH).json()
    assert cancelled["status"] == "cancelled"

    retried = client.post(f"/api/jobs/{job_id}/retry", headers=AUTH).json()
    assert retried["status"] == "queued"

    process_job(job_id, "test-worker")
    got = client.get(f"/api/jobs/{job_id}", headers=AUTH).json()
    assert got["status"] == "succeeded"


def test_metrics_overview(client):
    r = client.get("/api/metrics/overview", headers=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert "queue_depth" in body
    assert body["jobs_total"] >= 0
