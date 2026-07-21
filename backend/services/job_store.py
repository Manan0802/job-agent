"""Persisting scraped and scored jobs.

Hunts run repeatedly and keep re-encountering the same listings, so saving is
an upsert. Crucially it never overwrites a score with nothing: a later run that
only pre-filtered a job must not throw away LLM work an earlier run paid for.
"""

from sqlalchemy import select

from backend.db.database import get_session
from backend.db.models import JobRow

_COLUMNS = (
    "title", "company", "location", "url", "description",
    "source_engine", "embedding", "prefilter_score",
    "llm_score", "llm_breakdown", "fetched_at",
)


def save_jobs(jobs: list[dict]) -> None:
    if not jobs:
        return
    with get_session() as session:
        for job in jobs:
            row = session.get(JobRow, job["id"])
            if row is None:
                row = JobRow(id=job["id"])
                session.add(row)
            for column in _COLUMNS:
                value = job.get(column)
                # Only overwrite a stored score when the new run actually has one.
                if value is None and column in ("llm_score", "llm_breakdown"):
                    continue
                if value is not None:
                    setattr(row, column, value)
        session.commit()


def load_jobs(limit: int | None = None) -> list[dict]:
    """Best-scored first; unscored jobs sort last."""
    with get_session() as session:
        rows = session.scalars(select(JobRow)).all()

    jobs = [
        {"id": row.id, **{column: getattr(row, column) for column in _COLUMNS}}
        for row in rows
    ]
    jobs.sort(key=lambda j: (j["llm_score"] is None, -(j["llm_score"] or 0)))
    return jobs[:limit] if limit else jobs
