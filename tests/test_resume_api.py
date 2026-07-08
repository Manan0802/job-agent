import io
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import init_db
from backend.schemas.profile import Profile, Personal

client = TestClient(app)

def test_health():
    assert client.get("/health").json() == {"status": "ok"}

def test_upload_rejects_non_pdf():
    r = client.post("/api/v1/resume/upload",
                    files={"file": ("resume.txt", io.BytesIO(b"hi"), "text/plain")})
    assert r.status_code == 400

def test_upload_pdf_returns_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("PROFILE_PATH", str(tmp_path / "p.json"))
    init_db()
    fake = Profile(personal=Personal(name="Manan"))
    with patch("backend.api.routes.resume.parse_resume_pdf", return_value=fake):
        r = client.post("/api/v1/resume/upload",
                        files={"file": ("resume.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")})
    assert r.status_code == 200
    assert r.json()["personal"]["name"] == "Manan"
