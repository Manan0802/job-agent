# 📘 PROJECT GUIDE — Job + Referral Finder AI Agent
### The complete A‑to‑Z explainer. Read this + the PRD + the code, and you understand everything.

> **Who this is for:** Anyone — even someone who has never seen this project (or barely codes).
> By the end you'll know **what** we're building, **why**, **how** the pieces fit, **which open‑source
> tools we reuse and what we take from each**, what's already built, and **how to run it**.
>
> **Reading order for a newcomer:**
> 1. This guide (the big picture) →
> 2. `job-referral-finder-PRD.md` (the original detailed product spec) →
> 3. `docs/superpowers/specs/2026-06-28-job-referral-finder-v2-design.md` (the optimized v2 design — what actually changed) →
> 4. `docs/superpowers/plans/2026-06-28-phase1-foundation.md` (the step‑by‑step build plan) →
> 5. `backend/` (the actual code).

---

## 1. What is this, in one breath?

A **personal AI career agent** that does the painful parts of job hunting automatically:

1. **Reads your resume once** → turns it into a structured profile (the "source of truth").
2. **Hunts jobs** across many job boards every few days → scores each one against your profile.
3. **Finds referral contacts** at the companies you like (a referral = ~10× better chance of an interview).
4. **Drafts personalized outreach** messages (LinkedIn DM / email) — *you approve before anything sends*.
5. **Tracks every application** in a simple pipeline (like a mini CRM) with follow‑up reminders.

It runs **locally on your machine**, stores everything **locally** (privacy first), and is built to cost
**~₹0/month** by using free tools and free AI models. Built for Manan (a software/AI engineer, student budget).

**The one‑line pitch:** *"Resume se job dhundhe, referral contacts identify kare — AI kare sab, tum sirf choose karo."*

---

## 2. Why does this exist? (the problem)

Job hunting in 2026 is broken:
- Applying cold gets **< 3%** response rate.
- A **referral** gets you ~**10×** the interview rate.
- Searching 10+ job boards by hand wastes hours every day.
- Generic copy‑paste outreach gets ignored.

So the equation we're changing: **smart search + warm intros + personalized outreach = far better outcomes.**

---

## 3. The 5 modules (plain language)

| # | Module | What it does | Think of it as… |
|---|---|---|---|
| 1 | **Resume Profiler** | PDF resume → clean structured JSON profile | Your "identity card" the whole app reads |
| 2 | **Job Hunter** | Scrapes many boards, de‑duplicates, scores each job vs you | A tireless assistant reading every job board |
| 3 | **Referral Finder** | Given a company, finds the warmest person who could refer you | A friend who "knows someone" everywhere |
| 4 | **Outreach Drafter** | Writes a personal message for each contact; **you approve** | A copywriter who drafts, never sends on its own |
| 5 | **Tracker / CRM** | Kanban board of all applications + follow‑up reminders | A whiteboard that never forgets |

Plus extras: **WhatsApp alerts** ("23 new jobs found"), and later (v2) **resume auto‑tailoring** per job and **interview prep**.

---

## 4. How it all fits together (architecture)

```
                ┌──────────────────────────┐
                │   React UI (browser)     │   ← you click here (built last, Phase 6)
                └────────────┬─────────────┘
                             │ HTTP
                ┌────────────▼─────────────┐
                │   FastAPI backend (Python)│   ← the brain's body
                │   + LangGraph orchestrator│   ← decides which module runs
                └────────────┬─────────────┘
        ┌───────────┬────────┼────────┬───────────┐
        ▼           ▼        ▼        ▼           ▼
   Resume      Job Hunter  Referral  Outreach   Tracker
   Profiler                Finder    Drafter
        │           │        │        │           │
        └───────────┴────────┴────────┴───────────┘
                             │
                  ┌──────────▼──────────┐
                  │   SQLite (local DB) │   ← all data stays on your machine
                  │  + profile.json     │
                  └─────────────────────┘
```

**The golden flow:**
`upload resume → profile.json` → `Job Hunter scrapes + scores jobs` → `you pick a job` →
`Referral Finder finds contacts` → `Outreach Drafter writes message → you approve → send` →
`Tracker logs it + reminds you to follow up`.

**Two clever cost tricks baked in:**
- **Local embeddings pre‑filter:** instead of paying an AI to score *every* job, we use a free local
  model to rank them by similarity, then only the AI judges the top ~15. (Cheaper + faster.)
- **Free‑first AI routing:** default to free models (Gemini/Groq); only escalate to a better model if quality demands it.

---

## 5. The Tool Ledger — every repo we researched, basic → max, and what we TAKE from each

This is the heart of the "don't reinvent the wheel" strategy. We **reuse** mature tools for commodity work,
and **build** custom only where our edge lives (scoring, warmth, orchestration).

Legend: ✅ USE · 🟨 MODIFY/LIFT · 📖 REFERENCE · 🔬 EVALUATE · ❌ AVOID/DEAD

### 5.1 Job scraping (getting the jobs)
| Tool | What it is | What we take | Verdict |
|---|---|---|---|
| **JobSpy** (`speedyapply/JobSpy`, 3.7k⭐, MIT) | One Python library that scrapes LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter, **Naukri**, Bayt at once → clean table | Our **main job‑ingestion engine**. Replaces ~5 hand‑written scrapers. India supported. | ✅ USE |
| **Remotive / RemoteOK / Arbeitnow / Himalayas APIs** | Free public APIs that list remote jobs (no scraping needed) | Free remote‑job coverage, called directly | ✅ USE |
| **`jwc20/waasuapi`** | A small scraper API for YC's `workatastartup.com` | YC startup jobs (JobSpy doesn't cover) | 🟨 MODIFY |
| **`ever-jobs/ever-jobs`** | Aggregator claiming 160+ sources, ships an MCP server | Might replace several custom scrapers — needs a coverage test | 🔬 EVALUATE |
| **JobFunnel** (`PaulMcInnis/JobFunnel`) | Older multi‑board scraper → spreadsheet, de‑dupes | De‑dup / spreadsheet patterns (reference only) | 📖 REFERENCE |

### 5.2 The hard, "walled" boards (Cloudflare / login‑protected)
| Tool | What it is | What we take | Verdict |
|---|---|---|---|
| **camofox-browser** (`jo-inc/camofox-browser`, MIT) | An **anti‑detection browser server**. Built on Camoufox (a Firefox fork that fakes its fingerprint at the C++ level so bot‑detectors like Cloudflare can't tell it's automated). Exposes a simple REST API; gives token‑efficient "accessibility snapshots" (~90% smaller than raw HTML); supports proxies, cookie import, search macros. | Our **stealth scraping engine** for boards that block normal scrapers — **Wellfound, Instahyre, Cutshort**, watchlist pages. Also an optional proxy layer for JobSpy's weak spot (LinkedIn). Runs as a tiny local sidecar service (~40MB). | ✅ USE |
| `daijro/camoufox` | The pure‑Python engine camofox wraps | Fallback if we want no server | 📖 REFERENCE |
| `nodriver`, `patchright`, `steel-browser` | Other stealth‑browser projects | Backup options | 📖 REFERENCE |

> ⚠️ **Safety rule for camofox:** use it for **public** Cloudflare‑walled boards only.
> **Do NOT** turn it into an authenticated LinkedIn auto‑scraper — that risks an account ban and breaks LinkedIn's rules.

### 5.3 Finding referral contacts (the highest‑value, trickiest part)
| Tool | What it is | What we take | Verdict |
|---|---|---|---|
| **SerpApi Google‑dork** (pattern lifted from our old app's `networking_agent.py`) | We ask Google (via SerpApi, 100 free searches/month) a query like `site:linkedin.com/in/ "Zepto" "SDE" "India"`. Google returns public LinkedIn profiles. | **Primary referral method.** Safe (public Google results, no LinkedIn login), cheap (free tier), already proven in our old project. | ✅ USE (lifted) |
| **Your own LinkedIn connections CSV** | LinkedIn lets you export your connections | 1st‑degree contacts at a company. (Note: LinkedIn now strips most emails from this export.) | ✅ USE |
| **Manual search URL fallback** | We just generate a LinkedIn search link for you to click | Zero‑cost backup when budgets run out | ✅ USE |
| **People Data Labs / Apollo** (free tiers) | People‑enrichment APIs (100 free/mo etc.) | Optional, only if SerpApi has gaps | 🔬 EVALUATE |
| **Proxycurl** | *Was* the popular LinkedIn data API the original PRD planned to use | — | ❌ **DEAD** (shut down July 2025 for illegal scraping). This is why the whole referral module had to be re‑designed. |

### 5.4 Resume parsing & tailoring
| Tool | What it is | What we take | Verdict |
|---|---|---|---|
| **markitdown** (`microsoft/markitdown`) | Converts PDF/DOCX → clean markdown text | Step 1 of reading your resume | ✅ USE |
| **career-ops** (`santifer/career-ops`) | A full Claude‑Code career plugin (job evaluation + CV tailoring at scale). Already installed as the `/career-ops` skill. | **v2 resume‑tailoring** (rewrite resume per job) — don't rebuild it; reference its job‑eval logic for our scorer | ✅ USE (v2) |
| `waygeance/AutoATS`, `JDAlchemy-ATSmaxxing` | Local‑LLM ATS resume tailoring projects | Patterns for v2 tailoring | 📖 REFERENCE |
| `pyresparser` | Old (2023) resume parser | — | ❌ stale, skip |

### 5.5 The AI brain (LLMs)
| Choice | What it is | Why |
|---|---|---|
| **Free‑first routing** (default Gemini Flash via OpenRouter + Groq free) | Cheap/free models do most of the work | Student budget → ~₹0 |
| **Escalate to a better Gemini model** only for high‑stakes tasks | Quality when it matters | Pay pennies only when needed |
| **NOT Claude (paid) by default** | The original PRD assumed paid Claude | We swapped to free to hit ₹0 |

### 5.6 Things we deliberately AVOID
| Tool / pattern | Why avoided |
|---|---|
| **AIHawk / ApplyPilot / EasyApplyBot / auto‑appliers** | Auto‑applying & auto‑DMing on LinkedIn gets accounts **banned** and invites **legal action** (the famous AIHawk repo was pulled by LinkedIn). We **never** auto‑apply or auto‑DM. Human approves everything. |
| **Proxycurl** | Dead (see 5.3). |
| Authenticated LinkedIn scraping at scale | Ban risk. We stay on public data. |

---

## 6. The big decisions, and WHY (so you understand the reasoning, not just the result)

1. **Reuse > rebuild (hybrid).** Commodity work (scraping, PDF parsing, DB) → grab a maintained library.
   Our edge (job scoring, referral warmth, orchestration) → build custom. Never hand‑write a LinkedIn
   scraper that 37 contributors already maintain in JobSpy.
2. **Proxycurl is dead → SerpApi Google‑dork instead.** Cheaper, safer, public data, already proven in our old code.
3. **Free‑first LLM, not paid Claude.** Hits the ₹0 budget. Quality escalation only when needed.
4. **Local embeddings pre‑filter before the LLM scores.** ~75% cost cut on scoring + it's faster.
5. **Human‑in‑the‑loop, always. No auto‑apply / auto‑DM.** Avoids bans and legal risk; keeps you in control.
6. **camofox for walled boards.** Turns "fragile scraper that gets blocked" into "anti‑detect engine + thin adapter."
7. **Everything local (SQLite + files).** Privacy, zero hosting cost.

> There is also a **predecessor project** (`Desktop/Ai-job`, a Streamlit app) that already did ~80% of
> this for free. We chose to **build fresh & cleaner**, but we **lift its proven ideas**: the SerpApi
> referral trick, resume tailoring, WhatsApp alerts, and free‑model usage.

---

## 7. Money: why this is ~₹0/month

| Piece | Cost |
|---|---|
| JobSpy + free remote APIs + camofox + custom scrapers | ₹0 |
| SerpApi (100 free searches/mo) for referrals | ₹0 |
| Free LLMs (Gemini Flash / Groq) | ₹0 |
| Local embeddings (sentence‑transformers) | ₹0 |
| SQLite, WhatsApp alerts | ₹0 |
| Occasional "better Gemini" escalation | ~₹0–50 |
| **Total** | **~₹0–150/mo** (budget cap was ₹500) |

---

## 8. What's actually BUILT so far (current status)

We are building **Phase 1 (Foundation)** with strict TDD (write test → see it fail → write code → see it pass → commit).

| Task | What it gives | Status |
|---|---|---|
| 1. Project scaffold + config | `.env` loader, folder structure, `requirements.txt` | ✅ done, tests pass |
| 2. SQLite database + profiles table | local DB + `ProfileRow` model | ✅ done, tests pass |
| 3. Free‑first LLM router | `complete(prompt, system, model)` — one place that talks to the AI | ✅ done, tests pass |
| 4. PDF → markdown | `pdf_to_markdown()` via markitdown | ⏳ next |
| 5. Profile schema + resume parser | markdown → validated `Profile` JSON | ⏳ |
| 6. FastAPI app + upload endpoint | `POST /resume/upload` returns your profile | ⏳ |
| 7. Profile edit endpoint | `PUT /resume/profile` | ⏳ |

**Phase 1 deliverable:** upload a PDF resume → get a clean structured profile, saved locally, editable.
This profile is the identity every later phase reads.

**The code lives in `backend/`:**
```
backend/
├── config.py          # reads .env (API keys, paths)
├── db/
│   ├── database.py     # SQLite connection + session
│   └── models.py       # ProfileRow table
├── llm/
│   └── router.py       # the single "talk to the AI" function
├── utils/              # (Phase 1 Task 4) pdf → markdown
├── schemas/            # (Task 5) the Profile shape
├── agents/             # (Task 5) the resume parser
├── services/           # (Task 6) save/load profile
└── api/routes/         # (Task 6) the web endpoints
tests/                  # one test file per piece (all pass)
```

---

## 9. How to RUN it (for a beginner, on a fresh machine)

> Requires **Python 3.10+** and **git**. Commands shown for Windows (PowerShell). On Mac/Linux,
> replace `.venv\Scripts\python.exe` with `.venv/bin/python`.

```bash
# 1. Clone
git clone https://github.com/Manan0802/job-agent
cd job-agent

# 2. Create a virtual environment (isolated Python) and activate it
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
# source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your secrets
#    Copy the example, then put your free OpenRouter key inside .env
copy .env.example .env        # Windows
# cp .env.example .env        # Mac/Linux
#    Get a free key at https://openrouter.ai  → paste into LLM_API_KEY in .env

# 5. Run the tests (everything should pass)
python -m pytest -v

# 6. Start the backend (once Phase 1 Task 6 is built)
uvicorn backend.main:app --reload
#    → open http://localhost:8000/docs  to see the API
#    → upload your resume PDF to POST /api/v1/resume/upload
```

> **Why a venv?** It keeps this project's Python packages separate from everything else on your computer.
> **Why `.env`?** That's where secret keys live. It is **never** committed to GitHub.

---

## 10. The roadmap (what comes after Phase 1)

| Phase | Builds | Key tools |
|---|---|---|
| **1. Foundation** ← *we are here* | Resume → profile, DB, AI router, API | markitdown, FastAPI, SQLite |
| **2. Job Hunter** | Scrape + score + alert | JobSpy, free remote APIs, camofox, embeddings, WhatsApp |
| **3. Referral Finder** | Find warm contacts | SerpApi dork, your CSV, warmth scoring |
| **4. Outreach Drafter** | Draft → you approve → send | free LLM, Gmail, WhatsApp |
| **5. Tracker CRM** | Kanban pipeline + reminders | React, SQLite |
| **6. Polish + UI** | The React front‑end, settings, logging | React + Tailwind |
| **v2** | Resume auto‑tailoring, interview prep | career-ops |

Each phase gets its own detailed step‑by‑step plan in `docs/superpowers/plans/` before it's built.

---

## 11. Glossary (for total beginners)

- **Scraping** — a program automatically reading a website to pull out data (here: job listings).
- **API** — a way for programs to talk to each other / fetch data without a browser.
- **LLM (Large Language Model)** — the AI (like Gemini/Claude) that reads and writes text.
- **Embeddings** — turning text into numbers so a computer can measure "how similar" two texts are
  (used to rank jobs cheaply without calling the AI).
- **FastAPI** — the Python framework that turns our code into a web server with endpoints.
- **SQLite** — a tiny database that's just a single file on your computer.
- **Pydantic** — a Python library that checks data has the right shape (e.g. "email is a string").
- **TDD (Test‑Driven Development)** — write the test first, watch it fail, then write code to pass it.
  Keeps the project reliable.
- **Referral** — when someone inside a company recommends you for a job (huge boost to your chances).
- **Human‑in‑the‑loop (HITL)** — the AI prepares things but a human approves before any real action.
- **Anti‑detect browser** — a browser that hides the fact it's automated, so anti‑bot systems don't block it.
- **Sidecar service** — a small helper program that runs alongside the main app (here: camofox).

---

## 12. The repos referenced, all in one place (quick links)

| Repo | URL |
|---|---|
| JobSpy | https://github.com/speedyapply/JobSpy |
| camofox-browser | https://github.com/jo-inc/camofox-browser |
| career-ops | https://github.com/santifer/career-ops |
| waasuapi (YC) | https://github.com/jwc20/waasuapi |
| ever-jobs | https://github.com/ever-jobs/ever-jobs |
| markitdown | https://github.com/microsoft/markitdown |
| JobFunnel | https://github.com/PaulMcInnis/JobFunnel |
| camoufox (engine) | https://github.com/daijro/camoufox |
| our predecessor (old) | https://github.com/Manan0802/Ai-job-portal |

Free APIs: Remotive (`remotive.com/api/remote-jobs`), RemoteOK (`remoteok.com/api`),
Arbeitnow (`arbeitnow.com/api`), Himalayas (`himalayas.app/api`), SerpApi (`serpapi.com`),
OpenRouter (`openrouter.ai`).

---

*This guide reflects the project's full understanding as of June 2026. If the code or specs change,
update this file so a newcomer always gets the truth.*
