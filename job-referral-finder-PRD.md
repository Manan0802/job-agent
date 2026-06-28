# 📄 PRODUCT REQUIREMENTS DOCUMENT
# Job + Referral Finder — AI Career Agent
**Version:** 1.0  
**Status:** Pre-Build (Research + Architecture Phase)  
**Author:** Manan  
**Stack:** Python + LangGraph + Claude Sonnet + FastAPI + React  
**Date:** June 2026

---

## TABLE OF CONTENTS
1. [Project Overview](#1-project-overview)
2. [Goals & Non-Goals](#2-goals--non-goals)
3. [User Persona](#3-user-persona)
4. [System Architecture](#4-system-architecture)
5. [Module 1 — Resume Profiler](#5-module-1--resume-profiler)
6. [Module 2 — Job Hunter](#6-module-2--job-hunter)
7. [Module 3 — Referral Finder](#7-module-3--referral-finder)
8. [Module 4 — Outreach Drafter](#8-module-4--outreach-drafter)
9. [Module 5 — Application Tracker / CRM](#9-module-5--application-tracker--crm)
10. [Data Models & Schemas](#10-data-models--schemas)
11. [API Design](#11-api-design)
12. [UI/UX Specifications](#12-uiux-specifications)
13. [Tech Stack — Full Detail](#13-tech-stack--full-detail)
14. [LinkedIn & Data Strategy](#14-linkedin--data-strategy)
15. [LangGraph Agent Architecture](#15-langgraph-agent-architecture)
16. [Relevant Open Source Projects](#16-relevant-open-source-projects)
17. [Relevant MCPs](#17-relevant-mcps)
18. [Budget & Cost Breakdown](#18-budget--cost-breakdown)
19. [Build Phases & Milestones](#19-build-phases--milestones)
20. [Future Roadmap](#20-future-roadmap)
21. [Known Risks & Mitigations](#21-known-risks--mitigations)

---

## 1. PROJECT OVERVIEW

### 1.1 What Is This?
An AI-powered personal career agent that automates the most painful parts of job hunting:
- Finding best-fit opportunities across multiple platforms
- Identifying warm referral paths through network analysis
- Drafting personalized outreach messages
- Tracking all applications in a CRM-style pipeline

### 1.2 Why Build This?
Manual job hunting in 2026 is broken:
- Applying cold = <3% response rate
- Referrals = 10x higher interview conversion
- Manually searching 10+ job boards = hours wasted daily
- Generic outreach messages get ignored

This agent changes the equation: **smart search + warm intros + personalized outreach = dramatically better outcomes.**

### 1.3 Tagline
> *"Resume se job dhundhe, referral contacts identify kare — AI kare sab, tum sirf choose karo."*

### 1.4 Scope for v1.0
- Personal use tool (for Manan)
- Local deployment (web UI on localhost)
- Targets: Indian Startups + International Remote + Big Tech + YC Companies
- Roles: Software Engineering / AI Engineering
- Budget: ₹500/month API costs max

---

## 2. GOALS & NON-GOALS

### ✅ GOALS (v1.0)
- [ ] Parse resume once, use everywhere as identity source of truth
- [ ] Scrape/aggregate jobs from 10+ platforms every 2-3 days
- [ ] Score each job against user profile (match %)
- [ ] Find referral contacts in target companies via LinkedIn network
- [ ] Draft personalized LinkedIn DM + email outreach per contact
- [ ] Human-in-the-loop approval before any message is sent
- [ ] Track all applications in a pipeline with follow-up reminders
- [ ] Web UI accessible from browser (localhost:3000)
- [ ] All data stored locally (privacy first)

### ❌ NON-GOALS (v1.0 — defer to later)
- Mobile app
- Multi-user SaaS
- Auto-apply without human review
- Full LLM-powered interview prep (separate tool)
- Integration with Freelancing Agent (Phase 2)
- Cloud deployment / remote access
- Payment / subscription features
- WhatsApp/SMS outreach channel

---

## 3. USER PERSONA

```
Name:         Manan
Role:         Software Engineer (AI Focus)
Background:   DTU CSE Graduate, LangGraph/LangChain expert
              Built SARA (multi-agent system at IndiaMART)
Current:      Employed, actively looking for better opportunity
Target Roles: SWE / AI Engineer / ML Engineer
Target Cos:   Indian Startups (early/growth), Remote, Big Tech, YC
Network:      1000-3000 LinkedIn connections, moderate DTU alumni contact
Budget:       ₹500/month
Tech Comfort: High — CLI, Python, APIs, LangGraph all familiar
Timeline:     Immediately active
```

---

## 4. SYSTEM ARCHITECTURE

### 4.1 High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        WEB UI (React)                         │
│         FastAPI Backend ← → LangGraph Orchestrator            │
└──────────────────┬───────────────────────────────────────────┘
                   │
    ┌──────────────▼──────────────┐
    │      ORCHESTRATOR NODE       │
    │   (LangGraph StateGraph)     │
    │   Routes tasks to agents     │
    └──┬──────┬──────┬─────┬──────┘
       │      │      │     │
       ▼      ▼      ▼     ▼
  ┌────────┐ ┌────┐ ┌────┐ ┌──────┐
  │RESUME  │ │JOB │ │REF │ │OUTCH │
  │PROFILER│ │HUNT│ │FIND│ │DRAFT │
  └────┬───┘ └──┬─┘ └──┬─┘ └──┬───┘
       │        │       │      │
       └────────┴───────┴──────┘
                    │
           ┌────────▼────────┐
           │   SQLite DB      │
           │  (local storage) │
           │                  │
           │  - profile.json  │
           │  - jobs table    │
           │  - contacts tbl  │
           │  - messages tbl  │
           │  - tracker tbl   │
           └─────────────────┘
```

### 4.2 Data Flow

```
USER UPLOADS RESUME
       │
       ▼
RESUME PROFILER
→ Extracts structured profile
→ Saves as profile.json + DB
       │
       ▼
JOB HUNTER (runs every 2-3 days via scheduler)
→ Scrapes all job boards
→ Scores each job vs profile
→ Deduplicates, filters, ranks
→ Saves to jobs table
→ Notifies user via UI
       │
       ▼
USER SELECTS TARGET JOB/COMPANY
       │
       ▼
REFERRAL FINDER
→ Takes company name
→ Searches LinkedIn network (CSV + Proxycurl)
→ Ranks contacts by warmth score
→ Returns: "3 contacts found — 1 DTU alumni, 2 SDE2"
       │
       ▼
OUTREACH DRAFTER
→ For each contact: generates personalized message
→ User reviews draft in UI
→ User approves → auto-send via LinkedIn/Email API
→ Saves to messages table
       │
       ▼
TRACKER / CRM
→ Logs application (company, role, date, contact)
→ Tracks status changes
→ Sets follow-up reminders (5-7 days)
→ Shows pipeline dashboard
```

---

## 5. MODULE 1 — RESUME PROFILER

### 5.1 Purpose
Convert user's PDF resume into a structured JSON identity object that every other module uses. Single source of truth.

### 5.2 Input
- PDF resume file (uploaded via UI)

### 5.3 Processing Pipeline

```
Step 1: PDF Upload
  → User uploads via web UI
  → Saved to /data/resume/resume.pdf

Step 2: PDF → Markdown Conversion
  → Tool: markitdown[all]
  → Command: markitdown /data/resume/resume.pdf > /tmp/resume.md
  → Output: Clean markdown text of resume

Step 3: Markdown → Structured JSON (LLM Extraction)
  → LLM: Claude Sonnet
  → System Prompt: Strict JSON extraction prompt (see schema below)
  → Output: profile.json

Step 4: Validation
  → Pydantic model validation
  → Missing fields flagged to user
  → User can manually edit via UI form

Step 5: Storage
  → Save profile.json to /data/profile/profile.json
  → Insert into SQLite profiles table
  → Broadcast to all other modules
```

### 5.4 Output Schema (profile.json)

```json
{
  "personal": {
    "name": "Manan",
    "email": "manan@email.com",
    "phone": "+91-XXXXXXXXXX",
    "location": "New Delhi, India",
    "linkedin_url": "https://linkedin.com/in/manan",
    "github_url": "https://github.com/manan",
    "portfolio_url": "https://manan.dev"
  },
  "education": [
    {
      "institution": "Delhi Technological University",
      "degree": "B.Tech",
      "field": "Computer Science",
      "graduation_year": 2024,
      "cgpa": 8.5,
      "relevant_courses": ["ML", "DSA", "DBMS"]
    }
  ],
  "experience": [
    {
      "company": "IndiaMART",
      "role": "AI Engineering Intern",
      "duration_months": 6,
      "start_date": "2024-01",
      "end_date": "2024-06",
      "highlights": ["Built SARA multi-agent system", "LangGraph orchestration"],
      "tech_used": ["LangGraph", "LangChain", "Python", "FastAPI"]
    }
  ],
  "skills": {
    "languages": ["Python", "JavaScript", "TypeScript", "SQL"],
    "frameworks": ["LangGraph", "LangChain", "FastAPI", "React", "Node.js"],
    "ai_ml": ["RAG", "FinBERT", "Embeddings", "Multi-Agent", "Groq", "Claude API"],
    "tools": ["Git", "Docker", "Postman", "VS Code"],
    "databases": ["MongoDB", "PostgreSQL", "SQLite", "Pinecone"],
    "cloud": ["Vercel", "Railway", "AWS basics"]
  },
  "projects": [
    {
      "name": "SARA",
      "description": "LangGraph-based multi-agent system at IndiaMART",
      "tech": ["LangGraph", "Python", "RAG"],
      "impact": "Handled X queries/day",
      "github": null
    },
    {
      "name": "InvestMate",
      "description": "MERN + Gemini AI portfolio tracker",
      "tech": ["React", "Node.js", "MongoDB", "Gemini API"],
      "impact": null,
      "github": "https://github.com/manan/investmate"
    }
  ],
  "preferences": {
    "target_roles": ["Software Engineer", "AI Engineer", "ML Engineer", "Full Stack Engineer"],
    "experience_level": "Entry-Mid (1-3 years)",
    "years_of_experience": 1,
    "preferred_salary_range_inr": {
      "min": 1200000,
      "max": 2500000
    },
    "preferred_salary_range_usd": {
      "min": 60000,
      "max": 120000
    },
    "work_mode": ["remote", "hybrid", "in-office"],
    "preferred_locations": ["New Delhi", "Bengaluru", "Mumbai", "Remote"],
    "target_company_types": ["indian_startup", "international_remote", "big_tech", "yc_backed"],
    "notice_period_days": 30,
    "open_to_relocation": true
  },
  "keywords": ["AI Engineering", "LangGraph", "Multi-Agent", "RAG", "Python", "MERN", "LangChain"],
  "profile_version": "1.0",
  "last_updated": "2026-06-27T00:00:00Z"
}
```

### 5.5 LLM Prompt (Resume Extraction)

```
SYSTEM:
You are a precise resume parser. Extract ALL information from the 
resume text provided and return ONLY a valid JSON object matching 
the schema below. No preamble, no markdown, no explanation. 
Pure JSON only.

Schema: [INSERT SCHEMA]

Rules:
- If a field is missing from resume, set it to null
- skills must be categorized correctly
- Extract ALL projects, not just recent ones
- Infer experience_level from YOE: 0-1=Junior, 1-3=Entry-Mid, 3-5=Mid, 5+=Senior
- Do NOT hallucinate any data not present in resume

USER:
[RESUME MARKDOWN TEXT]
```

### 5.6 UI for Resume Profiler
- Upload button (PDF only, max 5MB)
- Progress bar during extraction
- Editable form view post-extraction
- "Update Resume" button for future updates
- Visual skills tag cloud

---

## 6. MODULE 2 — JOB HUNTER

### 6.1 Purpose
Scrape, aggregate, deduplicate and score job listings from 10+ platforms. Alert user every 2-3 days with best matches.

### 6.2 Job Sources (Priority Order)

#### Tier 1 — API/Official Access (most reliable)
| Platform | Method | Cost | Coverage |
|---|---|---|---|
| Wellfound (AngelList) | Unofficial API / scrape | Free | Best for Indian + global startups |
| RemoteOK | Public JSON API | Free | Remote roles globally |
| YC Jobs | Public scrape (workatastartup.com) | Free | YC-backed companies |
| LinkedIn Jobs | PhantomBuster / Apify actor | ~Free tier | Widest coverage |

#### Tier 2 — Scraping Required
| Platform | Method | Notes |
|---|---|---|
| Naukri.com | Playwright scraper | India's largest job board |
| Instahyre | Playwright scraper | AI-matched Indian platform |
| Cutshort | API (free tier available) | Indian startup focused |
| Indeed India | Playwright scraper | High volume |

#### Tier 3 — Direct Company Career Pages
| Company Type | Method | Notes |
|---|---|---|
| Watchlist companies | Direct URL scraper | User defines watchlist |
| YC W24/S24 batch | Hardcoded URL list + scraper | Freshest startups |
| Unicorn startups India | Hardcoded list | Zepto, Meesho, etc. |

### 6.3 Job Scraping Architecture

```python
# LangGraph nodes for job hunting

class JobHunterState(TypedDict):
    profile: dict          # from profile.json
    raw_jobs: list         # scraped raw listings
    filtered_jobs: list    # after basic filter
    scored_jobs: list      # after LLM scoring
    new_jobs: list         # after dedup vs DB
    
# Nodes:
1. fetch_wellfound_node()     → scrape Wellfound
2. fetch_remoteok_node()      → call RemoteOK JSON API
3. fetch_yc_jobs_node()       → scrape workatastartup.com
4. fetch_linkedin_node()      → Apify actor / scraper
5. fetch_naukri_node()        → Playwright scraper
6. fetch_cutshort_node()      → Cutshort API
7. fetch_watchlist_node()     → scrape user-defined URLs
8. dedup_and_filter_node()    → remove duplicates, basic filter
9. score_jobs_node()          → LLM scoring vs profile
10. save_and_notify_node()    → save to DB, trigger UI notification

# All nodes run in parallel where possible (LangGraph parallel edges)
```

### 6.4 Job Scoring Logic

Each job gets scored by Claude Sonnet against user profile:

```
Score Components (out of 100):
- Technical Skills Match:     35 points
  (how many required skills does user have?)
- Role Title Match:           20 points  
  (SWE/AI Eng/ML Eng = high match)
- Experience Level Match:     15 points
  (junior role vs user's YOE)
- Company Type Match:         15 points
  (startup/big tech/YC preference alignment)
- Salary Range Match:         10 points
  (if salary info available)
- Remote/Location Match:       5 points

Final: "87% match" displayed in UI
```

### 6.5 Job Scoring Prompt

```
SYSTEM:
You are a precise job-candidate matcher. Given a job listing and 
candidate profile, output ONLY a JSON scoring object.

Output format:
{
  "match_score": 87,
  "match_breakdown": {
    "skills_match": 32,
    "role_match": 18,
    "experience_match": 13,
    "company_type_match": 15,
    "salary_match": 7,
    "location_match": 2
  },
  "matched_skills": ["Python", "LangGraph", "FastAPI"],
  "missing_skills": ["Kubernetes", "Go"],
  "why_good_fit": "Strong AI/ML background aligns with role requirements",
  "why_might_not_fit": "Requires 3+ years, user has 1 year",
  "apply_recommendation": "strong_yes | yes | maybe | no"
}

USER:
Job Listing: [JOB TEXT]
Candidate Profile: [PROFILE JSON]
```

### 6.6 Job Data Schema (DB)

```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,              -- hash of company+title+date
    platform TEXT,                    -- wellfound/linkedin/naukri etc
    company_name TEXT,
    company_stage TEXT,               -- seed/series-a/growth/public
    role_title TEXT,
    role_type TEXT,                   -- fulltime/contract/freelance
    location TEXT,
    is_remote BOOLEAN,
    salary_min INTEGER,               -- in INR or USD
    salary_max INTEGER,
    salary_currency TEXT,
    tech_stack TEXT,                  -- JSON array stored as text
    job_description TEXT,
    apply_url TEXT,
    posted_date TEXT,
    scraped_date TEXT,
    match_score INTEGER,
    match_breakdown TEXT,             -- JSON
    matched_skills TEXT,             -- JSON array
    missing_skills TEXT,             -- JSON array
    apply_recommendation TEXT,
    status TEXT DEFAULT 'new',       -- new/saved/applied/ignored
    is_notified BOOLEAN DEFAULT FALSE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 6.7 Deduplication Strategy
- Hash: `company_name + role_title + date` → unique ID
- If same job found on multiple platforms → merge, keep highest quality source
- Mark job as "seen before" if same hash exists in DB (older than 7 days)

### 6.8 Scheduler
```python
# APScheduler for periodic runs
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    run_job_hunter,
    'interval',
    hours=60,  # every 2.5 days approximately
    id='job_hunt_scheduler'
)
scheduler.start()
```

### 6.9 Notification System (UI)
- Red badge on "Jobs" tab in UI showing new count
- Toast notification on page load: "23 new jobs found since last check"
- Jobs sorted by match_score descending by default

---

## 7. MODULE 3 — REFERRAL FINDER

### 7.1 Purpose
Given a target company, find the warmest possible path to get a referral. This is the highest-value feature — referral = 10x interview rate.

### 7.2 Warmth Scoring Framework

```
Warmth Levels (1-5):
  5 ★★★★★  DTU alumni + 1st degree connection
  4 ★★★★   DTU alumni + 2nd degree
  3 ★★★    1st degree connection (any college)
  3 ★★★    Delhi-based employee (1st degree)  
  2 ★★     SDE2/SDE3 employee (2nd degree)
  2 ★★     Same tech stack person (2nd degree)
  1 ★      Any employee at company (cold DM)
```

### 7.3 Data Sources for Referral Finding

#### Source 1: LinkedIn CSV Export (FREE — user's own data)
- User exports own LinkedIn connections CSV (Settings → Data privacy → Get a copy of your data)
- Contains: First Name, Last Name, Position, Company, Connected On, Email (sometimes)
- Agent parses this CSV to find 1st degree connections at target companies
- Refresh: User re-exports every 3 months (or when network grows significantly)

**How to get it:**
```
LinkedIn → Me → Settings & Privacy → 
Data Privacy → Get a copy of your data → 
Connections → Request Archive → Download CSV
```

#### Source 2: Proxycurl API (PAID — for 2nd degree + employee discovery)
- Find employees at a company: `/proxycurl/api/linkedin/company/employees/`
- Get person profile: `/proxycurl/api/v2/linkedin`
- Cost: ~$0.01 per API call (employee listing), $0.03 per profile
- Budget allocation: Max 200 calls/month = ~$2-3 (~₹250) per month
- Strategy: Only call for high-priority companies (match_score > 80)

#### Source 3: Apollo.io / Hunter.io (Email Finding — FREE tier)
- Find email of a person when only name + company known
- Apollo: 50 free credits/month
- Hunter.io: 25 free searches/month
- Use for email outreach path when LinkedIn DM not preferred

#### Source 4: Manual LinkedIn Search (fallback, always available)
- When Proxycurl budget exhausted → generate search URL
- `https://linkedin.com/search/results/people/?keywords=DTU&company=TARGET_COMPANY`
- Present this URL to user as "Search Link" to manually find contacts

### 7.4 Referral Finder Flow

```python
class ReferralFinderState(TypedDict):
    target_company: str
    target_job_id: str
    user_profile: dict
    linkedin_connections: list    # from parsed CSV
    company_employees: list       # from Proxycurl
    scored_contacts: list         # after warmth scoring
    top_contacts: list            # top 3-5 to reach out

# Nodes:
1. parse_linkedin_csv_node()
   → Load user's connections CSV
   → Filter by company_name == target_company
   → Returns: 1st degree connections at company

2. fetch_company_employees_node()
   → Call Proxycurl company employees API
   → Filter by SDE/Engineer roles
   → Returns: list of employees with profiles

3. cross_reference_node()
   → Match Proxycurl results with user's CSV
   → Identify: 1st degree vs 2nd degree
   → Flag: DTU alumni (check education field)

4. warmth_score_node()
   → Score each contact per warmth framework
   → Additional signals:
     - Graduation year proximity (±2 years = warmer)
     - Shared past employer = warmer
     - Mutual connections count

5. rank_and_present_node()
   → Sort by warmth score descending
   → Prepare output for UI display
   → Trigger outreach drafter for top contacts
```

### 7.5 Contact Schema (DB)

```sql
CREATE TABLE referral_contacts (
    id TEXT PRIMARY KEY,
    target_company TEXT,
    target_job_id TEXT,
    linkedin_url TEXT,
    name TEXT,
    current_role TEXT,
    current_company TEXT,
    education TEXT,               -- JSON (college, year)
    location TEXT,
    degree_type TEXT,             -- 1st / 2nd
    warmth_score INTEGER,         -- 1-5
    warmth_reasons TEXT,          -- JSON array of reasons
    email TEXT,                   -- if found via Apollo/Hunter
    phone TEXT,                   -- if available
    mutual_connections INTEGER,
    outreach_status TEXT DEFAULT 'pending',  -- pending/drafted/sent/replied/referred
    outreach_message_id TEXT,     -- FK to messages table
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_updated TEXT
);
```

### 7.6 UI Output Example

```
🎯 Referral Contacts for: Zepto (SDE-II, Backend)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ★★★★★  Rahul Sharma — SDE-2 @ Zepto
   DTU CSE 2022 • 1st Degree Connection
   "Warm intro path: Direct LinkedIn DM"
   [Draft Message] [View Profile]

2. ★★★★   Priya Gupta — Backend Engineer @ Zepto
   DTU IT 2021 • 2nd Degree via Ankit (common connection)
   "Ask Ankit for intro, or cold DM"
   [Draft Message] [View Profile]

3. ★★★    Mohit Jain — Software Engineer @ Zepto
   NSUT 2022 • 1st Degree Connection
   "Delhi-based, same YOE — peer reach"
   [Draft Message] [View Profile]
```

---

## 8. MODULE 4 — OUTREACH DRAFTER

### 8.1 Purpose
Generate personalized, context-rich outreach messages for each referral contact. NOT generic templates. Human reviews and approves before any send.

### 8.2 Message Types

| Type | When | Channel | Length |
|---|---|---|---|
| Referral Request | Asking for job referral | LinkedIn DM | 150-200 words |
| Cold Intro | No shared context | LinkedIn DM | 100-150 words |
| Alumni Warm DM | Same college | LinkedIn DM | 120-180 words |
| Email Outreach | If email available | Email | 200-250 words |
| Follow-up (no reply) | After 5-7 days silence | Same channel | 80-100 words |
| Thank You | After referral given | LinkedIn/Email | 80-100 words |

### 8.3 Message Generation Prompt

```
SYSTEM:
You are an expert at writing warm, authentic professional outreach 
messages. Write a referral request message with these rules:

TONE RULES:
- Warm and genuine, NOT corporate/formal
- Peer-to-peer for same-age contacts (casual but professional)
- More formal for senior contacts (3+ years gap)
- Never sycophantic ("I really admire your work at X")
- Specific to their background, not generic
- Short — people skim DMs

CONTENT RULES:
- Open with ONE genuine connection point (alumni/mutual connection)
- Brief intro of sender (2 sentences max)
- Clear ask — referral for specific role at their company
- Respect their time — "no pressure" framing
- Close with a specific CTA (not vague "let me know")
- Never attach resume in first message

OUTPUT FORMAT:
{
  "subject": "email subject if email, null if DM",
  "message": "full message text",
  "tone": "casual|professional|formal",
  "word_count": 145,
  "personalization_elements": ["DTU alumni", "both SDE-2 level", "worked on similar RAG stack"]
}

INPUTS:
Sender Profile: [PROFILE JSON]
Recipient Info: [CONTACT JSON]  
Target Job: [JOB JSON]
Warmth Level: [1-5]
Message Type: [referral_request|cold_intro|etc]
```

### 8.4 Message Examples (What Agent Should Generate)

**Example — Alumni Referral Request (DM):**
```
Hey Rahul!

Saw we both graduated from DTU CSE — you 2022, me 2024. 
Small world 😄

I'm a software engineer currently working at [current company] with 
focus on AI/LangGraph-based systems. I saw Zepto has an opening for 
SDE-2 Backend and honestly it looks like a great fit.

Would you be open to referring me? I've built production multi-agent 
systems and RAG pipelines — happy to share my resume if helpful.

Totally understand if not, no pressure at all. But if you can, 
it'd mean a lot!

— Manan
```

**Example — Follow-up (no reply after 6 days):**
```
Hey Rahul, just bumping this up in case it got buried. 
No worries if the timing isn't right — just wanted to check once more!
```

### 8.5 Human-in-the-Loop (HITL) Flow

```
Agent generates draft
       │
       ▼
UI shows draft to user with:
  - [Edit] button (inline editor)
  - [Approve & Send] button
  - [Regenerate] button (try again)
  - [Skip] button (don't send to this person)
       │
       ▼ (User edits if needed, then Approves)
       │
  LinkedIn DM Send:
  → Via LinkedIn API (if available)
  → OR via Playwright automation (if no API)
  → OR generate deep link for manual send
  
  Email Send:
  → Via Gmail API (OAuth) / SMTP
       │
       ▼
Message logged to DB
Status updated: pending → sent
Reminder set: 6 days later for follow-up
```

### 8.6 Messages Schema (DB)

```sql
CREATE TABLE outreach_messages (
    id TEXT PRIMARY KEY,
    contact_id TEXT,              -- FK referral_contacts
    job_id TEXT,                  -- FK jobs
    message_type TEXT,            -- referral_request/followup/etc
    channel TEXT,                 -- linkedin_dm/email
    subject TEXT,                 -- null for DMs
    body TEXT,
    tone TEXT,
    status TEXT DEFAULT 'draft',  -- draft/approved/sent/delivered/replied
    sent_at TEXT,
    reply_received BOOLEAN DEFAULT FALSE,
    reply_text TEXT,
    follow_up_scheduled_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## 9. MODULE 5 — APPLICATION TRACKER / CRM

### 9.1 Purpose
Track every job application in a visual pipeline. Never lose track of where you stand. Get reminded to follow up. Free, local, no Notion required.

### 9.2 Pipeline Stages

```
[Saved] → [Applied] → [Referral Pending] → [Interview Scheduled] 
       → [Interview Done] → [Offer Received] → [Accepted/Rejected]
```

### 9.3 Features

**Pipeline Board (Kanban view):**
- Drag-and-drop cards between columns
- Each card shows: company logo, role, match score, date applied
- Click card to expand: full details, contact info, message history

**Table View (sortable):**
- Sort by: date, match score, company, status
- Filter by: platform, remote, salary range, status

**Follow-up Reminders:**
- "Applied 5 days ago, no reply — send follow-up?" 
- "Interview was 3 days ago — send thank you?"
- "Offer expires in 2 days — decide!"

**Stats Dashboard:**
- Total applied: 34
- Response rate: 18%
- Active pipelines: 5
- Offers received: 1
- Most effective source: Wellfound (40% response rate)

### 9.4 Applications Schema (DB)

```sql
CREATE TABLE applications (
    id TEXT PRIMARY KEY,
    job_id TEXT,                  -- FK jobs table
    company_name TEXT,
    role_title TEXT,
    platform_applied TEXT,
    apply_url TEXT,
    applied_via TEXT,             -- direct/referral/cold
    referral_contact_id TEXT,     -- FK referral_contacts (if via referral)
    status TEXT DEFAULT 'saved',  -- saved/applied/referral_pending/interview_scheduled/etc
    applied_date TEXT,
    interview_date TEXT,
    offer_date TEXT,
    offer_amount_inr INTEGER,
    offer_amount_usd INTEGER,
    notes TEXT,
    follow_up_due TEXT,
    resume_version_used TEXT,
    cover_letter TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_updated TEXT
);
```

---

## 10. DATA MODELS & SCHEMAS

### 10.1 Complete SQLite DB Structure

```sql
-- Tables:
1. profiles           -- user resume data
2. jobs               -- scraped job listings  
3. referral_contacts  -- potential referral contacts
4. outreach_messages  -- drafted/sent messages
5. applications       -- tracked applications
6. watchlist          -- companies to monitor
7. scheduler_log      -- when last run, what found

-- Watchlist Table:
CREATE TABLE watchlist (
    id TEXT PRIMARY KEY,
    company_name TEXT,
    career_page_url TEXT,
    notify_on_any_opening BOOLEAN DEFAULT TRUE,
    target_roles TEXT,            -- JSON array of role keywords
    active BOOLEAN DEFAULT TRUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 10.2 File System Structure

```
job-referral-finder/
├── backend/
│   ├── main.py                   # FastAPI entry point
│   ├── config.py                 # API keys, settings
│   ├── agents/
│   │   ├── orchestrator.py       # LangGraph main graph
│   │   ├── resume_profiler.py    # Module 1
│   │   ├── job_hunter.py         # Module 2
│   │   ├── referral_finder.py    # Module 3
│   │   ├── outreach_drafter.py   # Module 4
│   │   └── tracker.py            # Module 5
│   ├── scrapers/
│   │   ├── wellfound.py
│   │   ├── remoteok.py
│   │   ├── yc_jobs.py
│   │   ├── linkedin.py
│   │   ├── naukri.py
│   │   ├── cutshort.py
│   │   └── career_page.py        # generic scraper
│   ├── services/
│   │   ├── proxycurl.py          # LinkedIn employee data
│   │   ├── apollo.py             # email finder
│   │   ├── gmail.py              # email sender
│   │   └── linkedin_send.py      # DM sender
│   ├── db/
│   │   ├── database.py           # SQLite connection
│   │   ├── models.py             # Pydantic models
│   │   └── migrations/
│   ├── utils/
│   │   ├── markitdown_parser.py  # PDF → markdown
│   │   ├── deduplicator.py
│   │   ├── scorer.py
│   │   └── scheduler.py          # APScheduler
│   └── api/
│       ├── routes/
│       │   ├── resume.py
│       │   ├── jobs.py
│       │   ├── referrals.py
│       │   ├── outreach.py
│       │   └── tracker.py
│       └── middleware.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Jobs.jsx
│   │   │   ├── Referrals.jsx
│   │   │   ├── Outreach.jsx
│   │   │   ├── Tracker.jsx
│   │   │   └── Profile.jsx
│   │   ├── components/
│   │   │   ├── JobCard.jsx
│   │   │   ├── ContactCard.jsx
│   │   │   ├── MessageEditor.jsx
│   │   │   ├── KanbanBoard.jsx
│   │   │   └── Sidebar.jsx
│   │   └── api/
│   │       └── client.js         # axios API client
│   └── package.json
├── data/
│   ├── resume/                   # uploaded resumes
│   ├── profile/                  # profile.json
│   ├── linkedin/                 # CSV exports
│   └── db/
│       └── career_agent.db       # SQLite DB
├── logs/
│   └── agent.log
├── .env                          # API keys (gitignored)
├── requirements.txt
├── package.json
├── README.md
└── docker-compose.yml            # optional, for easy setup
```

---

## 11. API DESIGN

### 11.1 Backend REST API (FastAPI)

```
BASE URL: http://localhost:8000/api/v1

# RESUME
POST   /resume/upload              # upload + parse resume
GET    /resume/profile             # get current profile
PUT    /resume/profile             # update profile manually
GET    /resume/profile/keywords    # get extracted keywords

# JOBS
GET    /jobs                       # list all jobs (filterable)
GET    /jobs/{id}                  # single job detail
POST   /jobs/search/trigger        # manual trigger job hunt
GET    /jobs/new/count             # count of unseen new jobs
PUT    /jobs/{id}/status           # update job status
GET    /jobs/stats                 # platform-wise stats
GET    /jobs/watchlist             # get watchlist
POST   /jobs/watchlist             # add to watchlist
DELETE /jobs/watchlist/{id}        # remove from watchlist

# REFERRALS
POST   /referrals/find             # find contacts for a company
GET    /referrals/{company}        # get contacts for company
GET    /referrals/contact/{id}     # single contact detail
PUT    /referrals/contact/{id}     # update contact info/status

# OUTREACH
POST   /outreach/draft             # generate message draft
PUT    /outreach/{id}              # edit draft
POST   /outreach/{id}/approve      # approve and send
POST   /outreach/{id}/regenerate   # regenerate draft
GET    /outreach/history           # message history
POST   /outreach/{id}/followup     # trigger follow-up draft

# TRACKER
GET    /tracker/applications       # all applications
POST   /tracker/applications       # add new application
PUT    /tracker/applications/{id}  # update status
GET    /tracker/pipeline           # kanban data
GET    /tracker/stats              # stats dashboard
GET    /tracker/reminders          # due follow-ups

# SCHEDULER
GET    /scheduler/status           # when last ran, next run
POST   /scheduler/trigger          # manual run
PUT    /scheduler/config           # change frequency
```

---

## 12. UI/UX SPECIFICATIONS

### 12.1 Tech Stack for UI
- **Framework:** React 18 + Vite
- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **Charts:** Recharts
- **Kanban:** @hello-pangea/dnd (drag and drop)
- **State:** Zustand (lightweight)
- **HTTP:** Axios
- **Notifications:** React Hot Toast

### 12.2 Page Structure

```
SIDEBAR (persistent):
├── 📊 Dashboard
├── 🔍 Jobs (badge: new count)
├── 🤝 Referrals
├── ✍️  Outreach (badge: pending approvals)
├── 📋 Tracker
└── 👤 My Profile

HEADER:
- Last scan: "2 days ago" | "Scan Now" button
- Status: "34 jobs tracked | 5 active"
```

### 12.3 Dashboard Page
- Summary stats cards (total jobs, match rate, applications, referrals)
- Top 5 new jobs (since last check)
- Pending outreach approvals (CTA)
- Follow-up reminders due today
- Quick actions: "Scan Now", "Upload New Resume"

### 12.4 Jobs Page
- Search bar + filters (remote, salary, company type, match score)
- Sort by: Match %, Date, Company
- Cards view (default) or Table view toggle
- Each card:
  - Company name + logo (fetched via Clearbit API — free)
  - Role title
  - Match score badge (color coded: green >80, yellow 60-80, red <60)
  - Salary range (if available)
  - Remote badge
  - Platform source badge
  - [Find Referral] button
  - [Apply] button (opens URL)
  - [Save] / [Ignore] buttons

### 12.5 Referrals Page
- Input: "Enter company name to find contacts"
- Results: Contact cards with warmth stars
- Each card: name, role, college, connection degree, warmth score
- [Draft Message] button per contact
- Status badges: pending / message sent / replied / referred

### 12.6 Outreach Page
- Queue of pending drafts needing approval
- Each item: contact info + message preview
- Inline editor (contentEditable or textarea)
- [Approve & Send] / [Edit] / [Regenerate] / [Skip] actions
- Sent history tab

### 12.7 Tracker Page
- Toggle: Kanban View / Table View
- Kanban: drag cards between pipeline stages
- Table: sortable columns, search
- Click any application → side panel with full detail:
  - Job details
  - Contact who referred (if any)
  - Message thread
  - Notes (editable)
  - Timeline of events

---

## 13. TECH STACK — FULL DETAIL

### 13.1 Core Stack

| Component | Technology | Why |
|---|---|---|
| Agent Orchestration | LangGraph 0.2+ | Familiar from SARA, best for complex multi-node flows |
| Primary LLM | Claude Sonnet (claude-sonnet-4-6) | Best quality for parsing + drafting |
| Fast LLM | Groq + Llama 3.3 70B | Low latency for classification, filtering |
| Embedding Model | OpenAI text-embedding-3-small OR sentence-transformers (local) | For semantic job matching |
| PDF Parsing | markitdown[all] | Already in Manan's setup, proven |
| Web Scraping | Playwright + BeautifulSoup4 | JS-heavy sites need Playwright |
| HTTP Client | httpx (async) + requests | Async scraping |
| API Framework | FastAPI 0.110+ | Fast, type-safe, OpenAPI docs auto-gen |
| Database | SQLite + SQLAlchemy | Local, zero-cost, sufficient for personal use |
| Scheduler | APScheduler 3.x | Simple background job scheduling |
| Frontend | React 18 + Vite | Fast dev experience |
| Styling | Tailwind CSS 3.x | Rapid UI development |
| Drag & Drop | @hello-pangea/dnd | Kanban board |

### 13.2 External APIs

| API | Purpose | Cost | Free Tier |
|---|---|---|---|
| Anthropic Claude | LLM for parsing/drafting | Pay per token | $5 free credit |
| Groq | Fast inference | Free tier generous | 6000 RPM free |
| Proxycurl | LinkedIn employee data | $0.01/call | No free tier, buy $10 = 1000 calls |
| Apollo.io | Email finding | Freemium | 50 credits/month free |
| Hunter.io | Email finding (backup) | Freemium | 25 searches/month |
| Clearbit Logo API | Company logos in UI | Free | Fully free |
| RemoteOK API | Remote job listings | Free | Public JSON API |

### 13.3 Python Dependencies (requirements.txt)

```
# Core
langgraph>=0.2.0
langchain-anthropic>=0.1.0
langchain-groq>=0.1.0
fastapi>=0.110.0
uvicorn>=0.27.0
python-dotenv>=1.0.0

# Database
sqlalchemy>=2.0.0
aiosqlite>=0.19.0

# Scraping
playwright>=1.40.0
beautifulsoup4>=4.12.0
httpx>=0.26.0
requests>=2.31.0

# Parsing
markitdown[all]>=0.0.1
pydantic>=2.0.0

# Scheduling
apscheduler>=3.10.0

# Utils
pandas>=2.0.0       # for LinkedIn CSV parsing
python-jose>=3.3.0  # JWT if auth added later
loguru>=0.7.0       # better logging
```

### 13.4 Frontend Dependencies (package.json)

```json
{
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "react-router-dom": "^6.0.0",
    "axios": "^1.6.0",
    "zustand": "^4.4.0",
    "@hello-pangea/dnd": "^16.0.0",
    "recharts": "^2.10.0",
    "lucide-react": "^0.383.0",
    "react-hot-toast": "^2.4.0",
    "tailwindcss": "^3.4.0",
    "@headlessui/react": "^2.0.0",
    "date-fns": "^3.0.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.0.0"
  }
}
```

---

## 14. LINKEDIN & DATA STRATEGY

### 14.1 Phase 1 — Free Approach (Start Here)

```
Step 1: User exports LinkedIn connections CSV
  → Go to: linkedin.com/mypreferences/d/categories/dma_portability
  → Request: Connections data
  → Download: connections.csv
  → Upload to app: /data/linkedin/connections.csv

Step 2: Agent parses CSV
  → Find: Who works at target company
  → Check education field for DTU
  → Rank by warmth

Step 3: Manual LinkedIn URL generation
  → For 2nd degree: generate search URL
  → User clicks URL to verify/find contacts
```

### 14.2 Phase 2 — Proxycurl (Spend ₹250/month of budget)

```
When to use Proxycurl:
  - Target company match score > 80
  - No 1st degree connections found in CSV
  - High-priority company (watchlist)

API Calls to use:
  1. Company Employee List: /proxycurl/api/linkedin/company/employees/
     → Input: company LinkedIn URL
     → Output: list of employees
     → Cost: $0.01 per call
     
  2. Person Profile: /proxycurl/api/v2/linkedin
     → Input: person LinkedIn URL
     → Output: full profile (education, role, etc.)
     → Cost: $0.03 per call
     
Monthly budget: $3 (~₹250) = ~300 employee lookups
```

### 14.3 Phase 3 — Optional: Apify LinkedIn Scraper
- Apify has LinkedIn Job Scraper actors (free tier: $5 credit)
- Use for job discovery from LinkedIn (not referral finding)
- Actor: `apify/linkedin-jobs-scraper`

### 14.4 Privacy & Safety
- All LinkedIn data stored locally only
- Never share LinkedIn credentials with any third-party
- Rate limit Proxycurl calls (max 10/day) to avoid detection
- For Playwright scraping: add random delays (2-5s between requests)
- User-agent rotation for scraping

---

## 15. LANGGRAPH AGENT ARCHITECTURE

### 15.1 Main Orchestrator Graph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class CareerAgentState(TypedDict):
    task: str                     # what to do
    profile: dict                 # user profile
    target_company: str           # for referral flow
    target_job_id: str
    jobs: list                    # for job hunter flow
    contacts: list                # for referral flow
    messages: list                # for outreach flow
    status: str
    error: str

# Graph definition
graph = StateGraph(CareerAgentState)

# Add nodes
graph.add_node("router", route_task)
graph.add_node("job_hunter", run_job_hunter)
graph.add_node("referral_finder", run_referral_finder)
graph.add_node("outreach_drafter", run_outreach_drafter)
graph.add_node("tracker_updater", run_tracker)

# Conditional routing
graph.add_conditional_edges(
    "router",
    decide_next_step,
    {
        "job_hunt": "job_hunter",
        "find_referral": "referral_finder",
        "draft_outreach": "outreach_drafter",
        "update_tracker": "tracker_updater"
    }
)

# Terminal edges
graph.add_edge("job_hunter", END)
graph.add_edge("referral_finder", "outreach_drafter")
graph.add_edge("outreach_drafter", END)
graph.add_edge("tracker_updater", END)

graph.set_entry_point("router")
app_graph = graph.compile()
```

### 15.2 Job Hunter Sub-Graph (Parallel Scraping)

```python
# Parallel scraping with LangGraph
from langgraph.graph import StateGraph
import asyncio

# All scrapers run in parallel using async
async def run_all_scrapers(state):
    results = await asyncio.gather(
        scrape_wellfound(state['profile']),
        scrape_remoteok(state['profile']),
        scrape_yc_jobs(state['profile']),
        scrape_linkedin_jobs(state['profile']),
        scrape_naukri(state['profile']),
        scrape_cutshort(state['profile']),
        scrape_watchlist(state['profile']),
    )
    return {"raw_jobs": [job for batch in results for job in batch]}
```

---

## 16. RELEVANT OPEN SOURCE PROJECTS

### 16.1 Job Scraping
| Project | GitHub | What It Does |
|---|---|---|
| `JobSpy` | `cullenwatson/JobSpy` | Scrapes LinkedIn, Indeed, Glassdoor, ZipRecruiter |
| `linkedin-jobs-scraper` | `spinlud/linkedin-jobs-scraper` | Node.js LinkedIn scraper |
| `wellfound-scraper` | Search on GitHub | Various Wellfound scrapers |
| `remote-ok-api` | Public | RemoteOK has public JSON endpoint |

### 16.2 LangGraph / Agent References
| Project | GitHub | What It Does |
|---|---|---|
| `langgraph-examples` | `langchain-ai/langgraph` | Official examples |
| `job-search-agent` | Search GitHub | Various job search agents |
| `gpt-job-hunter` | Search GitHub | GPT-based job hunters |

### 16.3 Resume Parsing
| Project | GitHub | What It Does |
|---|---|---|
| `resume-parser` | `alonakonst/resume-parser` | Open source resume parser |
| `pyresparser` | `OmkarPathak/pyresparser` | Python resume parser |
| `markitdown` | `microsoft/markitdown` | PDF/DOCX to Markdown (USE THIS) |

### 16.4 LinkedIn Tools
| Project | GitHub | What It Does |
|---|---|---|
| `linkedin-api` | `tomquirk/linkedin-api` | Unofficial LinkedIn API (use carefully) |
| `proxycurl-py` | Proxycurl GitHub | Official Python SDK for Proxycurl |
| `li-scraper` | Various | LinkedIn connection CSV parsers |

### 16.5 Outreach Tools
| Project | GitHub | What It Does |
|---|---|---|
| `gmail-api-python` | Google docs | Official Gmail API Python quickstart |
| `yagmail` | `kootenpv/yagmail` | Simple Gmail sender |
| `linkedin-messaging-api` | Research needed | LinkedIn DM automation |

---

## 17. RELEVANT MCPs

### 17.1 Already Connected (Manan's Workspace)
| MCP | Relevance | Use Case |
|---|---|---|
| **Gmail MCP** | HIGH | Auto-send email outreach after approval |
| **Google Calendar MCP** | MEDIUM | Schedule interview reminders |
| **Google Drive MCP** | MEDIUM | Store/retrieve resume versions |

### 17.2 MCPs to Research & Add

| MCP | Search For | Use Case |
|---|---|---|
| **LinkedIn MCP** | "linkedin mcp server" on Smithery/GitHub | DM sending, profile lookup |
| **Notion MCP** | `makenotion/notion-mcp-server` | If tracker in Notion preferred |
| **Slack MCP** | Built by Anthropic | Get job-related alerts in Slack |
| **Playwright MCP** | `microsoft/playwright-mcp` | Browser automation for scraping |
| **Proxycurl MCP** | Check Smithery | LinkedIn data (if available) |
| **Apollo MCP** | Check Smithery | Email finding |
| **Airtable MCP** | Check Smithery | Alternative to SQLite for tracker |

### 17.3 Where to Find MCPs
- **Smithery:** `smithery.ai` — biggest MCP registry
- **MCP.so:** `mcp.so` — community MCPs
- **Awesome MCP Servers:** `github.com/punkpeye/awesome-mcp-servers`
- **Glama:** `glama.ai/mcp/servers`

---

## 18. BUDGET & COST BREAKDOWN

### 18.1 Monthly Cost Estimate

| Service | Usage | Cost |
|---|---|---|
| Anthropic Claude API | ~500 calls/month (parsing + drafting) | ~₹200 |
| Groq (Llama 3.3) | ~2000 fast calls (filtering, scoring) | FREE |
| Proxycurl | ~300 calls/month (employee lookup) | ~₹250 |
| Apollo.io | 50 free credits | FREE |
| Hunter.io | 25 free searches | FREE |
| RemoteOK | Public API | FREE |
| Playwright scraping | No API cost | FREE |
| SQLite DB | Local | FREE |
| **TOTAL** | | **~₹450/month ✅ Under ₹500** |

### 18.2 Cost Optimization Strategies
- Cache job scores (don't re-score same job twice)
- Cache Proxycurl results (store in DB, don't re-fetch)
- Use Groq for filtering/classification (free), Claude only for final quality tasks
- Batch Claude API calls where possible
- Rate limit job board scraping (every 60-65 hours to stay under 2-3 day threshold)

---

## 19. BUILD PHASES & MILESTONES

### Phase 1 — Foundation (Week 1-2)
```
✅ Project structure setup
✅ SQLite DB + all table schemas
✅ FastAPI skeleton with all routes
✅ Resume upload endpoint
✅ markitdown PDF → markdown pipeline
✅ Claude extraction → profile.json
✅ Profile viewer/editor in UI
✅ .env setup for all API keys

Deliverable: Upload resume → see structured profile in UI
```

### Phase 2 — Job Hunter (Week 3-4)
```
✅ RemoteOK scraper (easiest, public API)
✅ YC Jobs scraper (workatastartup.com)
✅ Wellfound scraper
✅ Naukri scraper (Playwright)
✅ Job deduplication logic
✅ Claude job scoring (vs profile)
✅ Jobs listing page in UI (filter/sort)
✅ APScheduler for 2-3 day auto-runs
✅ Watchlist feature

Deliverable: Jobs page shows scored, ranked jobs refreshed auto
```

### Phase 3 — Referral Finder (Week 5-6)
```
✅ LinkedIn CSV parser
✅ CSV upload UI
✅ 1st degree contact finder (from CSV + company name)
✅ Proxycurl integration (2nd degree + employee search)
✅ Warmth scoring algorithm
✅ Contact ranking + display in UI
✅ DTU alumni detection

Deliverable: "Find Referrals" for any company → ranked contact list
```

### Phase 4 — Outreach Drafter (Week 7)
```
✅ Message generation (Claude Sonnet)
✅ Message editor in UI
✅ HITL approval flow
✅ Gmail integration (OAuth) for email send
✅ LinkedIn DM: manual link generation (auto-send v2)
✅ Follow-up scheduling (APScheduler)

Deliverable: Generate → Edit → Approve → Send messages in 1 flow
```

### Phase 5 — Tracker CRM (Week 8)
```
✅ Applications table in DB
✅ Kanban board UI
✅ Status drag-and-drop
✅ Follow-up reminders
✅ Stats dashboard
✅ Full pipeline view

Deliverable: Complete CRM working, all modules integrated
```

### Phase 6 — Polish (Week 9-10)
```
✅ Error handling + loading states throughout UI
✅ Logging (loguru) for all agent actions
✅ Settings page (API keys, scheduler config, preferences)
✅ LinkedIn scraper add-on (LinkedIn Jobs via Playwright)
✅ Performance: caching, async everywhere
✅ README + setup instructions

Deliverable: Production-quality personal tool, ready for daily use
```

---

## 20. FUTURE ROADMAP

### v2.0 — Automation Enhancement
- LinkedIn DM auto-send (not just draft) via unofficial API
- Auto-apply to high-match roles (with human approval)
- Interview prep module (auto-generates prep list based on JD)
- Resume auto-tailoring per job description

### v3.0 — Unified Career OS
```
┌─────────────────────────────────────────┐
│           UNIFIED CAREER OS              │
│                                         │
│  Job + Referral Finder (this tool)      │
│           +                             │
│  Freelancing Agent (client finder)      │
│           +                             │
│  Content Agent (YouTube/Instagram)      │
│                                         │
│  → One dashboard, one profile           │
│  → Shared identity/resume data          │
│  → Unified income tracking              │
└─────────────────────────────────────────┘
```

### v4.0 — SaaS Potential
- Multi-user with auth
- Cloud deployment (Railway/Render)
- Paid tiers (₹499/month for pro features)
- API for other tools to use
- Target market: Final-year students + early career devs in India

---

## 21. KNOWN RISKS & MITIGATIONS

| Risk | Impact | Mitigation |
|---|---|---|
| LinkedIn blocks scraper IP | HIGH | Use Proxycurl API instead of direct scraping. Add delays. Rotate user agents |
| Naukri/Wellfound changes DOM | MEDIUM | Use CSS selectors with fallbacks. Monitor with alerts. Playwright handles JS |
| Proxycurl API cost overrun | MEDIUM | Hard cap: 300 calls/month max. Cache all results in DB |
| Claude API rate limits | LOW | Batch calls. Use Groq for non-critical tasks. Implement retry logic |
| LinkedIn ToS violation | MEDIUM | Use Proxycurl (ToS compliant). Own CSV export = 100% safe. Avoid credentials |
| Resume parsing inaccuracy | LOW | Manual edit UI after parse. Pydantic validation with field-level errors |
| Email deliverability (spam) | MEDIUM | Gmail OAuth (not SMTP) for best deliverability. One email per person only |
| Job data freshness | LOW | 2-3 day schedule. Show "posted X days ago" prominently |

---

## APPENDIX — ENV VARIABLES (.env template)

```bash
# LLM APIs
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...

# LinkedIn Data
PROXYCURL_API_KEY=...

# Email Finding
APOLLO_API_KEY=...
HUNTER_API_KEY=...

# Gmail (OAuth — from Google Cloud Console)
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GMAIL_REDIRECT_URI=http://localhost:8000/auth/gmail/callback

# App Config
APP_ENV=development
DB_PATH=./data/db/career_agent.db
RESUME_DIR=./data/resume/
LINKEDIN_CSV_PATH=./data/linkedin/connections.csv
PROFILE_PATH=./data/profile/profile.json

# Scheduler
JOB_SCAN_INTERVAL_HOURS=60

# Scraping
SCRAPING_DELAY_MIN=2
SCRAPING_DELAY_MAX=5
MAX_JOBS_PER_SOURCE=50
```

---

*PRD Version 1.0 — Job + Referral Finder AI Agent*  
*Ready for: Claude Code handoff, Open Source Research, MCP Discovery*
