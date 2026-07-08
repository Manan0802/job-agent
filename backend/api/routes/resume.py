import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.agents.resume_profiler import parse_resume_pdf
from backend.services.profile_store import save_profile, load_profile

router = APIRouter(prefix="/api/v1/resume", tags=["resume"])


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        profile = parse_resume_pdf(tmp_path)
    finally:
        os.unlink(tmp_path)
    save_profile(profile)
    return profile.model_dump()


@router.get("/profile")
async def get_profile():
    profile = load_profile()
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile yet")
    return profile.model_dump()
