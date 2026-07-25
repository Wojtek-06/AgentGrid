from __future__ import annotations

AUTH = {"Authorization": "Bearer test-token"}


def test_merge_conflict_flagged_on_second_success(client):
    from agentgrid.workers.coding_worker import process_job

    first = client.post(
        "/api/jobs",
        json={"issue_id": "cv-basis-bps", "mode": "multi"},
        headers=AUTH,
    ).json()
    process_job(first["id"], "w1")
    got1 = client.get(f"/api/jobs/{first['id']}", headers=AUTH).json()
    assert got1["status"] == "succeeded"
    assert not (got1.get("plan_json") or {}).get("merge_warning")

    second = client.post(
        "/api/jobs",
        json={"issue_id": "cv-basis-bps", "mode": "multi"},
        headers=AUTH,
    ).json()
    process_job(second["id"], "w2")
    got2 = client.get(f"/api/jobs/{second['id']}", headers=AUTH).json()
    assert got2["status"] == "succeeded"
    warning = (got2.get("plan_json") or {}).get("merge_warning", "")
    assert "merge_conflict_risk" in warning
    assert "basis.py" in warning
    assert "merge_conflict_risk" in (got2.get("error") or "")


def test_detect_file_conflict_helper(client, tmp_path, monkeypatch):
    from agentgrid.agents.merge import detect_file_conflict
    from agentgrid.db import SessionLocal
    from agentgrid.models import AgentMode, Job, JobStatus
    from agentgrid.workers.coding_worker import process_job

    r = client.post(
        "/api/jobs",
        json={"issue_id": "cv-basis-bps", "mode": "single"},
        headers=AUTH,
    ).json()
    process_job(r["id"], "w1")

    db = SessionLocal()
    try:
        job = Job(
            id="conflict-probe",
            issue_id="cv-basis-bps",
            title="probe",
            mode=AgentMode.multi,
            status=JobStatus.succeeded,
        )
        db.add(job)
        db.commit()
        msg = detect_file_conflict(db, job)
        assert msg is not None
        assert "merge_conflict_risk" in msg
    finally:
        db.close()
