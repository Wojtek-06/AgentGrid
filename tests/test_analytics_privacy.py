from __future__ import annotations

from datetime import datetime, timezone

AUTH = {"Authorization": "Bearer test-token"}


def test_funnel_insight_and_deletion(client):
    events = []
    for i in range(10):
        sid = f"s{i}"
        events.append(
            {
                "event_id": f"e{i}a",
                "user_id": "u1",
                "session_id": sid,
                "name": "page_view_research",
                "ts": datetime.now(timezone.utc).isoformat(),
                "consent": True,
            }
        )
        if i < 8:
            events.append(
                {
                    "event_id": f"e{i}b",
                    "user_id": "u1",
                    "session_id": sid,
                    "name": "load_data",
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "consent": True,
                }
            )
        if i < 3:
            events.append(
                {
                    "event_id": f"e{i}c",
                    "user_id": "u1",
                    "session_id": sid,
                    "name": "configure_experiment",
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "consent": True,
                }
            )

    client.post("/api/analytics/consent", json={"user_id": "u1", "consent_analytics": True}, headers=AUTH)
    r = client.post("/api/analytics/events", json={"events": events}, headers=AUTH)
    assert r.json()["accepted"] >= 10

    funnel = client.get("/api/analytics/funnel", headers=AUTH).json()
    assert "insight" in funnel
    assert "evidence" in funnel["insight"]

    erased = client.delete("/api/analytics/users/u1", headers=AUTH).json()
    assert erased["deleted"] is True
    count = client.get("/api/analytics/users/u1/events", headers=AUTH).json()
    assert count["event_count"] == 0

    # Further ingest blocked
    r2 = client.post(
        "/api/analytics/events",
        json={
            "events": [
                {
                    "event_id": "after-delete",
                    "user_id": "u1",
                    "session_id": "sx",
                    "name": "page_view_research",
                    "consent": True,
                }
            ]
        },
        headers=AUTH,
    )
    assert r2.json()["accepted"] == 0
