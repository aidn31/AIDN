# AIDN Project Status

**Last Updated:** January 24, 2026
**Status:** END-TO-END CALLS WORKING - Dashboard → API → Voice Agent → Phone

---

## Current State: Full Demo Flow Working

Dashboard "Call" button triggers real phone calls. Voice agent answers, greets lead by name, handles objections, and books appointments.

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

---

## System Components

| Component | Status | Notes |
|-----------|--------|-------|
| **Voice Agent** | ✅ WORKING | LiveKit SIP + Telnyx, 700-800ms latency |
| **Dashboard** | ✅ WORKING | React + Next.js, real data from API |
| **Backend API** | ✅ WORKING | FastAPI with /leads and /calls/initiate |
| **Database** | ✅ COMPLETE | PostgreSQL with leads, agents, appointments |
| **Phone Provider** | ✅ WORKING | Telnyx |

---

## Recent Milestones

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
- **Days Remaining:** ~16 days
- **Status:** Dashboard integration complete, booking flow next
