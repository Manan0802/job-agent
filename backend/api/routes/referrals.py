import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.agents.referral_finder_graph import find_referrals
from backend.services.contact_store import load_contacts
from backend.services.profile_store import load_profile

router = APIRouter(prefix="/api/v1/referrals", tags=["referrals"])


class ReferralRequest(BaseModel):
    company: str
    role: str | None = None


def _public(contact: dict) -> dict:
    """`warmth_reasons` is stored as JSON text; callers get a real list."""
    raw = contact.get("warmth_reasons")
    reasons = []
    if raw:
        try:
            reasons = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            reasons = [raw]
    return {**contact, "warmth_reasons": reasons}


@router.post("/find")
def find(request: ReferralRequest):
    """Find who could refer you into a company, warmest contact first."""
    profile = load_profile()
    if profile is None:
        raise HTTPException(
            status_code=400,
            detail="No profile yet — upload a resume at /api/v1/resume/upload first",
        )

    result = find_referrals(profile, company=request.company, role=request.role)
    contacts = result.get("contacts", [])
    return {
        "company": result.get("company", request.company),
        "count": len(contacts),
        "contacts": [_public(c) for c in contacts],
        "manual_search_url": result.get("manual_search_url"),
    }


@router.get("")
def list_referrals(company: str | None = None):
    contacts = [_public(c) for c in load_contacts(company=company)]
    return {"count": len(contacts), "contacts": contacts}
