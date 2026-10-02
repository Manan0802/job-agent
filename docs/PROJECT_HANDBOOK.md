# 📘 jba — The Complete Project Handbook

### Job + Referral Finder: an AI career agent that runs on your own laptop

> **Who this is for:** anyone who has to understand this project, from someone who has
> never written code to an engineer who has to change it tomorrow.
>
> **Written:** 2026-10-02, against commit `f7ec019` (the latest code commit on `main`).
> Facts about the code were checked against the code itself on that date; research findings and
> measurements come from the repo's docs, commit messages and the project's notes, with their own
> dates. The test suite was run on that date: **386 passed**.
>
> **This file replaces `docs/PROJECT_GUIDE.md` as the "start here" document.** That guide
> was written in June 2026, when only the first piece existed, and much of it is now out of
> date. See [§23 Old docs that are out of date](#23-old-docs-that-are-out-of-date).

---

## How to read this document

| If you are… | Read these sections | Time |
|---|---|---|
| **New to code, or just curious** | 1 → 2 → 3 → 4 → 15 → 26 (glossary) | 20 min |
| **Going to run or use the app** | 1 → 3 → 13 → 14 → 24 | 30 min |
| **Going to change the code** | Everything, especially 5 → 12, 16, 19, 21, 25 | 2–3 hours |
| **Joining the work** (how we research, decide, build, verify) | 17 → 18 → 19 → 21 | 45 min |
| **Reviewing decisions and research** | 15 → 16 → 17 → 18 → 22 | 45 min |

Words in **bold** the first time they appear are explained in the [glossary (§26)](#26-glossary).

---

## Table of contents

1. [What this is, in one minute](#1-what-this-is-in-one-minute)
2. [Why it exists (the problem)](#2-why-it-exists-the-problem)
3. [What it does, as a user sees it](#3-what-it-does-as-a-user-sees-it)
4. [The big picture (architecture)](#4-the-big-picture-architecture)
5. [Every folder and file at the top level](#5-every-folder-and-file-at-the-top-level)
6. [Inside `backend/`, file by file](#6-inside-backend-file-by-file)
7. [How each feature works inside](#7-how-each-feature-works-inside)
8. [The AI part: how the app talks to language models](#8-the-ai-part-how-the-app-talks-to-language-models)
9. [The database](#9-the-database)
10. [The API (every endpoint)](#10-the-api-every-endpoint)
11. [The frontend (what you see in the browser)](#11-the-frontend-what-you-see-in-the-browser)
12. [Configuration (`.env`), every setting explained](#12-configuration-env-every-setting-explained)
13. [How to run it, step by step](#13-how-to-run-it-step-by-step)
14. [Tests](#14-tests)
15. [The rules this project never breaks](#15-the-rules-this-project-never-breaks)
16. [Big decisions and why they were made](#16-big-decisions-and-why-they-were-made)
17. [The research behind the project](#17-the-research-behind-the-project)
18. [Field research: using the app for a real job search](#18-field-research-using-the-app-for-a-real-job-search)
19. [How we work](#19-how-we-work)
20. [History: how it was built, phase by phase](#20-history-how-it-was-built-phase-by-phase)
21. [Bugs that only showed up in real runs (the main lesson)](#21-bugs-that-only-showed-up-in-real-runs-the-main-lesson)
22. [What is missing, and what to do next](#22-what-is-missing-and-what-to-do-next)
23. [Old docs that are out of date](#23-old-docs-that-are-out-of-date)
24. [Privacy and safety: what never goes to GitHub](#24-privacy-and-safety-what-never-goes-to-github)
25. [How to extend it (recipes for developers)](#25-how-to-extend-it-recipes-for-developers)
26. [Glossary](#26-glossary)

---

## 1. What this is, in one minute

**jba** ("job agent") is a personal assistant for finding a job. You give it your resume once,
and it:

1. **Reads your resume** and turns it into a tidy list of your skills, jobs and education.
2. **Hunts for jobs** on about a dozen job sites at once, throws away duplicates, and ranks
   them by how well they fit you.
3. **Finds people who could refer you** at a company you like, and explains why each person
   is a good bet.
4. **Writes a short personal message** to each of those people. **You** read it, edit it, and
   send it yourself. The app never sends anything on its own.
5. **Tracks every application** on a board (Saved → Applied → Interview → Offer) and reminds you
   when something has gone quiet.
6. **Tells you how to tailor your resume** for one job, and **helps you prepare for an interview**,
   without ever suggesting you claim something your resume does not show.
7. **Hunts on a schedule** if you want it to, and messages you on Telegram only about jobs it
   has not already told you about.

Three things make it unusual:

- **It costs about ₹0 a month.** It uses free AI models, free job sources, and a small AI model
  that runs on your own laptop.
- **Everything stays on your laptop.** Your resume, your contacts, your messages are all in one
  file on your machine. Nothing is uploaded to a cloud service.
- **It is honest by design.** Some honesty rules are checked by code, not just requested from
  the AI, because asking the AI nicely turned out not to be enough (see §7.7).

| | |
|---|---|
| **GitHub repo** | `Manan0802/job-agent` |
| **Local folder** | `~/Desktop/manan/jba` |
| **Owner** | Manan (the app was built for Manan's own job search; the plan is to make it a product later) |
| **Languages** | Python (backend), TypeScript + React (frontend) |
| **Size** | ~6,000 lines of app code, 55 test files, 386 tests, 61 commits |
| **Built** | 2026-06-28 → 2026-07-29 |
| **Status** | Everything planned is built and working. See §22 for what is still missing. |

---

## 2. Why it exists (the problem)

Job hunting is slow and mostly wasted effort:

- Applying "cold" (just clicking Apply) gets a reply **less than 3%** of the time.
- Being **referred** by someone inside the company gets you an interview roughly **10× more often**.
- Checking 10+ job sites by hand takes hours every day.
- Generic copy-paste messages to strangers get ignored.

So the idea is: **search smarter + get warm introductions + write personal messages =
far better results**, with an AI doing the boring parts and the human making every real decision.

**The gap it fills.** When this was researched (July 2026), the other job-search tools —
Teal, Careerflow, Sonara, LazyApply, JobCopilot, Simplify, LoopCV, JobHire.AI — all compete on
resume tailoring and "apply to 500 jobs automatically". **None of them finds referral contacts
for the job seeker.** The only "AI + referrals" products found work for *employers*, not
candidates. That referral finder is this project's main differentiator.

One-line pitch from the original idea (in Hinglish): *"Resume se job dhundhe, referral contacts
identify kare — AI kare sab, tum sirf choose karo."* ("It finds jobs from your resume and spots
referral contacts. The AI does the work, you just choose.")

---

## 3. What it does, as a user sees it

You open `http://localhost:8000` in a browser. There are **six tabs** across the top, plus a
light/dark theme button.

### Step 0 — Upload your resume (first visit only)

Until you upload a resume, every tab shows one screen: **"Start with your resume"**. You press
**Choose a PDF**; it shows "Reading your resume…" while the AI reads it; then the app opens. Everything else in
the app reads this profile, which is why it comes first.

### Tab 1 — **Today** (the home screen)

Three boxes:
- **Needs a nudge** — applications you have not touched in a while (e.g. "Applied 8 days ago, no
  reply yet — send a follow-up?").
- **Drafts waiting for you** — messages the app wrote that you have not reviewed yet.
- **How it's going** — your numbers: how many applications, how many heard back, response rate,
  offers, and which job source has actually produced replies.

### Tab 2 — **Jobs**

- Type a role (e.g. "Backend Engineer") and a location, press **Hunt jobs**. It takes 1–4 minutes.
- You get a list of the **best matches**, each with a score out of 100, a sentence on why, the
  skills you already have (green) and the ones you lack ("needs Kubernetes").
- Each job card has buttons:
  - **Track** — put it on your Pipeline board.
  - **Open** — open the original job posting.
  - **Tailor** — "what should I change on my resume for this job?" It splits the answer into
    *what you already prove*, *what you have but buried*, and *what you genuinely lack*.
  - **Cover letter** — a short letter (under 200 words) built only from your real experience.

### Tab 3 — **Referrals**

- Type a company (and optionally a role), press **Find people**.
- You get a ranked list of people, each with a **warmth score from 1 to 5** and the reasons
  ("DTU alumni", "already a 1st-degree connection", "senior enough to refer (SDE-3)").
- **Draft message** writes a message to that person.
- There is always a **manual LinkedIn search link** too, which works even with no API keys at all.

### Tab 4 — **Outreach**

Every drafted message, for you to review:
- Edit the text → **Approve** → **Copy** the text → **Open profile** (for a LinkedIn message:
  opens their profile so you paste and send) or **Open email** (opens your own mail app with the
  message filled in) → **I sent it** once you have actually sent it.
- **Skip** if you decide not to send.
- Under a message you sent, "No reply yet?" → **Draft a nudge** writes a short, polite follow-up
  that does not repeat your whole pitch.

### Tab 5 — **Pipeline**

A **kanban board** with columns: Saved → Applied → Waiting on referral → Interview booked →
Interviewed → Offer. Each card has a button to move it forward ("Mark applied", "Got an
interview", "Interview done", "Got an offer", "Accept"); accepted and rejected applications are
listed separately below the board. While an interview is still ahead, a card
also offers **Interview prep**: 6–8 questions this specific job is likely to ask, which of your own
projects answers each, your weak spots, and good questions to ask them.

### Tab 6 — **Setup**

A checklist of everything the app can use, whether it is configured, what it unlocks, and where
to get it free. It also shows how many free searches are left this month and what the last
automatic hunt did. It never shows the keys themselves.

### The golden flow, end to end

```
Upload resume ─► Hunt jobs ─► pick a job ─► Find people at that company
      │                                            │
      │                                            ▼
      │                          Draft a message ─► you edit + approve ─► YOU send it
      │                                                                      │
      ▼                                                                      ▼
Tailor resume / cover letter            Track it on the Pipeline ─► reminders ─► interview prep
```

---

## 4. The big picture (architecture)

> **If you are new:** a web app usually has two halves. The **frontend** is what you see in the
> browser (buttons, lists). The **backend** is a program running on a computer that does the real
> work (talking to the AI, saving data) and answers the frontend's requests. Here, both halves run
> on your own laptop, started by one command.

```
                     ┌────────────────────────────────────────┐
  You, in a browser  │  Frontend: React app (6 tabs)          │   frontend/
  http://localhost:8000  built into frontend/dist/            │
                     └───────────────────┬────────────────────┘
                                         │ HTTP requests to /api/v1/...
                     ┌───────────────────▼────────────────────┐
                     │  Backend: FastAPI app (Python)         │   backend/main.py
                     │  • password gate (optional)            │   backend/middleware/
                     │  • API routes                          │   backend/api/routes/
                     │  • scheduler (optional, every N hours) │   backend/services/scheduler.py
                     └──┬──────────┬──────────┬───────────┬───┘
                        │          │          │           │
             ┌──────────▼──┐ ┌─────▼─────┐ ┌──▼────────┐ ┌▼──────────────┐
             │ "Agents"    │ │ Services  │ │ LLM router│ │ Local          │
             │ (AI steps + │ │ (scraping,│ │ Gemini ─► │ │ embedding model│
             │  LangGraph  │ │  storage, │ │ Groq      │ │ (bge-small,    │
             │  pipelines) │ │  scoring) │ │ fallback  │ │  runs offline) │
             └──────┬──────┘ └─────┬─────┘ └─────┬─────┘ └───────┬────────┘
                    └──────────────┴──────┬──────┴───────────────┘
                                          │
                     ┌────────────────────▼───────────────────┐
                     │  SQLite database: data/db/career_agent.db
                     │  + data/profile/profile.json            │
                     └─────────────────────────────────────────┘

  Outside the laptop (all free tiers, all called over the internet):
  Job boards (LinkedIn, Indeed, Glassdoor, Naukri, Google Jobs via JobSpy),
  Remotive, RemoteOK, Arbeitnow, Himalayas, Jobicy, YC jobs,
  Gemini + Groq (AI), Serper / SerpApi (Google search for referrals), Telegram (alerts)
```

**One command runs everything:** `uvicorn backend.main:app`. That starts the backend, which
also serves the already-built frontend files. There is no separate frontend server in normal use.

### The layers, from top to bottom

| Layer | Folder | What lives there | Analogy |
|---|---|---|---|
| Routes | `backend/api/routes/` | The URLs the frontend calls. Thin: check input, call an agent or service, return JSON. | The reception desk |
| Agents | `backend/agents/` | The steps that need the AI, and the two **LangGraph** pipelines. | The specialists |
| Services | `backend/services/` | Everything else: scraping, saving, scoring warmth, reminders, alerts. | The back office |
| LLM router | `backend/llm/` | The **only** place that talks to an AI model. | The one phone line to the AI |
| Schemas | `backend/schemas/` | The exact shape of data (profile, job score, draft…), checked by **Pydantic**. | The forms everyone fills in |
| Database | `backend/db/` | Table definitions and the connection to the SQLite file. | The filing cabinet |
| Utils | `backend/utils/` | Small helpers: PDF → text, dedup ids, name matching. | The toolbox |

---

## 5. Every folder and file at the top level

This is what you see in `~/Desktop/manan/jba`. The **Git?** column says whether it is saved in the
GitHub repo (✅) or exists only on this laptop (🚫).

```
jba/
├── backend/                 ✅  The Python server: all the logic
├── frontend/                ✅  The React website you click on
├── tests/                   ✅  386 automated checks (55 files)
├── docs/                    ✅  This handbook, design docs, phase write-ups, deploy notes
├── data/                    🚫  YOUR data: database, parsed resume, LinkedIn export
├── README.md                ✅  Short overview + quick start
├── job-referral-finder-PRD.md ✅ The original product idea (v1.0, partly outdated)
├── requirements.txt         ✅  The Python libraries the backend needs
├── share.sh                 ✅  Opens a public link to the app (for your phone)
├── .env.example             ✅  Template of every setting, with comments
├── .env                     🚫  Your real settings and API keys (SECRET)
├── .gitignore               ✅  The list of things Git must never upload
├── Manan_Kumar_Tech.pdf     🚫  The resume used for real testing (gitignored: *.pdf)
├── .venv/                   🚫  The project's private Python install
├── .pytest_cache/           🚫  Leftovers from running tests (safe to delete)
├── .claude  → symlink       🚫  Shortcut to the shared Claude Code toolkit
├── .mcp.json → symlink      🚫  Shortcut to the shared AI-tool server config
├── AGENTS.md                🚫  Instructions for the Codex AI tool (not part of the app)
├── .agents/                 🚫  Codex skill folder (not part of the app)
├── .codex/                  🚫  Codex tool config (not part of the app)
├── logs/                    🚫  Logs from AI developer tools (not part of the app)
└── .DS_Store                🚫  macOS junk file (ignored)
```

### 5.1 The folders that ARE the app

#### `backend/` — the server
All the logic. Detailed file by file in [§6](#6-inside-backend-file-by-file).

#### `frontend/` — the website
A React + TypeScript app. Detailed in [§11](#11-the-frontend-what-you-see-in-the-browser).
- `src/` is the source code you edit.
- `dist/` is the **built** version (created by `npm run build`). The backend serves this folder.
  It is not in Git; you rebuild it on each machine.
- `node_modules/` holds the JavaScript libraries (created by `npm install`, not in Git).
- `public/fonts/` holds the Geist fonts, bundled locally (see §11 for why).
- `frontend/README.md` is the untouched default template text from Vite. Ignore it.

#### `tests/` — the automated checks
One file per piece of the backend, named `test_<thing>.py`. Detailed in [§14](#14-tests).

#### `docs/` — the paper trail
| File | What it is | Up to date? |
|---|---|---|
| `docs/PROJECT_HANDBOOK.md` | This file — the "start here" document | ✅ Yes (2026-10-02) |
| `docs/DEPLOY.md` | Why the app runs on the laptop and not on Vercel/Render/etc. | ✅ Yes |
| `docs/PROJECT_GUIDE.md` | The June 2026 beginner guide | ⚠️ Partly stale (§23) |
| `docs/superpowers/specs/2026-06-28-job-referral-finder-v2-design.md` | The improved design after research (v2.1) | ⚠️ Plan, not what was built in every detail |
| `docs/superpowers/plans/2026-06-28-phase1-foundation.md` | Step-by-step plan for Phase 1 (800 lines, with code) | Historical |
| `docs/superpowers/plans/2026-07-13-phase2-job-hunter.md` | Phase 2 plan **and** write-up of what shipped | ✅ Yes |
| `docs/superpowers/plans/2026-07-22-phase3-referral-finder.md` | Phase 3 write-up | ✅ Yes |
| `docs/superpowers/plans/2026-07-27-phase4-outreach-drafter.md` | Phase 4 write-up | ✅ Yes |
| `docs/superpowers/plans/2026-07-27-phase5-tracker.md` | Phase 5 write-up | ✅ Yes |

The phase write-ups are the best "why" documents in the repo: each says what was built, what
deviated from the plan on purpose, and which bugs only appeared against real data.

> The folder name `superpowers` comes from the planning tool used to write these docs. It has no
> meaning for the app.

#### `data/` — your personal data (never uploaded)
| Path | What is in it |
|---|---|
| `data/db/career_agent.db` | **The whole database**, one SQLite file. On 2026-10-02 it held 68 jobs (54 scored by the AI), 17 referral contacts, 2 outreach messages, 4 tracked applications. Of the 68 jobs, 31 came from the two real job searches described in §18 (`manual-hunt-2026-08-06`: 13, saved unscored; `intern-hunt-2026-08-21`: 18) and the rest from the app's own hunts (Arbeitnow 14, YC 7, Jobicy 6, LinkedIn 4, Himalayas 3, Indeed 2, RemoteOK 1). |
| `data/profile/profile.json` | Your parsed resume, as JSON. (Also stored inside the database.) |
| `data/connections/Connections.csv` | Your LinkedIn connections export. **The file there now is small sample/test data**, not a real export. |

Delete `data/db/career_agent.db` and the app starts fresh (empty). Back it up if it matters.

### 5.2 The files at the root

| File | What it does |
|---|---|
| `README.md` | Short overview, quick start, feature status, the three enforced rules. Accurate. |
| `job-referral-finder-PRD.md` | **PRD** = Product Requirements Document. The original 1,600-line vision (v1.0). It has a "READ FIRST" banner because a lot changed (§23). Still useful for the *intent* behind each module. |
| `requirements.txt` | Python libraries: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `pydantic-settings`, `python-dotenv`, `python-multipart`, `markitdown`, `openai`, `pytest`, `httpx`, `python-jobspy`, `pandas`, `langgraph`, `sentence-transformers`. |
| `share.sh` | Starts the app and opens a free Cloudflare tunnel so you can open it from your phone. Refuses to run without `APP_PASSWORD`. See §13.5. |
| `.env.example` | Every setting with a comment explaining it. Copy it to `.env` and fill in. |
| `.env` | **Your secrets** (API keys, password). Gitignored. Never share or commit it. |
| `.gitignore` | Keeps out: `.env`, `.venv/`, `data/db/*.db`, `data/profile/*.json`, `data/resume/*`, `data/connections/*`, every `*.pdf` and `*.csv`, caches, `.DS_Store`, and the `.claude` / `.mcp.json` symlinks. |
| `Manan_Kumar_Tech.pdf` | The real resume used to test the app against real data. Gitignored. |

### 5.3 The folders that are NOT part of the app (developer tooling)

These exist because of the AI coding tools used to build the project. The app does not read
any of them. You can ignore them unless you use the same tools.

| Item | What it is |
|---|---|
| `.claude` → `../claude-transfer/.claude` | A **symlink** (a shortcut) to a shared toolkit used by the Claude Code assistant across all projects in `~/Desktop/manan/`: skills, agent definitions, a "router" that suggests tools, and per-project rules. Gitignored. |
| `.mcp.json` → `../claude-transfer/.mcp.json` | A symlink to the shared list of **MCP** servers (plug-in tools for AI assistants). Gitignored. |
| `AGENTS.md`, `.agents/skills/manan-arsenal/`, `.codex/config.toml` | Added on **2026-10-02** by an install script for the **Codex** AI tool. They point Codex at the same shared toolkit (`~/Desktop/manan/.codex-arsenal/`). Not in Git (currently shown as untracked). |
| `logs/` | Log files written by those AI tools (e.g. a Puppeteer browser-tool log). Not app logs. |
| `.venv/` | The project's own Python 3.12 install with all libraries. Created by `python3 -m venv .venv`. |
| `.pytest_cache/` | Created automatically when tests run. Safe to delete. |

> **Note for a helper:** if you commit, don't accidentally add `AGENTS.md`, `.agents/`, `.codex/`
> or `logs/`. They are local tooling, not product code. (They are not in `.gitignore` yet, so
> `git add .` *would* pick them up. Use `git add <specific files>`.)

### 5.4 Where else knowledge about this project lives (outside the repo)

- **Obsidian notes:** `~/Desktop/manan/manan-memory/Projects/jba.md` and the folder
  `Projects/jba/` (`jba-architecture.md`, `jba-decisions.md`, `jba-gotchas.md`,
  `jba-running-it.md`, `jba-job-search-log.md`). Written in Hinglish. They match this handbook;
  `jba-job-search-log.md` is the record of the first real job search done with the app's help
  (personal; not in the repo).

---

## 6. Inside `backend/`, file by file

> **If you are new:** every `.py` file is one Python "module". `__init__.py` files are empty
> markers that tell Python "this folder is a package". You can skip them.

### 6.1 Top level

| File | Lines | What it does |
|---|---|---|
| `main.py` | 72 | **The entry point.** Creates the FastAPI app, adds the password gate, plugs in all 8 route files, creates the database tables at startup, starts the scheduler if it is turned on, turns "AI model busy" errors into a friendly 503 message, exposes `/health`, and **last of all** serves the built frontend (last, so the website can never hide an API URL). |
| `config.py` | 49 | Reads `.env` into a `Settings` object (via `pydantic-settings`). Every setting has a safe default. `get_settings()` is cached so the file is read once. |

### 6.2 `backend/agents/` — the steps that use the AI

> "Agent" here just means "a step where the AI does the thinking". Each one builds a prompt,
> calls the LLM router, checks the answer's shape, and **retries up to 3 times** because AI
> output is not always well-formed.

| File | What it does |
|---|---|
| `resume_profiler.py` | PDF → text (via markitdown) → AI → a validated `Profile`. Uses the **heavy** model (`LLM_MODEL_HEAVY`) because it is rare and harder. The prompt spells out the exact JSON shape, because when it only listed the field names, the model returned `skills` in the wrong shape. |
| `job_hunter_graph.py` | **The job hunt pipeline**, built with LangGraph: `ingest → dedup → prefilter → score → save → notify`. Details in §7.2. |
| `job_scorer.py` | Asks the AI to score one job 0–100 against your profile, with reasoning, matched skills and missing skills. Scores a shortlist "probe-first, then fan out" (§7.2). |
| `referral_finder_graph.py` | **The referral pipeline**, also LangGraph: `gather → merge → score → save`. Details in §7.4. |
| `outreach_drafter.py` | Writes a message to one contact. Six message types, a strict tone/honesty prompt, special rules for follow-ups. Details in §7.5. |
| `resume_tailor.py` | "How should I change my resume for this job?" and "write a cover letter". Runs the code-level honesty check on every suggestion. Details in §7.7. |
| `interview_prep.py` | 6–8 likely questions for one job, each tied to your own experience, plus weak spots and questions to ask them. Details in §7.8. |
| `grounding.py` | Shared helpers used by tailoring and interview prep: renders your resume and the job as text, and contains **the honesty check** (`unsupported_terms`). Details in §7.7. |

### 6.3 `backend/services/` — everything that is not the AI

| File | What it does |
|---|---|
| `job_sources/jobspy_adapter.py` | Calls the **JobSpy** library to scrape LinkedIn, Indeed, Glassdoor, Naukri and Google Jobs at once (public listings, no login), and converts the results into the app's job format. |
| `job_sources/remote_apis.py` | Five free public job APIs: Remotive, RemoteOK, Arbeitnow, Himalayas, Jobicy. No keys, no login. If one is down, it is skipped. |
| `job_sources/yc_adapter.py` | Y Combinator startup jobs. Reads the JSON that YC embeds inside its public job pages. No login, no browser. |
| `embeddings.py` | The **local** AI model (`BAAI/bge-small-en-v1.5`) that turns text into numbers, so jobs can be ranked by similarity to your profile for free, offline. |
| `job_store.py` | Saves jobs to the database (an **upsert**: update if it exists, insert if not). Never wipes out an AI score with "nothing". |
| `new_matches.py` | For scheduled hunts: picks strong jobs you have **not** been told about yet, and marks them as told. |
| `scheduler.py` | Runs a hunt every N hours in the background, if turned on. Never crashes. Remembers what the last run did for the Setup tab. |
| `notify.py` | Sends a Telegram message. If no Telegram token is set, it quietly does nothing. |
| `profile_store.py` | Saves/loads your profile (to both `profile.json` and the database). |
| `connections_csv.py` | Reads your LinkedIn connections export and finds people at a given company. |
| `people_search.py` | Searches Google (through Serper or SerpApi) for public LinkedIn profiles of people at a company. |
| `api_budget.py` | Counts how many paid-API calls were used this month, per provider, and refuses to go over the free limit. |
| `warmth.py` | Scores each contact 1–5 for "how likely to refer you", with reasons. |
| `contact_store.py` | Saves/loads referral contacts. Never resets someone you already messaged back to "pending". |
| `message_store.py` | Saves outreach messages and moves them through draft → approved → sent / skipped. |
| `send_links.py` | Builds the "hand-off": a `mailto:` link or a profile link + the text to paste. **Contains no sending code, on purpose** (a test enforces this). |
| `application_store.py` | The pipeline board: track a job, move it between stages, add notes, record an offer. Sets follow-up dates. |
| `tracker_insights.py` | Overdue reminders and statistics (response rate, best source…). |

### 6.4 `backend/api/routes/` — the URLs

| File | URL prefix | Purpose |
|---|---|---|
| `resume.py` | `/api/v1/resume` | Upload a PDF, get/edit the profile |
| `jobs.py` | `/api/v1/jobs` | Run a hunt, list saved jobs |
| `referrals.py` | `/api/v1/referrals` | Find people at a company, list contacts |
| `outreach.py` | `/api/v1/outreach` | Draft, edit, approve, mark sent, skip, follow up |
| `applications.py` | `/api/v1/applications` | Track jobs, move stages, notes, offers, reminders, stats |
| `tailor.py` | `/api/v1/tailor` | Fit analysis and cover letter for one job |
| `interview.py` | `/api/v1/interview` | Interview prep for one job |
| `setup.py` | `/api/v1/setup` | What is configured (never returns a key) |

Full list of endpoints in [§10](#10-the-api-every-endpoint).

### 6.5 The rest

| File | What it does |
|---|---|
| `llm/router.py` | The only door to the AI. Gemini first, Groq as backup, with retries and a "circuit breaker". §8. |
| `llm/errors.py` | `ModelUnavailable`: "the AI was busy or gave junk after retries" — different from a bug in our code. |
| `middleware/auth.py` | The optional password gate (HTTP Basic auth). §7.10. |
| `db/database.py` | Opens the SQLite file, creates tables, **adds missing columns to an older database**, hands out sessions. §9. |
| `db/models.py` | The six tables, as Python classes. §9. |
| `schemas/profile.py` | Shape of a profile: personal, skills (5 lists), experience, education, keywords. |
| `schemas/job_score.py` | Shape of a job score: score 0–100, reasoning, matched_skills, missing_skills. |
| `schemas/outreach.py` | Shape of a message draft. |
| `schemas/tailoring.py` | Shape of a fit analysis: verdict, strengths, buried, missing, suggestions. |
| `utils/pdf_parser.py` | 7 lines: PDF → markdown text with Microsoft's `markitdown`. |
| `utils/dedup.py` | Makes stable ids for jobs and contacts so duplicates collapse into one. |
| `utils/text.py` | Matches messy real-world names: company suffixes, university acronyms, whole-word skill matching. Exists because of four real bugs (§21). |

---

## 7. How each feature works inside

### 7.1 Resume → profile

```
PDF ─► markitdown ─► plain text ─► AI (heavy model) ─► JSON ─► Pydantic checks shape ─► save
                                         ▲                           │
                                         └──── retry (up to 3×) ◄────┘ if broken
```

- The profile has: **personal** (name, email, phone, location, LinkedIn, GitHub), **skills** split
  into five lists (languages, frameworks, ai_ml, tools, databases), **experience** (company, role,
  months, highlights, tech used), **education** (institution, degree, field, year), **keywords**.
- It is saved to `data/profile/profile.json` **and** to the `profiles` table (always row id 1;
  there is one user).
- You can edit it through `PUT /api/v1/resume/profile`.
- The prompt says "do not invent data; use null when the resume does not state it".

### 7.2 The job hunt (the core pipeline)

```
            ┌─ JobSpy: LinkedIn, Indeed, Glassdoor, Naukri, Google ─┐
 INGEST ────┼─ 5 free remote APIs                                     ├─► ~500 raw jobs
 (parallel) └─ YC startup jobs                                       ─┘
                                     │
 DEDUP      same company + same title = same job  ───────────────────► ~490 unique
                                     │
 PREFILTER  local embedding model ranks all of them by similarity
            to your profile (free, offline)  ────────────────────────► top 10–15
                                     │
 SCORE      AI scores only the shortlist 0–100 with reasons  ────────► scored list
                                     │
 SAVE       upsert into the jobs table
                                     │
 NOTIFY     Telegram message (skipped if no token, or on scheduled runs)
```

**Ingest.** The three source groups run at the same time (a thread pool). If one fails — Naukri
often answers `406 recaptcha required`, Glassdoor sometimes `400` — it is logged and skipped. A
blocked source costs coverage, never the whole run.

| Source | How | Settings in code |
|---|---|---|
| JobSpy | Python library `python-jobspy`, public search pages | sites: linkedin, indeed, glassdoor, naukri, google · 20 results per site · posted in the last 72 hours · Indeed country India |
| Remotive, RemoteOK, Arbeitnow, Himalayas, Jobicy | Plain HTTP `GET` of free JSON APIs | none needed |
| YC | Fetches 4 public pages (`/jobs`, `/jobs/role/eng`, `/jobs/role/design`, `/jobs/location/remote`) and reads the job JSON embedded in the HTML | Builds a description from structured fields (role, experience, salary, equity, visa, batch) |

Every source is converted into the same shape: `title, company, location, url, description,
date_posted, source_engine, fetched_at`. `source_engine` records where it came from, e.g.
`jobspy:linkedin`, `remotive`, `yc`.

**Dedup.** Each job gets an id = **SHA-256 hash of "company|title"**, after lower-casing and
squashing spaces. Same id = same job, keep the first. The date is deliberately *not* part of the
key, because every source writes dates differently (ISO, ISO+time, raw numbers), so including it
would mean nothing ever matched across sources.

**Prefilter (the money-saving step).** Scoring 500 jobs with the AI is impossible on a free tier
(Gemini's free tier is about 20 requests a day per model). So:
1. Your profile (skills + roles + tech + degrees + keywords; *not* your contact details) is turned
   into a vector of numbers by the local model.
2. Each job (title + company + location + first 1,000 characters of description) is turned into
   a vector too.
3. **Cosine similarity** (how close two vectors point) ranks every job.
4. Only the top N go to the AI: default **15** from the Jobs tab, **10** for scheduled hunts.

The model `BAAI/bge-small-en-v1.5` downloads once (~130 MB) and then runs offline on the CPU.

**Score.** For each shortlisted job the AI gets a short candidate summary and the first 2,000
characters of the job description, and must return JSON: `score`, `reasoning`, `matched_skills`,
`missing_skills`. "80+ means a strong fit worth applying to today; below 40 means a poor fit."
- **Probe first, then fan out.** It scores the first job alone. If the main model (Gemini) is
  healthy, it scores the rest **5 at a time**; if the app has fallen back to Groq, **1 at a time**.
  Measured: going wide on the fallback made a real run *slower* (13.5 s/job vs 4.3 s/job), because
  Groq's limit is tokens per minute, not requests.
- A job that cannot be scored keeps its place with no score rather than throwing away the run.
- Results are sorted best first.

**Save.** Upsert. A later run that only pre-filtered a job never erases the AI score an earlier
run already paid for.

**Notify.** If Telegram is configured, sends "N strong matches out of M jobs found" with up to 10
jobs, scores and links.

**Real numbers from live runs:** 486 unique jobs → ML Engineer at 88/100 in ~100 s (Phase 2);
553 jobs found in a scheduled hunt (post-plan).

### 7.3 Scheduled hunting (what makes it an "agent")

- **Off by default.** It turns on only when **both** `HUNT_SEARCH_TERM` is set and
  `HUNT_EVERY_HOURS` > 0. A server that spends your free AI quota without being asked is a bug.
- **Waits first.** It does not hunt at startup; it waits one full interval. Restarting the server
  (which happens on every code reload during development) is not a request to hunt.
- **Runs in a background thread**, so the website stays responsive during a multi-minute hunt.
- **Never crashes.** If a hunt fails, it records the error and tries again next interval.
- **Alerts only on new matches.** After each hunt, `claim_new_matches(ALERT_MIN_SCORE)` picks jobs
  that scored at least 70 (default) **and** have not been alerted at this score or higher. Each
  job remembers `alerted_at` and `alerted_score`, so a job that later re-scores *higher* can still
  be announced. Jobs are marked as "told" *before* sending: losing one alert is better than an
  alert loop that repeats forever.
- **Verified live:** run 1 found 553 jobs → 2 new matches; run 2 (same jobs) → **0 new, no
  message**. Exactly as designed.
- The Setup tab shows the last run: when, how many found, how many new, whether an alert went out.

### 7.4 The referral finder

```
 GATHER ─┬─ your LinkedIn connections CSV (1st-degree, free)
         └─ Google search for public LinkedIn profiles (2nd-degree, metered)
 MERGE  ─── same person from both? keep one, keep "1st-degree"
 SCORE  ─── warmth 1–5 + reasons for each person
 SAVE   ─── upsert contacts + build a manual LinkedIn search link
```

**Source 1: your LinkedIn export** (`connections_csv.py`). LinkedIn lets you download your own
connections (Settings & Privacy → Data Privacy → Get a copy of your data → Connections). The
parser skips the notes LinkedIn puts above the header row, and matches employers loosely
("Zepto" matches "Zepto Marketplace Private Limited"). These people are **1st-degree** — you
actually know them.

**Source 2: Google search** (`people_search.py`). A query like
`site:linkedin.com/in "Zepto" "SDE" "New Delhi"` sent through **Serper** (2,500 free searches,
one-time grant) or, when that is gone, **SerpApi** (250 free per month, forever). Each search is
counted in the `api_budget` table first; when both budgets are used up it quietly returns nothing.
From each result it extracts **name, role (sometimes), current company, profile URL**. That is all
Google reliably shows since LinkedIn hid headlines and work history from search engines in 2024.
No LinkedIn login and no LinkedIn API are ever used. These people are **2nd-degree** (strangers).

**Source 3: the manual link** — always given. A LinkedIn people-search URL with the company,
role and your college, for you to click. Free and always works.

**Merge.** A person's id = hash of their profile URL, or name+company when the URL is missing
(LinkedIn's export often omits it). If someone appears in both sources, they become one record
and keep their 1st-degree status.

**Warmth score** (`warmth.py`) — how likely is this person to refer you?

| Situation | Base score |
|---|---|
| Same college **and** already a connection | **5** |
| Same college (alumni) | **4** |
| Already a connection | **3** |
| Stranger | **1** |

Then adjustments (never above 5):
- **+1** if their title is senior (SDE-2/3, Senior, Staff, Principal, Lead, Manager, Head, Director,
  Architect, VP) — they can actually approve a referral.
- **at least 2** if a stranger shares part of your tech stack.
- **+1** if they also worked at one of your past employers.
- "based in your city" is added as a reason (no points).

**Nothing is hard-coded to one person.** The original PRD's table said "DTU alumni", "Delhi-based".
The code takes your college, city, past employers and skills from **your** parsed profile, so it
works for any user. Every score comes with its reasons, because you decide who to message.

### 7.5 The outreach drafter

**Six message types** (`outreach_drafter.py`):

| Type | Channel | Max words | Used when |
|---|---|---|---|
| `alumni_dm` | LinkedIn DM | 180 | The reasons include "alumni" — opens on the shared college, then asks for the referral |
| `referral_request` | LinkedIn DM | 200 | A 1st-degree connection |
| `cold_intro` | LinkedIn DM | 150 | A stranger |
| `email_outreach` | Email | 250 | When chosen explicitly |
| `followup` | LinkedIn DM | 90 | A sent message got no reply |
| `thank_you` | LinkedIn DM | 90 | Someone referred you |

**What the prompt insists on:** warm, not corporate; never flattering; open with **one** genuine
shared point (taken from the warmth reasons); introduce yourself in at most two sentences; make
the ask specific; give an easy out ("no pressure"); end with one concrete next step; no resume in
a first message; a DM is a chat, so no "Best regards" sign-off; and **use only facts from your
profile — never invent an employer, title, project or skill.**

If you pass a `job_id`, the real job title and description are included. (Without it, a real draft
once offered to apply for "SDE-1" when the role was SDE-2.)

**Follow-ups** get extra rules: do not re-introduce yourself, do not repeat the pitch, two or three
sentences. (A real follow-up draft re-introduced the sender in 58 words; after the fix, 24.)

**Message lifecycle** (`message_store.py`):

```
          redraft replaces an un-sent draft (never a sent one)
                  │
   ┌────────┐  approve  ┌──────────┐  you send it yourself,  ┌──────┐
   │ draft  │──────────►│ approved │────── then "Mark sent" ►│ sent │──► follow-up = a NEW draft
   └────────┘◄──────────└──────────┘                          └──────┘
       │      editing an approved message sends it back to draft
       └──── skip ───► skipped
```

The contact's own status follows along: `pending` → `drafted` → `sent` or `skipped`.

**The hand-off** (`send_links.py`): for an email with a known address, a `mailto:` link opens
**your** mail app with subject and body filled in. For a LinkedIn DM, you get the profile URL and
the text to paste. Either way, **you press send**. A test fails if anyone ever adds a function
named `send_*`, `auto_*` or `post_*` to this module.

### 7.6 The application tracker

**Stages:** `saved → applied → referral_pending → interview_scheduled → interview_done →
offer_received → accepted | rejected`.

Every stage change sets a follow-up date:

| Stage | Nudge after | The reminder says |
|---|---|---|
| saved | 3 days | You saved this but never applied — still interested? |
| applied | 6 days | No reply yet — send a follow-up? |
| referral_pending | 5 days | Your referrer hasn't come back — worth a gentle nudge? |
| interview_scheduled | 1 day | Interview coming up — confirm the slot and prep. |
| interview_done | 2 days | Send a thank-you note while it's still fresh. |
| offer_received | 3 days | They're waiting on your answer — decide on this offer. |
| accepted / rejected | never | (finished) |

Reaching `applied`, `interview_scheduled` or `offer_received` stamps that date the first time.
Tracking a job you already track returns the existing card (it never rewinds progress). Notes are
appended with a date, never overwritten. Offers store an amount and a currency (default INR).

**Statistics** (`tracker_insights.py`), and two deliberate judgement calls:
- **A rejection counts as a response.** You mark something rejected when they actually replied; a
  company that ghosted you stays in `applied`. Counting rejections as silence would make the
  response rate look worse than reality.
- **Jobs only ever saved are left out of the rate.** Never applying is not the same as being
  ignored.
- "Best source" must have produced at least one reply. (Before this rule it once showed
  "best: arbeitnow" next to a 0% response rate.)

### 7.7 Resume tailoring and cover letters — and the honesty check

**Fit analysis** (`resume_tailor.py`) returns:
- `verdict` — one honest sentence on the fit;
- `strengths` — what already matches;
- **`buried`** — what you **have** but your resume hides (worth rewriting for);
- **`missing`** — what you **genuinely lack** (worth knowing, not worth faking);
- up to **4** concrete `suggestions` (section, change, why).

It deliberately does **not** generate a new resume file. Your resume lives in whatever tool you
made it in; what you need is which lines to change and why.

**Cover letter:** under 200 words, opens on the single most relevant thing you have actually done,
no flattery.

**The honesty check** (`grounding.py → unsupported_terms`). The prompt already said "never invent
experience". A live run still suggested "Experienced in building distributed, scalable backend
systems" for a resume that never says "distributed", and in another run told the user to claim
Kubernetes right after listing it as missing. So **code** now checks every suggestion and every
cover letter:

> A word is flagged if it appears in the **job posting**, does **not** appear anywhere in your
> **resume**, is not the company/title name, and is not a harmless generic word ("add", "team",
> "build"…). Flagged words are shown next to the suggestion as a warning.

Two refinements, both found in live runs:
- **Admissions are not claims.** "Acknowledge the lack of Java on the resume" is good advice, not a
  boast. The check works sentence-part by sentence-part (split on `.`, `;`, "but", "although"…),
  so "lack of Java, **but** emphasise Kubernetes" skips Java and still catches Kubernetes.
- **Two strictness levels.** Tailoring uses the wide rule (a lowercase word like "distributed" *is*
  the claim). Interview prep uses `named_only=True`, which only checks capitalised technology names,
  because the wide rule flagged "about", "high" and "designing" in five of six answers — all false
  alarms. A warning that is usually wrong teaches people to ignore warnings.

### 7.8 Interview prep

`interview_prep.py` returns: `role_focus` (what the interview is really testing), 6–8
`questions` each with `why` (what in the posting makes it likely) and `answer_from` (which of
**your** projects answers it), `weak_spots` (what they want that you lack, so you can prepare an
honest answer), and `ask_them` (good questions for the interviewer). The honesty check runs on
every `answer_from` in `named_only` mode.

**Where it appears:** only on the **Pipeline** board, and only while an interview is still ahead
(`applied`, `referral_pending`, `interview_scheduled`) and the card is linked to a job. Offering it
for 500 un-applied jobs would be noise and burn the free quota; offering it after the interview is
too late. It opens in a native browser `<dialog>`.

### 7.9 Setup status

`GET /api/v1/setup` reports seven items — AI model (required), backup model, referral search,
LinkedIn connections, password, scheduled hunting, job alerts — each with `configured`, what it
`unlocks`, and `how` to get it. It shows remaining Serper/SerpApi searches and the last scheduled
hunt. **It never returns a key**, only whether one exists.

### 7.10 Password gate and sharing

- `middleware/auth.py`: if `APP_PASSWORD` is empty, there is no gate (fine on `localhost`). If
  set, every request needs **HTTP Basic auth**; the browser shows its own login box. The username
  is ignored (there is one user). `/health` stays open so uptime checks work without a secret.
  Passwords are compared with `secrets.compare_digest` (timing-safe).
- `share.sh`: refuses to run without `APP_PASSWORD`, checks `cloudflared` is installed, starts the
  app on port 8000, waits for `/health`, then opens a free **Cloudflare quick tunnel** and prints a
  `https://<random>.trycloudflare.com` URL. The URL changes every run. Ctrl+C stops both.

---

## 8. The AI part: how the app talks to language models

**Everything goes through one function:** `complete(prompt, system, model, max_tokens)` in
`backend/llm/router.py`. No other file knows which AI provider is used.

### 8.1 Free-first, with a backup

```
complete() ─► Gemini (primary) ── up to 3 tries, waits 2 s then 4 s between ──► answer
                    │
                    └─ failed / busy / out of daily quota
                                │
                                ▼
                 Groq  openai/gpt-oss-20b  (fallback) ──► answer
```

- **Primary:** Google **Gemini**, called through Google's OpenAI-compatible endpoint, using the
  `openai` Python library (that is why `openai` is in `requirements.txt`; no OpenAI service is used).
- **Fallback:** **Groq**, model `openai/gpt-oss-20b`, also free.
- **Two Gemini models with separate daily budgets:**
  - `LLM_MODEL=gemini-3.5-flash-lite` — the volume work (one score per job, drafts, prep).
  - `LLM_MODEL_HEAVY=gemini-3.5-flash` — resume parsing only (rare, harder).

### 8.2 Why it is built this way (the measured facts)

| Fact (measured against the live API on 2026-07-28) | What the code does about it |
|---|---|
| Gemini's free tier is **20 requests per day, per model** (Google's quota id: `GenerateRequestsPerDayPerProjectPerModel-FreeTier`). Not documented; found by testing. | Two models → two budgets. The circuit breaker is kept **per model**, so the cheap model running dry does not block the heavy one. |
| Gemini often answers "503, busy" for a few minutes. | Retry the primary 3 times before falling back. After 3 failures, skip it for **2 minutes** (the **circuit breaker**). |
| A "daily quota used up" 429 will not clear in minutes. | No retries at all for that; go straight to Groq and skip Gemini for **30 minutes**. |
| The `openai` library secretly retries on its own. Its 3 × our 3 = 9 requests per call, against a 20-a-day budget. | Clients are created with `max_retries=0`. Retrying is the router's job. |
| Groq's free limit is **8,000 tokens per minute**, and it counts the `max_tokens` you *reserve*, not just what you use. | Every task asks for only what it needs: score 1,200 · draft 1,500 · cover letter 1,500 · fit analysis 3,000 · interview prep 3,000. Defaults: 8,000 (Gemini), 6,000 (Groq). |
| Without `max_tokens`, Groq cut the resume JSON off mid-string. | Always set. |

**Measured effect:** 6 real jobs scored in **3 s** total on flash-lite, against ~5 s *per job* on the
Groq fallback. Earlier in the project, scoring went from **41 s/job → 4.3 s/job** after the retry
and breaker work.

### 8.3 When the AI fails anyway

Every agent retries 3 times. If it still fails, it raises `ModelUnavailable`, and `main.py` turns
that into HTTP **503** with: *"The free AI model is busy right now and couldn't finish that. Give
it a minute and try again."* — instead of a scary 500 error.

---

## 9. The database

One **SQLite** file: `data/db/career_agent.db`. No database server to install. **SQLAlchemy 2**
maps tables to Python classes in `backend/db/models.py`.

| Table | One row = | Key columns |
|---|---|---|
| `profiles` | your profile (always id 1) | `data` (the profile as JSON text), `embedding`, `updated_at` |
| `jobs` | one job posting | `id` (hash of company+title), `title`, `company`, `location`, `url`, `description`, `source_engine`, `embedding`, `prefilter_score`, `llm_score`, `llm_breakdown` (JSON), `fetched_at`, `alerted_at`, `alerted_score` |
| `referral_contacts` | one person who could refer you | `id`, `target_company`, `name`, `linkedin_url`, `current_role`, `current_company`, `location`, `degree_type` (1st/2nd), `warmth_score` (1–5), `warmth_reasons` (JSON list), `email`, `source` (csv/search), `outreach_status` |
| `outreach_messages` | one message | `id`, `contact_id`, `job_id`, `message_type`, `channel`, `subject`, `body`, `tone`, `personalization`, `status`, `created_at`, `sent_at` |
| `applications` | one job you are pursuing | `id`, `job_id`, `company_name`, `role_title`, `apply_url`, `source`, `applied_via` (direct/referral/cold), `referral_contact_id`, `status`, `applied_date`, `interview_date`, `offer_date`, `offer_amount`, `offer_currency`, `notes`, `follow_up_due`, `created_at`, `last_updated` |
| `api_budget` | one paid provider's usage this month | `provider` (serper/serpapi), `month` (YYYY-MM), `calls_used`, `monthly_cap` |

**Things worth knowing:**
- **Tables are created automatically** at startup (`init_db()`). There is no migration tool.
- **Missing columns are added automatically.** SQLAlchemy's `create_all()` creates missing *tables*
  but never missing *columns*. When `alerted_at` was added, every test passed (tests build fresh
  databases) but the real database broke on its first query. So `init_db()` now compares each
  table to the model and runs `ALTER TABLE … ADD COLUMN` for any missing **nullable** column. A
  new *non-nullable* column on an existing table cannot be added this way (it logs a warning) —
  make new columns nullable.
- **Each database path gets its own engine**, created lazily. Tests point `DB_PATH` at a temporary
  file and get a fully isolated database.
- Dates are stored as ISO-8601 text in UTC.
- Several columns from the PRD were dropped on purpose (phone, mutual connections, separate INR/USD
  offer columns…), because their only data source was the dead Proxycurl service or they belong to
  features not built.

---

## 10. The API (every endpoint)

Interactive docs are built in: open **http://localhost:8000/docs** while the app runs (FastAPI
generates this page automatically). All endpoints except `/health` sit behind the password gate
when `APP_PASSWORD` is set.

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | `{"status":"ok"}`. Always open. |
| POST | `/api/v1/resume/upload` | Upload a PDF (form field `file`); returns the parsed profile. |
| GET | `/api/v1/resume/profile` | Your profile, or 404 if none yet. |
| PUT | `/api/v1/resume/profile` | Replace the profile with an edited one. |
| POST | `/api/v1/jobs/hunt` | Body `{search_term, location="India", top_n=15 (1–50)}`. Runs the full hunt (1–4 min). Returns `total_found`, `scored_count`, `alert_sent`, `jobs`. |
| GET | `/api/v1/jobs?limit=` | Saved jobs, best score first. |
| POST | `/api/v1/referrals/find` | Body `{company, role?}`. Returns ranked `contacts` and `manual_search_url`. |
| GET | `/api/v1/referrals?company=` | Saved contacts, warmest first. |
| POST | `/api/v1/outreach/draft` | Body `{contact_id, job_id?, message_type?}`. Writes and saves a draft. |
| GET | `/api/v1/outreach?contact_id=&status=` | Messages, each with its send hand-off attached. |
| PUT | `/api/v1/outreach/{id}` | Body `{body?, subject?}`. Edit (an approved message goes back to draft). |
| POST | `/api/v1/outreach/{id}/approve` | Mark ready. Sends nothing. |
| POST | `/api/v1/outreach/{id}/sent` | Record that **you** sent it. |
| POST | `/api/v1/outreach/{id}/skip` | Decide not to send. |
| POST | `/api/v1/outreach/{id}/follow-up` | Draft a short nudge (only for a sent message). |
| POST | `/api/v1/applications/track` | Body `{job_id, applied_via="direct", referral_contact_id?}`. Put a job on the board. |
| GET | `/api/v1/applications` | All tracked applications. |
| POST | `/api/v1/applications/{id}/stage` | Body `{status}`. Move to a stage. |
| POST | `/api/v1/applications/{id}/note` | Body `{note}`. Append a dated note. |
| POST | `/api/v1/applications/{id}/offer` | Body `{amount, currency="INR"}`. |
| GET | `/api/v1/applications/reminders` | Overdue items, most neglected first. |
| GET | `/api/v1/applications/stats` | Totals, by stage, response rate, by source, best source. |
| POST | `/api/v1/tailor/analyze` | Body `{job_id}`. Fit analysis + checked suggestions. |
| POST | `/api/v1/tailor/cover-letter` | Body `{job_id}`. Checked cover letter. |
| POST | `/api/v1/interview/prep` | Body `{job_id}`. Interview prep. |
| GET | `/api/v1/setup` | Configuration status (no secrets). |

Example with `curl`:

```bash
curl -F "file=@my_resume.pdf" http://localhost:8000/api/v1/resume/upload
curl -X POST http://localhost:8000/api/v1/jobs/hunt \
     -H "Content-Type: application/json" \
     -d '{"search_term": "Backend Engineer", "location": "India", "top_n": 10}'
```

---

## 11. The frontend (what you see in the browser)

**Stack:** Vite 8 (build tool) + React 19 + TypeScript 6 + Tailwind CSS v4 + Phosphor icons.
Linted with `oxlint`. **No component library** — the basic building blocks (Button, Card, Pill,
Empty state, Loading, Error note, Section header) are hand-made in `src/components/ui.tsx`.

```
frontend/src/
├── main.tsx              starts React
├── App.tsx               the shell: top bar, 6 tabs, theme toggle, "upload resume first" gate
├── index.css             Tailwind + the colour tokens (light and dark)
├── lib/
│   ├── api.ts            every backend call + the TypeScript types for each response
│   ├── useAsync.ts       small hook: loading / data / error / reload for any request
│   ├── view.ts           the list of tab ids and the props every tab receives
│   └── cn.ts             joins CSS class names
├── views/                one file per tab
│   ├── ResumeGate.tsx    "Start with your resume" (shown until a profile exists)
│   ├── Today.tsx         reminders, drafts waiting, stats
│   ├── Jobs.tsx          hunt form, job cards, Track / Open / Tailor / Cover letter
│   ├── Referrals.tsx     find people, warmth, Draft message
│   ├── Outreach.tsx      review, edit, approve, copy, open, "I sent it", skip, draft a nudge
│   ├── Pipeline.tsx      kanban board + Interview prep
│   └── Settings.tsx      the "Setup" tab
└── components/
    ├── ui.tsx            the hand-made building blocks
    ├── FitPanel.tsx      shows the tailoring result in three groups
    └── InterviewPanel.tsx the interview prep dialog
```

**Design decisions worth knowing:**
- **Routing by URL hash** (`#jobs`, `#pipeline`…), so refresh keeps your place and the back button
  works. (It used to live only in React state; refresh lost your place.)
- **Theme is set before the page paints**, by a tiny script inside `index.html`, so there is no
  white flash in dark mode. Your choice is saved in `localStorage`.
- **Colours:** warm stone neutrals and one teal accent. Warning/good/critical colours are kept
  separate from the accent so a warning never looks like branding.
- **Fonts:** Geist and Geist Mono, copied into `public/fonts/`. (Importing them from the `geist`
  npm package fails the build because it does not export the raw font files.)
- **Every list has loading, empty and error states**, and empty states link to the action that
  fills them ("No jobs yet → Hunt jobs").

**How it is served:** `npm run build` writes `frontend/dist/`. When that folder exists,
`backend/main.py` serves `/assets`, `/fonts` and `index.html` at `/`. If you never build the
frontend, the API still works on its own.

**During UI development:** `cd frontend && npm run dev` gives a hot-reloading server on port 5173
that forwards `/api` calls to the backend on 8000.

---

## 12. Configuration (`.env`), every setting explained

Copy `.env.example` to `.env`. **Only `LLM_API_KEY` is required**; the app degrades gracefully
without everything else, and the Setup tab tells you what each missing piece would unlock.

| Setting | Default | Meaning |
|---|---|---|
| `LLM_API_KEY` | — | **Required.** Free Gemini key from aistudio.google.com/apikey (no card). |
| `LLM_BASE_URL` | Google's OpenAI-compatible URL | Leave as is. |
| `LLM_MODEL` | `gemini-3.5-flash-lite` | Model for volume work. |
| `LLM_MODEL_HEAVY` | `gemini-3.5-flash` | Model for resume parsing. |
| `GROQ_API_KEY` | — | Backup AI. Free at console.groq.com/keys. Strongly recommended — Gemini is often busy. |
| `GROQ_BASE_URL` / `GROQ_MODEL` | Groq URL / `openai/gpt-oss-20b` | Leave as is. |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | — | Job alerts on your phone. Create a bot with @BotFather, message it once, read your chat id from `https://api.telegram.org/bot<TOKEN>/getUpdates`. |
| `SERPER_API_KEY` | — | Finding strangers for referrals. 2,500 free searches, one time, no card (serper.dev). |
| `SERPAPI_API_KEY` | — | Same, as the monthly floor. 250 free per month, no card (serpapi.com). |
| `LINKEDIN_CONNECTIONS_CSV` | `./data/connections/Connections.csv` | Where your LinkedIn export lives. |
| `HUNT_SEARCH_TERM` | empty (= scheduler off) | e.g. `Backend Engineer`. |
| `HUNT_EVERY_HOURS` | `0` (= off) | e.g. `12`. |
| `HUNT_LOCATION` | `India` | Location for scheduled hunts. |
| `HUNT_TOP_N` | `10` | How many jobs the AI scores per scheduled hunt. |
| `ALERT_MIN_SCORE` | `70` | Minimum score to be announced. |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | The local ranking model. |
| `APP_PASSWORD` | empty (= no gate) | Set before sharing beyond your laptop. |
| `DB_PATH` | `./data/db/career_agent.db` | The database file. |
| `PROFILE_PATH` | `./data/profile/profile.json` | The profile file. |

Also in `config.py` but not in `.env.example` (rarely changed): `SERPER_MONTHLY_CAP=2500`,
`SERPAPI_MONTHLY_CAP=250`, `LLM_MAX_TOKENS=8000`, `GROQ_MAX_TOKENS=6000`.

**Changing `.env` needs a server restart** — settings are read once and cached.

**Status on this laptop (2026-10-02):** the AI keys are set and working. Telegram, Serper/SerpApi,
the real LinkedIn export and the scheduler settings are **not** set yet (see §22).

---

## 13. How to run it, step by step

### 13.1 What you need first

- **Python 3.10+** (this laptop uses 3.12) — check with `python3 --version`.
- **Node.js** (for building the frontend) — check with `node --version`.
- **git**.
- A free **Gemini API key**.
- About **2 GB** of disk (the Python libraries include PyTorch, ~530 MB on its own).

### 13.2 First-time setup

```bash
# 1. Get the code
git clone https://github.com/Manan0802/job-agent
cd job-agent

# 2. Make a private Python environment for this project and switch into it
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install the Python libraries (takes a few minutes the first time)
pip install -r requirements.txt

# 4. Create your settings file and add your Gemini key
cp .env.example .env               # then open .env and fill in LLM_API_KEY

# 5. Build the website once
cd frontend && npm install && npm run build && cd ..

# 6. Start everything
uvicorn backend.main:app --reload
```

Open **http://localhost:8000** (the app) or **http://localhost:8000/docs** (the API).

> **Why a "venv"?** It keeps this project's Python libraries separate from everything else on
> the computer. Always `source .venv/bin/activate` before running Python commands here (or call
> `.venv/bin/python` directly).
>
> **The first hunt is slower**: it downloads the ~130 MB embedding model once.

### 13.3 Day to day (on this laptop)

```bash
cd ~/Desktop/manan/jba
source .venv/bin/activate
uvicorn backend.main:app --port 8000
```

### 13.4 Working on the code

```bash
python -m pytest -q                    # run all 386 tests (~20 s, no internet needed)
python -m pytest tests/test_warmth.py  # run one file
cd frontend && npm run dev             # UI with hot reload on :5173 (backend must run on :8000)
cd frontend && npm run build           # rebuild the UI the backend serves
cd frontend && npm run lint            # lint the UI
```

### 13.5 Opening it from your phone

```bash
brew install cloudflared     # once
# make sure APP_PASSWORD=<something long> is in .env
./share.sh
```

It prints a `https://….trycloudflare.com` link. The laptop must stay awake and online. The link
changes each time. For a permanent link: put a domain on Cloudflare and use a named tunnel with
Cloudflare Access (also free, gives an email login).

### 13.6 Common problems

| Symptom | Cause / fix |
|---|---|
| Every tab says "Start with your resume" | No profile yet. Upload a PDF. |
| "The free AI model is busy right now…" | Gemini rate limit or daily quota. Wait, or add `GROQ_API_KEY`. |
| Referrals only show a manual link | No Serper/SerpApi key and no LinkedIn CSV. That is expected; add one. |
| A hunt finds fewer jobs than usual | One source blocked (Naukri `406 recaptcha`, Glassdoor `400` are common). Check the server log. |
| No Telegram message after a hunt | `TELEGRAM_*` not set — alerts are silently skipped. |
| `share.sh` says "Refusing to share" | Set `APP_PASSWORD` in `.env`. |
| Changed `.env` and nothing happened | Restart the server. |
| Opening `/` shows JSON 404 | The frontend is not built. Run `npm run build` in `frontend/`. |

---

## 14. Tests

- **386 tests in 55 files** under `tests/`, run with `pytest`. Last run: 2026-10-02, **386 passed**
  in ~19 s (3 harmless deprecation warnings about FastAPI's `on_event`).
- **No test touches the internet.** Every outside call (job boards, Gemini, Groq, Serper, Telegram,
  the embedding model) is replaced with a fake ("mocked").
- Naming: `test_<module>.py` tests `<module>.py`; `test_<area>_api.py` tests the HTTP endpoints.
- `tests/conftest.py` has two fixtures that run for every test:
  1. it forces the password gate **off**, so a developer's own `APP_PASSWORD` cannot break 70 API
     tests (that happened once); `test_auth.py` tests the gate explicitly;
  2. it resets the AI circuit breaker, because it is shared module-level state that would otherwise
     leak from one test into the next.
- Tests that change `DB_PATH` must call `init_db()` themselves after changing it.
- Some tests pin **rules**, not just behaviour: e.g. `test_send_links.py` fails if a `send_*`
  function ever appears; prompt tests check the honesty and tone rules are present in the prompt
  text (model output itself cannot be asserted).
- `test_warmth_real_data.py` encodes the four bugs real LinkedIn data exposed.

**How the project was built:** strict **TDD** — write the test, watch it fail, write the code, watch
it pass, commit. **And then run it for real** against the real resume, the real APIs and the real
database. That second step found every serious bug (§21).

---

## 15. The rules this project never breaks

These are the non-negotiables. Several are enforced by code or tests, not just by convention.

1. **Nothing is ever sent on your behalf.** No auto-apply, no auto-DM, no auto-email. The app
   drafts; you send. *Why:* automating LinkedIn messages is what got the well-known AIHawk project
   taken down, and the account at risk is your own — the same one you are job hunting with.
   *Enforced:* `send_links.py` has no sender, and a test fails if one is added.
2. **No logged-in scraping.** LinkedIn is only read through public search pages (via JobSpy) and
   public Google results. YC turned out not to need a login either. *Why:* ban risk and terms of
   service.
3. **Never claim what the resume cannot back.** Tailoring suggestions, cover letters and interview
   answers are checked **in code** (§7.7), because instructing the model was not enough.
4. **Free first.** The target is ₹0/month. Paid APIs are metered and capped per month. The scheduler
   is off until you turn it on.
5. **Local first.** Your data lives in one SQLite file on your laptop. Secrets live in `.env`, which
   is never committed. Other people's data (the LinkedIn export) is gitignored.
6. **Human in the loop.** You approve every message, decide every stage change, and choose who to
   contact. Reasons are always shown next to scores so you can judge them.
7. **Fail soft.** One broken source, one failed score or one failed Telegram message never throws
   away the rest of a run.

---

## 16. Big decisions and why they were made

| Decision | Why |
|---|---|
| **Runs on the laptop, not in the cloud** (`docs/DEPLOY.md`) | Vercel: `torch` alone is 529 MB vs a 250 MB limit, a hunt takes 2–4 min vs a 60 s limit, and SQLite needs a disk that survives. Cloudflare Workers can't load native libraries like torch. Render free has 512 MB RAM (the model doesn't fit), sleeps after 15 min idle (kills the scheduler), and has no lasting disk. **Any** cloud host moves scraping to a datacenter IP, which LinkedIn and Indeed throttle; your home IP is what makes scraping work. |
| **Reuse, don't rebuild** | JobSpy replaces ~5 hand-written scrapers; markitdown reads PDFs; sentence-transformers ranks. Custom code only where the value is: scoring, warmth, honesty checks, orchestration. |
| **Local embedding pre-filter before the AI** | The single biggest cost decision. 500 jobs → 10–15 for the AI. Without it a hunt cannot fit in a free tier. |
| **Gemini first, Groq as fallback; no paid Claude/OpenAI** | ₹0 budget. Two providers, each with its own free tier. |
| **LangGraph for the pipelines** | Manan's choice, over a plain-Python alternative the research suggested. Uses the in-memory checkpointer; durability comes from the save step writing to SQLite, and a hunt is short. |
| **Telegram for alerts** (not WhatsApp/Twilio) | Free, no per-message cost, 2-minute setup. |
| **Proxycurl → Google search** for referrals | Proxycurl (the PRD's plan) shut down in July 2025. Public Google results need no LinkedIn login. |
| **Serper first, SerpApi as the floor** | Serper: 2,500 free once. SerpApi: 250 free every month, forever. Google's own Custom Search API is closed to new sign-ups; Brave dropped its free tier in Feb 2026. |
| **YC without login** | The plan said use `waasuapi` (real login + Selenium, last updated 2024). YC's public pages already embed the jobs as JSON. |
| **Dedup on company + title only** | Dates are formatted differently by every source. |
| **Alerts only on new matches** | Daily repeats of the same jobs teach you to mute the alert. |
| **Scheduler off by default, waits before first run** | Never spend the free tier unasked; a restart is not a request to hunt. |
| **Interview prep on the Pipeline, not Jobs** | Only useful while an interview is ahead. |
| **Basic auth instead of a login page** | The whole feature in ten lines; every browser already does the client side. |
| **No generated resume file** | Your resume tool makes a better resume; the app tells you what to change. |
| **No component library in the UI** | A small, custom set of primitives is easier to keep consistent and accessible. |
| **Rejection counts as a response; saved-only jobs excluded from the rate** | So the response rate reflects reality. |

---

## 17. The research behind the project

> **Short version:** almost every design choice in this repo came from checking something first —
> reading a tool's code, testing an API with a real key, timing a real run — rather than from what
> a blog post or the tool's own README claimed. This section records that research: what was
> checked, what it found, and what it changed. Sources: the PRD, the v2 design spec, the phase
> write-ups, commit messages, and the project notes in the Obsidian vault.

### 17.1 Where it started: the PRD and the old app

**The PRD (v1.0, written before any research)** — `job-referral-finder-PRD.md` set the goal and
the shape that still stand: five modules (resume profiler, job hunter, referral finder, outreach
drafter, tracker), human approval before anything is sent, data kept locally, a ₹500/month cap.
Its user persona is Manan: a software/AI engineer comfortable with Python and LangGraph, employed
and looking for something better, targeting Indian startups, remote roles, big tech and YC
companies, with 1,000–3,000 LinkedIn connections.

What the PRD assumed, what research found, and what was actually built:

| PRD v1.0 assumed | What research found | What was built |
|---|---|---|
| 7 hand-written scrapers (Playwright etc.) | JobSpy already scrapes 7 boards including Naukri, and is maintained by many contributors | JobSpy + 5 free APIs + a YC adapter |
| Proxycurl API for LinkedIn people data (~₹250/month) | Proxycurl **shut down in July 2025** after legal action over scraping | Google search (Serper/SerpApi) + your own LinkedIn export + a manual link |
| Claude Sonnet (paid) for every AI call | Free Gemini/Groq tiers are enough if the AI only ever sees a shortlist | Gemini → Groq, ~₹0 |
| The AI scores every job | No free tier can do that; a local embedding model can rank hundreds for free | Embedding pre-filter → AI scores the top 10–15 |
| Roadmap v2: auto-send LinkedIn DMs, auto-apply | Auto-appliers like AIHawk were taken down under LinkedIn pressure; the user's own account is at risk | Never. Enforced by a test. |
| Notifications as a badge in the UI | You shouldn't have to open the app to find out | Telegram |
| React 18 + Zustand + drag-and-drop kanban + Recharts + Axios + toasts | Not needed at this size | React 19 + Tailwind, hand-made primitives, buttons to move cards |
| APScheduler, every 2–3 days | A small asyncio loop is enough | `scheduler.py`, interval set in `.env` |
| ~₹450/month | | ~₹0/month |

The PRD's long-term roadmap is still the vision: **v3 "Unified Career OS"** (this tool + a
freelancing client-finder + a content agent, sharing one profile) and **v4 SaaS** (multi-user,
a paid tier around ₹499/month, aimed at final-year students and early-career developers in India).

**The predecessor app (`Ai-job`).** Before jba there was a Streamlit app
(`github.com/Manan0802/Ai-job-portal`, local folder `Desktop/Ai-job`) that already did roughly 80%
of the PRD for free, but messily (ad-hoc scripts, Google Sheets as storage). The decision on
2026-06-28 was: **build fresh and properly, but lift what the old app had already proven.**

| From `Ai-job` | Verdict | What became of it in jba |
|---|---|---|
| JobSpy + Remotive scraping | Lift | `jobspy_adapter.py`, `remote_apis.py` |
| SerpApi Google "dork" for referrals (`site:linkedin.com/in/ "Company" "Role"`) | Lift — became the primary referral method | `people_search.py`, with Serper added in front |
| `resume_tailor.py` (gap analysis + tailored PDF + cover letter) | Lift the logic | `resume_tailor.py`, rewritten with the honesty check and without PDF generation |
| WhatsApp alerts via Twilio | Lift | Replaced by Telegram (free) |
| Free Gemini through OpenRouter | Lift the free-first idea | Direct Gemini + Groq |
| `interview_war_room.py` | Bank for later | `interview_prep.py` |
| Streamlit UI, Google Sheets storage | Drop | React + FastAPI + SQLite |

A security finding from that review shaped a rule: the old app kept plaintext API keys in a
(gitignored) config file. They never leaked, but jba's rule became **secrets in `.env` only**.

### 17.2 The 30-tool research (2026-06-28)

Manan collected about 30 open-source projects and services that looked relevant. Each was triaged
as ✅ use, 🟨 modify, 📖 reference only, 🔬 evaluate, or ❌ avoid. The last column says what
actually happened.

| Tool | Verdict then | What actually happened |
|---|---|---|
| JobSpy (`speedyapply/JobSpy`, MIT) | ✅ Use | The core ingestion engine |
| Remotive / RemoteOK / Arbeitnow / Himalayas APIs | ✅ Use | Built, plus Jobicy |
| SerpApi (from the old app) | ✅ Use | Built, with Serper in front of it (§17.4) |
| markitdown (Microsoft) | ✅ Use | Reads the resume PDF |
| camofox-browser (anti-detect browser server) | ✅ Use | **Not built** — it needs Docker, which is not installed. Walled boards remain the biggest gap. |
| camoufox, nodriver, patchright, steel-browser | 📖 Reference | Not needed |
| career-ops (a Claude Code career skill) | ✅ Use for tailoring | Not used. Tailoring was built in-house, because the honesty check had to live in code. |
| `jwc20/waasuapi` (YC scraper) | 🟨 Modify | Unnecessary — YC's public pages embed their jobs as JSON (§17.6) |
| ever-jobs (160+ sources, ships an MCP server) | 🔬 Evaluate | Never needed |
| Resume Matcher, OpenResume, Reactive Resume, ATS Screener, AutoATS, JDAlchemy | 📖 Reference | Ideas only |
| JobSync | 📖 Reference | Tracker UX ideas |
| `sergio11/langgraph_jobsearch_assistant` | 📖 Reference | LangGraph pattern reference |
| Interview-prep repos (tech-interview-handbook, system-design-primer…) | 📚 Link out | Not linked; prep is grounded in the user's own resume instead |
| AIHawk, ApplyPilot, EasyApplyBot, Auto_job_applier, AutoApplyMax | ❌ Avoid | Never — account bans and legal risk |
| Job Application Bot (Ollama) | 📖 Reference | — |
| Upwork scrapers, JSON Resume, OpenCATS, SpotAxis | ⏭ Out of scope | — |
| Proxycurl | ❌ Dead | — |
| pyresparser | ❌ Stale (2023) | markitdown + the AI instead |

The rule that came out of this: **reuse mature tools for commodity work; build custom only where
the value is** — scoring, warmth, honesty checks and the glue between steps.

### 17.3 Market research: is anyone already doing this?

Checked during Phase 2–3 planning: Teal, Careerflow, Sonara, LazyApply, JobCopilot, Simplify,
LoopCV, JobHire.AI. All of them compete on resume tailoring and application volume. **None of them
finds referral contacts for the job seeker.** The only "AI + referrals" products found help
*employers* mine their own staff. That made the referral finder the project's differentiator, and
the reason a product might come out of this later.

### 17.4 Research on where referral data can come from (2026-07-22)

| Option | What was found | Decision |
|---|---|---|
| Proxycurl | Shut down July 2025 | Dead |
| LinkedIn's official API | No people search for this use | No |
| Logged-in LinkedIn scraping | Ban risk on the user's own account | Never |
| **Serper.dev** | 2,500 free searches, no card, a **one-time** grant | Primary |
| **SerpApi** | **250 free per month, forever**, no card, 50/hour. (The PRD and spec said 100 — that was wrong.) | The monthly floor |
| Google Custom Search JSON API | **Closed to new sign-ups**; returns HTTP 410 from January 2027 | Not possible |
| Brave Search API | **Free tier removed in February 2026**; needs a card and bills overage with no cap | A bill risk on a ₹0 budget — rejected |
| People Data Labs / Apollo free tiers | Possible gap-fillers | Not needed so far |
| Your own LinkedIn export | Free, and the only source that knows who you actually know (emails are mostly stripped now) | Built |

Also confirmed: a `site:linkedin.com/in/` Google search still works, but since LinkedIn hid
headlines and work history from search engines in 2024, a result only reliably gives **name,
profile URL and current employer** (from the page title). That is enough — the user opens the
profile and decides.

### 17.5 AI model research and measurements

- **OpenRouter → direct keys (2026-07-12).** The plan used free Gemini through OpenRouter. It
  switched to Google's own Gemini API (through its OpenAI-compatible endpoint) with Groq as a direct
  fallback. With two providers, a 30-line router beats a routing library.
- **The quota was measured, not read** (2026-07-28). Google's docs only point to AI Studio, so each
  model was called with the real key:

  | Model | Result on this key |
  |---|---|
  | `gemini-3.5-flash` | Works; **20 requests per day, per model** |
  | `gemini-3.5-flash-lite` | Works; its own separate budget |
  | `gemini-3.1-flash-lite` | Works; its own separate budget |
  | `gemini-2.5-flash`, `gemini-2.5-flash-lite` | 404 (not available) |
  | `gemini-2.0-flash-lite` | 429 on input tokens per minute |

- **Groq's real limit** is 8,000 tokens per minute, and it counts the `max_tokens` you *reserve*.
- **Timings that drove the code:**

  | Change | Before | After |
  |---|---|---|
  | Retry Gemini before falling back + circuit breaker + right-sized `max_tokens` | 41 s per job | 4.3 s per job |
  | Score 5 at a time on the fallback (an "optimization") | 4.3 s per job | **13.5 s per job, 5/6 scored** — reverted |
  | Probe one job first, go wide only if Gemini is up | 13.5 s per job | 5.0 s per job, 6/6 scored |
  | Volume work moved to `flash-lite` | ~5 s per job on Groq | 6 jobs in 3 s total |

- **Orchestration.** The research favoured plain Python, because the pipeline is mostly a straight
  line; AutoGen was ruled out (Microsoft moved it to maintenance mode). Manan chose **LangGraph**
  anyway, for structure and room to branch later. It runs the two pipelines.
- **Embedding model.** `BAAI/bge-small-en-v1.5`: English, runs on a CPU, reads up to 512 tokens
  (hence cutting descriptions at 1,000 characters). Planned fallback if it was too slow:
  `all-MiniLM-L6-v2` — never needed.

### 17.6 Scraping research

- **YC.** The plan's `waasuapi` needs real login details plus Selenium/Chromedriver, was last
  updated in August 2024, and its own last commit says "please fix chromedriver pathing". Reading
  YC's public pages showed the listings sitting as JSON in a `data-page` attribute, so plain HTTP
  works: no login, no browser. Each filter page returns a different slice and there is no
  pagination, so four pages are read. Verified: 92 unique jobs.
- **JobSpy in practice.** LinkedIn works on the public path; Naukri often answers
  `406 recaptcha required`; Glassdoor sometimes `400`. JobSpy pins `numpy==1.26.3`, but real scrapes
  were verified working on numpy 2.5.1.
- **What each free API actually contains** (learned during the real job search, §18):

  | Source | Useful fields |
  |---|---|
  | Himalayas | The richest: min/max salary, currency, seniority, location restrictions |
  | Jobicy | `jobLevel` (can filter junior roles), `jobGeo` |
  | Remotive | `?category=software-dev` filter; salary is free text |
  | RemoteOK | Salary fields were always empty |
  | Unstop *(not a source yet)* | Experience range, salary in LPA, WFH/office — the cleanest India data |

- **What needs a login** (the real search, 2026-08-06):

  | Board | Without login | With login |
  |---|---|---|
  | Wellfound | Page 1 only | 719 AI Engineer jobs in India across 22 pages, experience filter |
  | LinkedIn | ~40 results per search | Experience-level and date filters |
  | Naukri | Listings visible | Needed to apply |
  | Instahyre / Cutshort | Nothing | Fully gated, curated India roles |

  Manan offered to use personal logins for genuinely gated boards. LinkedIn stays public-only
  regardless. Nothing built so far has needed a login.

### 17.7 Hosting research

Covered in §16 and fully in `docs/DEPLOY.md`: Vercel, Cloudflare Workers, Render, Fly and Oracle
Always Free compared against the app's real numbers (`torch` 529 MB, full environment 1.4 GB,
hunts of 2–4 minutes, SQLite on disk, scraping needing a home IP). Conclusion: run locally, share
through a Cloudflare tunnel behind a password. Upgrade path if ever needed: a domain on Cloudflare,
a named tunnel and Cloudflare Access (free, email login).

### 17.8 The open questions, and how each was answered

| Open question (from the design spec and the pre-Phase-2 list) | Answer |
|---|---|
| Plain Python or LangGraph? | LangGraph — Manan's call, 2026-07-13 |
| YC and Wellfound: scrapeable, or behind a login? | YC: public JSON, no login. Wellfound: only page 1 without login — still open |
| Login policy | Never log in where public access works; LinkedIn public-only forever; personal logins only for genuinely gated boards |
| Does ever-jobs cover Indian and startup boards? | Never needed |
| SerpApi free tier: 100 or 250? | 250/month — and Serper is the better lead |
| Best free Gemini model? | Measured: flash-lite for volume, flash for resume parsing |
| WhatsApp or Telegram? | Telegram — free; WhatsApp via Twilio costs money outside template windows |
| Can outreach send through Gmail? | Deferred on purpose; `mailto:` keeps the user in control with zero setup |

---

## 18. Field research: using the app for a real job search

The app was built to be used, and its first real uses turned out to be the most useful product
research of all.

### 18.1 First real search (2026-08-06)

Manan's target: SDE, AI, data, product or consulting roles in Bengaluru, Hyderabad, Gurgaon,
Noida, or remote.

**Attempt 1 — remote jobs paid in USD — failed, and the failure was the finding:**

```
~700 remote jobs (Himalayas, RemoteOK, Remotive, Jobicy, Arbeitnow, YC, LinkedIn)
  → 191 tech roles
  →  55 not senior
  →   9 open to applicants in India
  →   1 matched the resume (85/100)
  →   0 actually applicable — that one required US citizenship or a green card
```

Measured seniority spread for remote AI roles: **19 senior vs 5 entry-level**, and the 5
entry-level ones were data-labelling jobs, not engineering. The reason is structural: remote hiring
usually means "we won't train you", so those roles ask for 3–6+ years. The USD requirement was
dropped and the search moved to India + remote.

**Attempt 2 — India + remote — worked:** 12 relevant jobs and 15 named referral contacts, all saved
into the app's database (the jobs are tagged `source_engine = manual-hunt-2026-08-06`).

**The method.** The app's own sources returned only 9 mostly irrelevant results for this search,
so discovery happened on the open web and the app did the judging:

1. **Search** — `firecrawl_search`, four searches in parallel (AI/LLM in Bengaluru, 1–3 years in
   NCR, product/consulting roles, startup boards).
2. **Scrape** — `firecrawl_scrape` on the listing pages those searches surfaced (Wellfound role
   pages, Unstop, Naukri). One site returned 200,000+ characters, so cap output before scraping.
3. **Filter** — regexes for tech roles and to drop senior ones.
4. **Score** — jba's own `score_jobs()` against the real resume.
5. **People** — the same Google search the app uses (`site:linkedin.com/in/ "<company>" engineer`),
   plus a same-college angle.
6. **Rank people** — jba's `score_contact()` for warmth; contacts saved to the database.
7. **Re-check** — two days later every link was HTTP-checked; one posting had gone `410 Gone` and
   was replaced. Postings expire within weeks, so open them again before applying.

**What the market looked like** for this profile (about 1.5 years of production LLM-agent work):
- Wellfound, Unstop and Naukri carried the best India data. Wellfound's "top 10% of responders"
  badge is a useful sign a company will actually reply.
- The strongest leads were small AI-native startups, which often don't post on the big boards;
  their own careers pages and their founders/CTOs on LinkedIn matter more.
- **Positioning lesson: don't describe yourself by years alone.** Real production work (multi-agent
  orchestration, sub-second voice AI, large measured cost reductions) clears many "2–4 years"
  requirements, and that band is where the better roles were.

**The full record** — every job, person and link — is in the vault note `jba-job-search-log.md`. It
is deliberately not copied here, because it contains other people's names and profiles.

### 18.2 Second search: internships and remote SDE roles (2026-08-21)

Same method: open-web discovery, then jba's scorer. 18 jobs saved (`source_engine =
intern-hunt-2026-08-21`), **all scored this time**. The 13 jobs from August 6 had been saved
without scores, so they sank to the bottom of the Jobs tab (unscored jobs sort last) — a mistake
not repeated.

| Source | Finding |
|---|---|
| YC job board | The best: paid India/remote roles with clear stipend and experience range |
| Wellfound | Several remote-India roles; stipend often missing |
| Internshala | High volume, poor quality — mostly unpaid or ₹1–2k a month |
| Unstop | In between |

### 18.3 What the real searches taught the product

The product changes are listed as TODOs in §22.2:

| Finding | Evidence | What the product needs |
|---|---|---|
| The scorer ignores work authorization | The top remote pick (85/100) required US citizenship | Read visa/citizenship lines; drop the score |
| Experience mismatch is invisible | "3+ years required" jobs scored ~45 with no flag | A separate experience-fit signal |
| Warmth is not usefulness | A CTO whose headline said "(Hiring!)" scored 1/5, and so did a person who owns hiring | A "hires / is hiring" signal next to warmth |
| India sources are missing | The whole August 6 search was done by hand | Wellfound, Unstop and Naukri adapters |
| Skill overlap is not rarity | Generic full-stack internships scored 90; a voice-AI role matching rare, proven experience scored 70 | Weight rare skills higher |
| Resume wording hides real skills | A voice-agent role listed "STT/TTS" as a gap for someone who built a voice-first agent — the resume just never uses those words | Tailoring helps today; the scorer could read project text |
| Pay and company quality don't count | A ₹1k/month and a ₹40k/month internship can rank the same | Store salary (there is no column today) and use it |
| For discovery, the open web beat the built-in sources | 9 weak results in the app vs 12 real ones from web search | Web search for discovery; the app for judging |

---

## 19. How we work

### 19.1 Who does what

| | Manan (owner) | Claude Code (the AI pair programmer) |
|---|---|---|
| Direction | Decides what to build and makes the big calls (LangGraph, Telegram, login policy, dropping USD) | Researches options, recommends with evidence, raises open decisions |
| Inputs | Resume, API keys, LinkedIn export, job preferences | — |
| Building | Reviews, tries it out | Plans, writes tests and code, runs it for real, writes it up |
| Anything that leaves the laptop | Sends every message, applies to every job, pushes code as `Manan0802` | Never sends, never applies |

Conversation happens in Hinglish. Repo docs and code comments are in English. Vault notes are in
Hinglish.

### 19.2 The life of a feature

```
Idea ─► PRD ─► research (check, measure) ─► design spec ─► phase plan
     ─► for each task:  test ─► watch it fail ─► code ─► watch it pass ─► commit ─► push ─► show
     ─► run it for real (real resume, real APIs, real database) and read the output
     ─► fix what the real run found, with a test that reproduces it
     ─► phase write-up ─► update README and vault notes
```

1. **Plan before code.** Each phase gets a plan in `docs/superpowers/plans/`: a goal, a one-line
   architecture, global constraints (₹0, secrets only in `.env`, no paid calls in tests), and
   numbered tasks listing the files, the interfaces, and the steps. These were written with the
   "superpowers" brainstorming and writing-plans workflow (hence the folder name).
2. **Strict TDD, one task at a time,** stopping to show the result after each task. The test count
   after each phase: 10 → 100 → 171 → 219 → 260 → 263 → 357 → 386.
3. **A real run after the tests pass.** Not optional: it found every serious bug (§21).
4. **A write-up at the end of each phase:** what shipped, the deliberate deviations from the plan
   and why, the bugs only real data exposed, and what is still needed from the user. The plan file
   becomes the record of what happened.

### 19.3 How decisions are made

- **Check, don't trust.** The Gemini quota was measured against the live API. The numpy pin was
  tested rather than obeyed. Pricing pages were read directly, which is how the SerpApi "100" turned
  out to be 250. A tool's own repo was read before adopting it, which is how `waasuapi` was dropped.
- **Write down the why,** so a decision does not get re-argued. `docs/DEPLOY.md` exists for exactly
  this reason.
- **Deviations are deliberate and recorded,** in the phase write-up that made them.
- **Open decisions go to Manan, with a recommendation.** Four were raised before Phase 2
  (orchestration, the YC login, the SerpApi limit, the alert channel) and settled on 2026-07-13.
- **The simplest thing that works.** No migration framework, no component library, no Gmail OAuth,
  no checkpoint database — each because the simpler option was enough.

### 19.4 What "done" means

- It ran for real, and someone **read** the output — "no error" is not enough.
- It was tried against the **old** database, not just a fresh one.
- Any performance change was **measured** before and after. (A change made on intuition once made
  scoring three times slower.)
- Any UI change was **screenshotted** in light mode, dark mode and at phone width (~390 px). On this
  Mac the Chrome extension and the Puppeteer tool don't work, so the working recipe is headless
  Chrome started with `--remote-debugging-port=9222`, driven from Python over the DevTools protocol
  (`websockets` + `httpx`, both already in the venv). To test the light theme, click the theme
  button — emulating the colour-scheme setting does not override the saved preference.
- Any warning or check was **counted**: how often does it fire, and how often is it right?
- Nothing is claimed to work without having been seen working. What was not verified is said plainly.

### 19.5 Code conventions

- **Every module starts with a docstring** saying why it exists and what failure it prevents.
- **Comments record decisions and past failures**, not syntax. Example from `config.py`: "Unset,
  providers truncated resume JSON mid-string."
- **Constants carry their reason** next to them (`_SCORE_MAX_TOKENS = 1200` with why it is not larger).
- **Only `backend/llm/router.py` knows which AI providers exist.**
- **Every AI step follows one recipe:** exact JSON shape in the prompt → strip markdown fences →
  validate with Pydantic → retry 3× → raise `ModelUnavailable`.
- **Every outside source fails soft:** log it and skip it; never lose the rest of the run.
- **Stores** list their columns in a `_COLUMNS`/`_FIELDS` tuple, save by upsert, never overwrite good
  data with nothing, and don't touch columns another flow owns (the referral store leaves
  `outreach_status` alone).
- **Anything that spends quota is off by default.**
- **Rules are pinned by tests**, not only behaviour: no sender function may exist; the prompts must
  contain the tone and honesty rules.
- **Nothing is hard-coded to one person.** College, city, employers and skills come from the parsed
  profile.
- **Tests:** one file per module; every outside call mocked; real-data regressions kept as their own
  tests (`test_warmth_real_data.py`).
- **Frontend:** hand-made primitives in one file; every list has loading, empty and error states; the
  whole API client and its types live in `src/lib/api.ts`.

### 19.6 Git conventions

- One branch, `main`, pushed straight to `origin/main`. One developer, so no pull requests.
- Commit prefixes across the 61 commits: `feat` 38, `fix` 8, `docs` 8, `perf` 3, `chore` 3,
  `refactor` 1.
- **The subject says the effect in plain English:** "fix: a third control overflowed the pipeline
  card"; "perf: score the shortlist as wide as the provider actually allows"; "feat: resume
  tailoring, with a check that it never asks you to lie".
- **The body explains why,** with measured numbers and what the real run showed. Commits written with
  the AI carry a `Co-Authored-By: Claude …` line.
- Push as the `Manan0802` GitHub account.
- Add files by name — never `git add -A` — so `.env`, `data/`, PDFs, CSVs and the AI-tool folders
  can never slip in.

### 19.7 Where knowledge is kept

| Place | What goes there | Language |
|---|---|---|
| Repo docs | README, `DEPLOY.md`, the phase write-ups, this handbook | English |
| Commit messages | Why each change happened | English |
| Code comments | Why a line is the way it is — often the bug that caused it | English |
| Obsidian vault (`~/Desktop/manan/manan-memory`) | The project hub `Projects/jba.md` with `jba-architecture`, `jba-decisions`, `jba-gotchas`, `jba-running-it` and `jba-job-search-log`; plus dated session logs (`2026-08-06.md` and others) so a new chat can pick up with nothing lost | Hinglish |
| Claude Code's memory | Short facts and feedback carried between AI sessions | English |

Vault conventions: each project note has *What it is · Stack · Status · Decisions · TODOs ·
Gotchas*; notes link with `[[wikilinks]]`; sub-note names carry the project prefix (`jba-gotchas`,
not `gotchas`), because Obsidian treats two files with the same name as one node and merges the
projects' graphs. The vault is a plain folder, not a git repo — back it up before renaming things.

Reports and dashboards go into the chat or the vault, **not** into published Artifacts (a privacy
choice).

### 19.8 The toolkit around the project

- **The manan hub.** `~/Desktop/manan/claude-transfer/.claude` holds shared skills, agent
  definitions, per-project rules and a tool router. Every project links to it through its `.claude`
  symlink (and `.mcp.json`), so one setup serves all projects.
- **The router and its hook.** On every substantive prompt, a `UserPromptSubmit` hook runs
  `router.py` and injects a "TOOL-FIRST PROTOCOL" list of the most relevant skills, agents, MCP
  servers, command-line tools and n8n workflows. The order of preference: built-in skill/agent →
  router suggestion → installed skill → specialist agent → MCP server → CLI → plugin → searching the
  wider ecosystem. It is good with precise requests and noisy on casual chat, so its list is treated
  as candidates, not orders. After adding tools, `router.py --reindex` refreshes it.
- **The tools that mattered for jba:** the superpowers planning and TDD workflow; firecrawl (web
  search and scraping) for research and job discovery; markitdown; headless Chrome for screenshots;
  the GitHub CLI; and the `design-taste-frontend` skill — but only its accessibility, state-coverage
  and anti-slop rules, because the skill itself says it is for landing pages, not product UI.
- **Secrets hygiene.** jba's `.env` is project-local, deliberately not the shared hub `.env`. The
  hub's `.mcp.json` is tracked in git, so it must contain only `${VAR}` placeholders; real keys live
  in the untracked `settings.local.json`.
- **Codex.** Since 2026-10-02 the same toolkit is also wired up for the Codex AI tool (`AGENTS.md`,
  `.agents/`, `.codex/`).
- **A lesson from Manan (2026-08-06): "use the whole arsenal."** Asked to find jobs, the AI kept
  reaching for jba because it was the familiar tool, and got 9 weak results. Web search and scraping
  found 12 real jobs and 15 people. Match the tool to the task, not to habit: discovery on the open
  web → firecrawl; scoring and ranking over your own data → jba's code.

### 19.9 How changes are explained

After any code work, the explanation covers: **what was done**; **each file changed and what it is
for**, in everyday words; for a bug, **what broke, what actually happened, how it was found and how
it was fixed**; **what deserves honesty** (anything known-broken, unverified, or visible to users);
and **a one-line version** for a standup. Assumptions are stated up front, ambiguity is asked about
rather than guessed, and changes stay surgical — every changed line should trace back to the request.

---

## 20. History: how it was built, phase by phase

61 commits between **2026-06-28** and **2026-07-29**. Test count after each phase shows how the
safety net grew.

| Phase | Done on | Tests | What it added |
|---|---|---|---|
| Planning | 2026-06-28 | — | PRD v1.0, research of ~30 tools, v2.1 design, Phase 1 plan |
| **1 · Foundation** | 2026-07-08 | 10 | Config, SQLite + profiles table, LLM router, PDF → markdown, profile schema + resume parser, upload/get/edit endpoints |
| (switch) | 2026-07-12 | — | Moved from OpenRouter to direct Gemini + Groq fallback |
| **2 · Job Hunter** | 2026-07-21 | 100 | Jobs + budget tables, JobSpy, 5 free APIs, YC, dedup, local embeddings, AI scorer, Telegram, LangGraph pipeline, hunt API. Scoring sped up 41 s → 4.3 s per job. |
| **3 · Referral Finder** | 2026-07-22 | 171 | Contacts table, LinkedIn CSV parser, people search with monthly budget, warmth scoring, referral pipeline + API, `utils/text.py` name matching |
| **4 · Outreach Drafter** | 2026-07-27 | 219 | Messages table + lifecycle, 6 message types, send hand-off (no sender), outreach API |
| **5 · Tracker** | 2026-07-27 | 260 | Applications table, stages + follow-up dates, reminders, stats, tracker API |
| **6 · React UI** | 2026-07-27 | 263 | The whole frontend, served by the backend |
| Setup view, UI fixes | 2026-07-28 | — | Setup tab; bugs found by actually looking at the running UI |
| **v2 · Resume tailoring** | 2026-07-28 | — | Fit analysis, cover letter, code-level honesty check |
| Closing loops | 2026-07-28 | — | Follow-up drafts, better default search, URL-hash routing, honest "best source" |
| **Scheduled hunting** | 2026-07-28 | — | Scheduler, new-match alerts, `alerted_at/alerted_score` |
| **Password + tunnel** | 2026-07-28 | 357 | Basic-auth gate, `share.sh`, `docs/DEPLOY.md`; per-model quota handling |
| **v2 · Interview prep** | 2026-07-29 | 386 | Prep agent + endpoint + Pipeline dialog; shared `grounding.py`; layout fix |
| README refresh | 2026-07-29 | 386 | Latest commit `f7ec019` |

After the build, no new code was committed; the work moved to using the app:

| Date | What happened |
|---|---|
| 2026-08-06 | **First real use** — a real job search: open-web discovery plus jba's scorer and warmth ranking. 12 jobs and 15 contacts saved. Exposed the product gaps in §22. Details in §18.1. |
| 2026-08-08 | Every saved link re-checked over HTTP; one expired posting replaced. |
| 2026-08-21 | **Second search** (internships / remote SDE): 18 jobs saved and scored. Found that skill overlap is not rarity, and that pay is ignored. Details in §18.2. |
| 2026-10-02 | Codex AI-tool files added to the folder (§5.3); this handbook written. |

---

## 21. Bugs that only showed up in real runs (the main lesson)

> **The single most important lesson of this project:** at every phase, the tests passed and the
> real run still broke. Green tests mean "what I thought of works". They cannot catch what nobody
> thought of. **Build with tests, then run it for real and read the output.**

8 of the 61 commits (~13%) fix bugs that passing tests did not catch:

| Commit | What broke in real use | The fix |
|---|---|---|
| `fc851c5` | Groq cut the resume JSON off mid-string (no `max_tokens`); the model returned `skills` as a flat list | Always set `max_tokens`; spell out the exact JSON shape; retry 3× |
| `f31b7d3` | Warmth scoring, 4 bugs with a real LinkedIn export: alumni written as an acronym ("DTU Delhi") didn't match; alumni written in full didn't match; the one-letter language **"C"** matched any word containing a c, so a *recruiter* "shared your stack"; "IndiaMART InterMESH Ltd" didn't match "ex-IndiaMART" | `utils/text.py`: university aliases, company suffix stripping, whole-word matching |
| `ab6582d` | UI bugs only visible by looking at the running app (e.g. white-on-light-teal button in dark mode) | Fixed after screenshots |
| `9a554fd` | Follow-up messages re-introduced the sender (58 words) | Follow-up-specific prompt rules (24 words) |
| `2cf4391` | A "speed-up" (5 jobs at once) made scoring **slower**: 13.5 s/job vs 4.3 s | Probe one job first; only go wide while the primary model is healthy. Measure, don't guess. |
| `a7056e8` | A real scheduled hunt found 3 bugs 345 tests missed: the old database lacked the new `alerted_at` column; the SDK's hidden retries made 9 requests per call; quota handling | Auto-add missing columns; `max_retries=0`; daily-quota handling |
| `a059430` | The honesty check flagged "Acknowledge the lack of Java" as a claim of Java, and flagged 5 of 6 interview answers on words like "about" | Admission-aware, clause-by-clause check; `named_only` mode for prep |
| `70bba82` | A third button pushed an icon outside the kanban card | Seen only in a screenshot; CSS fix |

Smaller ones found the same way: the alumni opener asked for "a chat" instead of the referral; DMs
ended with an email sign-off; the API accepted `job_id` and never used it (draft said SDE-1 for an
SDE-2 role); the default search was "AI" (too broad); "best: arbeitnow" shown at 0% response rate;
`APP_PASSWORD` in a developer's `.env` broke 70 tests.

**Checklist after building any feature:**
- [ ] Run it against the real resume / API / database and **read** the output.
- [ ] Run it against an **old** database. Did you add a column? Is it nullable?
- [ ] Could the model's answer be cut off? Set `max_tokens`.
- [ ] Added a warning or check? Count how often it fires. Mostly-wrong warnings are worse than none.
- [ ] Changed performance? **Measure** before and after.
- [ ] Changed the UI? **Take a screenshot**, including at phone width (~390 px).
- [ ] Added an `.env` setting? Make sure the test suite does not depend on your own `.env`.

---

## 22. What is missing, and what to do next

### 22.1 Needs only configuration (all free)

| Missing | Effect today | How to fix |
|---|---|---|
| **Telegram bot token + chat id** | Scheduled hunts can find new jobs but cannot tell anyone. **The biggest gap.** | @BotFather → token; message the bot; read chat id from `getUpdates`; put both in `.env`. |
| **Serper (or SerpApi) key** | Referrals come only from your connections + the manual link. | serper.dev, 2,500 free, no card. |
| **Real LinkedIn connections export** | The CSV in `data/connections/` is sample data. | Download from LinkedIn and save it there. |
| **Scheduler settings** | No automatic hunting. | `HUNT_SEARCH_TERM=…`, `HUNT_EVERY_HOURS=12`. |

### 22.2 Product gaps found in the real job searches (2026-08-06 and 2026-08-21)

1. **No Wellfound, Unstop or Naukri-specific source.** These carry the best India data (experience
   range, salary in LPA, remote/office), and the real search had to be done largely by hand because
   of this. Naukri via JobSpy often hits a captcha. **Highest-value next feature.**
2. **The scorer ignores work authorization.** A remote job scored 85/100 and was the top pick even
   though the posting required US citizenship. The score measures skill fit only.
3. **Experience mismatch is buried in the reasoning text.** "3+ years required" jobs still scored
   ~45 without a clear flag. It should be its own signal.
4. **Warmth measures "how well you know them", not "do they hire".** A CTO whose LinkedIn headline
   literally said "(Hiring!)" scored 1/5. A "hiring signal" should be combined with warmth.
5. **Skill overlap is not rarity.** Generic full-stack internships scored 90 because React/Node
   matched trivially, while a voice-AI role matching rare, proven experience scored 70. Rare skills
   should weigh more than many common ones.
6. **Pay and company quality are ignored.** There is no salary column, so "₹25–40k/month" only
   lives in description text, and a ₹1k/month internship can rank next to a ₹40k/month one.
   Parse and store salary, then use it.
7. **Jobs saved without a score sink out of sight.** The 13 jobs saved by hand on 2026-08-06 were
   never scored, so they sort last in the Jobs tab. Either score everything that is saved, or show
   unscored jobs separately.

### 22.3 Planned earlier but deliberately not built

- **Stealth browser scraping** (`camofox-browser`) for Wellfound/Instahyre/Cutshort — needs Docker,
  which is not installed. Deferred.
- **Sending email through the Gmail API** — `mailto:` works with zero setup and keeps you in control.
- **Pushing tracker reminders to Telegram** — reminders are computed on request; a small addition
  once Telegram is configured.
- **`ever-jobs`, People Data Labs, Apollo** — evaluated on paper, never needed.

### 22.4 Small housekeeping noticed while writing this

- `backend/db/models.py` comments `JobRow.id` as `sha256(company|title|date)`; the real key is
  `company|title` (see `utils/dedup.py`).
- `backend/main.py` uses FastAPI's deprecated `@app.on_event("startup")` (the 3 test warnings);
  the modern replacement is a `lifespan` handler.
- `AGENTS.md`, `.agents/`, `.codex/`, `logs/` are untracked tooling and not in `.gitignore`.
- `docs/PROJECT_GUIDE.md` is stale (§23).

---

## 23. Old docs that are out of date

The repo keeps its history honestly, but some docs describe plans, not reality. Here is what they
get wrong today:

| Doc | Says | Reality |
|---|---|---|
| `docs/PROJECT_GUIDE.md` (June 2026) | "We are building Phase 1"; status table shows Phase 1 half done | Everything is built (§20) |
| same | Free LLM via **OpenRouter** | Direct **Gemini** + **Groq** fallback since 2026-07-12 |
| same | **WhatsApp** alerts | **Telegram** |
| same | **camofox** used for walled boards | Not built (needs Docker) |
| same | SerpApi = 100 free searches/month | **250**/month; **Serper** (2,500 one-time) leads |
| same | `career-ops` reused for tailoring | Tailoring was built in-house (`resume_tailor.py`) with its own honesty check |
| same | Windows-first run instructions, OpenRouter key | See §13 here |
| `job-referral-finder-PRD.md` (v1.0) | Proxycurl, paid Claude, custom scrapers, APScheduler, ₹450/month | Proxycurl is dead; free models; JobSpy; asyncio scheduler; ~₹0/month. Its "READ FIRST" banner says so. |
| `docs/superpowers/specs/…v2-design.md` | The plan after research | Mostly right in direction; differences are recorded in each phase write-up |
| `docs/superpowers/plans/2026-07-13-phase2-…` (schema block) | Job id hashes company+title+**date** | company+title (recorded as a deliberate deviation in the same file) |

**Accurate today:** `README.md`, `docs/DEPLOY.md`, the Phase 2–5 write-ups, the code, and this file.

---

## 24. Privacy and safety: what never goes to GitHub

| Thing | Where | Why it must stay private |
|---|---|---|
| API keys, password | `.env` | Anyone with them can spend your quotas or open your app |
| Your profile | `data/profile/profile.json`, the database | Your personal details |
| The database | `data/db/career_agent.db` | Jobs, contacts, drafts, offers |
| LinkedIn export | `data/connections/Connections.csv` | **Other people's** names, employers and emails |
| Resume PDFs | anywhere (`*.pdf` is gitignored) | Personal |

All of these are in `.gitignore`. Before any commit, run `git status` and make sure none of them
appear. **Never paste `.env` contents into a chat, ticket or document.**

If the app is shared through `share.sh`, everything above is behind that URL — which is why the
script refuses to run without `APP_PASSWORD`.

**Pushing to GitHub:** the repo belongs to the **`Manan0802`** GitHub account; pushes must come
from that account. If a push fails with **403**, check `gh auth status` and switch to `Manan0802`.
Do not add other accounts as collaborators to fix it.

---

## 25. How to extend it (recipes for developers)

**House style:** small modules with a docstring that explains *why*; comments explain decisions and
past failures, not syntax; every agent retries 3× and raises `ModelUnavailable`; every external
source fails soft; every new behaviour gets a test first.

### Add a new job source (e.g. Wellfound)

1. Create `backend/services/job_sources/wellfound_adapter.py` with
   `fetch_wellfound_jobs(...) -> list[dict]`, returning the standard shape:
   `title, company, location, url, description, date_posted, source_engine="wellfound", fetched_at`.
   No login. Catch per-page errors and log them.
2. Write `tests/test_wellfound_adapter.py` with a saved sample response (mock `httpx`).
3. Add it to the `sources` dict in `_ingest()` in `backend/agents/job_hunter_graph.py`.
4. Run a real hunt and check the jobs look right (titles, companies, links).

### Add a column to a table

1. Add it to the model in `backend/db/models.py` **as nullable** (`nullable=True`).
2. Add it to the `_COLUMNS`/`_FIELDS` tuple of the matching store in `backend/services/`.
3. `init_db()` will add it to existing databases automatically on next start. Test against the
   real, old database too.

### Add an endpoint

1. Add the function to the right file in `backend/api/routes/` (or create a new router and
   `include_router` it in `main.py`).
2. Keep it thin: validate with a Pydantic model, call a service/agent, return JSON.
3. Add `tests/test_<area>_api.py` using FastAPI's `TestClient`; point `DB_PATH` at a temp file and
   call `init_db()`.
4. Add the call and its TypeScript type to `frontend/src/lib/api.ts`.

### Add a new AI task

1. New file in `backend/agents/`. Use `complete()` from `backend/llm/router.py` only.
2. Spell out the exact JSON shape in the system prompt; strip markdown fences; validate with
   Pydantic; retry 3×; raise `ModelUnavailable` at the end.
3. Pick a `max_tokens` that fits the task (not the 8,000 default).
4. If the output could claim experience, run `unsupported_terms()` from `grounding.py` on it.
5. Mock `complete` in tests; then run it for real several times and read the answers.

### Add a tab to the UI

1. Add the id to `ViewId` in `frontend/src/lib/view.ts`.
2. Create `frontend/src/views/MyTab.tsx` taking `ViewProps`.
3. Add it to `VIEWS` in `App.tsx`.
4. Give every list loading / empty / error states. Screenshot it in light, dark and at ~390 px.

---

## 26. Glossary

| Term | Plain meaning |
|---|---|
| **Agent** | Here: a step where an AI does the thinking. "AI agent" in general: software that acts on its own toward a goal (like the scheduled hunt). |
| **API** | A way for programs to talk to each other over the web. The backend's API is the list of URLs in §10. |
| **API key** | A secret password that lets you use someone's API (Gemini, Groq, Serper…). |
| **Backend / frontend** | The part that does the work on a server / the part you see in the browser. |
| **Basic auth** | The simplest web login: the browser pops up a username/password box. |
| **Circuit breaker** | After a service fails several times, stop calling it for a while instead of hammering it. |
| **Cloudflare tunnel** | A free service that gives your laptop a public HTTPS address without opening your router. |
| **Cosine similarity** | A number from −1 to 1 saying how similar two lists of numbers (embeddings) are. |
| **Codex** | Another AI coding tool; its config files sit next to the project (§5.3). |
| **Dedup** | Removing duplicates. |
| **DevTools protocol (CDP)** | The remote-control interface built into Chrome; used here to click and screenshot the UI from a script. |
| **Dork (Google dork)** | A Google search using operators like `site:linkedin.com/in/` to find very specific pages. |
| **Embedding** | Turning text into a list of numbers so a computer can measure how similar two texts are. |
| **FastAPI** | The Python framework that turns functions into web URLs. |
| **Firecrawl** | A web search and scraping service used (through an MCP server) for research and job discovery. |
| **Hook** | A script Claude Code runs automatically at a set moment — here, before each prompt, to suggest tools. |
| **Free tier** | The amount of a paid service you can use for free (e.g. 20 requests/day). |
| **Gitignore** | A file listing what Git must never save or upload. |
| **Groq / Gemini** | Two companies offering AI models with free tiers. Gemini is Google's. |
| **Hash (SHA-256)** | A fixed-length fingerprint of some text. Same text → same fingerprint. Used for ids. |
| **Human in the loop** | The AI prepares, a human approves before anything real happens. |
| **JobSpy** | An open-source Python library that scrapes several job boards at once. |
| **JSON** | A common text format for structured data: `{"name": "Asha", "skills": ["Python"]}`. |
| **Kanban** | A board with columns for stages; cards move left to right. |
| **LangGraph** | A library for building step-by-step AI pipelines as a graph of named steps. |
| **LLM** | Large Language Model — the AI that reads and writes text (Gemini, GPT, Claude…). |
| **markitdown** | Microsoft's library that converts PDF/Word into plain text (markdown). |
| **MCP** | Model Context Protocol — a standard way to plug tools into AI assistants. Only used by the developer tools around this repo, not by the app. |
| **Middleware** | Code that runs on every web request before the real handler (here: the password check). |
| **Mock** | A fake stand-in for an outside service, used in tests. |
| **Obsidian vault** | A folder of linked markdown notes, viewed in the Obsidian app; the project's long-term notebook. |
| **PRD** | Product Requirements Document — the written plan of what to build. |
| **Prompt** | The instructions and text sent to an AI model. |
| **Pydantic** | A Python library that checks data has the right shape and types. |
| **Rate limit / quota** | How many requests a service allows per minute / per day. |
| **React** | A JavaScript library for building interactive web pages. |
| **Referral** | Someone inside a company recommending you for a job. |
| **Scraping** | A program reading a website automatically to pull out data. |
| **SQLite** | A database that is just one file. No server needed. |
| **SQLAlchemy** | The Python library used to read and write the database. |
| **Superpowers** | The planning workflow (brainstorm → design spec → step-by-step plan → TDD) used to plan each phase; it names the `docs/superpowers/` folder. |
| **Symlink** | A shortcut: a file or folder that points to another location. |
| **TDD** | Test-Driven Development: write the test first, watch it fail, then write the code. |
| **Token** | A chunk of text (~¾ of a word) that AI models count for limits and cost. |
| **Upsert** | Update the row if it exists, insert it if it doesn't. |
| **uvicorn** | The program that runs the FastAPI backend as a web server. |
| **venv** | A private Python installation for one project. |
| **Vite** | The tool that builds the frontend into plain files a browser can load. |
| **Warmth score** | This app's 1–5 rating of how likely a contact is to refer you. |

---

*Keep this file true. If you change how something works, update the matching section here in the
same commit, so the next person reading it gets reality and not history.*
