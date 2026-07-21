from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.agents.job_hunter_graph import DEFAULT_TOP_N, run_hunt
from backend.services.job_store import load_jobs
from backend.services.profile_store import load_profile

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

# The raw vector is only useful server-side for ranking.
_HIDDEN_FIELDS = {"embedding"}


class HuntRequest(BaseModel):
    search_term: str
    location: str = "India"
    top_n: int = Field(default=DEFAULT_TOP_N, ge=1, le=50)


def _public(job: dict) -> dict:
    return {k: v for k, v in job.items() if k not in _HIDDEN_FIELDS}


@router.post("/hunt")
def hunt(request: HuntRequest):
    """Run a full hunt. Takes a couple of minutes: it scrapes every source,
    ranks everything locally, then scores only the shortlist with the LLM."""
    profile = load_profile()
    if profile is None:
        raise HTTPException(
            status_code=400,
            detail="No profile yet — upload a resume at /api/v1/resume/upload first",
        )

    result = run_hunt(
        profile,
        search_term=request.search_term,
        location=request.location,
        top_n=request.top_n,
    )
    scored = result.get("scored", [])
    return {
        "total_found": result.get("total_found", 0),
        "scored_count": len(scored),
        "alert_sent": result.get("alert_sent", False),
        "jobs": [_public(job) for job in scored],
    }


@router.get("")
def list_jobs(limit: int | None = None):
    jobs = [_public(job) for job in load_jobs(limit=limit)]
    return {"count": len(jobs), "jobs": jobs}
