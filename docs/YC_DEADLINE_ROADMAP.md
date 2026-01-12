# YC Application Deadline Roadmap
**Deadline: February 9, 2026**  
**Days Remaining: ~35 days**  
**Last Updated: January 5, 2026**

---

## 🎯 Critical Path: What MUST Be Done for YC Demo

### ✅ Already Complete
- [x] Working outbound calls via LiveKit SIP + Telnyx
- [x] AI conversation with casual Aiden persona
- [x] Objection handling (12 scenarios)
- [x] React dashboard UI
- [x] FastAPI backend
- [x] PostgreSQL database
- [x] 3-layer RAG architecture (slim prompt + RAG tools)

### 🔴 CRITICAL: Voice Optimization (Weeks 1-2)
**Why:** Current latency (1400-2400ms) is too slow for convincing demo. Target: <500ms

#### Week 1: Diagnose & Fix Latency (Jan 5-11)
**Priority: HIGHEST** - This is the biggest blocker

1. **Add Latency Logging** (Day 1-2)
   - [ ] Add per-component latency logging (STT, LLM TTFT, TTS TTFB)
   - [ ] Log TTFT for each turn number (Turn 1, Turn 2, Turn 3...)
   - [ ] Record 5-10 test calls with full latency data
   - [ ] Answer: Is Turn 2+ faster than Turn 1? (KV caching check)

2. **Test Groq LLM** (Day 2-3)
   - [ ] Sign up for Groq (console.groq.com)
   - [ ] Test Groq Llama 3.1 70B in agent
   - [ ] Compare TTFT: Groq vs GPT-4o-mini
   - [ ] If Groq is faster, switch to it (may reduce LLM TTFT from 800-1600ms → <300ms)
   - **Expected Impact:** Biggest latency reduction possible

3. **Verify Streaming** (Day 3)
   - [ ] Verify STT is streaming partial transcripts
   - [ ] Verify LLM is streaming tokens (not waiting for full response)
   - [ ] Verify TTS starts on first sentence (not full response)

4. **Prompt Optimization** (Day 4)
   - [ ] Confirm prompt is built ONCE at call start (not every turn)
   - [ ] Verify system prompt is under 600 tokens (currently ~1200)
   - [ ] Ensure messages are appended (not rebuilt each turn)

#### Week 2: Voice Quality & Integration (Jan 12-18)

5. **Improve Voice Naturalness** (Day 5-6)
   - [ ] Add filler words instruction to prompt: "Use umm, yeah, so, oh"
   - [ ] Enforce short responses: "Max 2 sentences, max 25 words"
   - [ ] Add natural punctuation instruction
   - [ ] Include example responses with fillers in prompt
   - [ ] Implement conditional filler injection when LLM takes >300ms

6. **Tune TTS & VAD** (Day 7)
   - [ ] Test Cartesia emotion controls (try `["content:medium", "confident:low"]`)
   - [ ] Consider switching to emotive-tagged voice (Marian: `26403c37-80c1-4a1a-8692-540551ca2ae5`)
   - [ ] Tune VAD settings (reduce min_silence_duration from 0.55s to 0.4s)
   - [ ] Test with real calls - ensure it doesn't cut people off

7. **Validation Testing** (Day 8-9)
   - [ ] Run 10 test calls after each change
   - [ ] Measure average total latency and P95 latency
   - [ ] Record 5+ test calls, listen for naturalness
   - [ ] Get feedback from someone who doesn't know it's AI
   - [ ] **Target:** Total latency consistently <500ms

### 🟡 HIGH: Dashboard Integration (Week 3: Jan 19-25)
**Why:** YC needs to see the full workflow, not just voice calls

8. **Dashboard Call Initiation** (Day 10-12)
   - [ ] Add "Call Lead" button to dashboard leads table
   - [ ] Wire up button to dispatch agent job via API
   - [ ] Pass lead_id and agent_id in job metadata
   - [ ] Show call status in real-time (calling → connected → ended)

9. **Lead Database Integration** (Day 13-14)
   - [ ] Load full lead context from database when call starts
   - [ ] Personalize greeting with lead name/address (already partially done)
   - [ ] Update lead status after call (call_outcome, last_called_at, call_count)
   - [ ] Display call logs in dashboard after completion

### 🟢 MEDIUM: End-to-End Booking Flow (Week 4: Jan 26-Feb 1)
**Why:** Complete the demo story - lead → call → appointment

10. **Appointment Booking Integration** (Day 15-17)
    - [ ] Connect `confirm_appointment` tool to database
    - [ ] Create appointment slots for agents (based on availability settings)
    - [ ] Implement atomic booking (prevent double-booking)
    - [ ] Update appointment_slots table when booking confirmed
    - [ ] Show booked appointments in dashboard

11. **End-to-End Testing** (Day 18-19)
    - [ ] Test full flow: Upload lead → Call lead → Book appointment → View in dashboard
    - [ ] Fix any integration bugs
    - [ ] Verify data flows correctly between components

### 🟢 MEDIUM: Demo Preparation (Week 5: Feb 2-8)
**Why:** Polish and prepare for YC application

12. **Demo Video** (Day 20-22)
    - [ ] Record 3-5 minute demo video showing:
      - Dashboard with leads
      - Click "Call Lead" button
      - Live call with Aiden (real phone number)
      - Natural conversation + objection handling
      - Appointment booking
      - Dashboard showing completed call + appointment
    - [ ] Edit video (add captions, highlights)
    - [ ] Upload to YouTube/Vimeo

13. **Application Materials** (Day 23-24)
    - [ ] Write YC application (incorporate demo video)
    - [ ] Document key metrics (latency improvements, conversion rates)
    - [ ] Prepare pitch deck (if needed)
    - [ ] Review all materials

14. **Final Testing** (Day 25)
    - [ ] Run 10+ test calls end-to-end
    - [ ] Verify all features work reliably
    - [ ] Test with real phone numbers
    - [ ] Fix any last-minute bugs

---

## 📊 Success Criteria for YC Demo

### Must Have (Critical)
- ✅ Working outbound calls
- ✅ AI conversation with casual persona
- ✅ Objection handling
- [ ] **Total latency <500ms** (currently 1400-2400ms)
- [ ] **Dashboard call initiation** (click button → call starts)
- [ ] **End-to-end booking flow** (call → appointment → dashboard)
- [ ] **Recorded demo video** showing full workflow

### Nice to Have (If Time Permits)
- [ ] Call recording & transcripts stored
- [ ] Basic analytics dashboard
- [ ] Multiple agent support
- [ ] Lead upload via CSV/Excel

---

## ⚠️ Risk Mitigation

### High Risk Items
1. **Voice Latency** - If Groq doesn't help, may need alternative approaches
   - **Mitigation:** Start testing Groq immediately (Day 2-3)
   - **Backup:** Optimize prompt further, consider faster LLM models

2. **Integration Bugs** - Dashboard ↔ Voice Agent ↔ Database
   - **Mitigation:** Test each integration point separately before combining
   - **Backup:** Have manual workarounds for demo if needed

3. **Demo Day Failures** - Live calls could fail during presentation
   - **Mitigation:** Record backup demo video with successful calls
   - **Backup:** Have pre-recorded segments ready

### Timeline Buffer
- **Week 1-2:** Voice optimization (critical path)
- **Week 3:** Dashboard integration (can be done in parallel with voice testing)
- **Week 4:** End-to-end flow (polish)
- **Week 5:** Demo prep (buffer week)

---

## 📅 Weekly Milestones

| Week | Dates | Milestone | Status |
|------|-------|-----------|--------|
| **Week 1** | Jan 5-11 | Latency diagnosis + Groq test | 🔴 In Progress |
| **Week 2** | Jan 12-18 | Voice quality improvements + validation | ⏳ Pending |
| **Week 3** | Jan 19-25 | Dashboard integration complete | ⏳ Pending |
| **Week 4** | Jan 26-Feb 1 | End-to-end booking flow | ⏳ Pending |
| **Week 5** | Feb 2-8 | Demo video + application | ⏳ Pending |
| **Deadline** | **Feb 9** | **YC Application Due** | 🎯 Target |

---

## 🎯 Daily Focus Areas

### This Week (Jan 5-11)
**Focus: Diagnose latency bottlenecks**

- **Monday-Tuesday:** Add comprehensive latency logging
- **Wednesday-Thursday:** Test Groq LLM alternative
- **Friday:** Verify streaming + prompt optimization
- **Weekend:** Analyze results, plan Week 2

### Next Week (Jan 12-18)
**Focus: Improve voice quality**

- **Monday-Tuesday:** Update prompt for naturalness
- **Wednesday:** Implement filler injection
- **Thursday:** Tune TTS/VAD settings
- **Friday-Saturday:** Validation testing (10+ calls)
- **Sunday:** Review metrics, ensure <500ms target

### Week 3 (Jan 19-25)
**Focus: Dashboard integration**

- **Monday-Wednesday:** Dashboard call button + API integration
- **Thursday-Friday:** Lead database integration
- **Weekend:** Testing + bug fixes

### Week 4 (Jan 26-Feb 1)
**Focus: End-to-end flow**

- **Monday-Wednesday:** Appointment booking integration
- **Thursday-Friday:** End-to-end testing
- **Weekend:** Polish + bug fixes

### Week 5 (Feb 2-8)
**Focus: Demo preparation**

- **Monday-Wednesday:** Record demo video
- **Thursday:** Edit video + application materials
- **Friday:** Final testing + review
- **Weekend:** Submit application

---

## 📝 Notes

- **Current Status:** Voice agent working, but latency too high (1400-2400ms)
- **Biggest Opportunity:** Groq LLM could reduce latency by 50-70%
- **Critical Path:** Voice optimization → Dashboard integration → Booking flow → Demo
- **Buffer:** Week 5 provides buffer for unexpected issues

---

**Last Updated:** January 5, 2026  
**Next Review:** End of Week 1 (Jan 11)
