from fastapi import FastAPI
from backend.db.database import init_db
from backend.api.routes import jobs, resume

app = FastAPI(title="Job + Referral Finder")


@app.on_event("startup")
def _startup():
    init_db()


app.include_router(resume.router)
app.include_router(jobs.router)


@app.get("/health")
def health():
    return {"status": "ok"}
