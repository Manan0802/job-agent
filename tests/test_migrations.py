"""Databases made by an earlier version have to keep working.

create_all() adds missing tables but never missing columns, so adding a column
to a model leaves every existing database on the old shape and the first query
against the new column fails with "no such column". Tests never caught this
because every one of them builds its database from scratch.
"""

import pytest
from sqlalchemy import create_engine, inspect, text

from backend.db.database import init_db
from backend.services.job_store import load_jobs, save_jobs


@pytest.fixture
def old_db(tmp_path, monkeypatch):
    """A jobs table as it was before alerted_at existed."""
    path = tmp_path / "old.db"
    monkeypatch.setenv("DB_PATH", str(path))
    engine = create_engine(f"sqlite:///{path}")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE jobs (id VARCHAR PRIMARY KEY, title VARCHAR, "
            "company VARCHAR, llm_score FLOAT)"
        ))
        conn.execute(text(
            "INSERT INTO jobs (id, title, company, llm_score) "
            "VALUES ('j1', 'Backend Engineer', 'Zepto', 88.0)"
        ))
    engine.dispose()
    return str(path)


def test_starting_up_adds_columns_the_old_database_is_missing(old_db):
    init_db()

    columns = {c["name"] for c in inspect(create_engine(f"sqlite:///{old_db}")).get_columns("jobs")}
    assert "alerted_at" in columns
    assert "alerted_score" in columns


def test_rows_that_were_already_there_survive(old_db):
    init_db()

    jobs = load_jobs()
    assert [j["id"] for j in jobs] == ["j1"]
    assert jobs[0]["alerted_at"] is None


def test_the_upgraded_database_is_writable(old_db):
    init_db()

    save_jobs([{"id": "j2", "title": "SDE", "company": "Swiggy", "llm_score": 70.0}])
    assert {j["id"] for j in load_jobs()} == {"j1", "j2"}


def test_running_it_twice_is_harmless(old_db):
    init_db()
    init_db()

    assert len(load_jobs()) == 1
