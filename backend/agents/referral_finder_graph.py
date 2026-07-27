"""The referral hunt, as a LangGraph pipeline.

    gather -> merge -> score -> save

Two sources feed it: the user's own LinkedIn export (1st-degree, free, and the
only place that knows who they actually know) and a public Google search
(2nd-degree, metered). Neither is required — whatever is missing just narrows
the result, and a manual LinkedIn search link is always offered as the
zero-cost floor.
"""

import json
import logging
from datetime import datetime, timezone
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from backend.config import get_settings
from backend.schemas.profile import Profile
from backend.services.connections_csv import find_connections_at
from backend.services.contact_store import save_contacts
from backend.services.people_search import manual_search_url, search_people
from backend.services.warmth import score_contact
from backend.utils.dedup import contact_id

log = logging.getLogger(__name__)

_settings = get_settings()


class ReferralState(TypedDict, total=False):
    profile: Profile
    company: str
    role: str | None
    connections: list[dict]
    strangers: list[dict]
    merged: list[dict]
    contacts: list[dict]
    manual_search_url: str


def _gather(state: ReferralState) -> ReferralState:
    company = state["company"]

    try:
        connections = find_connections_at(_settings.linkedin_connections_csv, company)
    except Exception as exc:
        log.warning("reading the LinkedIn export failed: %s", exc)
        connections = []

    try:
        strangers = search_people(
            company,
            role=state.get("role"),
            location=state["profile"].personal.location,
        )
    except Exception as exc:
        log.warning("people search failed: %s", exc)
        strangers = []

    log.info("referral sources -> %d from CSV, %d from search",
             len(connections), len(strangers))
    return {"connections": connections, "strangers": strangers}


def _merge(state: ReferralState) -> ReferralState:
    """Combine both sources, keyed on identity.

    Search results call everyone a stranger, but the CSV knows who the user
    actually knows — so a contact found in both keeps its 1st-degree standing
    while still picking up whatever the search added.
    """
    merged: dict[str, dict] = {}

    for contact in [*state.get("strangers", []), *state.get("connections", [])]:
        key = contact_id(contact.get("linkedin_url"), contact.get("name"),
                         contact.get("current_company"))
        existing = merged.get(key, {})
        combined = {**existing, **{k: v for k, v in contact.items() if v is not None}}
        if existing.get("degree_type") == "1st" or contact.get("degree_type") == "1st":
            combined["degree_type"] = "1st"
        merged[key] = {**combined, "id": key}

    return {"merged": list(merged.values())}


def _score(state: ReferralState) -> ReferralState:
    profile = state["profile"]
    company = state["company"]
    now = datetime.now(timezone.utc).isoformat()

    scored = []
    for contact in state.get("merged", []):
        warmth, reasons = score_contact(contact, profile)
        scored.append({
            **contact,
            "target_company": company,
            "warmth_score": warmth,
            "warmth_reasons": json.dumps(reasons),
            "created_at": now,
        })

    scored.sort(key=lambda c: -c["warmth_score"])
    return {"contacts": scored}


def _save(state: ReferralState) -> ReferralState:
    save_contacts(state.get("contacts", []))
    school = next((e.institution for e in state["profile"].education if e.institution), None)
    return {
        "manual_search_url": manual_search_url(
            state["company"], role=state.get("role"), school=school)
    }


def build_graph():
    graph = StateGraph(ReferralState)
    graph.add_node("gather", _gather)
    graph.add_node("merge", _merge)
    graph.add_node("score", _score)
    graph.add_node("save", _save)

    graph.add_edge(START, "gather")
    graph.add_edge("gather", "merge")
    graph.add_edge("merge", "score")
    graph.add_edge("score", "save")
    graph.add_edge("save", END)
    return graph.compile()


def find_referrals(profile: Profile, company: str, role: str | None = None) -> ReferralState:
    return build_graph().invoke({"profile": profile, "company": company, "role": role})
