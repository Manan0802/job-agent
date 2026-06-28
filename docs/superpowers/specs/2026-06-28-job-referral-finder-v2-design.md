# Job + Referral Finder — AI Career Agent (Optimized Design v2.1)

**Status:** Research-validated design (supersedes PRD v1.0)
**Author:** Manan · **Last updated:** 2026-06-28
**Decision:** Fresh proper build (not evolving old `Ai-job`), lifting proven patterns from it.
**Stack:** Python · LangGraph · **free-first LLM (Gemini/Groq via OpenRouter)** · FastAPI · React
**Budget target:** ≤ ₹500/month — **projected ~₹0** (all free tiers)

> Successor to `job-referral-finder-PRD.md`. Keeps the PRD's 5-module structure, but rewrites
> what 2026 research + the existing `Ai-job` codebase proved wrong or wasteful. Read the PRD for
> full module/UI/schema detail; read this for **what changed and why**.

---

## 0. Context: there is already a working predecessor (`Ai-job`)

A prior Streamlit app exists at `Desktop/Ai-job` (repo: `github.com/Manan0802/Ai-job-portal`).
**Decision (2026-06-28): build a fresh, properly-architected tool** — the old one is considered
messy — **but lift its proven patterns.** It already does ~80% of the PRD, for free:

| Already-built pattern | Verdict for new build |
|---|---|
| Job scraping via **JobSpy + Remotive** | **LIFT** — same engines, cleaner wrapper |
| **Referral via SerpApi Google-dork** (`site:linkedin.com/in/ "Co" "Role" "India"`) | **LIFT — this becomes the primary referral method** (safest, cheapest) |
| `resume_tailor.py` (gap analysis + tailored PDF + cover letter) | **LIFT logic** into v2 tailoring module |
| **WhatsApp alerts** (Twilio) | **LIFT** — add as notification channel (PRD lacked this) |
| Free **OpenRouter** LLM (Gemini Flash) | **LIFT — free-first LLM strategy** |
| `interview_war_room.py` | bank for later (out of v1 scope) |
| Streamlit UI, ad-hoc scripts, Google-Sheets storage | **DROP** — replaced by React + FastAPI + SQLite |

⚠️ **Security note:** old `Ai-job/scrapper/ai_config.json` holds plaintext keys (OpenRouter,
SerpApi, Twilio). It is gitignored (not leaked), but rotate those keys and never commit them.
New build uses `.env` only.

---

## 1. What Changed From PRD v1.0 (executive summary)

| # | Area | PRD v1.0 | v2.1 (this doc) | Reason |
|---|---|---|---|---|
| 1 | Job scrapers | 7 custom scrapers | **JobSpy** + free remote APIs + few custom | Maintained lib; old app already proves it works |
| 2 | Referral data | Proxycurl (₹250/mo) | **SerpApi Google-dork** (primary) + CSV + manual fallback | Proxycurl **dead (Jul 2025)**; SerpApi safer & free |
| 3 | LLM | Claude Sonnet (paid) | **Free-first: Gemini Flash / Groq (free), escalate to better Gemini only for quality** | Student budget; free models already proven in old app |
| 4 | Job scoring | Claude every job | **Local embeddings pre-filter** → LLM scores top ~15 | Cost + speed |
| 5 | Outreach | auto-send roadmap | **HITL only, no auto-DM/auto-apply ever** | LinkedIn legal action killed auto-appliers (AIHawk) |
| 6 | Notifications | UI badge only | **+ WhatsApp/Telegram alerts** | Lifted from old app; pull-free awareness |
| 7 | Budget | ~₹450/mo | **~₹0/mo** | All free tiers |

**Build philosophy:** hybrid — wrap proven OSS, lift proven old-app patterns, build custom only
for differentiators (warmth scoring, India-niche boards, orchestration glue).

---

## 2. Validated Tooling Decisions

### 2.1 Job ingestion (all free)
- **JobSpy** (`speedyapply/JobSpy`, 3.7k⭐, MIT, `pip install python-jobspy`) — one call scrapes
  LinkedIn, Indeed, Glassdoor, Google, ZipRecruiter, **Naukri**, Bayt. India supported. Tier-1 engine.
- **Free remote-job APIs (no scraping):** Remotive (`remotive.com/api/remote-jobs`), RemoteOK
  (`remoteok.com/api`), Arbeitnow, Himalayas. Add as cheap high-quality remote coverage.
- **Custom / niche boards (not in JobSpy):**
  - YC `workatastartup` → **REUSE/MODIFY `jwc20/waasuapi`** (scraper API, maintained to 2025).
  - Wellfound / Instahyre / Cutshort (Cloudflare/JS-walled) → **scrape via camofox-browser** (see 2.6).
  - Watchlist career pages → camofox or generic Playwright.

### 2.6 Stealth scraping engine — **camofox-browser** (`jo-inc/camofox-browser`, MIT)
Anti-detect browser server (Camoufox = Firefox with C++-level fingerprint spoofing; beats
Cloudflare/Google where plain Playwright is blocked). Runs as a **local sidecar service**
(~40MB idle, Docker/$5 VPS), our scrapers call its REST API.
- **Use for:** Wellfound, Instahyre, Cutshort, watchlist pages, and as an optional **proxy/GeoIP
  layer for JobSpy's LinkedIn** (its weak point).
- **Token-efficient:** accessibility snapshots (~90% smaller than HTML) → cheap to feed free LLMs.
- Features we lean on: `@google_search`/`@linkedin_search` macros, cookie import (own cookies, no
  credential sharing), proxy rotation, session persistence.
- ⚠️ **Boundary:** use for public Cloudflare-walled boards only. **Do NOT** turn it into an
  authenticated LinkedIn auto-scraper (ban/ToS risk). Referral discovery stays on SerpApi (public
  Google results). Matches the safe-cheap rule.
- Alternatives if needed: `daijro/camoufox` (pure-Python, no server), `ultrafunkamsterdam/nodriver`,
  `Vinyzu/patchright`, `steel-dev/steel-browser`.

### 2.7 Resume tailoring (v2) — **career-ops** (`santifer/career-ops`)
Full Claude-Code career plugin (job eval + CV tailoring at scale) — already installed as the
`/career-ops` skill. **Reuse for v2 tailoring** instead of rebuilding; reference its job-eval logic
for our scorer.
- **Evaluate:** `ever-jobs/ever-jobs` — aggregates 160+ sources, ships an MCP server. Could
  replace several custom scrapers if coverage is good (research task).

### 2.2 Referral finding (all free, all safe) — re-architected
Primary method lifted from old app:
1. **SerpApi Google-dork** (PRIMARY) — `site:linkedin.com/in/ "{company}" "{role}" "India"`,
   100 free searches/mo. Hits *public* LinkedIn via Google — no login, no ToS breach, no ban risk.
2. **Own LinkedIn connections CSV** — free, 1st-degree, ToS-clean (emails mostly stripped now).
3. **Manual search URL fallback** — generated `linkedin.com/search/...` link, zero cost.
- Proxycurl: ❌ dead. PDL/Apollo: optional, only if SerpApi coverage gaps appear.
- Warmth scoring framework from PRD §7.2 unchanged.

### 2.3 LLM strategy (free-first routing)
- **Default:** Gemini Flash (via OpenRouter free) + Groq (Llama) free — classification, filtering,
  scoring, drafting.
- **Escalate:** better Gemini model (e.g. Gemini Pro) only for high-stakes parsing/drafting where
  free output is weak. Track spend; stay ~₹0.
- Implement as a thin `llm_router` (task → model) so providers swap without touching logic.

### 2.4 Resume parsing & tailoring
- Parse: **markitdown → LLM → Pydantic `profile.json`** (PRD plan). Lift `resume_reader.py` ideas.
- Tailoring (v2): lift `resume_tailor.py` (gap analysis + PDF + cover letter). Patterns banked:
  `waygeance/AutoATS`, `vikasmishra16/JDAlchemy-ATSmaxxing`.

### 2.5 Architecture reference
Model LangGraph orchestration on `sergio11/langgraph_jobsearch_assistant` (reference only).

---

## 3. Cost Model

| Service | Usage | Monthly cost |
|---|---|---|
| Gemini Flash (OpenRouter free) + Groq free | parse, score shortlist, draft | **₹0** |
| Better Gemini model (escalation) | rare high-stakes calls | ~₹0–50 |
| `sentence-transformers` (local) | embed jobs for pre-filter | **₹0** |
| JobSpy + Remotive/RemoteOK/Arbeitnow/Himalayas + custom | ingestion | **₹0** |
| SerpApi free (100/mo) | referral discovery | **₹0** |
| SQLite + WhatsApp(Twilio trial)/Telegram | storage + alerts | **₹0** |
| **Total** | | **~₹0/mo** (≤ ₹500 ✅) |

Cost rules: cache scores & SerpApi results in DB; free models first; escalate only when needed.

---

## 4. System Architecture (deltas from PRD §4)

Same shape (React → FastAPI → LangGraph → SQLite). Key deltas:

### 4.1 Job Hunter sub-graph
```
ingest (JobSpy + Remotive/RemoteOK/Arbeitnow/Himalayas + custom, parallel async)
  → normalize to jobs schema → dedup (hash company+title+date)
  → EMBED + cosine-prefilter vs profile embedding   [local, free]
  → top N (~15) → LLM score+breakdown (free Gemini/Groq)
  → save → notify (UI badge + WhatsApp/Telegram alert)
```

### 4.2 Referral Finder sub-graph
```
serpapi_dork(company, role)  [PRIMARY, free 100/mo]
  → parse_csv (1st-degree match)  [free]
  → cross-reference + DTU/alumni flag
  → warmth_score (PRD §7.2)
  → if budget spent → manual search URL  [free]
  → rank + present → outreach drafter
```
Budget caps (SerpApi, any LLM escalation) enforced via `api_budget` table.

---

## 5. Schema Additions (on PRD §10)
```sql
ALTER TABLE jobs ADD COLUMN embedding BLOB;          -- cached job embedding
ALTER TABLE jobs ADD COLUMN source_engine TEXT;      -- 'jobspy' | 'remotive' | 'custom:wellfound'...
ALTER TABLE jobs ADD COLUMN prefilter_score REAL;    -- cosine sim, pre-LLM

CREATE TABLE api_budget (                             -- enforce free-tier caps
    provider TEXT PRIMARY KEY,                        -- 'serpapi' | 'gemini_pro' | ...
    month TEXT, calls_used INTEGER DEFAULT 0, monthly_cap INTEGER
);
```
`profiles` gains cached `profile_embedding BLOB`. Rest of PRD §10 stands.

---

## 6. v1 Scope
In: **Resume Profiler, Job Hunter, Referral Finder, Outreach Drafter, Tracker CRM** + **WhatsApp/Telegram alerts**.
Deferred to v2: resume auto-tailoring (lift `resume_tailor.py`), interview prep (lift
`interview_war_room.py`), LinkedIn auto-DM, auto-apply.

---

## 7. Safety / Legal
- **No auto-DM, no auto-apply in v1.** Draft → human approves → send. (AIHawk pulled under
  LinkedIn legal pressure.)
- Referral data only via: SerpApi (public Google results), own CSV, manual links. **No direct
  authenticated LinkedIn scraping.**
- JobSpy: respect rate limits, delays, optional proxies on LinkedIn.
- All user data local (SQLite + files). Secrets in `.env`, never committed.

---

## 8. Tool Triage (from Manan's 30-tool research, 2026-06-28)

| Tool | Verdict | Note |
|---|---|---|
| **JobSpy** | ✅ USE | Tier-1 ingestion |
| **Remotive / RemoteOK / Arbeitnow / Himalayas APIs** | ✅ USE | free remote coverage, no scraping |
| **SerpApi** (via old `networking_agent`) | ✅ USE | primary referral method |
| **camofox-browser** (`jo-inc/camofox-browser`, MIT) | ✅ USE | stealth engine for walled boards (Wellfound/Instahyre) + JobSpy proxy layer |
| `daijro/camoufox`, `nodriver`, `patchright`, `steel-browser` | 📖 REFERENCE | camofox alternatives if needed |
| **career-ops** (`santifer/career-ops`) | ✅ USE (v2) | resume tailoring + job-eval (already installed skill) |
| `jwc20/waasuapi` | 🟨 MODIFY | YC workatastartup scraper |
| **ever-jobs** (160+ sources, MCP) | 🔬 EVALUATE | could replace custom scrapers |
| **Resume Matcher** | 📖 REFERENCE | matching/keyword logic for scorer |
| **OpenResume / Reactive Resume** | 📖 REFERENCE | ATS parser + resume render ideas (v2) |
| **career-ops** (Claude skill, already installed) | ✅ USE (v2) | resume tailoring / job eval |
| **JobSync** | 📖 REFERENCE | self-hosted tracker UX ideas |
| **ATS Screener / AutoATS / JDAlchemy** | 📖 REFERENCE (v2) | ATS scoring + tailoring patterns |
| Interview prep repos (CIU, tech-interview-handbook, system-design-primer) | 📚 LINK-OUT | resource list in interview module (v2) |
| **AIHawk / ApplyPilot / EasyApplyBot / Auto_job_applier / AutoApplyMax** | ❌ AVOID | auto-apply = ban + legal risk |
| **Job Application Bot (Ollama)** | 📖 REFERENCE | local-LLM referral/hiring-manager pattern |
| Upwork scrapers, JSON Resume, OpenCATS, SpotAxis | ⏭️ OUT OF SCOPE | freelance/ATS-host, not this tool |
| Proxycurl, pyresparser | ❌ DEAD/STALE | — |

---

## 9. Open Research Tasks (owner: Manan)
1. Wellfound + YC `workatastartup` — current DOM/anti-bot; working 2026 scraper or login-walled?
2. `ever-jobs` — does its 160-source coverage include Indian + startup boards well? (could cut custom work)
3. SerpApi free tier — confirm 100/mo still current; test dork quality for Indian profiles.
4. Best free Gemini model tier on OpenRouter for parsing/drafting quality.
5. Gmail MCP / WhatsApp — confirm send capability for outreach.

---

## 10. Build Phases (revised)
| Phase | Focus |
|---|---|
| 1 — Foundation | FastAPI + SQLite + `.env` + resume upload → `profile.json` + `llm_router` |
| 2 — Job Hunter | JobSpy adapter + free remote APIs + embed-prefilter + free-LLM shortlist scoring + alerts |
| 3 — Referral Finder | SerpApi dork (lifted) + CSV + warmth scoring + manual fallback + budget caps |
| 4 — Outreach | HITL draft/edit/approve + Gmail/WhatsApp send |
| 5 — Tracker CRM | Kanban + stats + follow-up reminders |
| 6 — Polish | React UI, logging, settings, budget dashboard |
| v2 | resume tailoring (lift), interview prep (lift), ATS scoring |

---

## 11. Reference Index
| Repo / Service | Verdict |
|---|---|
| `speedyapply/JobSpy` (3.7k⭐, MIT) | USE — ingestion |
| Remotive / RemoteOK / Arbeitnow / Himalayas | USE — free remote APIs |
| SerpApi | USE — referral dork |
| `ever-jobs/ever-jobs` | EVALUATE |
| `sergio11/langgraph_jobsearch_assistant` | REFERENCE — LangGraph agent |
| `microsoft/markitdown` | USE — PDF→markdown |
| `waygeance/AutoATS`, `JDAlchemy-ATSmaxxing`, career-ops | BANK for v2 — tailoring |
| Proxycurl | ❌ DEAD (Jul 2025) |
| AIHawk / auto-appliers | ❌ legal/ban risk |
| `pyresparser` | ❌ stale |

---

*v2.1 — research + existing-codebase validated. Next: implementation plan (writing-plans) once approved.*
