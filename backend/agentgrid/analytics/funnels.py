from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentgrid.models import AnalyticsEvent, UserPrivacy

# Preferred quant narrative: research UI journey
FUNNEL_STEPS = [
    "page_view_research",
    "load_data",
    "configure_experiment",
    "run_backtest",
    "open_report",
]


def _allowed_user_ids(db: Session) -> set[str] | None:
    """None means all; otherwise only consented non-deleted users present in privacy table."""
    rows = db.execute(select(UserPrivacy)).scalars().all()
    if not rows:
        return None
    return {r.user_id for r in rows if r.consent_analytics and not r.deleted}


def compute_funnel(db: Session, *, since: datetime | None = None) -> dict:
    q = select(AnalyticsEvent).where(AnalyticsEvent.consent.is_(True))
    if since is not None:
        q = q.where(AnalyticsEvent.ts >= since)
    events = db.execute(q).scalars().all()
    allowed = _allowed_user_ids(db)
    if allowed is not None:
        events = [e for e in events if e.user_id in allowed]

    # Per session: max step reached
    session_steps: dict[str, set[str]] = defaultdict(set)
    for e in events:
        session_steps[e.session_id].add(e.name)

    counts = []
    prev = None
    for step in FUNNEL_STEPS:
        n = sum(1 for steps in session_steps.values() if step in steps)
        drop = None if prev is None else (prev - n)
        rate = None if prev in (None, 0) else round(n / prev, 4)
        counts.append({"step": step, "sessions": n, "drop_off": drop, "conversion_from_prev": rate})
        prev = n

    return {
        "domain": "trading_research_journeys",
        "steps": counts,
        "sessions_total": len(session_steps),
    }


def detect_anomalies(funnel: dict) -> list[dict]:
    """Flag abrupt conversion collapse between adjacent steps."""
    anomalies = []
    steps = funnel["steps"]
    for i in range(1, len(steps)):
        rate = steps[i]["conversion_from_prev"]
        if rate is not None and rate < 0.35 and steps[i - 1]["sessions"] >= 5:
            anomalies.append(
                {
                    "type": "funnel_drop",
                    "from": steps[i - 1]["step"],
                    "to": steps[i]["step"],
                    "conversion": rate,
                    "evidence": {
                        "from_sessions": steps[i - 1]["sessions"],
                        "to_sessions": steps[i]["sessions"],
                    },
                }
            )
    return anomalies


OPERATOR_FUNNEL_STEPS = [
    "ops_submit_job",
    "ops_watch_worker",
    "ops_inspect_failure",
    "ops_approve_merge",
]


def compute_operator_funnel(db: Session, *, since: datetime | None = None) -> dict:
    q = select(AnalyticsEvent).where(AnalyticsEvent.consent.is_(True))
    if since is not None:
        q = q.where(AnalyticsEvent.ts >= since)
    events = db.execute(q).scalars().all()
    allowed = _allowed_user_ids(db)
    if allowed is not None:
        events = [e for e in events if e.user_id in allowed]

    session_steps: dict[str, set[str]] = defaultdict(set)
    for e in events:
        session_steps[e.session_id].add(e.name)

    counts = []
    prev = None
    for step in OPERATOR_FUNNEL_STEPS:
        n = sum(1 for steps in session_steps.values() if step in steps)
        rate = None if prev in (None, 0) else round(n / prev, 4)
        counts.append({"step": step, "sessions": n, "conversion_from_prev": rate})
        prev = n

    return {
        "domain": "agent_platform_operator_telemetry",
        "steps": counts,
        "sessions_total": len(
            [s for s, steps in session_steps.items() if steps & set(OPERATOR_FUNNEL_STEPS)]
        ),
    }


def compute_retention(db: Session) -> dict:
    """Day-0 / Day-1 retention by distinct user_id with a research page view."""
    events = db.execute(
        select(AnalyticsEvent).where(
            AnalyticsEvent.consent.is_(True),
            AnalyticsEvent.name == "page_view_research",
        )
    ).scalars().all()
    allowed = _allowed_user_ids(db)
    if allowed is not None:
        events = [e for e in events if e.user_id in allowed]

    by_user: dict[str, set[str]] = defaultdict(set)
    for e in events:
        day = e.ts.date().isoformat()
        by_user[e.user_id].add(day)

    if not by_user:
        return {"users": 0, "day1_retention": 0.0, "cohorts": []}

    multi_day = sum(1 for days in by_user.values() if len(days) >= 2)
    cohorts = [
        {"user_hash": f"u{i}", "active_days": len(days)}
        for i, days in enumerate(sorted(by_user.values(), key=len, reverse=True)[:8])
    ]
    return {
        "users": len(by_user),
        "day1_retention": round(multi_day / len(by_user), 4),
        "cohorts": cohorts,
        "note": "cohorts are anonymized aggregates (no raw user ids)",
    }


def grounded_insight(funnel: dict, anomalies: list[dict]) -> dict:
    """NL insight that must cite aggregate evidence (no raw user PII)."""
    if not anomalies:
        top = funnel["steps"][0]["sessions"] if funnel["steps"] else 0
        last = funnel["steps"][-1]["sessions"] if funnel["steps"] else 0
        text = (
            f"Overall research-journey completion is {last}/{top} sessions "
            f"reaching open_report."
        )
        return {"text": text, "evidence": {"sessions_start": top, "sessions_report": last}}

    a = anomalies[0]
    text = (
        f"Largest abandonment is between {a['from']} → {a['to']} "
        f"(conversion {a['conversion']:.0%}). "
        f"Evidence: {a['evidence']['from_sessions']} sessions at prior step, "
        f"{a['evidence']['to_sessions']} at next."
    )
    return {"text": text, "evidence": a["evidence"]}
