# Phase 5 — Application Tracker

**Goal:** never lose track of where an application stands, and know whether any of this is actually working.

## Pipeline

`saved → applied → referral_pending → interview_scheduled → interview_done → offer_received → accepted | rejected`

Every stage change sets when to check back, and only a finished application stops asking:

| Stage | Nudge after | What it says |
|---|---|---|
| saved | 3 days | You saved this but never applied — still interested? |
| applied | 6 days | No reply yet — send a follow-up? |
| referral_pending | 5 days | Your referrer hasn't come back — worth a gentle nudge? |
| interview_scheduled | 1 day | Confirm the slot and prep. |
| interview_done | 2 days | Send a thank-you while it's still fresh. |
| offer_received | 3 days | They're waiting on your answer. |

## Tasks — all complete (2026-07-27)

- [x] **Task 1 — Pipeline store.** `ApplicationRow` and `backend/services/application_store.py`. Re-saving a job you have already progressed returns the existing application rather than rewinding it; notes append rather than overwrite.
- [x] **Task 2 — Reminders and stats.** `backend/services/tracker_insights.py`.
- [x] **Task 3 — API.** `backend/api/routes/applications.py`: `POST /track`, `GET`, `POST /{id}/stage`, `POST /{id}/note`, `POST /{id}/offer`, `GET /reminders`, `GET /stats`.

## Two judgement calls worth writing down

**A rejection counts as a response.** The user marks something rejected when they actually hear back; a job that ghosted them stays sitting in `applied`. Counting rejections as silence would make the response rate read far worse than reality.

**Jobs only ever saved are excluded from the rate entirely.** Never applying is not the same as being ignored, and letting saved jobs drag the denominator down would punish the user for browsing.

Both matter because the response rate is the number that tells the user whether to change strategy.

## Deviations from the PRD schema

- **One `offer_amount` + `offer_currency`** instead of separate INR and USD columns — covers both without inventing a conversion rate.
- **`resume_version_used` and `cover_letter` dropped** — they belong to resume tailoring, which is a v2 feature.

## Phase 5 Deliverable — done
Verified live through the real API, all the way from a resume: 490 jobs found and scored → top job tracked → moved through every stage → offer of ₹24,00,000 recorded → stats reporting 100% response rate and naming the source that produced it. 260 tests passing.

## Deferred
- **The Kanban board itself** is Phase 6 (React UI). The API already returns everything a board needs — stage, dates, notes, and the whole pipeline in one call.
- **Reminder notifications.** Reminders are computed on request; pushing them to Telegram is a small addition once the user sets a bot token.
