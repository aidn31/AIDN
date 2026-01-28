# Voice Agent Development Rules - AIDN

**Purpose:** Task-specific rules for working on AIDN voice agent (Aiden). Load this when optimizing latency, updating prompts, or modifying conversation flow.

---

## 🎯 Core Performance Targets

### Latency Budget
| Component | Current | Target | Status |
|-----------|---------|--------|--------|
| **Total Latency** | 700-800ms | <500ms | 🟡 Needs improvement |
| **STT (Deepgram Nova-2)** | ~350ms | <120ms | 🟡 Needs optimization |
| **LLM TTFT (Groq Llama 3.1 8B)** | 300-500ms | <200ms | 🟡 Acceptable |
| **TTS TTFB (Cartesia Sonic 2)** | ~320ms | <80ms | 🟡 Needs optimization |

**Industry Standard:** Top AI sales agents (Air.ai, Bland.ai) achieve 300-500ms total latency.

**Critical:** Always log latency per component on every call for monitoring.

---

## 🏗️ Architecture: 3-Layer RAG System

### Overview
AIDN uses a 3-layer architecture to keep prompts slim and latency low:

```
┌─────────────────────────────────────────────────────────────┐
│              LAYER 1: SLIM CORE PROMPT                      │
│  core_prompt.py (~66 lines, ~1200 tokens)                  │
│  • Aiden persona and voice style                           │
│  • Conversation flow structure                             │
│  • Lead/agent info injected at runtime                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              LAYER 2: RAG TOOLS                             │
│  get_objection_response() - retrieves from objection_kb    │
│  get_available_times() - appointment availability          │
│  confirm_appointment() - tie-down with confirmation code   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              LAYER 3: KNOWLEDGE BASE                        │
│  objection_kb.json (16 handlers + fallback)               │
└─────────────────────────────────────────────────────────────┘
```

### Critical Rules
- **Core prompt must stay <1500 tokens** - Use RAG for anything longer
- **Never bake objection scripts into prompt** - Use `get_objection_response()` tool
- **Lead info injected at runtime** - Name, address, phone dynamically filled
- **Rebuild prompt ONCE per call** - Not every turn (breaks KV caching)

---

## 🎤 Aiden Persona & Voice Style

### Personality
- **Casual, friendly neighbor** - NOT a salesperson
- **Sound busy but friendly** - Like squeezing them in as a favor
- **Assume familiarity** - Greet like you know them already

### Speech Patterns
- **Use contractions:** "gonna" (not "going to"), "wanna" (not "want to"), "yuh" (not "you")
- **Natural fillers:** "umm", "hmm", "yuh know", "let me see here"
- **Short responses:** MAX 2 sentences, MAX 25 words
- **Always end with question:** Keep control of conversation

### Example Good Response
```
"Umm... let me check here. Morning or afternoon work better?"
"Oh gotcha, gotcha. And you're still at 123 Oak Street, right?"
"Yeah so... they've got availability tomorrow. Does 10am work?"
```

### Example Bad Response
```
"I wanted to let you know that we have availability tomorrow morning or afternoon if either of those times works for you."
```
*Why bad: Too long, formal, no fillers, no question*

---

## ⚡ LLM Configuration: Groq

### Why Groq?
- **TTFT:** 300-500ms (vs 800-1600ms with OpenAI GPT-4o-mini)
- **Cost:** Lower than OpenAI
- **Quality:** Llama 3.1 8B handles casual conversation well

### Setup
```python
from livekit.plugins import groq

llm = groq.LLM(
    model="llama-3.1-8b-instant",  # Fast, good quality
    api_key=os.getenv("GROQ_API_KEY"),
)
```

### Alternative Models
- `llama-3.1-70b-versatile` - Higher quality, slower (~500-700ms)
- `llama-3.1-8b-instant` - Current choice, best balance

### KV Caching Verification
- Turn 1 TTFT: ~500ms (expected - cold start)
- Turn 2+ TTFT: ~300ms (should be faster - caching working)
- **If Turn 2+ is NOT faster** → Prompt is being rebuilt every turn (FIX THIS)

---

## 🗣️ Text-to-Speech: Cartesia Sonic 2

### Basic Setup
```python
from livekit.plugins import cartesia

tts = cartesia.TTS(
    model="sonic-2",  # or "sonic-3" for latest
    voice="your_voice_id",
    speed=1.0,
    emotion=["content:medium", "confident:low"],
)
```

### Speed Control
**API Parameter:**
```python
speed=1.0  # Range: 0.6 (slow) to 1.5 (fast)
# Granular: -1.0 to 1.0 (-1.0 = slowest, 0.0 = default, 1.0 = fastest)
```

**SSML Tag (in transcript):**
```python
transcript = '<speed ratio="1.2"/>I want to speak faster here.'
transcript = '<speed ratio="0.8"/>Now I am speaking more slowly.'
```

### Emotion Control
**Recommended for Insurance Sales:**
```python
emotion=[
    "content:medium",   # Satisfied, relaxed tone
    "confident:low",    # Slight confidence without arrogance
]
```

**Alternative combos to test:**
- `["friendly:medium"]` - Warm and approachable
- `["enthusiastic:low", "content:medium"]` - Upbeat but not pushy
- `["calm:medium", "confident:low"]` - Trustworthy and professional

**Primary Emotions (Best Results):**
- `neutral` - Default, professional
- `content` - Satisfied, friendly
- `excited` - Enthusiasm, good news
- `angry` - Frustration (use carefully)
- `sad` - Empathy, bad news
- `scared` - Urgency, concern

**SSML Tag (in transcript):**
```python
transcript = '<emotion value="excited"/>Wow, that sounds amazing!'
transcript = '<emotion value="content"/>Oh yeah, that works perfectly for me.'
```

### Best Voice for Emotion
**Recommended:** Use voices tagged 'Emotive' in Cartesia Voice Library
**Top Choice:** Marian - ID: `26403c37-80c1-4a1a-8692-540551ca2ae5`

### Natural Pauses (No SSML Needed)
Use punctuation to create natural pauses:
- Period (.) = full pause
- Comma (,) = short pause
- Ellipsis (...) = hesitation pause
- Dash (—) = quick pause

Example:
```
"Oh yeah... so they've got Mike in your area tomorrow. Morning, or afternoon?"
```

---

## 🎧 VAD (Voice Activity Detection) Tuning

### Current Settings (Optimized)
```python
vad = silero.VAD.load(
    min_silence_duration=0.15,  # 150ms - how long silence before considering speech ended
    min_speech_duration=0.05,   # 50ms - minimum speech to trigger
    max_buffered_speech=30.0,   # 30 seconds max
)
```

### Why These Settings?
- **150ms silence** - Fast turnaround without cutting people off
- **50ms speech trigger** - Catches quick responses like "yeah"
- Previously was 550ms → caused 400ms unnecessary delay

### Tuning Guide
- **Too aggressive (100ms):** Cuts people off mid-sentence
- **Too conservative (500ms+):** Awkward pauses, feels slow
- **Sweet spot:** 150-200ms for insurance sales conversations

---

## 📞 Testing Procedures

### Testing Strategy

**3 Levels of Testing:**
1. **Unit Tests** - Test individual functions (prompt building, RAG retrieval)
2. **Integration Tests** - Test component interactions (LLM → TTS pipeline)
3. **E2E Tests** - Real phone calls (most important for voice)

### Unit Tests (pytest)

**Location:** `tests/test_voice_agent.py`

**Test prompt generation:**
```python
import pytest
from src.voice_agent.core_prompt import build_core_prompt

def test_prompt_includes_lead_name():
    """Verify lead name is injected into prompt"""
    lead = {
        "first_name": "John",
        "last_name": "Smith",
        "address": "123 Oak St",
        "county": "Cook"
    }
    agent = {"agent_name": "Mike"}
    
    prompt = build_core_prompt(lead, agent)
    
    assert "John" in prompt
    assert "123 Oak St" in prompt
    assert "Mike" in prompt

def test_prompt_token_count():
    """Verify prompt stays under 1500 tokens"""
    lead = {...}
    agent = {...}
    
    prompt = build_core_prompt(lead, agent)
    estimated_tokens = len(prompt) // 4
    
    assert estimated_tokens < 1500, f"Prompt too long: {estimated_tokens} tokens"
```

**Test RAG retrieval:**
```python
from src.voice_agent.aidn_agent_v2 import get_objection_response

@pytest.mark.asyncio
async def test_objection_retrieval():
    """Verify objection handler returns correct response"""
    response = await get_objection_response("I'm not interested")
    
    assert response is not None
    assert len(response) > 0
    assert "not interested" in response.lower() or "no worries" in response.lower()

@pytest.mark.asyncio
async def test_objection_fallback():
    """Verify fallback for unknown objection"""
    response = await get_objection_response("xyz unknown objection xyz")
    
    assert response is not None  # Should return fallback response
```

**Run tests:**
```bash
pytest tests/test_voice_agent.py -v
```

### Integration Tests

**Test LLM → TTS pipeline:**
```python
@pytest.mark.asyncio
async def test_conversation_turn():
    """Test full turn: user input → LLM → TTS"""
    from livekit.plugins import groq, cartesia
    
    llm = groq.LLM(model="llama-3.1-8b-instant")
    tts = cartesia.TTS(voice="marian")
    
    # Simulate user input
    messages = [
        {"role": "system", "content": "You are a friendly assistant."},
        {"role": "user", "content": "What time works best?"}
    ]
    
    # Get LLM response
    response = await llm.chat(messages)
    assert len(response.content) > 0
    assert len(response.content) < 200  # Short response
    
    # Generate TTS
    audio_stream = tts.stream(response.content)
    assert audio_stream is not None
```

### E2E Tests (Real Phone Calls)

**Always Test With Real Phone Calls**

**Never use:**
- Simulators
- Text-based testing
- Audio file playback

**Why:** Real calls expose issues simulators miss:
- Network jitter
- Audio codec artifacts
- Real-world background noise
- Actual conversation dynamics

### Test Call Checklist
Before considering voice work complete:

1. **Latency Test**
   - [ ] Make 5+ test calls
   - [ ] Log STT, LLM TTFT, TTS TTFB per turn
   - [ ] Verify Turn 2+ is faster than Turn 1 (KV caching)
   - [ ] Average total latency <800ms

2. **Conversation Quality**
   - [ ] Greets by name correctly
   - [ ] Sounds casual, not corporate
   - [ ] Uses filler words naturally
   - [ ] Responses are short (<25 words)
   - [ ] Always ends with question

3. **Objection Handling**
   - [ ] Test all 16 objection scenarios
   - [ ] Verify RAG tool triggers correctly
   - [ ] Check response quality
   - [ ] Log any objections not handled well

4. **Appointment Booking**
   - [ ] Books appointment successfully
   - [ ] Creates Google Calendar event
   - [ ] Provides confirmation code
   - [ ] Handles "no available times" gracefully

5. **Edge Cases**
   - [ ] Background noise
   - [ ] Fast talkers
   - [ ] Interruptions
   - [ ] "I need to think about it"
   - [ ] Wrong number

### Latency Logging Template
```python
import logging
logger = logging.getLogger("aidn.voice")

# Log per turn
logger.info(f"Turn {turn_num} | STT: {stt_ms}ms | LLM: {llm_ttft_ms}ms | TTS: {tts_ttfb_ms}ms | Total: {total_ms}ms")
```

---

## 🛠️ Objection Handling (RAG System)

### How It Works
1. User says objection: "I'm not interested"
2. Agent detects objection type
3. Agent calls: `get_objection_response("I'm not interested")`
4. RAG looks up in `objection_kb.json` → finds `not_interested_1`
5. Returns formatted response with lead info filled in
6. Agent speaks response

### Objection KB Structure
```json
{
  "id": "not_interested_1",
  "name": "Not Interested - Direct",
  "triggers": ["not interested", "don't want", "not for me"],
  "strategy": "Acknowledge, soft redirect to info only",
  "response": "Oh no worries {first_name}, this is just about the info you requested. {agent_name} is just gonna drop it off and go over it real quick. Takes like 10 minutes. Morning or afternoon?"
}
```

### Adding New Objections
1. Edit `src/voice_agent/objection_kb.json`
2. Add new object to `objections` array
3. Include multiple trigger phrases
4. Test with real calls
5. Iterate based on results

### 16 Current Objection Handlers
1. What is it / What info
2. Not interested (direct)
3. Not interested (soft)
4. How did you get my number
5. Is this a scam
6. I'm busy right now
7. Call me back later
8. I already have insurance
9. Send me information
10. I need to think about it
11. Talk to my spouse
12. Don't have time
13. Not a good time
14. Put me on do not call
15. Wrong number
16. Hang up (fallback)

---

## 💰 Cost Tracking & Optimization

### Per-Call Cost Breakdown (Current Stack)

**MVP Cost Structure:**
```python
# Average 2-3 minute call
STT (Deepgram Nova-2):     $0.004/minute × 2.5min = $0.010
LLM (Groq Llama 3.1 8B):   $0.10/1M tokens × ~1K tokens = $0.0001
TTS (Cartesia Sonic 2):    $0.005/minute × 2.5min = $0.0125
LiveKit:                   $0.005/minute × 2.5min = $0.0125

Total per call:            $0.0351 (~3.5 cents)
```

**With 10% booking rate:**
- Cost per appointment: ~$0.35 (10 calls to get 1 booking)
- Monthly cost for 1000 calls: ~$35
- Monthly cost for 10,000 calls: ~$350

### Cost Logging (Per Call)

**Track in call_logs table:**
```python
call_metrics = {
    "call_id": call_id,
    "duration_seconds": duration,
    
    # Costs
    "cost_stt": duration_minutes * 0.004,
    "cost_llm": (prompt_tokens + completion_tokens) / 1_000_000 * 0.10,
    "cost_tts": duration_minutes * 0.005,
    "cost_livekit": duration_minutes * 0.005,
    "cost_total": sum([cost_stt, cost_llm, cost_tts, cost_livekit]),
}

await call_log_repo.create_call_log(call_metrics)
```

### Daily Cost Monitoring

**Dashboard query:**
```sql
SELECT 
    DATE(started_at) as date,
    COUNT(*) as calls_count,
    SUM(cost_total) as total_cost,
    AVG(cost_total) as avg_cost_per_call,
    SUM(CASE WHEN outcome = 'booked' THEN 1 ELSE 0 END) as appointments,
    SUM(cost_total) / NULLIF(SUM(CASE WHEN outcome = 'booked' THEN 1 ELSE 0 END), 0) as cost_per_appointment
FROM call_logs
WHERE started_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(started_at)
ORDER BY date DESC;
```

### Budget Alerts

**Set up alerts (see monitoring_rules.md):**
- Daily spend > $50 → Email alert
- Cost per call > $0.10 (3x normal) → Investigate
- Monthly projection > $500 → Warning

### Cost Optimization Strategies

#### 1. KV Caching (Reduces LLM Cost 40%)

**Current implementation:**
```python
# Build prompt ONCE at call start
system_prompt = build_core_prompt(lead, agent)
messages = [{"role": "system", "content": system_prompt}]

# Append messages (don't rebuild)
messages.append({"role": "user", "content": user_text})
response = await llm.chat(messages)
messages.append({"role": "assistant", "content": response})
```

**Impact:** Turn 2+ costs 40-60% less than Turn 1

#### 2. Hang Up Quickly on Wrong Number

**Current:** Voice agent detects wrong number → Says goodbye → Hangs up
**Optimization:** Detect in first 10 seconds, minimize TTS cost

```python
if "wrong number" in user_text or "who is this" in user_text:
    await session.say("Oh sorry, wrong number!")  # Short response
    await session.end()  # Hang up immediately
```

**Savings:** $0.02-0.03 per wrong number (vs full conversation)

#### 3. Cache Common TTS Phrases

**Future optimization (post-MVP):**
```python
# Pre-generate common phrases
common_phrases = {
    "greeting": await tts.generate("Hey {name}! This is Aiden..."),
    "not_home": await tts.generate("Oh gotcha, when's better?"),
    "wrong_number": await tts.generate("Oh sorry, wrong number!")
}

# Use cached audio instead of generating every time
await session.play_audio(common_phrases["greeting"])
```

**Savings:** ~30% of TTS cost (most calls use same phrases)

#### 4. Smart Retry Logic

**Don't retry expensive failures:**
```python
if call_outcome == "disconnected":
    # Number out of service - don't retry
    mark_lead_inactive(lead_id)
elif call_outcome == "wrong_number":
    # Wrong person - don't retry
    mark_lead_inactive(lead_id)
elif call_outcome == "no_answer":
    # Retry 2 more times (3 total)
    schedule_retry(lead_id, delay_hours=2)
```

**Savings:** Don't waste money calling disconnected numbers

### Competitive Cost Analysis

**AIDN vs Competitors:**

| Provider | Cost per Call | Notes |
|----------|---------------|-------|
| **AIDN** | **$0.035** | Your current cost |
| Air.ai | $0.10-0.15 | Higher quality voice |
| Bland.ai | $0.08-0.12 | Mid-tier pricing |
| Synthflow | $0.05-0.08 | Similar stack |
| Human caller | $0.50-2.00 | Hourly wage + benefits |

**Your advantage:** 3-10x cheaper than human, competitive with AI competitors

### Monthly Cost Projections

**At different call volumes:**

| Calls/Month | Cost at $0.035/call | Appointments (10% rate) | Cost per Appt |
|-------------|---------------------|-------------------------|---------------|
| 1,000 | $35 | 100 | $0.35 |
| 5,000 | $175 | 500 | $0.35 |
| 10,000 | $350 | 1,000 | $0.35 |
| 50,000 | $1,750 | 5,000 | $0.35 |
| 100,000 | $3,500 | 10,000 | $0.35 |

**Note:** Cost scales linearly, cost per appointment stays constant

### Budget Planning

**MVP Budget (First Month):**
- Testing (500 calls): $17.50
- Demo to investors (100 calls): $3.50
- Buffer for mistakes: $30
- **Total:** ~$50/month

**Growth Budget (3 Months Post-Launch):**
- 10,000 calls/month: $350
- Error buffer (5%): $18
- **Total:** ~$370/month

**Scale Budget (6 Months):**
- 50,000 calls/month: $1,750
- Better pricing (volume discount): -$250
- **Total:** ~$1,500/month

---

## 🔄 Prompt Optimization Workflow

### When to Update Core Prompt
- Aiden sounds too formal/corporate
- Responses are too long
- Missing key persona elements
- Conversation flow broken

### When to Update Objection KB
- New objection pattern emerges
- Current response not working
- Need more trigger phrases
- Better response discovered

### Editing Guidelines
**Core Prompt (`core_prompt.py`):**
- Keep under 1500 tokens (~66 lines)
- Focus on persona and flow
- Don't add specific scripts
- Test token count after edits

**Objection KB (`objection_kb.json`):**
- Add trigger variations liberally
- Keep responses conversational
- Include lead/agent variable placeholders: `{first_name}`, `{agent_name}`, `{address}`
- Test each objection with real calls

### Token Counting
```bash
cd src/voice_agent
python3 -c "
from core_prompt import build_core_prompt
prompt = build_core_prompt()
print(f'Prompt length: {len(prompt)} chars')
print(f'Estimated tokens: {len(prompt) // 4}')
"
```
**Target: ~1200 tokens or less**

---

## 🚫 Common Pitfalls (Voice-Specific)

### ❌ Don't Do This
1. **Don't bloat the core prompt**
   - Adding objection scripts directly → Use RAG
   - Long backstory → Keep it minimal
   - Excessive examples → 2-3 max

2. **Don't rebuild prompt every turn**
   - Breaks KV caching
   - Adds 300-500ms per turn
   - Build once at call start

3. **Don't skip latency logging**
   - Can't optimize what you don't measure
   - Log STT, LLM TTFT, TTS TTFB separately
   - Track per turn, not just averages

4. **Don't test with simulators**
   - Real calls expose real issues
   - Network latency matters
   - Background noise matters

5. **Don't hardcode lead/agent info in prompt**
   - Inject at runtime: `{first_name}`, `{address}`
   - Makes prompt reusable
   - Enables dynamic personalization

6. **Don't forget fire-and-forget for calendar**
   - Appointment booking must succeed even if Google Calendar API fails
   - Log calendar errors but don't block booking

### ✅ Do This Instead
1. **Keep prompt slim** - Use RAG for everything else
2. **Build prompt once** - Append messages, don't rebuild
3. **Log everything** - STT, LLM, TTS latency per turn
4. **Test with real calls** - Always
5. **Inject variables** - `{first_name}`, `{agent_name}` at runtime
6. **Graceful degradation** - Booking > Calendar event creation

---

## 📊 Performance Monitoring

### What to Track
```python
# Per call
- total_latency_ms
- stt_latency_ms
- llm_ttft_ms (per turn)
- tts_ttfb_ms
- turn_count
- conversation_duration_seconds

# Per turn
- turn_number
- user_input_length
- ai_response_length
- llm_ttft_ms (should decrease after Turn 1)

# Outcomes
- appointment_booked (bool)
- calendar_event_created (bool)
- objections_handled (list)
- hang_up_reason
```

### Target Metrics
- **P50 latency:** <500ms (industry competitive)
- **P95 latency:** <700ms
- **KV cache improvement:** Turn 2+ should be 40-60% faster than Turn 1
- **Response length:** <25 words average
- **Appointment rate:** >10% of conversations

---

## 🔧 Troubleshooting

### Issue: High Latency (>1000ms)
**Check:**
1. Is KV caching working? (Turn 2+ faster than Turn 1?)
2. Is prompt under 1500 tokens?
3. Using Groq or OpenAI? (Groq is faster)
4. STT/TTS latency acceptable?

**Fix:**
- Verify prompt built once, not every turn
- Trim prompt if over 1500 tokens
- Switch to Groq if using OpenAI
- Check network latency to APIs

### Issue: Aiden Sounds Robotic
**Check:**
1. Using Cartesia emotion controls?
2. Prompt includes filler words instruction?
3. Responses under 25 words?
4. Using casual contractions?

**Fix:**
- Add emotion: `["content:medium"]`
- Update prompt to enforce fillers
- Add max word limit to prompt
- Test with emotive voice (Marian)

### Issue: Objections Not Handled
**Check:**
1. Is RAG tool triggering?
2. Are trigger phrases in `objection_kb.json`?
3. Is response quality good?

**Fix:**
- Add more trigger variations
- Test manually: `get_objection_response("not interested")`
- Update response script in JSON
- Add new objection handler if pattern not covered

### Issue: Turn 2+ Not Faster
**Check:**
1. Prompt being rebuilt every turn?
2. Messages appended or replaced?

**Fix:**
- Build prompt once at session start
- Append messages: `messages.append({"role": "user", "content": text})`
- Don't create new prompt/context per turn

---

## 🎯 Success Criteria for Voice Agent Work

Voice agent work is complete when:

- [ ] Total latency consistently <500ms (competitive with top AI sales agents)
- [ ] Turn 2+ TTFT is 40-60% faster than Turn 1 (KV caching)
- [ ] Responses sound natural (pass "friend test")
- [ ] Responses are short (under 25 words average)
- [ ] All 16 objection scenarios handled gracefully
- [ ] 10+ test calls with good metrics
- [ ] E2E flow working: Dashboard → Call → Appointment → Calendar
- [ ] Latency logged and monitored

---

*Reference Doc | Voice Agent | Last Updated: January 27, 2026*
