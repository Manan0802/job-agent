"""Local embeddings + cheap pre-filter.

Scoring every scraped job with an LLM would burn the free tier in one run. So we
embed locally (free, offline) and only the closest handful ever reach the LLM.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.config import get_settings
from backend.schemas.profile import Profile

_model: SentenceTransformer | None = None

# bge-small truncates at 512 tokens; long JD boilerplate past this adds nothing.
_DESCRIPTION_CHARS = 1000


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(get_settings().embedding_model)
    return _model


def _encode(texts: list[str]) -> list[bytes]:
    vectors = _get_model().encode(texts, normalize_embeddings=True, batch_size=32)
    return [np.asarray(v, dtype=np.float32).tobytes() for v in vectors]


def embed_text(text: str) -> bytes:
    return _encode([text])[0]


def cosine_similarity(a: bytes, b: bytes) -> float:
    va = np.frombuffer(a, dtype=np.float32)
    vb = np.frombuffer(b, dtype=np.float32)
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    if denom == 0.0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def _job_text(job: dict) -> str:
    parts = [
        job.get("title"),
        job.get("company"),
        job.get("location"),
        (job.get("description") or "")[:_DESCRIPTION_CHARS],
    ]
    return " ".join(p for p in parts if p)


def _profile_text(profile: Profile) -> str:
    """What the profile is *about* — skills and work, not contact details."""
    s = profile.skills
    parts = [
        *s.languages, *s.frameworks, *s.ai_ml, *s.tools, *s.databases,
        *(e.role for e in profile.experience if e.role),
        *(tech for e in profile.experience for tech in e.tech_used),
        *(f"{e.degree or ''} {e.field or ''}".strip() for e in profile.education),
        *profile.keywords,
    ]
    return " ".join(p for p in parts if p)


def embed_profile(profile: Profile) -> bytes:
    return embed_text(_profile_text(profile))


def prefilter_jobs(jobs: list[dict], profile_embedding: bytes, top_n: int = 15) -> list[dict]:
    """Rank every job by cosine similarity, return only the top_n for LLM scoring."""
    if not jobs:
        return []
    vectors = _encode([_job_text(job) for job in jobs])
    scored = [
        {**job, "embedding": vec, "prefilter_score": cosine_similarity(vec, profile_embedding)}
        for job, vec in zip(jobs, vectors)
    ]
    scored.sort(key=lambda job: job["prefilter_score"], reverse=True)
    return scored[:top_n]
