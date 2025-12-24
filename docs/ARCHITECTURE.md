# AIDN Architecture

**Last Updated:** December 25, 2025 - 12:30 AM
**Status:** AUDIO BRIDGE IMPLEMENTED - TESTING REQUIRED

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
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐     ┌─────────────────────────────────────┐
│   TWILIO CALLS      │     │     AIDN VOICE AGENT (LiveKit)      │
│  Phone: +18136380935│     │  Stack: Deepgram + GPT-4 + TTS      │
│  Status: ✅ WORKING │     │  Worker: AW_pfC62LYxQhvV            │
└─────────┬───────────┘     └──────────────▲──────────────────────┘
          │                                │
          │    ┌─────────────────────┐     │
          └───►│   AUDIO BRIDGE      │─────┘
               │   Status: ❌ MISSING │
               └─────────────────────┘
```

---

## 🚨 Missing Integration: Twilio ↔ LiveKit Audio Bridge

This is the critical gap preventing the AI voice agent from speaking on phone calls.

### Current Flow (Broken)
```
1. Dashboard clicks "Call" → API calls CallManager.initiate_call()
2. Twilio dials phone number → Phone rings ✅
3. User answers → Twilio calls /twilio-webhook
4. Webhook returns static <Say> TwiML → User hears pre-recorded message ❌
5. Call hangs up → No AI conversation ❌
```

### Required Flow (Target)
```
1. Dashboard clicks "Call" → API calls CallManager.initiate_call()
2. Twilio dials phone number → Phone rings ✅
3. User answers → Twilio calls /twilio-webhook
4. Webhook returns <Stream> TwiML with WebSocket URL
5. Twilio streams audio via WebSocket → Server receives audio
6. Server bridges audio to LiveKit room
7. AIDNVoiceAgent joins room with lead context
8. Deepgram STT → GPT-4 → OpenAI TTS pipeline runs
9. AI audio streams back through WebSocket → Twilio → User's phone
10. Real-time conversation with casual persona ✅
```

### Implementation Required

**1. WebSocket Handler for Twilio `<Stream>`**
```python
@app.websocket("/twilio-audio-stream")
async def twilio_audio_stream(websocket: WebSocket):
    await websocket.accept()
    
    # Get room/lead info from query params
    room_name = websocket.query_params.get("room")
    lead_id = websocket.query_params.get("lead_id")
    
    # Connect to LiveKit room
    livekit_room = await connect_to_livekit_room(room_name)
    
    # Bridge audio bidirectionally
    async for message in websocket.iter_bytes():
        # Convert μ-law to PCM
        pcm_audio = convert_mulaw_to_pcm(message)
        # Send to LiveKit
        await livekit_room.publish_audio(pcm_audio)
```

**2. Updated Webhook Response**
```python
@app.post("/twilio-webhook")
async def twilio_webhook(request: Request):
    form_data = await request.form()
    room_name = request.query_params.get("room")
    lead_id = request.query_params.get("lead_id")
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://your-server.com/twilio-audio-stream?room={room_name}&lead_id={lead_id}">
        </Stream>
    </Connect>
</Response>"""
    
    return Response(content=twiml, media_type="text/xml")
```

**3. Voice Agent Room Entry**
```python
# When room is created, voice agent auto-joins
@agents.worker()
async def handle_incoming_call(ctx: agents.JobContext):
    # Get lead context from room metadata
    lead = await load_lead_from_db(ctx.room.metadata["lead_id"])
    agent_info = await load_agent_info(ctx.room.metadata["agent_id"])
    
    # Create voice agent with context
    agent = AIDNVoiceAgent(db_manager)
    await agent.set_call_context(lead, agent_id, agent_info)
    
    # Start the conversation
    await agent.run(ctx)
```

---

## Technology Stack

| Component | Technology | Status | Notes |
|-----------|------------|--------|-------|
| **Frontend** | React + Next.js + TypeScript + Tailwind CSS | 🟢 COMPLETE | Port 3000 |
| **Backend API** | FastAPI + Python | 🟢 COMPLETE | Port 8000 |
| **Voice Agent** | LiveKit v1.3.10 | 🟢 REGISTERED | Worker ID: AW_pfC62LYxQhvV |
| **Phone Calls** | Twilio | 🟢 CONFIGURED | +18136380935 |
| **Speech-to-Text** | Deepgram Nova-2 | 🟢 READY | In voice agent code |
| **Text-to-Speech** | OpenAI TTS | 🟢 READY | "echo" voice |
| **LLM** | OpenAI GPT-4-mini | 🟢 READY | Temperature 0.7 |
| **Database** | PostgreSQL | 🟢 COMPLETE | Full schema |
| **Audio Bridge** | WebSocket | 🟢 IMPLEMENTED | Ready for testing |

---

## Key Architectural Decisions

### December 24, 2025 - Unified Codebase
**Decision:** Consolidate 3 separate AIDN implementations into single repository
**Rationale:** Faster path to working prototype than building from scratch
**Result:** All code now in `/Users/thomasroldan/Documents/GitHub/AIDN`

### December 24, 2025 - React Dashboard over Streamlit
**Decision:** Build production React dashboard instead of keeping Streamlit prototype
**Rationale:** YC demo needs professional appearance
**Result:** Modern SaaS UI with Linear/Vercel/Stripe aesthetic

### December 24, 2025 - FastAPI Backend
**Decision:** Use FastAPI for REST API instead of direct database access from frontend
**Rationale:** Better separation of concerns, easier scaling
**Result:** Full API at `/api` endpoints

### Voice Technology Choices
- **LiveKit:** Chosen for real-time voice agent hosting
- **Deepgram:** Nova-2 model for fast, accurate phone audio transcription
- **OpenAI TTS:** Good quality, easy integration
- **GPT-4-mini:** Fast enough for real-time, smart enough for objections

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

-- Call tracking with recordings and transcripts
call_logs (id, lead_id, agent_id, call_sid, started_at, ended_at,
           duration_seconds, outcome, recording_url, transcript, notes)
```

### PostgreSQL Functions
- `book_appointment(slot_id, lead_id)` - Atomic booking prevents double-booking
- `generate_appointment_slots(agent_id, start_date, end_date)` - Auto-create slots

---

## Objection Handling Architecture

### Implemented Scenarios
1. **"I'm not interested"** → Soft redirect with value proposition
2. **"How did you get my number?"** → Reference lead source
3. **"Is this a scam?"** → Legitimacy reassurance
4. **"I'm busy right now"** → Offer callback
5. **"I already have insurance"** → No-cost review offer

### Technical Implementation
- `ObjectionHandler` class in `src/voice_agent/objection_handler.py`
- `ScriptKnowledgeBase` class for dynamic scripts by lead type
- Casual persona responses integrated into AIDNVoiceAgent

---

## Sample Data (YC Demo Ready)

### Agent Profile
- **Name:** John Smith
- **Description:** Male, 6 feet tall, brown hair, dark suit
- **Vehicle:** Silver Honda Accord, license ABC-1234

### Test Leads (5 Illinois Counties)
1. Mary Johnson - Cook County, Chicago - Final Expense
2. Robert Davis - Sangamon County, Springfield - Term Life
3. Jennifer Wilson - Peoria County, Peoria - Whole Life
4. Michael Brown - Winnebago County, Rockford - Mortgage Protection
5. Sarah Miller - DuPage County, Naperville - Final Expense

### Appointment Slots
- 18 slots generated for next 7 days
- 2-hour gaps between appointments

---

## Security & Compliance

### TCPA Compliance
- Do Not Call list management
- Calling hours enforcement (8 AM - 9 PM local)
- Consent tracking via lead source

### Data Protection
- All credentials in environment variables
- Database credentials not in code
- API keys rotatable

---

## Deployment Architecture

### Current (Development)
- All services run locally
- PostgreSQL local instance
- LiveKit cloud worker

### Production Path
```
Local Dev → Docker Containers → Cloud Deployment
```

Docker infrastructure exists in:
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `Dockerfile.*` for each service

---

## Success Metrics (YC Targets)

| Metric | Industry Average | AIDN Target | Current Capability |
|--------|------------------|-------------|-------------------|
| **Connection Rate** | 5-10% | 15%+ | Can test when audio bridge complete |
| **Booking Rate** | 2-5% | 10%+ | Objection handling ready |
| **Show Rate** | 50-60% | 75%+ | Smart scheduling implemented |
| **Cost per Appointment** | $50-100 | $20-30 | Automation reduces costs |
| **Agent Time Saved** | - | 70%+ | Full automation when bridge complete |

---

## Next Steps

1. **Implement Twilio ↔ LiveKit audio bridge** (Critical - 2-3 days)
2. **Connect voice agent to calls** (1 day)
3. **Wire up dashboard Call button** (4-6 hours)
4. **End-to-end testing** (1-2 days)
5. **YC demo preparation** (ongoing)
