"""The user's own LinkedIn connections export — the free, ToS-clean source of
1st-degree contacts.

Export it from LinkedIn: Me → Settings & Privacy → Data Privacy →
Get a copy of your data → Connections → Download.
"""

import csv
import logging
import os

from backend.utils.text import normalize_company

log = logging.getLogger(__name__)

_EXPECTED_HEADER = "first name"
_MAX_PREAMBLE_LINES = 10


def _open_at_header(path: str):
    """LinkedIn prefixes the export with a notes blurb, so the header is not
    always the first line."""
    handle = open(path, newline="", encoding="utf-8-sig")
    position = handle.tell()
    for _ in range(_MAX_PREAMBLE_LINES):
        line = handle.readline()
        if not line:
            break
        if _EXPECTED_HEADER in line.lower():
            handle.seek(position)
            return handle
        position = handle.tell()

    handle.seek(0)
    return handle


def load_connections(path: str) -> list[dict]:
    if not path or not os.path.exists(path):
        log.info("no LinkedIn connections export at %s", path)
        return []

    contacts: list[dict] = []
    with _open_at_header(path) as handle:
        for row in csv.DictReader(handle):
            name = " ".join(
                part for part in (
                    (row.get("First Name") or "").strip(),
                    (row.get("Last Name") or "").strip(),
                ) if part
            )
            if not name:
                continue
            contacts.append({
                "name": name,
                "linkedin_url": (row.get("URL") or "").strip() or None,
                "email": (row.get("Email Address") or "").strip() or None,
                "current_company": (row.get("Company") or "").strip() or None,
                "current_role": (row.get("Position") or "").strip() or None,
                "degree_type": "1st",
                "source": "csv",
            })
    return contacts


def find_connections_at(path: str, company: str) -> list[dict]:
    target = normalize_company(company)
    if not target:
        return []
    return [
        contact for contact in load_connections(path)
        if (normalized := normalize_company(contact["current_company"]))
        and (target in normalized or normalized in target)
    ]
