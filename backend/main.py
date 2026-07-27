from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.routes import applications, jobs, outreach, referrals, resume
from backend.db.database import init_db

app = FastAPI(title="Job + Referral Finder")


@app.on_event("startup")
def _startup():
    init_db()


app.include_router(resume.router)
app.include_router(jobs.router)
app.include_router(referrals.router)
app.include_router(outreach.router)
app.include_router(applications.router)


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
