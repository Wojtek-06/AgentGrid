from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agentgrid.analytics.funnels import compute_funnel, detect_anomalies, grounded_insight
from agentgrid.analytics.privacy import delete_user_data, is_ingest_allowed, upsert_consent
from agentgrid.api.deps import require_token
from agentgrid.db import get_db
from agentgrid.models import AnalyticsEvent
from agentgrid.schemas import ConsentIn, EventBatchIn

router = APIRouter(
    prefix="/api/analytics", tags=["analytics"], dependencies=[Depends(require_token)]
)


@router.post("/events")
def ingest_events(body: EventBatchIn, db: Session = Depends(get_db)) -> dict:
    accepted = 0
    skipped = 0
    for ev in body.events:
        if not is_ingest_allowed(db, ev.user_id, ev.consent):
            skipped += 1
            continue
        row = AnalyticsEvent(
            event_id=ev.event_id or str(uuid.uuid4()),
            user_id=ev.user_id,
            session_id=ev.session_id,
            name=ev.name,
            ts=ev.ts or datetime.now(timezone.utc),
            props=ev.props,
            consent=ev.consent,
        )
        try:
            db.add(row)
            db.commit()
            accepted += 1
        except Exception:  # noqa: BLE001 — idempotent skip on duplicate event_id
            db.rollback()
            skipped += 1
    return {"accepted": accepted, "skipped": skipped}


@router.get("/funnel")
def funnel(db: Session = Depends(get_db)) -> dict:
    f = compute_funnel(db)
    anomalies = detect_anomalies(f)
    insight = grounded_insight(f, anomalies)
    return {"funnel": f, "anomalies": anomalies, "insight": insight}


@router.post("/consent")
def set_consent(body: ConsentIn, db: Session = Depends(get_db)) -> dict:
    row = upsert_consent(db, body.user_id, body.consent_analytics)
    return {
        "user_id": row.user_id,
        "consent_analytics": row.consent_analytics,
        "deleted": row.deleted,
    }


@router.delete("/users/{user_id}")
def erase_user(user_id: str, db: Session = Depends(get_db)) -> dict:
    return delete_user_data(db, user_id)


@router.get("/users/{user_id}/events")
def user_events(user_id: str, db: Session = Depends(get_db)) -> dict:
    """Debug helper for privacy tests — returns count only (minimization)."""
    from sqlalchemy import func, select

    n = db.execute(
        select(func.count()).select_from(AnalyticsEvent).where(AnalyticsEvent.user_id == user_id)
    ).scalar_one()
    return {"user_id": user_id, "event_count": int(n)}
