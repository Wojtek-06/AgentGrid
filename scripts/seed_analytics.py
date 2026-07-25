#!/usr/bin/env python3
"""Seed synthetic trading/research + operator telemetry events."""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import delete  # noqa: E402

from agentgrid.analytics.privacy import upsert_consent  # noqa: E402
from agentgrid.db import SessionLocal, init_db  # noqa: E402
from agentgrid.models import AnalyticsEvent  # noqa: E402

STEPS = [
    "page_view_research",
    "load_data",
    "configure_experiment",
    "run_backtest",
    "open_report",
]

OPS_STEPS = [
    "ops_submit_job",
    "ops_watch_worker",
    "ops_inspect_failure",
    "ops_approve_merge",
]


def main() -> None:
    init_db()
    db = SessionLocal()
    db.execute(delete(AnalyticsEvent))
    db.commit()

    day0 = datetime.now(timezone.utc) - timedelta(days=1)
    day1 = datetime.now(timezone.utc)
    n_sessions = 40
    reach = [40, 36, 30, 10, 8]

    for i in range(n_sessions):
        user = f"user_{i % 12}"
        upsert_consent(db, user, True)
        session = f"sess_{i}"
        for step_i, step in enumerate(STEPS):
            if i >= reach[step_i]:
                break
            db.add(
                AnalyticsEvent(
                    event_id=str(uuid.uuid4()),
                    user_id=user,
                    session_id=session,
                    name=step,
                    ts=day0 + timedelta(minutes=i * 3 + step_i),
                    props={"source": "seed"},
                    consent=True,
                )
            )
        # Day-1 return for half the users (retention demo)
        if i % 2 == 0:
            db.add(
                AnalyticsEvent(
                    event_id=str(uuid.uuid4()),
                    user_id=user,
                    session_id=f"sess_{i}_d1",
                    name="page_view_research",
                    ts=day1 + timedelta(minutes=i),
                    props={"source": "seed"},
                    consent=True,
                )
            )

    # Operator telemetry funnel
    ops_reach = [20, 18, 12, 9]
    for i in range(20):
        user = f"ops_{i % 5}"
        upsert_consent(db, user, True)
        session = f"ops_sess_{i}"
        for step_i, step in enumerate(OPS_STEPS):
            if i >= ops_reach[step_i]:
                break
            db.add(
                AnalyticsEvent(
                    event_id=str(uuid.uuid4()),
                    user_id=user,
                    session_id=session,
                    name=step,
                    ts=day0 + timedelta(hours=2, minutes=i * 2 + step_i),
                    props={"source": "seed_ops"},
                    consent=True,
                )
            )

    db.commit()
    db.close()
    print(f"Seeded research reach {reach} + operator reach {ops_reach}")


if __name__ == "__main__":
    main()
