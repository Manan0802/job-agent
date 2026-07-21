"""The job hunt, as a LangGraph pipeline.

    ingest -> dedup -> prefilter -> score -> save -> notify

Ingest runs the sources concurrently and tolerates any one of them being down,
since a blocked scraper should cost coverage rather than the whole run. Only
the pre-filtered shortlist reaches the LLM, which is what keeps a hunt inside
the free tier.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from backend.agents.job_scorer import score_jobs
from backend.schemas.profile import Profile
from backend.services.embeddings import embed_profile, prefilter_jobs
from backend.services.job_sources.jobspy_adapter import fetch_jobs
from backend.services.job_sources.remote_apis import fetch_all_remote
from backend.services.job_sources.yc_adapter import fetch_yc_jobs
from backend.services.job_store import save_jobs
from backend.services.notify import format_job_alert, send_telegram_alert
from backend.utils.dedup import dedupe_jobs

log = logging.getLogger(__name__)

DEFAULT_TOP_N = 15


class HuntState(TypedDict, total=False):
    search_term: str
    location: str
    top_n: int
    profile: Profile
    raw_jobs: list[dict]
    unique_jobs: list[dict]
    shortlist: list[dict]
    scored: list[dict]
    total_found: int
    alert_sent: bool


def _ingest(state: HuntState) -> HuntState:
    search_term = state["search_term"]
    location = state.get("location", "India")

    sources = {
        "jobspy": lambda: fetch_jobs(search_term, location=location),
        "remote_apis": fetch_all_remote,
        "yc": fetch_yc_jobs,
    }

    jobs: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(sources)) as pool:
        futures = {name: pool.submit(fn) for name, fn in sources.items()}
        for name, future in futures.items():
            try:
                found = future.result()
                log.info("ingest %s -> %d jobs", name, len(found))
                jobs.extend(found)
            except Exception as exc:
                log.warning("ingest source %s failed: %s", name, exc)

    return {"raw_jobs": jobs}


def _dedup(state: HuntState) -> HuntState:
    unique = dedupe_jobs(state.get("raw_jobs", []))
    return {"unique_jobs": unique, "total_found": len(unique)}


def _prefilter(state: HuntState) -> HuntState:
    jobs = state.get("unique_jobs", [])
    if not jobs:
        return {"shortlist": []}
    profile_embedding = embed_profile(state["profile"])
    shortlist = prefilter_jobs(jobs, profile_embedding, state.get("top_n") or DEFAULT_TOP_N)
    return {"shortlist": shortlist}


def _score(state: HuntState) -> HuntState:
    shortlist = state.get("shortlist", [])
    if not shortlist:
        return {"scored": []}
    return {"scored": score_jobs(shortlist, state["profile"])}


def _save(state: HuntState) -> HuntState:
    save_jobs(state.get("scored", []))
    return {}


def _notify(state: HuntState) -> HuntState:
    message = format_job_alert(state.get("scored", []), state.get("total_found", 0))
    return {"alert_sent": send_telegram_alert(message)}


def build_graph():
    graph = StateGraph(HuntState)
    graph.add_node("ingest", _ingest)
    graph.add_node("dedup", _dedup)
    graph.add_node("prefilter", _prefilter)
    graph.add_node("score", _score)
    graph.add_node("save", _save)
    graph.add_node("notify", _notify)

    graph.add_edge(START, "ingest")
    graph.add_edge("ingest", "dedup")
    graph.add_edge("dedup", "prefilter")
    graph.add_edge("prefilter", "score")
    graph.add_edge("score", "save")
    graph.add_edge("save", "notify")
    graph.add_edge("notify", END)
    return graph.compile()


def run_hunt(
    profile: Profile,
    search_term: str,
    location: str = "India",
    top_n: int = DEFAULT_TOP_N,
) -> HuntState:
    return build_graph().invoke({
        "profile": profile,
        "search_term": search_term,
        "location": location,
        "top_n": top_n,
    })
