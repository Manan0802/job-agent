"""Tailoring advice for one job."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.agents.resume_tailor import analyze_fit, draft_cover_letter
from backend.services.job_store import get_job
from backend.services.profile_store import load_profile

router = APIRouter(prefix="/api/v1/tailor", tags=["tailor"])


class TailorRequest(BaseModel):
    job_id: str


def _context(job_id: str):
    profile = load_profile()
    if profile is None:
        raise HTTPException(
            status_code=400,
            detail="No profile yet — upload a resume at /api/v1/resume/upload first",
        )
    job = get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=404, detail=f"No job {job_id} — run /api/v1/jobs/hunt first"
        )
    return job, profile


@router.post("/analyze")
def analyze(request: TailorRequest):
    """What this posting wants, split into what you prove, what you buried,
    and what you genuinely lack."""
    job, profile = _context(request.job_id)
    analysis = analyze_fit(job, profile)
    return {
        "job": {"id": job["id"], "title": job.get("title"), "company": job.get("company")},
        **analysis.model_dump(),
        "has_unsupported": analysis.has_unsupported,
    }


@router.post("/cover-letter")
def cover_letter(request: TailorRequest):
    job, profile = _context(request.job_id)
    letter = draft_cover_letter(job, profile)
    return {
        "job": {"id": job["id"], "title": job.get("title"), "company": job.get("company")},
        **letter.model_dump(),
        "has_unsupported": letter.has_unsupported,
    }
