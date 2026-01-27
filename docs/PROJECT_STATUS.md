# AIDN Project Status

**Last Updated:** January 26, 2026
**Status:** GOOGLE CALENDAR INTEGRATION COMPLETE - Full Booking Flow Working

---

## Current State: Full Demo Flow with Calendar Integration

Dashboard "Call" button triggers real phone calls. Voice agent (Aiden) greets lead by name, handles objections, books appointments, and **automatically creates Google Calendar events**.

### What's Working
- ✅ Outbound calls via LiveKit SIP + Telnyx
- ✅ **Aiden persona** - casual, friendly appointment setter
- ✅ Real-time speech-to-text (Deepgram Nova-2)
- ✅ LLM responses (Groq Llama 3.1 8B)
- ✅ **Low-latency TTS (Cartesia)** - ~320ms TTFB
- ✅ Full objection handling (16 scenarios)
- ✅ Appointment tie-down flow with confirmation codes
- ✅ Decision maker verification
- ✅ React dashboard with real data
- ✅ **FastAPI backend with /leads and /calls/initiate endpoints**
- ✅ **Dashboard "Call" button triggers real calls**
- ✅ PostgreSQL database
- ✅ **Google Calendar integration** - appointments auto-create calendar events

---

## System Components

| Component | Status | Notes |
|-----------|--------|-------|
| **Voice Agent** | ✅ WORKING | LiveKit SIP + Telnyx, 700-800ms latency |
| **Dashboard** | ✅ WORKING | React + Next.js, real data from API |
| **Backend API** | ✅ WORKING | FastAPI with /leads and /calls/initiate |
| **Database** | ✅ COMPLETE | PostgreSQL with leads, agents, appointments |
| **Phone Provider** | ✅ WORKING | Telnyx |
| **Calendar Integration** | ✅ WORKING | Google Calendar via service account |

---

## Recent Milestones

### January 26, 2026 - Google Calendar Integration Complete
- Added `src/voice_agent/google_calendar.py` module
- Service account authentication (no OAuth popups)
- `confirm_appointment` tool now creates Google Calendar events
- Fire-and-forget: booking succeeds even if calendar fails
- Calendar events include lead name, phone, address, confirmation code

### January 24, 2026 - End-to-End Call Flow Complete
- Added FastAPI backend (`src/api/server.py`)
- Added `GET /leads` endpoint returning real leads with UUIDs
- Added `POST /calls/initiate` endpoint that dispatches LiveKit agent
- Wired dashboard "Call" button to API
- Dashboard now fetches real leads from database
- Fixed AIDNVoiceAgent instructions property issue
- **Full flow working: Dashboard → API → LiveKit → Voice Agent → Phone**

### January 24, 2026 - Voice Optimization Complete
- Reduced latency from 1400-2400ms → 700-800ms (50-65% improvement)
- Switched to Groq LLM (300-500ms TTFT)
- Optimized VAD settings (150ms silence threshold)

### January 2, 2026 - LiveKit SIP Migration Complete
- Deleted 3,700+ lines of custom bridge code
- Removed Twilio dependency
- Implemented LiveKit SIP outbound calling

---

## Running the System

### Start All Services

```bash
# Terminal 1: Voice Agent
python -m src.voice_agent.main dev

# Terminal 2: API Server
uvicorn src.api.server:app --reload --port 8000

# Terminal 3: Dashboard
cd web-dashboard && npm run dev
```

### Make a Call

1. Open http://localhost:3000/leads
2. Click "Call" on any lead
3. Phone rings, Aiden greets by name
4. Book appointment → Calendar event created automatically

---

## Environment Variables Required

```bash
DATABASE_URL=postgresql://...
DEEPGRAM_API_KEY=...
CARTESIA_API_KEY=sk_car_...
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
SIP_OUTBOUND_TRUNK_ID=ST_...
GROQ_API_KEY=gsk_...
LLM_PROVIDER=groq
GROQ_MODEL=llama-3.1-8b-instant

# Google Calendar Integration
GOOGLE_CALENDAR_CREDENTIALS_PATH=./google-calendar-credentials.json
GOOGLE_CALENDAR_ID=your-calendar-id@gmail.com
```

---

## Voice Metrics

| Metric | Value |
|--------|-------|
| **Total Latency** | 700-800ms |
| **STT Latency** | ~350ms (Deepgram Nova-2) |
| **LLM TTFT** | 300-500ms (Groq) |
| **TTS TTFB** | ~320ms (Cartesia) |

---

## YC Application Timeline

- **Deadline:** February 9, 2026
- **Days Remaining:** ~14 days
- **Status:** Calendar integration complete, demo video next
