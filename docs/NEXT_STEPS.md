# AIDN Next Steps

**Last Updated:** January 26, 2026
**Status:** Google Calendar Integration Complete - Demo Video Next

---

## Completed

### January 26, 2026 - Google Calendar Integration
- [x] Create `src/voice_agent/google_calendar.py` module
- [x] Set up Google Cloud project with Calendar API
- [x] Configure service account authentication
- [x] Integrate `confirm_appointment` tool with Google Calendar
- [x] Fire-and-forget design (booking succeeds even if calendar fails)
- [x] **Appointments now automatically create Google Calendar events**

### January 24, 2026 - Dashboard Integration
- [x] Add FastAPI backend (`src/api/server.py`)
- [x] Add `GET /leads` endpoint returning real leads with UUIDs
- [x] Add `POST /calls/initiate` endpoint with LiveKit dispatch
- [x] Wire dashboard "Call" button to API
- [x] Dashboard fetches real leads from database
- [x] Fix AIDNVoiceAgent instructions property issue
- [x] **End-to-end call flow working: Dashboard → API → LiveKit → Phone**

### January 24, 2026 - Voice Optimization
- [x] Add per-component latency logging (STT, LLM TTFT, TTS TTFB)
- [x] Switch to Groq LLM (Llama 3.1 8B Instant)
- [x] Optimize VAD settings (min_silence=150ms, endpointing=50-400ms)
- [x] **Reduced latency from 1400-2400ms → 700-800ms (50-65% improvement)**

### January 2, 2026 - LiveKit SIP Migration
- [x] Delete old Twilio bridge code
- [x] Implement LiveKit SIP outbound calling
- [x] Test outbound calls with Telnyx

---

## Immediate Next Steps

### 1. Demo Video (HIGH PRIORITY)
**Goal:** Record YC demo video showing full workflow

- [ ] Record 3-5 minute demo showing:
  - Dashboard with leads
  - Click "Call Lead" button
  - Live call with Aiden
  - Natural conversation + objection handling
  - Appointment booking with confirmation code
  - Google Calendar event created
- [ ] Edit video (add captions if needed)
- [ ] Upload to YouTube/Vimeo

### 2. YC Application Materials
- [ ] Write YC application
- [ ] Document key metrics
- [ ] Prepare pitch deck (if needed)

### 3. Final Testing
- [ ] Run 10+ test calls end-to-end
- [ ] Verify calendar events created correctly
- [ ] Test with real phone numbers

---

## Optional Enhancements (If Time Permits)

### Database Integration
- [ ] Connect `confirm_appointment` to appointment_slots table
- [ ] Update lead status after call (call_outcome, last_called_at)
- [ ] Store call logs in database
- [ ] Show booked appointments in dashboard

### Voice Quality
- [ ] Add filler words instruction
- [ ] Enforce short responses
- [ ] Test Cartesia emotion controls

### Scale
- [ ] Deploy agent to LiveKit Cloud
- [ ] Set up auto-scaling
- [ ] Add call queuing system

---

## YC Demo Prep

- **Deadline:** February 9, 2026
- **Days Remaining:** ~14 days

### Demo Checklist
- [x] Working outbound calls
- [x] AI conversation with casual persona
- [x] Objection handling (16 scenarios)
- [x] Voice latency ~700-800ms
- [x] Dashboard call initiation
- [x] **Google Calendar integration**
- [ ] Recorded demo video
- [ ] YC application submitted
