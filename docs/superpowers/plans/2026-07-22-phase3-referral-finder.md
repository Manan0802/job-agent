# Phase 3 — Referral Finder

**Goal:** given a target company, find the warmest people who could refer the user in, ranked with the reasons behind each ranking.

**Why it matters:** a referral is worth roughly 10× a cold application, and research during Phase 2 planning found that **no consumer job-search copilot does this** — Teal, Careerflow, Sonara, LazyApply, JobCopilot, Simplify, LoopCV and JobHire.AI all compete on resume tailoring and apply-volume. The only "AI + referrals" products found work the opposite direction, helping employers mine their own staff. This is the project's differentiator.

**Architecture:** `gather → merge → score → save`, as a LangGraph `StateGraph`.

## Sources, in order of what they cost

| Source | Degree | Cost | Notes |
|---|---|---|---|
| The user's own LinkedIn export | 1st | free | The only source that knows who the user actually knows |
| Public Google search for LinkedIn profiles | 2nd | metered | No login, no LinkedIn API — ToS-clean |
| Manual LinkedIn search link | — | free | Always offered, works when everything else is gone |

**Search providers** (researched 2026-07-22): **Serper** leads — 2,500 free searches, one-time grant, no card. **SerpApi** is the permanent floor — 250/month, resets forever, no card. Every call is checked against the `api_budget` table before it goes out.

Two providers were ruled out. **Google's Custom Search JSON API is closed to new signups** and returns HTTP 410 from Jan 2027 — building on it was not possible. **Brave's free tier was removed in Feb 2026**; it now requires a card and meters overage with no spending cap, which is a real bill risk on a ₹0 budget.

**What a search result actually yields:** LinkedIn de-indexed headlines and work history in early 2024, so a SERP hit reliably gives **name, profile URL and current employer** (from the page title) and little else. That is enough — the user opens the profile to decide.

## Tasks — all complete (2026-07-22)

- [x] **Task 1 — `referral_contacts` table.** `ContactRow` in `backend/db/models.py`, plus `contact_id()` in `backend/utils/dedup.py` keyed on the profile URL (a contact can arrive from both the CSV and a search; the URL proves they are the same person) and falling back to name+company, since LinkedIn's export often omits the URL.
- [x] **Task 2 — LinkedIn connections CSV parser.** `backend/services/connections_csv.py`. Handles the notes preamble LinkedIn puts before the header row, and matches employers across legal suffixes ("Zepto" vs "Zepto Marketplace Private Limited").
- [x] **Task 3 — People search + budget cap.** `backend/services/people_search.py` and `backend/services/api_budget.py`. Provider chain with per-provider monthly metering; with no keys set it returns nothing quietly so the free path still works.
- [x] **Task 4 — Warmth scoring.** `backend/services/warmth.py`. 1–5 per the PRD's table, and every score carries its reasons.
- [x] **Task 5 — Pipeline + API.** `backend/agents/referral_finder_graph.py`, `backend/services/contact_store.py`, `backend/api/routes/referrals.py`: `POST /api/v1/referrals/find`, `GET /api/v1/referrals`.

## Deviations from the PRD, all deliberate

- **Nothing is hardcoded to one candidate.** The PRD's warmth table is written around its author — "DTU alumni", "Delhi-based". Alma mater, home city, past employers and tech stack all come from the user's own parsed profile instead, so the scoring works for any user.
- **Seniority counts for everyone, not only strangers.** The PRD lists seniority only under 2nd-degree rows. But LinkedIn's export carries no education field, so in CSV-only mode every connection tied at the same score and the ranking said nothing. A manager can approve a referral; a junior usually cannot.
- **Four columns dropped** — `phone`, `mutual_connections`, `outreach_message_id`, `notes`. Their only data source was Proxycurl, which shut down in 2025, or they belong to a later phase.
- **Proxycurl replaced entirely** by the public-search path, as the v2 design already anticipated.

## Bugs that only real data exposed

Fixture tests passed while all four of these were broken; each surfaced the first time the scorer ran against the actual parsed resume:
- Alumni written as an acronym ("DTU Delhi") did not match "Delhi Technological University (DTU), New Delhi".
- Alumni written in full did not match either — the campus-city suffix was being required.
- The one-letter language "C" matched *any* word containing a c, so a recruiter "shared your stack".
- "IndiaMART InterMESH Ltd" did not match a profile saying "ex-IndiaMART".

Fixed by `backend/utils/text.py`, which builds institution aliases (bracketed acronym, derived acronym, core name) and matches employers and skills on word boundaries.

## Phase 3 Deliverable — done
`POST /api/v1/referrals/find` returns ranked contacts with reasons, plus a manual search link. Verified live end to end: a sample export produced correctly-ranked, correctly-explained contacts through the real HTTP API. 171 tests passing.

## Still needed from the user
- **The real LinkedIn connections export** (LinkedIn → Settings & Privacy → Data Privacy → Get a copy of your data → Connections) at `data/connections/Connections.csv`. It is gitignored — it holds other people's names, employers and emails.
- **A Serper or SerpApi key** (both free, neither needs a card) to unlock 2nd-degree discovery. Without one, referrals come from the CSV and the manual link only.
