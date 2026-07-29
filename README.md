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
| `HUNT_SEARCH_TERM` + `HUNT_EVERY_HOURS` | Hunting on a schedule, without opening the app | your target role, e.g. `Backend Engineer` and `12` |
| `APP_PASSWORD` | Reaching the app from your phone — see [`docs/DEPLOY.md`](docs/DEPLOY.md) | anything long |

The **Setup** tab inside the app shows all of this: what is configured, what
each missing piece unlocks, where to get it, and what is left of each free tier.

Working on the UI itself? `cd frontend && npm run dev` gives hot reload on
port 5173 and proxies the API to 8000.

---

## 🏗️ Status

Everything planned is built, with **386 tests** and every stage verified
against live data rather than mocks.

| Phase | What it does |
|---|---|
| 1 · Foundation | Resume PDF → structured profile everything else reads |
| 2 · Job Hunter | Scrapes every board, ranks locally, scores the shortlist with an LLM |
| 3 · Referral Finder | Who could refer you into a company, warmest first, with reasons |
| 4 · Outreach | Drafts a personal message per contact; you approve and send |
| 5 · Tracker | Pipeline, follow-up reminders, response rate by source |
| 6 · UI | The whole thing in a browser, served by the same backend |
| v2 · Resume tailoring | What to change for one job, split into what you buried and what you lack |
| v2 · Interview prep | Questions this posting makes likely, each answered from your own work |
| **Scheduled hunting** | Hunts on its own and messages you about **new** matches only |

### Hunting on a schedule

This is what makes it an agent rather than a tool. Set `HUNT_SEARCH_TERM` and
`HUNT_EVERY_HOURS` and it hunts without being opened.

It alerts **only on jobs it has not already told you about**. A scheduled hunt
re-finds the same listings every run, so alerting on all of them daily is how an
alert gets muted. Each job records the score it was alerted at, so one that
later scores higher can still surface.

### Three rules the code enforces

- **Nothing sends on your behalf.** `backend/services/send_links.py` has a test
  asserting it never grows a `send_*` function.
- **No authenticated scraping.** LinkedIn stays on the public path only.
- **No claiming what your resume cannot back.** Tailoring advice and interview
  answers are checked *in code*, because instructing the model not to invent
  experience did not stop it.

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

## 🌍 Reaching it from your phone

It runs on your machine and is shared over a free Cloudflare tunnel:

```bash
brew install cloudflared   # once
./share.sh                 # prints a public HTTPS URL
```

`share.sh` refuses to open a tunnel unless `APP_PASSWORD` is set — your resume,
connections export and drafts all sit behind that URL.

It is deliberately **not** deployed to Vercel, Workers or Render.
[`docs/DEPLOY.md`](docs/DEPLOY.md) records why: `torch` alone is twice Vercel's
bundle limit, a hunt outlives the function timeout, SQLite needs a filesystem
that survives — and every cloud host puts scraping on a datacenter IP that job
boards throttle.

---

*Personal project · free/open‑source first · not affiliated with any job board.*
