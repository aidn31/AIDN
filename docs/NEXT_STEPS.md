# AIDN Next Steps

**Last Updated:** January 24, 2026
**Status:** Dashboard Integration Complete - Appointment Booking Next

---

## Completed

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

### 1. Appointment Booking Integration (HIGH PRIORITY)
**Goal:** Complete the demo story - lead → call → appointment → dashboard

- [ ] Connect `confirm_appointment` tool to database
- [ ] Create appointment slots for agents
- [ ] Implement atomic booking (prevent double-booking)
- [ ] Update appointment_slots table when booking confirmed
- [ ] Show booked appointments in dashboard

### 2. Call Status & Logging
- [ ] Update lead status after call (call_outcome, last_called_at)
- [ ] Store call logs in database
- [ ] Display call history in dashboard

### 3. Voice Quality Improvements (Optional - Lower Priority)
- [ ] Add filler words instruction: "Use umm, yeah, so, oh"
- [ ] Enforce short responses: "Max 2 sentences, max 25 words"
- [ ] Test Cartesia emotion controls

---

## Future Enhancements

### Call Quality
- [ ] Add call recording
- [ ] Store transcripts in database
- [ ] Implement call analytics

### Scale
- [ ] Deploy agent to LiveKit Cloud
- [ ] Set up auto-scaling for multiple concurrent calls
- [ ] Add call queuing system

### Features
- [ ] Inbound call handling
- [ ] SMS follow-up after calls
- [ ] Calendar integration for agents

---

## YC Demo Prep

- **Deadline:** February 9, 2026
- **Days Remaining:** ~16 days

### Demo Checklist
- [x] Working outbound calls
- [x] AI conversation with casual persona
- [x] Objection handling (16 scenarios)
- [x] Voice latency ~700-800ms
- [x] **Dashboard call initiation**
- [ ] End-to-end booking flow (appointment shows in dashboard)
- [ ] Recorded demo video
