from fastapi import FastAPI
from backend.db.database import init_db
from backend.api.routes import jobs, outreach, referrals, resume

app = FastAPI(title="Job + Referral Finder")


@app.on_event("startup")
def _startup():
    init_db()


app.include_router(resume.router)
app.include_router(jobs.router)
app.include_router(referrals.router)
app.include_router(outreach.router)


@app.get("/health")
def health():
    return {"status": "ok"}
