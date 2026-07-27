"""Tracking where every application stands, and what is owed next."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.application_store import (
    PIPELINE_STAGES,
    add_note,
    get_application,
    load_applications,
    move_stage,
    record_offer,
    track_job,
)
from backend.services.job_store import get_job
from backend.services.tracker_insights import due_reminders, pipeline_stats

router = APIRouter(prefix="/api/v1/applications", tags=["applications"])


class TrackRequest(BaseModel):
    job_id: str
    applied_via: str = "direct"
    referral_contact_id: str | None = None


class StageRequest(BaseModel):
    status: str


class NoteRequest(BaseModel):
    note: str


class OfferRequest(BaseModel):
    amount: int = Field(ge=0)
    currency: str = "INR"


def _require(application_id: str) -> dict:
    application = get_application(application_id)
    if application is None:
        raise HTTPException(status_code=404, detail=f"No application {application_id}")
    return application


@router.post("/track")
def track(request: TrackRequest):
    job = get_job(request.job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"No job {request.job_id} — run /api/v1/jobs/hunt first",
        )
    application_id = track_job(
        job,
        applied_via=request.applied_via,
        referral_contact_id=request.referral_contact_id,
    )
    return _require(application_id)


# Declared before the /{application_id} routes so these names are not read as ids.
@router.get("/reminders")
def reminders():
    """What has been left to go stale, most neglected first."""
    overdue = due_reminders()
    return {"count": len(overdue), "reminders": overdue}


@router.get("/stats")
def stats():
    return pipeline_stats()


@router.get("")
def list_applications(status: str | None = None):
    applications = load_applications(status=status)
    return {"count": len(applications), "applications": applications}


@router.post("/{application_id}/stage")
def set_stage(application_id: str, request: StageRequest):
    _require(application_id)
    try:
        move_stage(application_id, request.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown stage {request.status!r} — use one of: "
                   f"{', '.join(PIPELINE_STAGES)}",
        )
    return _require(application_id)


@router.post("/{application_id}/note")
def note(application_id: str, request: NoteRequest):
    _require(application_id)
    add_note(application_id, request.note)
    return _require(application_id)


@router.post("/{application_id}/offer")
def offer(application_id: str, request: OfferRequest):
    _require(application_id)
    record_offer(application_id, request.amount, request.currency)
    return _require(application_id)
