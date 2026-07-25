from __future__ import annotations

from datetime import datetime, timedelta, timezone

AUTH = {"Authorization": "Bearer test-token"}


def test_retention_and_operator_funnel(client):
    now = datetime.now(timezone.utc)
    events = [
        {
            "event_id": "r1",
            "user_id": "ru1",
            "session_id": "s0",
            "name": "page_view_research",
            "ts": (now - timedelta(days=1)).isoformat(),
            "consent": True,
        },
        {
            "event_id": "r2",
            "user_id": "ru1",
            "session_id": "s1",
            "name": "page_view_research",
            "ts": now.isoformat(),
            "consent": True,
        },
        {
            "event_id": "o1",
            "user_id": "op1",
            "session_id": "os1",
            "name": "ops_submit_job",
            "ts": now.isoformat(),
            "consent": True,
        },
        {
            "event_id": "o2",
            "user_id": "op1",
            "session_id": "os1",
            "name": "ops_watch_worker",
            "ts": now.isoformat(),
            "consent": True,
        },
    ]
    client.post(
        "/api/analytics/consent",
        json={"user_id": "ru1", "consent_analytics": True},
        headers=AUTH,
    )
    client.post(
        "/api/analytics/consent",
        json={"user_id": "op1", "consent_analytics": True},
        headers=AUTH,
    )
    client.post("/api/analytics/events", json={"events": events}, headers=AUTH)

    ret = client.get("/api/analytics/retention", headers=AUTH).json()
    assert ret["users"] >= 1
    assert ret["day1_retention"] > 0

    ops = client.get("/api/analytics/operator-funnel", headers=AUTH).json()
    assert ops["funnel"]["steps"][0]["sessions"] >= 1
