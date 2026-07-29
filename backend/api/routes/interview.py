"""Preparing for one interview.

Same shape as tailoring: it needs a resume and a job you have actually found,
and it reports whether any suggested answer would have you overclaim.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.agents.interview_prep import prepare_for
from backend.services.job_store import get_job
from backend.services.profile_store import load_profile

router = APIRouter(prefix="/api/v1/interview", tags=["interview"])


class PrepRequest(BaseModel):
    job_id: str


@router.post("/prep")
def prep(request: PrepRequest):
    """Questions this posting makes likely, and which of your own work answers
    each one."""
    profile = load_profile()
    if profile is None:
        raise HTTPException(
            status_code=400,
            detail="No profile yet — upload a resume at /api/v1/resume/upload first",
        )
    job = get_job(request.job_id)
    if job is None:
        raise HTTPException(
            status_code=404, detail=f"No job {request.job_id} — run /api/v1/jobs/hunt first"
        )

    result = prepare_for(job, profile)
    return {
        "job": {"id": job["id"], "title": job.get("title"), "company": job.get("company")},
        **result.model_dump(),
        "has_unsupported": result.has_unsupported,
    }
