from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import init_db

client = TestClient(app)

def test_put_profile_persists(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "u.db"))
    monkeypatch.setenv("PROFILE_PATH", str(tmp_path / "u.json"))
    init_db()
    body = {"personal": {"name": "Edited"}, "skills": {"languages": ["Go"]},
            "experience": [], "education": [], "keywords": []}
    r = client.put("/api/v1/resume/profile", json=body)
    assert r.status_code == 200
    assert r.json()["personal"]["name"] == "Edited"
    g = client.get("/api/v1/resume/profile")
    assert g.json()["skills"]["languages"] == ["Go"]
