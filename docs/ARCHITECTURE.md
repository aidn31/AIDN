# AIDN Architecture

**Last Updated:** January 24, 2026
**Status:** END-TO-END WORKING - Dashboard → API → LiveKit → Voice Agent → Phone

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│           MODERN SAAS REACT DASHBOARD                           │
│               (http://localhost:3000)                           │
│  Linear/Vercel/Stripe aesthetic • Slate + Emerald design       │
│  Fetches real leads from API • "Call" button triggers calls    │
│  Status: ✅ WORKING                                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/REST API
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                              │
│               (http://localhost:8000)                           │
│  GET /leads - Returns leads with UUIDs                         │
│  POST /calls/initiate - Dispatches LiveKit agent               │
│  Status: ✅ WORKING                                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │ Database + LiveKit API
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  POSTGRESQL DATABASE                            │
│  Tables: leads, agent_profiles, agent_availability,            │
│          agent_territories, appointment_slots, call_logs       │
│  Status: ✅ COMPLETE                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    LIVEKIT SIP + TELNYX                         │
│  Outbound calls via SIP trunk • No custom bridge needed        │
│  Status: ✅ WORKING                                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │ SIP Protocol
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 AIDN VOICE AGENT (LiveKit)                      │
│  Stack: Deepgram STT + Groq LLM + Cartesia TTS                 │
│  Architecture: Slim Prompt (~1200 tokens) + RAG Objections     │
│  Agent: aidn-outbound                                          │
│  Status: ✅ WORKING                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## End-to-End Call Flow (Working)

```
1. User clicks "Call" button in dashboard
2. Dashboard sends POST /calls/initiate with lead_id
3. API looks up lead in database (gets phone number)
4. API creates LiveKit room
5. API dispatches aidn-outbound agent with metadata
6. Agent receives job, connects to room
7. Agent creates SIP participant via Telnyx
8. Phone rings, user answers
9. Agent greets by name: "Hey Mary! This is Aiden..."
10. Deepgram STT → Groq LLM → Cartesia TTS pipeline
11. Natural conversation with objection handling
12. Call ends → session closes
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/leads` | GET | Returns all active leads with UUIDs |
| `/calls/initiate` | POST | Dispatches call to a lead |

### POST /calls/initiate

**Request:**
```json
{
  "lead_id": "79199dd6-2e54-41fb-ab47-44a8809031c6",
  "agent_id": "optional-agent-uuid"
}
```

**Response:**
```json
{
  "status": "dispatched",
  "call_id": "call-79199dd6-20260124153045",
  "lead_id": "79199dd6-2e54-41fb-ab47-44a8809031c6"
}
```

---

## Technology Stack

| Component | Technology | Status | Notes |
|-----------|------------|--------|-------|
| **Frontend** | React + Next.js + TypeScript + Tailwind CSS | ✅ WORKING | Port 3000, fetches real data |
| **Backend API** | FastAPI + Python | ✅ WORKING | Port 8000, `src/api/server.py` |
| **Voice Agent** | LiveKit Agents v1.3.10 | ✅ WORKING | aidn-outbound |
| **Phone Provider** | Telnyx (via LiveKit SIP) | ✅ WORKING | No custom bridge |
| **Speech-to-Text** | Deepgram Nova-2 | ✅ WORKING | ~350ms latency |
| **Text-to-Speech** | Cartesia Sonic 2 | ✅ WORKING | ~320ms TTFB |
| **LLM** | Groq Llama 3.1 8B Instant | ✅ WORKING | 300-500ms TTFT |
| **Database** | PostgreSQL | ✅ COMPLETE | Full schema |
| **VAD** | Silero | ✅ WORKING | min_silence=150ms |

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://...

# Voice Agent
DEEPGRAM_API_KEY=...
CARTESIA_API_KEY=...
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
SIP_OUTBOUND_TRUNK_ID=ST_...

# LLM (Groq)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.1-8b-instant
```

---

## Key Files

| File | Purpose |
|------|---------|
| `src/api/server.py` | FastAPI backend with /leads and /calls/initiate |
| `src/voice_agent/main.py` | Agent entry point, SIP dialing, session config |
| `src/voice_agent/aidn_agent_v2.py` | Voice agent with RAG tools |
| `src/voice_agent/core_prompt.py` | Slim system prompt (~1200 tokens) |
| `src/voice_agent/objection_kb.json` | RAG knowledge base (16 objection handlers) |
| `src/shared/database/` | Database connection and repositories |
| `web-dashboard/app/leads/page.tsx` | Leads page with "Call" button |

---

## 3-Layer RAG Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 1: SLIM CORE PROMPT                    │
│  core_prompt.py (~66 lines, ~1200 tokens)                      │
│  • Role, voice style, conversation flow                         │
│  • Lead/agent info injected at runtime                         │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 2: RAG TOOLS                           │
│  get_objection_response() - retrieves from objection_kb.json   │
│  get_available_times() - appointment availability              │
│  confirm_appointment() - tie-down with confirmation code       │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 LAYER 3: KNOWLEDGE BASE                         │
│  objection_kb.json (16 handlers + fallback)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Running the System

```bash
# Terminal 1: Voice Agent
python -m src.voice_agent.main dev

# Terminal 2: API Server
uvicorn src.api.server:app --reload --port 8000

# Terminal 3: Dashboard
cd web-dashboard && npm run dev
```

Then open http://localhost:3000/leads and click "Call" on any lead.

---

## Voice Latency Metrics

| Metric | Value |
|--------|-------|
| **Total Latency** | 700-800ms |
| **STT** | ~350ms (Deepgram Nova-2) |
| **LLM TTFT** | 300-500ms (Groq Llama 3.1 8B) |
| **TTS TTFB** | ~320ms (Cartesia Sonic 2) |

**Improvement:** 50-65% faster than original 1400-2400ms

---

## Database Schema

```sql
-- Lead management
leads (id, first_name, last_name, phone, address, city, county, state,
       zip_code, lead_type, lead_source, agent_id, created_at, uploaded_at,
       last_called_at, next_call_at, call_count, call_outcome, is_active)

-- Agent profiles
agent_profiles (id, agent_name, phone, email, physical_description,
                car_description, earliest_appointment_time,
                latest_appointment_time, slot_gap_hours, is_active)

-- Appointment slots
appointment_slots (id, agent_id, date, time, status, lead_id, booked_at)

-- Call tracking
call_logs (id, lead_id, agent_id, call_sid, started_at, ended_at,
           duration_seconds, outcome, recording_url, transcript, notes)
```
