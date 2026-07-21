from backend.db.database import init_db
from backend.services.job_store import save_jobs, load_jobs
from backend.utils.dedup import job_id


def _job(company="Zepto", title="SDE-1", **extra):
    return {
        "id": job_id(company, title),
        "title": title, "company": company, "location": "Mumbai",
        "url": "https://x.com/1", "description": "build things",
        "source_engine": "jobspy:linkedin", "fetched_at": "2026-07-21",
        **extra,
    }


def test_saves_and_reads_back_jobs(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "a.db"))
    init_db()
    save_jobs([_job(llm_score=87.0, llm_breakdown='{"score": 87}')])

    jobs = load_jobs()
    assert len(jobs) == 1
    assert jobs[0]["company"] == "Zepto"
    assert jobs[0]["llm_score"] == 87.0


def test_rerunning_a_hunt_updates_instead_of_duplicating(tmp_path, monkeypatch):
    """The same listing shows up on every run; it must not pile up in the table."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "b.db"))
    init_db()
    save_jobs([_job(llm_score=50.0)])
    save_jobs([_job(llm_score=91.0)])

    jobs = load_jobs()
    assert len(jobs) == 1
    assert jobs[0]["llm_score"] == 91.0


def test_a_rescore_never_erases_an_existing_score(tmp_path, monkeypatch):
    """A later run that only pre-filtered this job must not blank out the
    score an earlier run already paid the LLM for."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "c.db"))
    init_db()
    save_jobs([_job(llm_score=91.0, llm_breakdown='{"score": 91}')])
    save_jobs([_job(llm_score=None, llm_breakdown=None)])

    assert load_jobs()[0]["llm_score"] == 91.0


def test_loads_best_scored_first(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "d.db"))
    init_db()
    save_jobs([
        _job("Swiggy", "SDE-2", llm_score=40.0),
        _job("Zepto", "SDE-1", llm_score=95.0),
        _job("Meesho", "SDE-3", llm_score=None),
    ])

    scores = [j["llm_score"] for j in load_jobs()]
    assert scores[0] == 95.0 and scores[1] == 40.0
    assert scores[2] is None      # unscored sinks to the bottom


def test_limit_caps_how_many_come_back(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "e.db"))
    init_db()
    save_jobs([_job(f"Co{i}", f"Role{i}", llm_score=float(i)) for i in range(5)])
    assert len(load_jobs(limit=2)) == 2


def test_saving_nothing_is_harmless(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "f.db"))
    init_db()
    save_jobs([])
    assert load_jobs() == []
