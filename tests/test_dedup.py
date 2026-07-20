from backend.utils.dedup import job_id, dedupe_jobs


def test_job_id_is_stable_hex():
    a = job_id("Zepto", "SDE-1")
    b = job_id("Zepto", "SDE-1")
    assert a == b
    assert len(a) == 64 and int(a, 16) >= 0     # sha256 hex digest


def test_job_id_ignores_case_and_extra_whitespace():
    """The same listing arrives from different boards with cosmetic differences."""
    assert job_id("Zepto", "SDE-1") == job_id("  zepto ", "sde-1  ")
    assert job_id("Zepto", "SDE  1") == job_id("zepto", "sde 1")


def test_job_id_differs_across_jobs():
    assert job_id("Zepto", "SDE-1") != job_id("Zepto", "SDE-2")
    assert job_id("Zepto", "SDE-1") != job_id("Swiggy", "SDE-1")


def test_dedupe_assigns_ids_and_drops_duplicates():
    jobs = [
        {"company": "Zepto", "title": "SDE-1", "source_engine": "jobspy:linkedin"},
        {"company": "zepto", "title": "sde-1", "source_engine": "jobspy:naukri"},
        {"company": "Swiggy", "title": "SDE-2", "source_engine": "remotive"},
    ]
    out = dedupe_jobs(jobs)
    assert len(out) == 2
    assert all(j["id"] for j in out)
    # first occurrence wins, so the LinkedIn copy survives
    assert out[0]["source_engine"] == "jobspy:linkedin"


def test_dedupe_tolerates_missing_fields():
    jobs = [
        {"company": None, "title": "Mystery Role"},
        {"company": None, "title": "Mystery Role"},
        {"title": None, "company": "Ghost Inc"},
    ]
    out = dedupe_jobs(jobs)
    assert len(out) == 2
    assert all("id" in j for j in out)


def test_dedupe_empty_list():
    assert dedupe_jobs([]) == []
