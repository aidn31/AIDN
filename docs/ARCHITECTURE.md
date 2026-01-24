# AIDN Architecture

**Last Updated:** January 24, 2026
**Status:** PRODUCTION READY - LiveKit SIP + Telnyx + Groq LLM + RAG Architecture

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│           MODERN SAAS REACT DASHBOARD                           │
│               (http://localhost:3000)                           │
│  Linear/Vercel/Stripe aesthetic • Slate + Emerald design       │
│  Status: ✅ COMPLETE                                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/REST API
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                              │
│               (http://localhost:8000)                           │
│  RESTful API • File Upload • CORS • Error Handling             │
│  Status: ✅ COMPLETE                                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │ Database operations
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
│  Stack: Deepgram STT + GPT-4o-mini + Cartesia TTS              │
│  Architecture: Slim Prompt (~1200 tokens) + RAG Objections     │
│  Agent: aidn-outbound                                          │
│  Status: ✅ WORKING                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Outbound Call Flow (Working)

```
1. Dispatch job with phone_number in metadata
2. Agent receives job, connects to room
3. Agent creates SIP participant via ctx.api.sip.create_sip_participant()
4. Telnyx dials the phone number
5. User answers → SIP participant joins room
6. Agent delivers greeting via session.say()
7. Deepgram STT → GPT-4o-mini → OpenAI TTS pipeline runs
8. Real-time conversation with casual persona
9. Call ends → session closes
```

### Key Code (main.py)

```python
# Dial the lead via SIP (Telnyx)
await ctx.api.sip.create_sip_participant(
    api.CreateSIPParticipantRequest(
        sip_trunk_id=os.getenv("SIP_OUTBOUND_TRUNK_ID"),
        sip_call_to=phone_number,
        room_name=ctx.room.name,
        participant_identity=f"lead-{phone_number}",
        wait_until_answered=True,
    )
)

# Greet after call is answered
await session.say(greeting)
```

---

## Technology Stack

| Component | Technology | Status | Notes |
|-----------|------------|--------|-------|
| **Frontend** | React + Next.js + TypeScript + Tailwind CSS | ✅ COMPLETE | Port 3000 |
| **Backend API** | FastAPI + Python | ✅ COMPLETE | Port 8000 |
| **Voice Agent** | LiveKit Agents v1.3.10 | ✅ WORKING | aidn-outbound |
| **Phone Provider** | Telnyx (via LiveKit SIP) | ✅ WORKING | No custom bridge |
| **Speech-to-Text** | Deepgram Nova-2 | ✅ WORKING | Real-time transcription, ~350ms |
| **Text-to-Speech** | Cartesia Sonic 2 | ✅ WORKING | ~320ms TTFB, streaming. Emotion: `["positivity:high", "curiosity:medium"]` |
| **LLM** | Groq Llama 3.1 8B Instant | ✅ WORKING | 300-500ms TTFT. Configurable via `LLM_PROVIDER` and `GROQ_MODEL` env vars |
| **Database** | PostgreSQL | ✅ COMPLETE | Full schema |
| **VAD** | Silero | ✅ WORKING | Voice activity detection, min_silence=150ms |

---

## Environment Variables

```bash
# Required for voice agent
DATABASE_URL=postgresql://...
DEEPGRAM_API_KEY=...
CARTESIA_API_KEY=...
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
SIP_OUTBOUND_TRUNK_ID=ST_...  # From LiveKit Cloud after Telnyx setup

# LLM Configuration (default: Groq)
LLM_PROVIDER=groq  # or "openai"
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.1-8b-instant  # or "llama-3.3-70b-versatile"
OPENAI_API_KEY=sk-...  # Only needed if LLM_PROVIDER=openai
```

---

## Key Files

| File | Purpose |
|------|---------|
| `src/voice_agent/main.py` | Agent entry point, SIP dialing, session config |
| `src/voice_agent/aidn_agent_v2.py` | Voice agent with RAG tools (AIDNVoiceAgent) |
| `src/voice_agent/core_prompt.py` | Slim system prompt (~1200 tokens) |
| `src/voice_agent/objection_kb.json` | RAG knowledge base (16 objection handlers) |
| `src/shared/database/` | Database connection and repositories |
| `scripts/test_call.py` | Test call dispatcher |

---

## 3-Layer RAG Architecture (v2)

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 1: SLIM CORE PROMPT                    │
│  core_prompt.py (~66 lines, ~1200 tokens)                      │
│  • Role, voice style, conversation flow                         │
│  • Lead/agent info injected at runtime                         │
│  • Guardrails and response style rules                         │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 2: RAG TOOLS                           │
│  get_objection_response() - retrieves from objection_kb.json   │
│  get_available_times() - appointment availability              │
│  confirm_appointment() - tie-down with confirmation code       │
│  schedule_callback() - callback scheduling                     │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 LAYER 3: KNOWLEDGE BASE                         │
│  objection_kb.json (16 handlers + fallback)                    │
│  • Trigger-based matching                                       │
│  • Personalized response templates                             │
│  • Strategy documentation per objection                        │
└─────────────────────────────────────────────────────────────────┘
```

### Latency Improvement

| Metric | Old (v1) | New (v2) |
|--------|----------|----------|
| System prompt | ~5000 tokens | ~1200 tokens |
| First response | 3-4 seconds | <1 second |
| Objection handling | In-prompt | RAG retrieval |

---

## Database Schema

### Core Tables
```sql
-- Lead management with full lifecycle
leads (id, first_name, last_name, phone, address, city, county, state,
       zip_code, lead_type, lead_source, agent_id, created_at, uploaded_at,
       last_called_at, next_call_at, call_count, call_outcome, is_active)

-- Agent profiles with identification info for prospects
agent_profiles (id, agent_name, phone, email, physical_description,
                car_description, google_calendar_id, earliest_appointment_time,
                latest_appointment_time, slot_gap_hours, is_active)

-- Agent availability by day of week
agent_availability (id, agent_id, day_of_week, is_available,
                    calling_start_time, calling_end_time, max_appointments,
                    first_appointment_time)

-- Territory assignment (counties, states, zip codes)
agent_territories (id, agent_id, county, state, zip_code, lead_types)

-- Appointment slots with atomic booking
appointment_slots (id, agent_id, date, time, status, lead_id, booked_at)

-- Call tracking
call_logs (id, lead_id, agent_id, call_sid, started_at, ended_at,
           duration_seconds, outcome, recording_url, transcript, notes)
```

---

## Making a Test Call

```python
from livekit import api
import json

lk_api = api.LiveKitAPI(url, api_key, api_secret)

# Create room
await lk_api.room.create_room(api.CreateRoomRequest(name="test-call"))

# Dispatch agent with phone number
await lk_api.agent_dispatch.create_dispatch(
    api.CreateAgentDispatchRequest(
        room="test-call",
        agent_name="aidn-outbound",
        metadata=json.dumps({"phone_number": "+1234567890"}),
    )
)
```

---

## Migration History

**January 2, 2026 - LiveKit SIP + Telnyx Migration**
- Removed: Custom Twilio WebSocket bridge (~3,700 lines)
- Removed: Railway hosting configuration
- Added: LiveKit SIP integration with Telnyx
- Result: Simpler architecture, working audio, lower costs

---

## Voice Optimization Status

**Current Latency:** 700-800ms total response time
**Previous Latency:** 1400-2400ms
**Improvement:** 50-65% faster
**Status:** ✅ OPTIMIZED (see `docs/VOICE_OPTIMIZATION_CHECKLIST.md`)

### Current Component Latencies (After Optimization)
- **STT:** ~350ms (Deepgram Nova-2)
- **LLM TTFT:** 300-500ms (Groq Llama 3.1 8B) - **60% improvement from GPT-4o-mini**
- **TTS TTFB:** ~320ms (Cartesia Sonic 2)

### Optimizations Completed
1. **Phase 1:** ✅ Added comprehensive latency logging (`src/voice_agent/latency_tracker.py`)
2. **Phase 2:** ✅ Switched to Groq LLM (reduced TTFT from 800-1600ms → 300-500ms)
3. **Phase 2:** ✅ Optimized VAD settings (min_silence=150ms, endpointing=50-400ms)
4. **Phase 3:** ⏳ Voice naturalness improvements (pending - lower priority)

---

## Success Metrics (YC Targets)

| Metric | Industry Average | AIDN Target | Status |
|--------|------------------|-------------|--------|
| **Connection Rate** | 5-10% | 15%+ | Ready to test |
| **Booking Rate** | 2-5% | 10%+ | Objection handling ready |
| **Show Rate** | 50-60% | 75%+ | Smart scheduling implemented |
| **Cost per Appointment** | $50-100 | $20-30 | Automation reduces costs |
| **Voice Latency** | N/A | <500ms | ✅ **700-800ms achieved** (50-65% improvement) |