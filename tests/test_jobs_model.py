import hashlib
from backend.db.database import init_db, get_session
from backend.db.models import JobRow, ApiBudgetRow


def test_insert_and_read_job(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "jobs.db"))
    init_db()
    jid = hashlib.sha256(b"Zepto|SDE-1|2026-07-01").hexdigest()
    with get_session() as s:
        s.add(JobRow(
            id=jid, title="SDE-1", company="Zepto", location="Mumbai",
            url="https://example.com/job", description="build stuff",
            source_engine="jobspy:linkedin", fetched_at="2026-07-13",
        ))
        s.commit()
    with get_session() as s:
        row = s.get(JobRow, jid)
        assert row is not None
        assert row.company == "Zepto"
        assert row.llm_score is None


def test_insert_and_read_api_budget(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "budget.db"))
    init_db()
    with get_session() as s:
        s.add(ApiBudgetRow(provider="serpapi", month="2026-07", calls_used=3, monthly_cap=250))
        s.commit()
    with get_session() as s:
        row = s.get(ApiBudgetRow, "serpapi")
        assert row.calls_used == 3
        assert row.monthly_cap == 250
