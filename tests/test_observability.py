from __future__ import annotations

AUTH = {"Authorization": "Bearer test-token"}


def test_health_returns_request_id(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert "x-request-id" in r.headers
    assert len(r.headers["x-request-id"]) >= 8


def test_propagates_client_request_id(client):
    r = client.get("/api/health", headers={"X-Request-ID": "client-rid-123456"})
    assert r.headers["x-request-id"] == "client-rid-123456"


def test_jobs_stream_emits_snapshot(client):
    client.post(
        "/api/jobs",
        json={"issue_id": "cv-basis-bps", "mode": "multi"},
        headers=AUTH,
    )
    with client.stream(
        "GET",
        "/api/jobs/stream?max_events=1",
        headers=AUTH,
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        body = "".join(response.iter_text())
    assert "event: jobs" in body
    assert "cv-basis-bps" in body


def test_jobs_stream_accepts_query_token(client):
    with client.stream(
        "GET",
        "/api/jobs/stream?token=test-token&max_events=1",
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())
    assert "event:" in body


def test_eval_latest_returns_published(client, tmp_path, monkeypatch):
    from pathlib import Path

    import agentgrid.api.eval_api as eval_api

    published = {
        "n_issues": 1,
        "single_success_rate": 0.0,
        "multi_success_rate": 1.0,
        "single_avg_tokens": 10,
        "multi_avg_tokens": 20,
        "rows": [],
    }
    path = tmp_path / "eval_results.json"
    path.write_text(__import__("json").dumps(published), encoding="utf-8")
    monkeypatch.setattr(eval_api, "_EVAL_PATH", Path(path))
    r = client.get("/api/eval/latest", headers=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert body["multi_success_rate"] == 1.0
    assert "source" in body


def test_worker_heartbeat_visible_on_health(client):
    from agentgrid.workers.heartbeat import beat

    beat("pytest-worker", status="idle")
    body = client.get("/api/health").json()
    assert body["workers_alive"] >= 1
    assert any(w["worker_id"] == "pytest-worker" for w in body["workers"])
