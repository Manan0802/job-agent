"""Which jobs are worth telling the user about right now.

A hunt that runs on a schedule re-finds the same listings every time, so
alerting on everything strong would mean the same message every day and the
user learning to ignore it.

`alerted_score` is remembered alongside the timestamp: a job that was too weak
to mention and later rescores higher is worth a mention after all.
"""

from datetime import datetime, timezone

from sqlalchemy import select

from backend.db.database import get_session
from backend.db.models import JobRow


def claim_new_matches(min_score: float) -> list[dict]:
    """Return strong matches not yet reported, marking them as reported.

    Marking happens here rather than after a successful send: a notification
    that fails is worth losing once, but an alert loop that repeats the same
    jobs forever is worse.
    """
    now = datetime.now(timezone.utc).isoformat()
    fresh: list[dict] = []

    with get_session() as session:
        rows = session.scalars(
            select(JobRow).where(JobRow.llm_score.is_not(None))
        ).all()

        for row in rows:
            if row.llm_score < min_score:
                continue
            # Already mentioned at this strength or better.
            if row.alerted_at and (row.alerted_score or 0) >= row.llm_score:
                continue

            fresh.append({
                "id": row.id, "title": row.title, "company": row.company,
                "location": row.location, "url": row.url,
                "llm_score": row.llm_score, "source_engine": row.source_engine,
            })
            row.alerted_at = now
            row.alerted_score = row.llm_score

        session.commit()

    fresh.sort(key=lambda job: -(job["llm_score"] or 0))
    return fresh
