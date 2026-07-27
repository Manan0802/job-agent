# Phase 4 — Outreach Drafter

**Goal:** turn a ranked referral contact into a message worth sending — personal, honest, short — and put the user in control of every send.

**The safety rule this phase is built around:** no auto-DM, no auto-apply, ever. LinkedIn had AIHawk pulled for exactly that, and the account at risk here is the user's own — the same one they are job hunting with. So nothing in this phase sends anything. `backend/services/send_links.py` has a test asserting the module never grows a `send_*` function.

## Tasks — all complete (2026-07-27)

- [x] **Task 1 — `outreach_messages` table + lifecycle.** `MessageRow` and `backend/services/message_store.py`. A message moves draft → approved → sent only on the user's action. Redrafting replaces an un-sent draft but never touches a sent one, and editing an approved message returns it to draft so nothing goes out under an approval given for different words.
- [x] **Task 2 — LLM message drafter.** `backend/agents/outreach_drafter.py`. Six message types with their own length and channel; the type is picked from the real relationship (alumni → alumni opener, connection → referral ask, stranger → cold intro).
- [x] **Task 3 — Send hand-off.** `backend/services/send_links.py`. Email opens the user's own mail client prefilled via `mailto:`; a DM hands back the profile link and the text to paste. Both end with the user pressing send.
- [x] **Task 4 — API.** `backend/api/routes/outreach.py`: `POST /draft`, `GET`, `PUT /{id}`, `POST /{id}/approve`, `POST /{id}/sent`, `POST /{id}/skip`. Recording a send also updates the contact, which is what the tracker will read in Phase 5.

## What the prompt enforces

Drawn from PRD §8.3, and every rule is pinned by a test on the prompt itself since model output cannot be asserted directly:

- Open on **one** genuine shared point, taken from the warmth reasons that picked this contact — not a stack of flattery.
- Introduce the sender in at most two sentences.
- Never sycophantic; never praise the recipient's work.
- Always give an easy out ("no pressure", "totally understand if not").
- Close on one specific next step.
- No resume in a first message.
- **Use only facts from the profile** — never invent an employer, title, project or skill.

## Three quality gaps only real drafts exposed

Fixture tests passed while all three were live:

1. **The alumni opener asked for a chat, not a referral.** The whole point of the feature is the referral; the brief now says so for every role-targeting type.
2. **DMs closed with "Best,\nManan".** An email sign-off in a chat window reads as templated — the prompt now says a DM is a chat, not a letter.
3. **The API accepted `job_id` and never used it.** A live draft offered to apply for "a relevant SDE-1 opening" when the role was SDE-2 Backend, because the drafter was never handed the job. Caught only by running the full flow through HTTP.

## Phase 4 Deliverable — done
Verified live end to end through the real API: resume → referrals → draft → edit → approve → record sent, with the contact's status following along. 219 tests passing.

A real draft, generated during that run:

> Hey Rohit, hope you're doing well! Great connecting with you on here.
>
> I'm Manan, currently working as an SDE-1 at Bachatt Trusave Fintech while finishing my B.Tech at DTU. I focus a lot on backend development with Python and building scalable systems.
>
> I saw Zepto is hiring for an SDE-2 Backend role. Given my experience with Python and backend engineering, I'd love to be considered for it. Would you be open to referring me?
>
> Totally understand if you're too busy or if it's not a good time, no pressure at all. If you're open to it, let me know and I can send over the job link.
>
> — Manan

Every fact in it came from the parsed resume.

## Deferred deliberately
- **Gmail API sending.** `mailto:` works today with zero setup and keeps the user in the loop. OAuth would add real setup burden for a step the user is doing anyway.
- **Follow-up reminders.** The `followup` and `thank_you` message types exist and draft correctly; scheduling *when* to nudge belongs with the tracker in Phase 5.
