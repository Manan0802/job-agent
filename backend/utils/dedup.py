"""Cross-source job dedup.

The same opening shows up on several boards with cosmetic differences ("Zepto"
vs "zepto ", "SDE  1" vs "SDE 1"), so the key is normalized before hashing.

Deliberately keyed on company+title only, NOT the posting date the Phase 2 plan
originally suggested: every source formats dates differently (ISO, ISO+time, raw
epoch), so including the date would defeat cross-source dedup entirely.
"""

import hashlib


def _norm(value: str | None) -> str:
    return " ".join((value or "").split()).lower()


def job_id(company: str | None, title: str | None) -> str:
    key = f"{_norm(company)}|{_norm(title)}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def dedupe_jobs(jobs: list[dict]) -> list[dict]:
    """Assign each job its id and keep only the first copy of each."""
    seen: set[str] = set()
    unique: list[dict] = []
    for job in jobs:
        jid = job_id(job.get("company"), job.get("title"))
        if jid in seen:
            continue
        seen.add(jid)
        unique.append({**job, "id": jid})
    return unique
