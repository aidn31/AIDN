# AIDN Next Steps

**Last Updated:** January 24, 2026
**Status:** Voice Optimization Complete - Dashboard Integration Next

---

## Completed

### January 24, 2026 - Voice Optimization
- [x] Add per-component latency logging (STT, LLM TTFT, TTS TTFB)
- [x] Log TTFT for each turn number
- [x] Test and switch to Groq LLM (Llama 3.1 8B Instant)
- [x] Optimize VAD settings (min_silence=150ms, endpointing=50-400ms)
- [x] **Reduced latency from 1400-2400ms → 700-800ms (50-65% improvement)**

### January 2, 2026 - LiveKit SIP Migration
- [x] Delete old Twilio bridge code
- [x] Implement LiveKit SIP outbound calling
- [x] Test outbound calls with Telnyx
- [x] Verify greeting and conversation flow
- [x] Update all documentation

---

## Immediate Next Steps

### 1. Voice Quality Improvements (Optional - Lower Priority)
**Goal:** Further improve voice naturalness

#### Phase 3: Improve Voice Quality
- [ ] Add filler words instruction to prompt: "Use umm, yeah, so, oh"
- [ ] Enforce short responses: "Max 2 sentences, max 25 words"
- [ ] Add natural punctuation instruction: "Use commas and periods for pauses"
- [ ] Implement conditional filler injection when LLM takes >300ms
- [ ] Test Cartesia emotion controls (currently using `["positivity:high", "curiosity:medium"]`)
- [ ] Consider switching to emotive-tagged voice (e.g., Marian: `26403c37-80c1-4a1a-8692-540551ca2ae5`)

**See `docs/VOICE_OPTIMIZATION_CHECKLIST.md` for complete checklist.**

### 2. Dashboard Integration (HIGH PRIORITY)
- [ ] Add "Call Lead" button to dashboard
- [ ] Dispatch agent job when button clicked
- [ ] Show call status in real-time
- [ ] Display call logs after completion

### 3. Lead Database Integration
- [ ] Pass lead_id in job metadata
- [ ] Load full lead context from database
- [ ] Personalize greeting with lead name/address
- [ ] Update lead status after call

### 4. Appointment Booking
- [ ] Connect book_appointment tool to database
- [ ] Create appointment slots for agents
- [ ] Confirm bookings via agent response

---

## Future Enhancements

### Call Quality
- [ ] Add call recording
- [ ] Store transcripts in database
- [ ] Implement call analytics
- [ ] Build latency monitoring dashboard (from optimization checklist)

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
- **Current Status:** Ahead of schedule

### Demo Checklist
- [x] Working outbound calls
- [x] AI conversation with casual persona
- [x] Objection handling
- [ ] Dashboard call initiation
- [ ] End-to-end booking flow
- [ ] Recorded demo video
