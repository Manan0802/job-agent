# 🎯 Job + Referral Finder — AI Career Agent

A **personal, local, ~₹0/month** AI agent that automates job hunting end‑to‑end:
finds best‑fit jobs across many boards, scores them against your resume, finds **warm referral
contacts**, drafts personalized outreach (you approve before sending), and tracks every application.

Built with **Python · FastAPI · LangGraph · free‑first LLMs (Gemini/Groq) · SQLite · React**.
Privacy‑first (everything runs locally). Human‑in‑the‑loop (never auto‑applies or auto‑DMs).

---

## 📖 New here? Read this first

👉 **[`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md)** — the complete A‑to‑Z explainer.
Written so **anyone** (even a non‑coder) understands *what* we're building, *why*, *how*, which
open‑source tools we reuse and *what we take from each*, the cost, the safety rules, what's built
so far, and how to run it.

Then, for depth:
- [`job-referral-finder-PRD.md`](job-referral-finder-PRD.md) — original product vision (v1.0).
- [`docs/superpowers/specs/2026-06-28-job-referral-finder-v2-design.md`](docs/superpowers/specs/2026-06-28-job-referral-finder-v2-design.md) — optimized **v2.1 design** (what changed & why).
- [`docs/superpowers/plans/2026-06-28-phase1-foundation.md`](docs/superpowers/plans/2026-06-28-phase1-foundation.md) — step‑by‑step Phase‑1 build plan.

---

## ⚡ Quick start

```bash
git clone https://github.com/Manan0802/job-agent
cd job-agent

python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then paste your free Gemini key into LLM_API_KEY

cd frontend && npm install && npm run build && cd ..
uvicorn backend.main:app --reload
```

Open **http://localhost:8000** for the app, or `/docs` for the API.

Only one key is required to start: a free Gemini key from
[aistudio.google.com/apikey](https://aistudio.google.com/apikey) (no card).
Everything below is optional and the app degrades gracefully without it:

| Add | Unlocks | Where |
|---|---|---|
| `GROQ_API_KEY` | Automatic fallback when Gemini is busy | [console.groq.com/keys](https://console.groq.com/keys) |
| `SERPER_API_KEY` | Finding people you *don't* already know | [serper.dev](https://serper.dev) — 2,500 free, no card |
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | Job alerts on your phone | @BotFather on Telegram |
| `data/connections/Connections.csv` | People you already know at a company | LinkedIn → Settings → Get a copy of your data |

Working on the UI itself? `cd frontend && npm run dev` gives hot reload on
port 5173 and proxies the API to 8000.

---

## 🏗️ Status

All six phases are built, with **263 tests** and every stage verified against
live data rather than mocks.

| Phase | What it does |
|---|---|
| 1 · Foundation | Resume PDF → structured profile everything else reads |
| 2 · Job Hunter | Scrapes every board, ranks locally, scores the shortlist with an LLM |
| 3 · Referral Finder | Who could refer you into a company, warmest first, with reasons |
| 4 · Outreach | Drafts a personal message per contact; you approve and send |
| 5 · Tracker | Pipeline, follow-up reminders, response rate by source |
| 6 · UI | The whole thing in a browser, served by the same backend |

Deferred to v2: resume tailoring per job, interview prep.

**Two rules the code enforces:** nothing sends on your behalf, and no
authenticated scraping. `backend/services/send_links.py` even has a test
asserting it never grows a `send_*` function.

---

## 🧰 Built on (the "reuse, don't reinvent" stack)

JobSpy · Remotive/RemoteOK/Arbeitnow/Himalayas/Jobicy APIs · YC public listings ·
Serper + SerpApi (referral search) · markitdown · sentence‑transformers (free local ranking) ·
LangGraph · React + Tailwind.
Full ledger of *what we take from each* is in the [PROJECT_GUIDE](docs/PROJECT_GUIDE.md#5-the-tool-ledger--every-repo-we-researched-basic--max-and-what-we-take-from-each).

Each phase has a write-up covering what shipped, what deviated from the plan,
and the bugs that only appeared against real data — see
[`docs/superpowers/plans/`](docs/superpowers/plans/).

---

*Personal project · free/open‑source first · not affiliated with any job board.*
