# Phase 1 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upload a PDF resume and get back a validated structured `profile.json`, served by a FastAPI backend with a free-first LLM router and a local SQLite store.

**Architecture:** A FastAPI app exposes resume upload + profile endpoints. Upload flow: PDF → markdown (markitdown) → structured JSON (free LLM via OpenRouter/Groq, routed by a thin `llm_router`) → Pydantic validation → persisted to SQLite and to `data/profile/profile.json`. Everything runs locally; secrets live in `.env`.

**Tech Stack:** Python 3.10+, FastAPI, Uvicorn, SQLAlchemy 2.x (sync), Pydantic v2, markitdown, `openai` SDK (OpenAI-compatible client pointed at OpenRouter), pytest.

## Global Constraints

- Python `>=3.10` (required by downstream JobSpy in Phase 2).
- LLM is **free-first**: default model from `.env` (`LLM_MODEL`, e.g. an OpenRouter free Gemini/Llama model); never hardcode a paid model.
- **All secrets in `.env` only.** Never commit `.env`; commit `.env.example`.
- Local-only storage: SQLite at `data/db/career_agent.db`; profile JSON at `data/profile/profile.json`.
- Budget ₹0 — no paid API calls in tests (LLM calls are mocked in tests).
- Every code change ends in a commit. TDD: test first, watch it fail, implement, watch it pass.

---

### Task 1: Project scaffold + config loader

**Files:**
- Create: `backend/__init__.py`
- Create: `backend/config.py`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `requirements.txt`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `backend.config.Settings` (Pydantic settings) with attributes `llm_api_key: str`, `llm_base_url: str`, `llm_model: str`, `groq_api_key: str | None`, `db_path: str`, `profile_path: str`. Produces `get_settings() -> Settings` (cached).

- [ ] **Step 1: Write `.gitignore` and `requirements.txt`**

`.gitignore`:
```
.env
__pycache__/
*.pyc
.venv/
data/db/*.db
data/profile/*.json
data/resume/*
.pytest_cache/
```

`requirements.txt`:
```
fastapi>=0.110.0
uvicorn>=0.27.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
python-multipart>=0.0.9
markitdown[all]>=0.0.1
openai>=1.0.0
pytest>=8.0.0
httpx>=0.26.0
```

- [ ] **Step 2: Write `.env.example`**

```
# Free-first LLM (OpenRouter, OpenAI-compatible)
LLM_API_KEY=sk-or-v1-xxxxx
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=google/gemini-2.0-flash-exp:free
# Optional second free provider
GROQ_API_KEY=
# Paths
DB_PATH=./data/db/career_agent.db
PROFILE_PATH=./data/profile/profile.json
```

- [ ] **Step 3: Write the failing test**

```python
# tests/test_config.py
import os
from backend.config import get_settings

def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test/model:free")
    get_settings.cache_clear()
    s = get_settings()
    assert s.llm_api_key == "test-key"
    assert s.llm_model == "test/model:free"
    assert s.llm_base_url.startswith("https://")
```

- [ ] **Step 4: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.config'`

- [ ] **Step 5: Write `backend/config.py`**

```python
# backend/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_api_key: str = ""
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "google/gemini-2.0-flash-exp:free"
    groq_api_key: str | None = None
    db_path: str = "./data/db/career_agent.db"
    profile_path: str = "./data/profile/profile.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Also create empty `backend/__init__.py`.

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/__init__.py backend/config.py .env.example .gitignore requirements.txt tests/test_config.py
git commit -m "feat: project scaffold + config loader"
```

---

### Task 2: SQLite database + profiles model

**Files:**
- Create: `backend/db/__init__.py`
- Create: `backend/db/database.py`
- Create: `backend/db/models.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Consumes: `backend.config.get_settings`.
- Produces: `backend.db.database.init_db() -> None`, `get_session() -> Session` (context-managed via `sessionmaker`), `Base`. Produces ORM model `backend.db.models.ProfileRow` with columns `id: int (pk)`, `data: str (JSON text)`, `embedding: bytes | None`, `updated_at: str`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_db.py
from backend.db.database import init_db, get_session, engine
from backend.db.models import ProfileRow

def test_insert_and_read_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    init_db()
    with get_session() as s:
        s.add(ProfileRow(id=1, data='{"name": "Manan"}', updated_at="2026-06-28"))
        s.commit()
    with get_session() as s:
        row = s.get(ProfileRow, 1)
        assert row is not None
        assert '"Manan"' in row.data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_db.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.db.database'`

- [ ] **Step 3: Write `backend/db/models.py`**

```python
# backend/db/models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ProfileRow(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[str] = mapped_column()              # JSON text
    embedding: Mapped[bytes | None] = mapped_column(nullable=True)
    updated_at: Mapped[str] = mapped_column()
```

- [ ] **Step 4: Write `backend/db/database.py`**

```python
# backend/db/database.py
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.config import get_settings
from backend.db.models import Base

_settings = get_settings()
_db_path = os.environ.get("DB_PATH", _settings.db_path)
os.makedirs(os.path.dirname(_db_path), exist_ok=True)

engine = create_engine(f"sqlite:///{_db_path}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)


@contextmanager
def get_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

Also create empty `backend/db/__init__.py`.

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_db.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/db/ tests/test_db.py
git commit -m "feat: sqlite database + profiles model"
```

---

### Task 3: Free-first LLM router

**Files:**
- Create: `backend/llm/__init__.py`
- Create: `backend/llm/router.py`
- Test: `tests/test_llm_router.py`

**Interfaces:**
- Consumes: `backend.config.get_settings`.
- Produces: `backend.llm.router.complete(prompt: str, system: str = "", model: str | None = None) -> str`. When `model` is None it uses the configured default. Internally uses an OpenAI-compatible client; this is the only place the provider is referenced, so later tasks call `complete()` without knowing the provider.

- [ ] **Step 1: Write the failing test (mock the client, no real API call)**

```python
# tests/test_llm_router.py
from unittest.mock import patch, MagicMock
from backend.llm import router

def test_complete_returns_text():
    fake = MagicMock()
    fake.choices = [MagicMock(message=MagicMock(content="hello world"))]
    with patch.object(router, "_client") as client:
        client.chat.completions.create.return_value = fake
        out = router.complete("say hi", system="be brief")
    assert out == "hello world"
    # default model from settings was used
    _, kwargs = client.chat.completions.create.call_args
    assert kwargs["model"]  # non-empty
    assert kwargs["messages"][0]["role"] == "system"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_router.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.llm.router'`

- [ ] **Step 3: Write `backend/llm/router.py`**

```python
# backend/llm/router.py
from openai import OpenAI
from backend.config import get_settings

_settings = get_settings()
_client = OpenAI(api_key=_settings.llm_api_key or "missing", base_url=_settings.llm_base_url)


def complete(prompt: str, system: str = "", model: str | None = None) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = _client.chat.completions.create(
        model=model or _settings.llm_model,
        messages=messages,
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()
```

Also create empty `backend/llm/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_router.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/llm/ tests/test_llm_router.py
git commit -m "feat: free-first LLM router"
```

---

### Task 4: PDF → markdown utility

**Files:**
- Create: `backend/utils/__init__.py`
- Create: `backend/utils/pdf_parser.py`
- Test: `tests/test_pdf_parser.py`

**Interfaces:**
- Produces: `backend.utils.pdf_parser.pdf_to_markdown(pdf_path: str) -> str`.

- [ ] **Step 1: Write the failing test (mock markitdown so no real PDF needed)**

```python
# tests/test_pdf_parser.py
from unittest.mock import patch, MagicMock
from backend.utils import pdf_parser

def test_pdf_to_markdown_returns_text():
    fake_result = MagicMock(text_content="# Manan\nSoftware Engineer")
    with patch.object(pdf_parser, "MarkItDown") as MD:
        MD.return_value.convert.return_value = fake_result
        out = pdf_parser.pdf_to_markdown("dummy.pdf")
    assert "Software Engineer" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pdf_parser.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.utils.pdf_parser'`

- [ ] **Step 3: Write `backend/utils/pdf_parser.py`**

```python
# backend/utils/pdf_parser.py
from markitdown import MarkItDown


def pdf_to_markdown(pdf_path: str) -> str:
    md = MarkItDown()
    result = md.convert(pdf_path)
    return result.text_content
```

Also create empty `backend/utils/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pdf_parser.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/utils/ tests/test_pdf_parser.py
git commit -m "feat: pdf to markdown utility"
```

---

### Task 5: Profile schema + resume parser

**Files:**
- Create: `backend/schemas/__init__.py`
- Create: `backend/schemas/profile.py`
- Create: `backend/agents/__init__.py`
- Create: `backend/agents/resume_profiler.py`
- Test: `tests/test_resume_profiler.py`

**Interfaces:**
- Consumes: `backend.llm.router.complete`, `backend.utils.pdf_parser.pdf_to_markdown`.
- Produces: Pydantic models `backend.schemas.profile.Profile` (fields: `personal: Personal`, `skills: Skills`, `experience: list[Experience]`, `education: list[Education]`, `keywords: list[str]`). Produces `backend.agents.resume_profiler.parse_resume_markdown(markdown: str) -> Profile` and `parse_resume_pdf(pdf_path: str) -> Profile`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_resume_profiler.py
from unittest.mock import patch
from backend.agents import resume_profiler

FAKE_JSON = '''{
  "personal": {"name": "Manan", "email": "m@x.com"},
  "skills": {"languages": ["Python"], "frameworks": ["FastAPI"]},
  "experience": [{"company": "IndiaMART", "role": "AI Intern"}],
  "education": [{"institution": "DTU", "degree": "B.Tech"}],
  "keywords": ["LangGraph", "RAG"]
}'''

def test_parse_resume_markdown_returns_profile():
    with patch.object(resume_profiler, "complete", return_value=FAKE_JSON):
        profile = resume_profiler.parse_resume_markdown("# Manan ...")
    assert profile.personal.name == "Manan"
    assert "Python" in profile.skills.languages
    assert profile.keywords == ["LangGraph", "RAG"]

def test_parse_strips_markdown_fences():
    fenced = "```json\n" + FAKE_JSON + "\n```"
    with patch.object(resume_profiler, "complete", return_value=fenced):
        profile = resume_profiler.parse_resume_markdown("# Manan ...")
    assert profile.personal.email == "m@x.com"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_resume_profiler.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.agents.resume_profiler'`

- [ ] **Step 3: Write `backend/schemas/profile.py`**

```python
# backend/schemas/profile.py
from pydantic import BaseModel, Field


class Personal(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None


class Skills(BaseModel):
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    ai_ml: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)


class Experience(BaseModel):
    company: str | None = None
    role: str | None = None
    duration_months: int | None = None
    highlights: list[str] = Field(default_factory=list)
    tech_used: list[str] = Field(default_factory=list)


class Education(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    graduation_year: int | None = None


class Profile(BaseModel):
    personal: Personal = Field(default_factory=Personal)
    skills: Skills = Field(default_factory=Skills)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
```

Also create empty `backend/schemas/__init__.py`.

- [ ] **Step 4: Write `backend/agents/resume_profiler.py`**

```python
# backend/agents/resume_profiler.py
import json
from backend.llm.router import complete
from backend.utils.pdf_parser import pdf_to_markdown
from backend.schemas.profile import Profile

SYSTEM_PROMPT = (
    "You are a precise resume parser. Extract information from the resume text and "
    "return ONLY a valid JSON object. No preamble, no markdown fences, no explanation. "
    "Use these top-level keys: personal, skills, experience, education, keywords. "
    "If a field is missing, omit it or use null. Do not invent data."
)


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def parse_resume_markdown(markdown: str) -> Profile:
    raw = complete(markdown, system=SYSTEM_PROMPT)
    data = json.loads(_strip_fences(raw))
    return Profile.model_validate(data)


def parse_resume_pdf(pdf_path: str) -> Profile:
    return parse_resume_markdown(pdf_to_markdown(pdf_path))
```

Also create empty `backend/agents/__init__.py`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_resume_profiler.py -v`
Expected: PASS (both tests)

- [ ] **Step 6: Commit**

```bash
git add backend/schemas/ backend/agents/ tests/test_resume_profiler.py
git commit -m "feat: profile schema + resume parser"
```

---

### Task 6: FastAPI app + resume upload endpoint

**Files:**
- Create: `backend/main.py`
- Create: `backend/api/__init__.py`
- Create: `backend/api/routes/__init__.py`
- Create: `backend/api/routes/resume.py`
- Create: `backend/services/__init__.py`
- Create: `backend/services/profile_store.py`
- Test: `tests/test_resume_api.py`

**Interfaces:**
- Consumes: `parse_resume_pdf`, `get_session`, `ProfileRow`, `init_db`.
- Produces: `backend.services.profile_store.save_profile(profile: Profile) -> None` (writes JSON file + upserts `ProfileRow` id=1) and `load_profile() -> Profile | None`. Produces FastAPI app `backend.main.app` with `POST /api/v1/resume/upload` (multipart file) returning the parsed profile JSON.

- [ ] **Step 1: Write `backend/services/profile_store.py`**

```python
# backend/services/profile_store.py
import os
import json
from datetime import datetime, timezone
from backend.config import get_settings
from backend.db.database import get_session
from backend.db.models import ProfileRow
from backend.schemas.profile import Profile


def save_profile(profile: Profile) -> None:
    settings = get_settings()
    path = os.environ.get("PROFILE_PATH", settings.profile_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = profile.model_dump_json()
    with open(path, "w", encoding="utf-8") as f:
        f.write(payload)
    now = datetime.now(timezone.utc).isoformat()
    with get_session() as s:
        row = s.get(ProfileRow, 1)
        if row is None:
            s.add(ProfileRow(id=1, data=payload, updated_at=now))
        else:
            row.data = payload
            row.updated_at = now
        s.commit()


def load_profile() -> Profile | None:
    with get_session() as s:
        row = s.get(ProfileRow, 1)
        if row is None:
            return None
        return Profile.model_validate(json.loads(row.data))
```

- [ ] **Step 2: Write `backend/api/routes/resume.py`**

```python
# backend/api/routes/resume.py
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
```

- [ ] **Step 3: Write `backend/main.py`**

```python
# backend/main.py
from fastapi import FastAPI
from backend.db.database import init_db
from backend.api.routes import resume

app = FastAPI(title="Job + Referral Finder")


@app.on_event("startup")
def _startup():
    init_db()


app.include_router(resume.router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

Create empty `backend/api/__init__.py`, `backend/api/routes/__init__.py`, `backend/services/__init__.py`.

- [ ] **Step 4: Write the failing test**

```python
# tests/test_resume_api.py
import io
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
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
    fake = Profile(personal=Personal(name="Manan"))
    with patch("backend.api.routes.resume.parse_resume_pdf", return_value=fake):
        r = client.post("/api/v1/resume/upload",
                        files={"file": ("resume.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")})
    assert r.status_code == 200
    assert r.json()["personal"]["name"] == "Manan"
```

- [ ] **Step 5: Run tests to verify they fail then pass**

Run: `pytest tests/test_resume_api.py -v`
Expected first run: PASS for all three (app + mocks are in place). If `test_upload_pdf_returns_profile` fails on DB path, ensure `init_db()` ran via startup; the TestClient context triggers startup.

- [ ] **Step 6: Manual smoke test (real, optional — uses free LLM)**

Run: `uvicorn backend.main:app --reload` then in another shell:
`curl -F "file=@data/resume/your_resume.pdf" http://localhost:8000/api/v1/resume/upload`
Expected: JSON profile with your real data. (Requires `LLM_API_KEY` in `.env`.)

- [ ] **Step 7: Commit**

```bash
git add backend/main.py backend/api/ backend/services/ tests/test_resume_api.py
git commit -m "feat: fastapi app + resume upload endpoint"
```

---

### Task 7: Profile update endpoint

**Files:**
- Modify: `backend/api/routes/resume.py` (add `PUT /api/v1/resume/profile`)
- Test: `tests/test_profile_update.py`

**Interfaces:**
- Consumes: `save_profile`, `load_profile`, `Profile`.
- Produces: `PUT /api/v1/resume/profile` accepting a full `Profile` JSON body, persisting it, returning the saved profile.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_profile_update.py
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_put_profile_persists(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "u.db"))
    monkeypatch.setenv("PROFILE_PATH", str(tmp_path / "u.json"))
    body = {"personal": {"name": "Edited"}, "skills": {"languages": ["Go"]},
            "experience": [], "education": [], "keywords": []}
    r = client.put("/api/v1/resume/profile", json=body)
    assert r.status_code == 200
    assert r.json()["personal"]["name"] == "Edited"
    g = client.get("/api/v1/resume/profile")
    assert g.json()["skills"]["languages"] == ["Go"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_profile_update.py -v`
Expected: FAIL with 405 Method Not Allowed (PUT route missing)

- [ ] **Step 3: Add the PUT route to `backend/api/routes/resume.py`**

Add this import near the top:
```python
from backend.schemas.profile import Profile
```
Add this route at the end of the file:
```python
@router.put("/profile")
async def update_profile(profile: Profile):
    save_profile(profile)
    return profile.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_profile_update.py -v`
Expected: PASS

- [ ] **Step 5: Run the full suite**

Run: `pytest -v`
Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/api/routes/resume.py tests/test_profile_update.py
git commit -m "feat: profile update endpoint"
```

---

## Phase 1 Deliverable

Running `uvicorn backend.main:app` gives a working backend where uploading a PDF resume returns a validated structured profile, persisted to SQLite + `profile.json`, editable via `PUT`. Free LLM only. This is the identity source-of-truth every later phase consumes.

## Next Plans (each its own file, built on this foundation)

- **Phase 2 — Job Hunter:** JobSpy adapter + Remotive/RemoteOK/Arbeitnow/Himalayas + camofox sidecar for walled boards + embedding pre-filter + free-LLM shortlist scoring + WhatsApp/Telegram alerts.
- **Phase 3 — Referral Finder:** SerpApi Google-dork (lifted from old `networking_agent`) + CSV 1st-degree + warmth scoring + manual fallback + `api_budget` caps.
- **Phase 4 — Outreach Drafter:** HITL draft/edit/approve + Gmail/WhatsApp send.
- **Phase 5 — Tracker CRM:** Kanban + stats + follow-up reminders.
- **Phase 6 — Polish + React UI.**
- **v2:** resume tailoring (career-ops), interview prep.

---

## Self-Review

- **Spec coverage (Phase 1 slice):** config/`.env` ✓ (T1), SQLite + schema seed ✓ (T2), free-first `llm_router` ✓ (T3), markitdown ✓ (T4), parse→Pydantic `profile.json` ✓ (T5), upload endpoint ✓ (T6), manual edit endpoint ✓ (T7). Embedding column present on `ProfileRow` (T2) for Phase 2 reuse. Phases 2–6 explicitly deferred to their own plans (scope decomposition).
- **Placeholder scan:** none — every code/test step contains full code.
- **Type consistency:** `Profile`/`Personal`/`Skills`/`Experience`/`Education` names consistent across T5–T7; `complete()`, `pdf_to_markdown()`, `parse_resume_pdf()`, `save_profile()`/`load_profile()`, `ProfileRow(id, data, embedding, updated_at)` consistent across consuming tasks.
