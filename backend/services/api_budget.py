"""Metering calls against a provider's free tier.

The quotas are small enough to exhaust by accident — SerpApi's free tier is
250 searches a month — so spend is counted per provider per calendar month and
checked before any request goes out.
"""

from datetime import datetime, timezone

from backend.db.database import get_session
from backend.db.models import ApiBudgetRow


def _this_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _used(provider: str, month: str) -> int:
    with get_session() as session:
        row = session.get(ApiBudgetRow, provider)
        # A row from a previous month has already reset.
        if row is None or row.month != month:
            return 0
        return row.calls_used


def remaining(provider: str, cap: int, month: str | None = None) -> int:
    return max(0, cap - _used(provider, month or _this_month()))


def can_spend(provider: str, cap: int, month: str | None = None) -> bool:
    return remaining(provider, cap, month) > 0


def record_call(provider: str, cap: int, month: str | None = None) -> None:
    month = month or _this_month()
    with get_session() as session:
        row = session.get(ApiBudgetRow, provider)
        if row is None:
            session.add(ApiBudgetRow(provider=provider, month=month,
                                     calls_used=1, monthly_cap=cap))
        elif row.month != month:
            row.month, row.calls_used, row.monthly_cap = month, 1, cap
        else:
            row.calls_used += 1
            row.monthly_cap = cap
        session.commit()
