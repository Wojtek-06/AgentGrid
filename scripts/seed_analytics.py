#!/usr/bin/env python3
"""Seed synthetic trading/research journey events for the analytics demo."""

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


def main() -> None:
    init_db()
    db = SessionLocal()
    # Clear prior seed (dev only)
    db.execute(delete(AnalyticsEvent))
    db.commit()

    base = datetime.now(timezone.utc) - timedelta(days=1)
    # 40 sessions enter; sharp drop before run_backtest (anomaly)
    n_sessions = 40
    reach = [40, 36, 30, 10, 8]  # intentional collapse at run_backtest

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
                    ts=base + timedelta(minutes=i * 3 + step_i),
                    props={"source": "seed"},
                    consent=True,
                )
            )
    db.commit()
    db.close()
    print(f"Seeded {n_sessions} sessions with funnel reach {reach}")


if __name__ == "__main__":
    main()
