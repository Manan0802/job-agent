# Phase 2 — Job Hunter Implementation Plan

**Goal:** Scrape jobs from multiple free sources, dedupe them, cheaply pre-filter with local embeddings against the user's profile, score only the top ~15 with the free LLM router, save results, and send a Telegram alert. Orchestrated as a LangGraph graph.

**Architecture:** `ingest (JobSpy + free remote APIs + YC, parallel) → normalize → dedup → embed+cosine-prefilter → top-N LLM score → save → notify (Telegram)`, wired together as a LangGraph `StateGraph`.

**Decisions locked in (2026-07-13):**
- Orchestration: **LangGraph** (chosen by user over the research-recommended plain-Python approach).
- Notifications: **Telegram** (free, no per-message cost).
- Login policy: portals that work **without** login stay login-free. The user agreed to log in personally where a portal genuinely requires it — but in the end **nothing built in this phase needs a login at all** (see Task 8), so the "no authenticated scraping" rule holds with no exception.
- Embedding model: **`BAAI/bge-small-en-v1.5`** (via `sentence-transformers`), English-only, CPU-friendly at this project's scale. Fallback if too slow: `all-MiniLM-L6-v2`.

**Tech additions:** `python-jobspy`, `sentence-transformers`, `langgraph`, `httpx` (already present), a plain Telegram Bot API integration (no extra SDK needed — just `httpx.post` to `api.telegram.org`).

## Schema additions (SQLite, on top of Phase 1's `profiles` table)

```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,              -- hash(company+title+date) for dedup
    title TEXT, company TEXT, location TEXT, url TEXT,
    description TEXT,
    source_engine TEXT,               -- 'jobspy:linkedin' | 'remotive' | 'jobspy:naukri' | 'yc' ...
    embedding BLOB,                   -- cached job embedding
    prefilter_score REAL,             -- cosine sim vs profile, pre-LLM
    llm_score REAL,                   -- final AI score, null until scored
    llm_breakdown TEXT,               -- JSON: why it scored this way
    fetched_at TEXT
);

CREATE TABLE api_budget (
    provider TEXT PRIMARY KEY,        -- 'serpapi' | future paid escalations
    month TEXT, calls_used INTEGER DEFAULT 0, monthly_cap INTEGER
);
```
`profiles` gains a cached `profile_embedding BLOB` column (Phase 1's `ProfileRow.embedding` column already exists for this — just needs to actually get populated in Phase 2).

## Task breakdown

Strict TDD throughout: write test → run to fail → implement → run to pass → commit → push. Stop and show after each task.

- [x] **Task 1 — Jobs table + budget table.** `backend/db/models.py`: add `JobRow`, `ApiBudgetRow`. Test: insert/read a `JobRow`, confirm dedup-friendly primary key (id = sha256 of `company|title|date`).
- [x] **Task 2 — JobSpy adapter.** `backend/services/job_sources/jobspy_adapter.py`: wraps `python-jobspy`'s `scrape_jobs()`, normalizes its dataframe output to a list of dicts matching the `jobs` schema, tags `source_engine='jobspy:<site>'`. Mock `jobspy.scrape_jobs` in tests — no real network calls in the test suite.
- [x] **Task 3 — Free remote-job APIs adapter.** `backend/services/job_sources/remote_apis.py`: `fetch_remotive()`, `fetch_remoteok()`, `fetch_arbeitnow()`, `fetch_himalayas()`, `fetch_jobicy()` — each an `httpx.get` + normalize to the same schema. Mock `httpx` responses in tests.
- [x] **Task 4 — Dedup utility.** `backend/utils/dedup.py`: `job_id(company, title, date) -> str` (sha256 hex digest) and `dedupe_jobs(jobs: list[dict]) -> list[dict]` (keeps first occurrence per id).
- [x] **Task 5 — Embedding + pre-filter.** `backend/services/embeddings.py`: `embed_text(text) -> bytes` (via `sentence-transformers`, model `BAAI/bge-small-en-v1.5`, cached model load), `cosine_similarity(a: bytes, b: bytes) -> float`, `prefilter_jobs(jobs, profile_embedding, top_n=15) -> list[dict]`. Mock the model in tests (no real model download in test suite — keeps tests fast and offline).
- [x] **Task 6 — LLM job scorer.** `backend/agents/job_scorer.py`: `score_job(job: dict, profile: Profile) -> dict` (returns `{"score": float, "breakdown": str}`) using `backend.llm.router.complete`. Mock `complete` in tests.
- [x] **Task 7 — Telegram notifier.** `backend/services/notify.py`: `send_telegram_alert(message: str) -> None`, reads `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` from settings, posts to `https://api.telegram.org/bot<token>/sendMessage`. Mock `httpx.post` in tests.
- [x] **Task 8 — YC startup jobs (no login needed after all).** `backend/services/job_sources/yc_adapter.py`. The plan assumed `waasuapi`, which needs real credentials plus Selenium/Chromedriver and was last updated in Aug 2024 (its own commit message says "please fix chromedriver pathing"). It turned out YC's public job pages embed their listings as JSON in the HTML, so the adapter reads them over plain HTTP: **no login, no browser, no stale dependency, and no exception to the "no authenticated scraping" rule**. Coverage comes from several public filter pages (`/jobs`, `/jobs/role/eng`, `/jobs/role/design`, `/jobs/location/remote`) since each returns a different slice and there is no pagination. Verified live: 92 unique jobs, all with title + company + url.
- [x] **Task 9 — LangGraph orchestration.** `backend/agents/job_hunter_graph.py`: a `StateGraph` with nodes `ingest → dedup → prefilter → score → save → notify`, using `langgraph`'s in-memory or SQLite checkpointer. Test the graph end-to-end with all external calls mocked.
- [x] **Task 10 — FastAPI trigger endpoint.** `backend/api/routes/jobs.py`: `POST /api/v1/jobs/hunt` (runs the graph, returns job count + top matches), `GET /api/v1/jobs` (list saved jobs, sorted by `llm_score`).

## Config additions (`.env.example`)
```
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```
(`YC_EMAIL`/`YC_PASSWORD` are not needed — see Task 8.)

## Phase 2 Deliverable — done (2026-07-21)
`POST /api/v1/jobs/hunt` pulls jobs from LinkedIn/Naukri/Indeed/Glassdoor/Google (via JobSpy, no login), Remotive/RemoteOK/Arbeitnow/Himalayas/Jobicy (free APIs), and YC (public JSON, no login) — dedupes, pre-filters locally with embeddings, scores only the shortlist with the free LLM, saves to SQLite, and alerts Telegram. `GET /api/v1/jobs` lists what's been found, best-scored first.

**Verified live, not just mocked:** a real hunt found **486 unique jobs**, scored the shortlist, and returned matches led by an ML Engineer role at 88/100. 100 tests passing.

### Deviations from this plan, all deliberate
- **Dedup keys on company+title, not company+title+date.** Every source formats dates differently (ISO, ISO+time, raw epoch), so including the date would have defeated cross-source dedup entirely.
- **YC needs no login** (Task 8) — the plan's `waasuapi` route was unnecessary.
- **Task 9 uses the in-memory checkpointer.** `SqliteSaver` ships in a separate package, and durability already comes from the save node writing to SQLite; a hunt runs in ~100s, too short to need resumable checkpoints.

### Performance work this phase
Scoring started at **41s/job** and ended at **4.3s/job**. Gemini sheds load with transient 503s; falling back on the first one sent everything to Groq, whose free tier allows only 8k tokens/min. Fixed by retrying the primary before falling back, skipping it for 2 minutes once it is clearly down, and sizing `max_tokens` to the task (Groq counts it toward admission, so reserving a resume-sized reply for a short job score throttled the run).

## Still needed from the user
- **Telegram bot token + chat id** — alerts are built and tested but skip silently until these are set. Create a bot via @BotFather, message it once, then read the chat id from `https://api.telegram.org/bot<TOKEN>/getUpdates`.
- **Job-search preferences** (target roles, locations) to tune the default hunt query.
- **Company career pages** he's collected, for a possible later custom-scraper task.
