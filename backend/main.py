import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api.routes import applications, jobs, outreach, referrals, resume, setup, tailor
from backend.db.database import init_db
from backend.llm.errors import ModelUnavailable
from backend.services import scheduler

log = logging.getLogger(__name__)

app = FastAPI(title="Job + Referral Finder")


@app.on_event("startup")
async def _startup():
    init_db()
    if scheduler.is_enabled():
        asyncio.create_task(scheduler.run_forever())


app.include_router(resume.router)
app.include_router(jobs.router)
app.include_router(referrals.router)
app.include_router(outreach.router)
app.include_router(applications.router)
app.include_router(setup.router)
app.include_router(tailor.router)


@app.exception_handler(ModelUnavailable)
def _model_unavailable(request: Request, exc: ModelUnavailable):
    """The free models get busy and rate-limited. That is not a crash, and the
    user should be told to retry rather than shown a bare 500."""
    log.warning("model gave up on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content={
            "detail": "The free AI model is busy right now and couldn't finish that. "
                      "Give it a minute and try again.",
        },
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve the built UI last, so it never shadows an API route. Without the build
# the API still runs on its own; `npm run build` in frontend/ produces it.
_UI = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if _UI.is_dir():
    app.mount("/assets", StaticFiles(directory=_UI / "assets"), name="assets")

    if (_UI / "fonts").is_dir():
        app.mount("/fonts", StaticFiles(directory=_UI / "fonts"), name="fonts")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(_UI / "index.html")
