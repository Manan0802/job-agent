"""Matching messy real-world names.

Resumes, LinkedIn profiles and job postings all write the same employer or
university differently — "IndiaMART InterMESH Ltd" vs "ex-IndiaMART",
"Delhi Technological University (DTU), New Delhi" vs "DTU Delhi".
"""

import re

# Legal and generic suffixes that differ between sources for the same employer.
COMPANY_NOISE = re.compile(
    r"\b(private|pvt|limited|ltd|llp|inc|incorporated|corp|corporation|"
    r"technologies|technology|labs|solutions|services|india|co)\b\.?",
    re.IGNORECASE,
)

_INSTITUTION_NOISE = {"the", "of", "and", "university", "college", "institute",
                      "school", "new", "campus"}


def normalize_company(name: str | None) -> str:
    cleaned = COMPANY_NOISE.sub(" ", name or "")
    return " ".join(re.sub(r"[^\w\s]", " ", cleaned).split()).lower()


def company_key(name: str | None) -> str:
    """The distinctive part of an employer name, for matching across sources."""
    normalized = normalize_company(name)
    return normalized.split()[0] if normalized else ""


def institution_aliases(name: str | None) -> set[str]:
    """Every way a university might be written on someone's profile.

    'Delhi Technological University (DTU), New Delhi' yields the core name, the
    acronym printed in brackets, and the acronym derived from the core words.
    """
    if not name:
        return set()

    aliases: set[str] = set()
    bracketed = re.findall(r"\(([A-Za-z]{2,10})\)", name)
    aliases.update(b.lower() for b in bracketed)

    core = re.sub(r"\(.*?\)", " ", name).split(",")[0]
    words = [w.lower() for w in re.findall(r"[A-Za-z]+", core)]
    significant = [w for w in words if w not in _INSTITUTION_NOISE]

    if words:
        aliases.add(" ".join(words))
    if significant:
        aliases.add(" ".join(significant))
        acronym = "".join(w[0] for w in significant)
        if len(acronym) >= 2:
            aliases.add(acronym)

    return {a for a in aliases if len(a) >= 2}


def contains_word(haystack: str, needle: str) -> bool:
    """Word-boundary match, so a one-letter skill like 'C' does not match
    'Recruiter'."""
    if not needle:
        return False
    return re.search(rf"(?<![\w+#]){re.escape(needle.lower())}(?![\w+#])", haystack.lower()) is not None
