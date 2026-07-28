"""What's configured, what each missing piece unlocks, and where to get it.

Everything except the LLM key is optional — the app degrades rather than
breaking — but from inside the UI there is otherwise no way to tell whether
referral search is quietly returning nothing because no key is set.

This endpoint reports whether a key exists. It never returns one.
"""

import os

from fastapi import APIRouter

from backend.config import get_settings
from backend.services import scheduler
from backend.services.api_budget import remaining

router = APIRouter(prefix="/api/v1/setup", tags=["setup"])

_settings = get_settings()


def _people_search_detail() -> str:
    """Show what's left of the free tiers, so running dry isn't a surprise."""
    left = []
    if _settings.serper_api_key:
        left.append(f"Serper: {remaining('serper', _settings.serper_monthly_cap)} searches left")
    if _settings.serpapi_api_key:
        left.append(
            f"SerpApi: {remaining('serpapi', _settings.serpapi_monthly_cap)} left this month"
        )
    return " · ".join(left)


@router.get("")
def status():
    csv_path = _settings.linkedin_connections_csv
    has_csv = bool(csv_path) and os.path.exists(csv_path)

    items = [
        {
            "id": "llm",
            "label": "AI model",
            "required": True,
            "configured": bool(_settings.llm_api_key),
            "unlocks": "Reading your resume, scoring jobs, and writing messages.",
            "detail": f"{_settings.llm_model}"
            + (f", falling back to {_settings.groq_model}" if _settings.groq_api_key else ""),
            "how": "Get a free key at aistudio.google.com/apikey and put it in .env as LLM_API_KEY.",
        },
        {
            "id": "llm_fallback",
            "label": "Backup model",
            "required": False,
            "configured": bool(_settings.groq_api_key),
            "unlocks": "Keeps working when Gemini is busy, which it often is.",
            "detail": _settings.groq_model if _settings.groq_api_key else "",
            "how": "Free key at console.groq.com/keys, then GROQ_API_KEY in .env.",
        },
        {
            "id": "people_search",
            "label": "Referral search",
            "required": False,
            "configured": bool(_settings.serper_api_key or _settings.serpapi_api_key),
            "unlocks": "Finding people you don't already know. Without it, referrals come "
                       "only from your own connections and a manual search link.",
            "detail": _people_search_detail(),
            "how": "Serper gives 2,500 free searches with no card at serper.dev, "
                   "then SERPER_API_KEY in .env.",
        },
        {
            "id": "connections",
            "label": "Your LinkedIn connections",
            "required": False,
            "configured": has_csv,
            "unlocks": "Surfacing people you already know at a company, who are the "
                       "warmest referrals you have.",
            "detail": csv_path if has_csv else "",
            "how": "LinkedIn → Settings & Privacy → Data Privacy → Get a copy of your data → "
                   f"Connections, then save it to {csv_path}.",
        },
        {
            "id": "password",
            "label": "Password",
            "required": False,
            "configured": bool(_settings.app_password),
            "unlocks": "Sharing the app beyond this laptop. Everything here is "
                       "personal, so ./share.sh will not open a tunnel without it.",
            "detail": "",
            "how": "Set APP_PASSWORD in .env to anything long, then restart. "
                   "See docs/DEPLOY.md.",
        },
        {
            "id": "schedule",
            "label": "Hunting on a schedule",
            "required": False,
            "configured": scheduler.is_enabled(),
            "unlocks": "The app hunts on its own every few hours and messages you only "
                       "about matches you have not seen before.",
            "detail": (
                f"Every {_settings.hunt_every_hours}h for "
                f"\u201c{_settings.hunt_search_term}\u201d in {_settings.hunt_location}"
                if scheduler.is_enabled() else ""
            ),
            "how": "Set HUNT_SEARCH_TERM (e.g. your target role) and HUNT_EVERY_HOURS=12 "
                   "in .env, then restart. Needs job alerts below to actually reach you.",
        },
        {
            "id": "alerts",
            "label": "Job alerts",
            "required": False,
            "configured": bool(_settings.telegram_bot_token and _settings.telegram_chat_id),
            "unlocks": "A message on your phone when a hunt finds strong matches.",
            "detail": "",
            "how": "Create a bot with @BotFather, message it once, then read your chat id from "
                   "api.telegram.org/bot<TOKEN>/getUpdates. Set TELEGRAM_BOT_TOKEN and "
                   "TELEGRAM_CHAT_ID in .env.",
        },
    ]

    return {
        "ready": bool(_settings.llm_api_key),
        "items": items,
        "embedding_model": _settings.embedding_model,
        "last_scheduled_hunt": scheduler.last_run,
    }
