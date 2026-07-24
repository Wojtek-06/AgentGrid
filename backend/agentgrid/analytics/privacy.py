from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from agentgrid.models import AnalyticsEvent, UserPrivacy


def upsert_consent(db: Session, user_id: str, consent: bool) -> UserPrivacy:
    row = db.get(UserPrivacy, user_id)
    if row is None:
        row = UserPrivacy(user_id=user_id, consent_analytics=consent)
        db.add(row)
    else:
        row.consent_analytics = consent
        if consent:
            row.deleted = False
            row.deleted_at = None
    db.commit()
    db.refresh(row)
    return row


def delete_user_data(db: Session, user_id: str) -> dict:
    """Right-to-be-forgotten: wipe events + mark privacy row deleted."""
    deleted_events = db.execute(
        delete(AnalyticsEvent).where(AnalyticsEvent.user_id == user_id)
    ).rowcount
    row = db.get(UserPrivacy, user_id)
    if row is None:
        row = UserPrivacy(user_id=user_id, consent_analytics=False)
        db.add(row)
    row.consent_analytics = False
    row.deleted = True
    row.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"user_id": user_id, "events_deleted": int(deleted_events or 0), "deleted": True}


def is_ingest_allowed(db: Session, user_id: str, consent_flag: bool) -> bool:
    row = db.get(UserPrivacy, user_id)
    if row and row.deleted:
        return False
    if row and not row.consent_analytics:
        return False
    return consent_flag
