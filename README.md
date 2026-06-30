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
python -m venv .venv
.venv\Scripts\activate          # Windows  (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # then paste a free OpenRouter key into LLM_API_KEY
python -m pytest -v             # all tests should pass
```

Get a free LLM key at **https://openrouter.ai**.

---

## 🏗️ Status

**Phase 1 — Foundation** (in progress, strict TDD):

- [x] Project scaffold + config loader
- [x] SQLite database + profiles model
- [x] Free‑first LLM router
- [ ] PDF → markdown (markitdown)
- [ ] Profile schema + resume parser
- [ ] FastAPI app + resume upload endpoint
- [ ] Profile edit endpoint

**Roadmap:** Phase 2 Job Hunter → 3 Referral Finder → 4 Outreach → 5 Tracker CRM → 6 React UI → v2 (resume tailoring, interview prep).
See the [PROJECT_GUIDE](docs/PROJECT_GUIDE.md#10-the-roadmap-what-comes-after-phase-1).

---

## 🧰 Built on (the "reuse, don't reinvent" stack)

JobSpy · Remotive/RemoteOK/Arbeitnow/Himalayas APIs · camofox-browser (anti‑detect) ·
SerpApi (referrals) · markitdown · career-ops (v2 tailoring) · sentence‑transformers (free scoring).
Full ledger of *what we take from each* is in the [PROJECT_GUIDE](docs/PROJECT_GUIDE.md#5-the-tool-ledger--every-repo-we-researched-basic--max-and-what-we-take-from-each).

---

*Personal project · free/open‑source first · not affiliated with any job board.*
