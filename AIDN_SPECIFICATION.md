# AIDN - AI-Powered Insurance Distribution Network

## Executive Summary

AIDN is a YC-caliber AI voice agent platform designed specifically for Life Insurance Independent Marketing Organizations (IMOs). AIDN automates outbound lead calling and appointment scheduling, allowing human agents to focus on what they do best—closing sales.

**Mission:** Eliminate the manual lead-calling burden for life insurance agents while maximizing appointment show rates and lead conversion.

**Target Market:** Life Insurance IMOs with field agents who rely on physical leads (mailers, forms, referrals) to generate appointments.

---

## Problem Statement

Life insurance field agents waste 60-70% of their productive time on:
- Manually calling leads (often 100+ calls to get one appointment)
- Playing phone tag with prospects
- Managing lead lists and follow-up schedules
- Administrative work instead of face-to-face selling

**The Result:** Agent burnout, low appointment rates, and wasted lead spend.

---

## Solution: AIDN Platform

AIDN is a two-agent AI system:

| Component | Technology | Purpose |
|-----------|------------|---------|
| **AIDN Voice Agent** | LiveKit + Twilio + LLM | Makes outbound calls, handles conversations, books appointments |
| **AIDN Dashboard Agent** | Pydantic AI + Supabase | Manages leads, agents, schedules, analytics |
| **Dashboard UI** | Web Application | Human agent interface for control and visibility |

---

## Core Features

### 1. Lead Management System

#### 1.1 Lead Upload
- **Supported Formats:** PDF, Excel (.xlsx, .xls), CSV
- **OCR Processing:** Extract lead data from scanned physical forms
- **Required Fields:**
  - First Name
  - Last Name
  - Phone Number
  - Address
  - City
  - County
  - State
  - Zip Code
  - Lead Source/Type (e.g., final_expense, term_life, whole_life, mortgage_protection)
  - Date Lead Was Generated (lead age)

#### 1.2 Lead Categorization & Organization
AIDN automatically categorizes leads by:
- **Geography:** County → State → City → Zip Code
- **Lead Age:** Days since lead was generated (newest first priority)
- **Lead Type:** Product interest (final_expense, term_life, whole_life, mortgage_protection)
- **Call Status:** Fresh, Attempted, Contacted, Scheduled, Not Interested, Do Not Call
- **Assignment:** Which human agent owns the lead

#### 1.3 Lead Prioritization Queue
```
Priority Order:
1. Fresh leads (never called) - sorted by lead age (newest first)
2. Callback requests (specific time requested by prospect)
3. No answers (retry after 2 hours from last attempt)
4. Not interested (retry after 7+ days)
```

#### 1.4 Lead Lifecycle States
```
┌─────────────┐
│   UPLOADED  │
└──────┬──────┘
       ▼
┌─────────────┐
│    QUEUED   │ ← Ready to be called
└──────┬──────┘
       ▼
┌─────────────┐     ┌─────────────┐
│   CALLING   │────▶│  NO_ANSWER  │──┐
└──────┬──────┘     └─────────────┘  │
       │                              │ (retry in 2 hrs)
       ▼                              │
┌─────────────┐     ┌─────────────┐  │
│  CONNECTED  │────▶│NOT_INTEREST │──┤ (retry in 7+ days)
└──────┬──────┘     └─────────────┘  │
       │                              │
       ▼                              │
┌─────────────┐     ┌─────────────┐  │
│   BOOKED    │     │   CALLBACK  │──┘ (call at specific time)
└─────────────┘     └─────────────┘

Dead States (no retry):
- DISCONNECTED (number out of service)
- WRONG_NUMBER (not the right person)
- DO_NOT_CALL (requested removal)
```

---

### 2. AIDN Voice Agent

#### 2.1 Calling Behavior

**Call Attempt Logic:**
```
AIDN picks up Lead from queue
│
├── Attempt 1: Let phone ring 3 times → No answer → Hang up immediately
├── Attempt 2: Let phone ring 3 times → No answer → Hang up immediately  
├── Attempt 3: Let phone ring 3 times → No answer → Mark as "no_answer"
│
└── If someone answers at ANY attempt → Begin conversation
```

**Critical Rules:**
- ✅ Call each lead up to 3 times in a row (back-to-back)
- ✅ Let phone ring exactly 3 times per attempt
- ❌ NEVER leave a voicemail
- ❌ NEVER call leads marked as Do Not Call
- ✅ Stop calling when daily appointment quota is reached

#### 2.2 Conversation Flow

**AIDN's Persona:**
- **Casual, friendly personality** - like someone they already know
- **Speak SLOWLY and relaxed** - not rushed or professional sounding
- **Sound busy but friendly** - like you're squeezing them in as a favor
- **Use natural speech patterns:** "umm", "hmm", "ya know", "let me see here"
- **Casual language:** "gonna" (not "going to"), "wanna" (not "want to"), "ya" (not "you")
- **Assume familiarity** - greet like you know them already ("Hey [Name]!")
- **NOT corporate or professional sounding** - this is a casual conversation

**Call Structure:**
```
1. GREETING (5-10 seconds)
   "Hey [First Name]! This is [AIDN Name], umm, I'm calling from the benefits
   center here in [County]... so we've got this package of info ready to go out
   to ya, and I was just making sure you still live at [Address], is that right?"

2. QUALIFY (10-20 seconds)
   - Confirm they requested information
   - Light rapport building
   - Gauge interest level

3. TRANSITION TO APPOINTMENT (10-15 seconds)
   "Great, well my job is pretty simple - get you the info and go over it
   with ya. Let me see here... they have me out there tomorrow..."

4. SCHEDULE (20-30 seconds)
   - Offer 2-3 specific time slots with casual language
   - "...they have me out there tomorrow around 8-9am and later around 3-4pm...
     which one works better for you?"
   - Confirm date, time, and address casually

5. CONFIRM & CLOSE (10-15 seconds)
   - Repeat appointment details
   - Describe what agent looks like / what car they drive
   - Set expectations for the visit
   - Warm goodbye
```

**Objection Handling:**
AIDN must handle common objections naturally:
- "I'm not interested" → Acknowledge, soft redirect, or graceful exit
- "How did you get my number?" → Reference the form they filled out
- "Is this a scam?" → Reassure, reference their specific inquiry
- "I'm busy right now" → Offer callback at specific time
- "I already have insurance" → Acknowledge, mention no-cost review
- "Send me information" → Redirect to in-person value, offer appointment

#### 2.3 Compliance & Safety

**AIDN Will NEVER:**
- Discuss specific policy details, prices, or coverage amounts
- Provide insurance advice or recommendations
- Make promises about benefits or savings
- Pressure or manipulate prospects
- Continue calling after "Do Not Call" request
- Call outside of legal calling hours (8am-9pm local time)

**AIDN Will ALWAYS:**
- Identify as calling on behalf of [Agency Name]
- Redirect insurance questions to the human agent
- Respect "not interested" after one soft redirect attempt
- Log all call outcomes accurately
- Comply with TCPA and state-specific regulations

---

### 3. Human Agent Dashboard

#### 3.1 Agent Profile Setup
Each human agent configures:
- **Personal Info:** Name, phone, email
- **Appearance:** Physical description (for prospect to identify them)
- **Vehicle:** Car make, model, color (for prospect to identify them)
- **Territory:** Which counties/zip codes they cover
- **Calendar Integration:** Google Calendar sync

#### 3.2 Availability & Scheduling Controls

**Agent sets their calling schedule:**
```
Example Configuration:
┌─────────────────────────────────────────────────────────┐
│ Agent: John Smith                                       │
├─────────────────────────────────────────────────────────┤
│ Monday:    AIDN calls 9am-12pm  │ Appointments: 4 max  │
│ Tuesday:   AIDN calls 9am-12pm  │ Appointments: 4 max  │
│ Wednesday: OFF                   │ Appointments: 0      │
│ Thursday:  AIDN calls 9am-12pm  │ Appointments: 5 max  │
│ Friday:    AIDN calls 9am-12pm  │ Appointments: 3 max  │
│ Saturday:  AIDN calls 10am-1pm  │ Appointments: 2 max  │
│ Sunday:    OFF                   │ Appointments: 0      │
├─────────────────────────────────────────────────────────┤
│ Appointment Settings:                                   │
│ - First appointment: 9:00 AM earliest                  │
│ - Last appointment: 6:00 PM latest                     │
│ - Time between appointments: 2 hours                   │
│ - Book appointments for: Next 2 days only              │
├─────────────────────────────────────────────────────────┤
│ Territory:                                              │
│ - Counties: Cook, Lake, DuPage, Will                   │
│ - Lead Types: final_expense, term_life                 │
└─────────────────────────────────────────────────────────┘
```

**Appointment Slot System:**
- Slots are pre-generated based on agent's settings
- 2-hour gaps between appointments (configurable)
- Once all slots for a day are booked → AIDN stops calling for that day
- Once all slots for both days are booked → AIDN stops calling entirely

#### 3.3 Lead Assignment Rules

Agent specifies which leads AIDN should call:
- **By County:** "Only call leads in Cook County and Lake County"
- **By Lead Type:** "Only call final_expense leads"
- **By Lead Age:** "Only call leads generated in the last 30 days"
- **Exclusions:** "Don't call leads in zip code 60601"

#### 3.4 Dashboard Views

**Main Dashboard:**
- Today's scheduled appointments
- Calls in progress
- Daily/weekly/monthly statistics
- Lead queue status

**Lead Management:**
- All leads with filters (status, county, date, type)
- Lead details and call history
- Manual status override
- Upload new leads

**Analytics:**
- Conversion rates (calls → appointments)
- Show rates (appointments → completed visits)
- Best performing counties/lead types
- Agent performance metrics

**Settings:**
- Profile configuration
- Availability schedule
- Territory settings
- Notification preferences

---

### 4. Technical Architecture

#### 4.1 System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        DASHBOARD UI                              │
│                    (React / Next.js)                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DASHBOARD AGENT (Pydantic AI)                   │
│                                                                  │
│  Tools:                                                          │
│  - upload_leads()         - get_appointments()                  │
│  - get_leads()            - get_call_statistics()               │
│  - update_agent_profile() - manage_availability()               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SUPABASE DATABASE                            │
│                                                                  │
│  Tables:                                                         │
│  - leads              - appointment_slots                        │
│  - agent_profiles     - call_logs                               │
│  - agent_availability - appointments                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AIDN VOICE AGENT (LiveKit)                     │
│                                                                  │
│  Components:                                                     │
│  - Twilio (phone calls)      - Deepgram (speech-to-text)       │
│  - LiveKit (real-time audio) - OpenAI/Claude (LLM)             │
│  - ElevenLabs (text-to-speech)                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.2 Database Schema

**leads**
```sql
- id (uuid)
- first_name, last_name, phone
- address, city, county, state, zip_code
- lead_type (final_expense, term_life, whole_life, mortgage_protection)
- lead_source
- agent_id (assigned human agent)
- created_at (when lead was generated - for lead age)
- uploaded_at (when uploaded to AIDN)
- last_called_at
- next_call_at
- call_count
- call_outcome (fresh, no_answer, not_interested, booked, callback, disconnected, wrong_number, dnc)
- is_active
```

**agent_profiles**
```sql
- id (uuid)
- agent_name, phone, email
- physical_description
- car_description
- google_calendar_id
- earliest_appointment_time
- latest_appointment_time
- slot_gap_hours
- is_active
```

**agent_availability**
```sql
- id (uuid)
- agent_id
- day_of_week (0-6)
- is_available
- calling_start_time
- calling_end_time
- max_appointments
- first_appointment_time
```

**agent_territories**
```sql
- id (uuid)
- agent_id
- county (nullable)
- state
- zip_code (nullable)
- lead_types (array)
```

**appointment_slots**
```sql
- id (uuid)
- agent_id
- date
- time
- status (available, booked, completed, no_show, cancelled)
- lead_id
- booked_at
```

**call_logs**
```sql
- id (uuid)
- lead_id
- agent_id
- call_sid (Twilio)
- started_at
- ended_at
- duration_seconds
- outcome
- recording_url (if enabled)
- transcript
- notes
```

#### 4.3 Appointment Booking Logic

**Atomic Booking (Prevents Double-Booking):**
```sql
UPDATE appointment_slots 
SET status = 'booked', lead_id = [lead_id], booked_at = NOW()
WHERE id = [slot_id] 
  AND status = 'available'
RETURNING *;

-- If 0 rows returned → slot was taken → offer alternative
-- If 1 row returned → booking successful → confirm with prospect
```

**Slot Generation (Daily Job):**
```python
For each active agent:
    For next 2 days:
        If agent is available that day:
            Generate slots based on:
                - first_appointment_time
                - max_appointments  
                - slot_gap_hours
                - latest_appointment_time
```

---

### 5. Success Metrics (KPIs)

#### 5.1 Operational Metrics
- **Connection Rate:** % of calls where someone answers
- **Conversation Rate:** % of connections that become conversations
- **Booking Rate:** % of conversations that result in appointments
- **Show Rate:** % of appointments where prospect is home

#### 5.2 Target Benchmarks (YC-Level Performance)
| Metric | Industry Average | AIDN Target |
|--------|------------------|-------------|
| Connection Rate | 5-10% | 15%+ |
| Booking Rate | 2-5% | 10%+ |
| Show Rate | 50-60% | 75%+ |
| Cost per Appointment | $50-100 | $20-30 |
| Agent Time Saved | - | 70%+ |

#### 5.3 Business Metrics
- Monthly Recurring Revenue (MRR)
- Customer Acquisition Cost (CAC)
- Lifetime Value (LTV)
- Churn Rate
- Net Promoter Score (NPS)

---

### 6. Competitive Advantages

1. **Built for Insurance:** Not a generic dialer - purpose-built for life insurance sales workflows

2. **Compliance-First:** TCPA compliant, state regulation aware, never discusses policy details

3. **Natural Conversations:** AI that sounds human, builds rapport, handles objections gracefully

4. **Smart Scheduling:** Atomic booking, territory awareness, calendar sync

5. **Lead Intelligence:** Prioritization, aging, outcome tracking, retry optimization

6. **Agent Control:** Full visibility and control over when, where, and how AIDN calls

---

### 7. Roadmap

#### Phase 0: Foundation (Weeks 1-2)
- [ ] Core voice agent working end-to-end
- [ ] Basic lead management
- [ ] Single agent support
- [ ] Manual testing

#### Phase 1: MVP (Weeks 3-4)
- [ ] Dashboard UI
- [ ] Lead upload (CSV/Excel)
- [ ] Multi-agent support
- [ ] Basic analytics

#### Phase 2: Production (Weeks 5-6)
- [ ] Google Calendar sync
- [ ] Call recording & transcripts
- [ ] Advanced analytics
- [ ] Territory management

#### Phase 3: Scale (Weeks 7-8)
- [ ] PDF/OCR lead upload
- [ ] Multi-IMO support
- [ ] API for integrations
- [ ] Mobile app

---

### 9. MVP Scope & Post-MVP Features

#### 9.1 MVP Scope (YC Demo Ready)

**Core Capabilities:**
- ✅ Single concurrent call (one call at a time)
- ✅ Basic lead management (upload, categorize, prioritize)
- ✅ AIDN voice agent with natural conversation flow
- ✅ Appointment booking with Google Calendar sync
- ✅ Single agent support
- ✅ Dashboard UI (leads, analytics, call history)
- ✅ Territory management (county/zip-based)
- ✅ Basic objection handling via RAG
- ✅ Call outcome tracking

**Performance Targets (MVP):**
- Voice latency: <1000ms total (STT + LLM + TTS)
- Connection rate: 10%+
- Booking rate: 5%+
- Show rate: 70%+

**Technical Stack (MVP):**
- LiveKit SIP (voice infrastructure)
- Groq Llama 3.1 8B Instant (LLM)
- Deepgram Nova-2 (STT)
- Cartesia Sonic 2 (TTS)
- FastAPI backend
- Next.js frontend
- PostgreSQL database

#### 9.2 Post-MVP Features (After YC)

**Scalability:**
- ⏳ 100+ concurrent calls (requires infrastructure scaling)
- ⏳ Multi-IMO support (white-label dashboard)
- ⏳ Advanced call distribution (load balancing)
- ⏳ Real-time call monitoring dashboard

**Advanced Features:**
- ⏳ PDF/OCR lead upload
- ⏳ SMS follow-up integration
- ⏳ Advanced analytics (ML-powered insights)
- ⏳ Mobile app for agents
- ⏳ API for third-party integrations
- ⏳ Call recording & transcript storage
- ⏳ A/B testing for scripts

**Compliance & Security:**
- ⏳ SOC 2 Type II certification
- ⏳ HIPAA compliance
- ⏳ Advanced DNC list management
- ⏳ State-specific regulation enforcement

**Performance Optimizations:**
- ⏳ Voice latency: <600ms (target for scale)
- ⏳ LLM prompt caching optimization
- ⏳ CDN for TTS response caching
- ⏳ Database query optimization at scale

#### 9.3 Implementation Impact: Concurrent Calls

**Current State (MVP):**
- AIDN makes one call at a time
- Simple queue processing: pick lead → call → log outcome → next lead
- Single LiveKit room per call
- Minimal infrastructure requirements

**Scaling to 100+ Concurrent Calls (Post-MVP):**

**Infrastructure Changes Required:**
1. **LiveKit Cloud:** Upgrade from free tier to production tier
2. **Database:** Connection pooling, read replicas, query optimization
3. **LLM Provider:** Groq rate limit increase (or multi-provider failover)
4. **TTS Provider:** Cartesia concurrent stream limits
5. **Orchestration:** Queue management system (Celery/Redis)

**Code Changes Required:**
1. **Async Call Manager:** Spawn multiple call tasks simultaneously
2. **Lead Locking:** Prevent duplicate calls to same lead
3. **Resource Pooling:** Manage LLM/TTS API connections
4. **Monitoring:** Real-time call status dashboard
5. **Error Handling:** Graceful degradation if services hit limits

**Cost Impact:**
- LiveKit Cloud: ~$0.005/minute → ~$300-500/month at 100 concurrent
- Groq API: ~$0.10/1M tokens → ~$50-100/month
- Database: Upgrade from free tier → ~$25-50/month
- **Total estimated:** ~$400-650/month infrastructure at 100 concurrent calls

**Timeline:**
- MVP: Single call capability (current)
- Post-YC Month 1-2: Test 5-10 concurrent calls
- Post-YC Month 3-4: Scale to 50+ concurrent calls
- Post-YC Month 5-6: Scale to 100+ concurrent calls

---

### 8. Technical Requirements

#### 8.1 Infrastructure
- **Cloud:** AWS or GCP
- **Database:** Supabase (PostgreSQL)
- **Voice:** LiveKit Cloud + Twilio
- **AI:** OpenAI GPT-4 / Anthropic Claude
- **Speech:** Deepgram (STT) + ElevenLabs (TTS)

#### 8.2 Security & Compliance
- SOC 2 Type II (target)
- HIPAA awareness (PHI handling)
- TCPA compliance
- Data encryption at rest and in transit
- Role-based access control

#### 8.3 Scalability Targets

**MVP Targets:**
- Single concurrent call
- Handle 1,000+ leads per IMO
- 99% uptime

**Post-MVP Targets:**
- Support 100+ concurrent calls
- Handle 10,000+ leads per IMO
- 99.9% uptime SLA

---

## Repository Analysis Request

Please analyze the following repositories to identify which components, patterns, and code can be leveraged to build AIDN:

### Repository 1: `/workshops`
Focus on: `livekit-rag-voice-agent`
- Voice agent architecture
- LiveKit integration
- Twilio phone connectivity
- Speech-to-text / text-to-speech
- Conversation handling

### Repository 2: `/ai-agent-mastery`
Focus on: `4_Pydantic_AI_Agent`, `6_Agent_Deployment`, `9_Agent_SaaS`
- Dashboard agent patterns
- Tool definitions
- Database integration
- Deployment infrastructure
- SaaS patterns

### Analysis Questions:
1. Which folders/files are directly applicable to AIDN?
2. Which can be deleted (not relevant)?
3. What's missing that needs to be built from scratch?
4. Recommended project structure combining both?
5. Technical gaps or concerns to address?

---

*AIDN - Turning leads into appointments, automatically.*
