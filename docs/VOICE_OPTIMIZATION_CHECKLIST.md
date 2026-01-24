# AIDN VOICE Optimization Checklist

## Phase 1: Diagnose (Do This First)
*Goal: Understand exactly where your latency is coming from*

### Logging & Measurement
- [x] Add per-component latency logging (STT, LLM TTFT, TTS TTFB)
- [x] Log TTFT for each turn number (Turn 1, Turn 2, Turn 3...)
- [x] Check if TTFT improves after Turn 1 (indicates KV caching is working)
- [ ] Log total token count sent per turn
- [ ] Record 5-10 test calls with full latency data

### Key Questions to Answer
- [ ] Is Turn 2+ faster than Turn 1? (If no → caching broken)
- [ ] Are you rebuilding the prompt every turn? (If yes → fix it)
- [ ] Is streaming enabled end-to-end? (If no → enable it)
- [ ] What's your actual STT latency? (Target: <150ms)
- [ ] What's your actual TTS TTFB? (Target: <100ms)

---

## Phase 2: Fix Latency (Critical Path)
*Goal: Get total latency from 1400-2400ms → <500ms*

### LLM (Your Biggest Problem: 800-1600ms → Target <300ms)
- [ ] Sign up for Groq (console.groq.com)
- [ ] Test Groq Llama 3.1 70B in your agent
- [ ] Compare TTFT: Groq vs GPT-4o-mini
- [ ] If Groq is faster, switch to it
- [ ] Verify KV caching is working (Turn 2 should be faster)

### Prompt Optimization
- [ ] Confirm prompt is built ONCE at call start (not every turn)
- [ ] Keep system prompt under 600 tokens
- [ ] Append messages to existing array (don't rebuild)
- [ ] Remove any unnecessary context from first turn

### Streaming
- [ ] Verify STT is streaming partial transcripts (`interim_results=True`)
- [ ] Verify LLM is streaming tokens (not waiting for full response)
- [ ] Verify TTS starts on first sentence (not full response)

### VAD Tuning
- [ ] Reduce `min_silence_duration` from 0.55s to 0.4s
- [ ] Test with real calls - make sure it doesn't cut people off
- [ ] Adjust if needed (range: 0.3s - 0.5s)

### Pre-warming
- [ ] Pre-load VAD model before calls
- [ ] Pre-load STT model before calls
- [ ] Pre-load TTS model/voice before calls
- [ ] Verify connection pooling for LLM API

---

## Phase 3: Improve Voice Quality
*Goal: Make Aiden sound human, not robotic*

### Cartesia Voice Controls (CONFIRMED SUPPORTED)
- [ ] Add emotion parameter to TTS config (e.g., `emotion=["positivity:high"]`)
- [ ] Test speed parameter (range: 0.6 to 1.5, or -1.0 to 1.0 for granular)
- [ ] Try SSML tags in transcript for pauses: `<speed ratio="0.9"/>`
- [ ] Test emotion SSML: `<emotion value="content"/>`
- [ ] Use recommended emotive voices (see Cartesia Voice Library tagged 'Emotive')

### Prompt Updates for Natural Speech
- [ ] Add filler words instruction: "Use umm, yeah, so, oh"
- [ ] Enforce short responses: "Max 2 sentences, max 25 words"
- [ ] Add natural punctuation instruction: "Use commas and periods for pauses"
- [ ] Include example responses with fillers in prompt

### Filler Injection (Conditional - Only When LLM is Slow)
- [ ] Implement filler injection when LLM takes >300ms
- [ ] Create filler word list: "Umm...", "Let me see...", "Oh yeah, so..."
- [ ] Test that fillers don't overlap with actual response
- [ ] Make sure filler only triggers on timeout, not every response

### Response Length Control
- [ ] Add max word limit to prompt (25 words)
- [ ] Add post-processing truncation as backup
- [ ] Verify responses end with questions (keeps control)

---

## Phase 4: Testing & Validation
*Goal: Confirm improvements with real data*

### Latency Testing
- [ ] Run 10 test calls after each change
- [ ] Measure average total latency
- [ ] Measure P95 latency (worst case)
- [ ] Compare before/after for each fix

### Voice Quality Testing
- [ ] Record 5+ test calls with new voice settings
- [ ] Listen for: natural pauses, filler words, pacing
- [ ] Get feedback from someone who doesn't know it's AI
- [ ] Rate naturalness 1-10

### Conversion Testing (Before YC)
- [ ] Track appointment set rate before changes
- [ ] Track appointment set rate after changes
- [ ] Measure call duration changes
- [ ] Note any common drop-off points

---

## Quick Reference: Target Metrics

| Metric | Before | After | Target | Status |
|--------|--------|-------|--------|--------|
| Total Latency | 1400-2400ms | **700-800ms** | <500ms | ✅ 50-65% improved |
| STT | 350-500ms | **~350ms** | <150ms | 🟡 Acceptable |
| LLM TTFT | 800-1600ms | **300-500ms** | <300ms | ✅ 60% improved |
| TTS TTFB | ~320ms | **~320ms** | <100ms | 🟡 Acceptable |
| Response Length | Unknown | Unknown | <25 words | ⏳ Pending |

---

## Completed Optimizations

### Phase 1: Diagnostics - DONE
1. ☑ Add latency logging per component
2. ☑ Check if Turn 2 is faster than Turn 1 (KV caching confirmed working)
3. ☑ Test Groq as LLM alternative
4. ☑ Verify streaming is enabled

### Phase 2: Latency Fixes - DONE
5. ☑ Switch to Groq Llama 3.1 8B Instant
6. ☑ Optimize VAD settings (min_silence=150ms)
7. ☑ Reduce endpointing delays (50ms-400ms)

### Still To Do (Lower Priority)
8. ☐ Update prompt for filler words and short responses
9. ☐ Implement conditional filler injection (only when slow)
10. ☐ Test Cartesia emotion controls
11. ☐ A/B test voice options

---

## Code Snippets to Implement

### 1. Latency Logging
```python
import time
import logging

logger = logging.getLogger("aidn")

class LatencyTracker:
    def __init__(self):
        self.metrics = {}

    async def track(self, name, coro):
        start = time.perf_counter()
        result = await coro
        elapsed = (time.perf_counter() - start) * 1000
        self.metrics[name] = elapsed
        logger.info(f"⏱ {name}: {elapsed:.0f}ms")
        return result

# Usage:
tracker = LatencyTracker()
transcript = await tracker.track("STT", stt.transcribe(audio))
response = await tracker.track("LLM", llm.generate(transcript))
audio = await tracker.track("TTS", tts.synthesize(response))
logger.info(f"📊 Total: {sum(tracker.metrics.values()):.0f}ms")
```

### 2. Check KV Caching (Per-Turn TTFT)
```python
turn_number = 0

async def on_user_message(message):
    global turn_number
    turn_number += 1

    start = time.perf_counter()
    response = await llm.generate(messages)
    ttft = (time.perf_counter() - start) * 1000

    logger.info(f"Turn {turn_number} TTFT: {ttft:.0f}ms")

    # Expected (caching working):
    # Turn 1: 900ms (slow - expected)
    # Turn 2: 350ms (fast!)
    # Turn 3: 320ms (fast!)

    # Problem (caching broken):
    # Turn 1: 900ms
    # Turn 2: 880ms  ← PROBLEM
    # Turn 3: 920ms  ← PROBLEM
```

### 3. Conditional Filler Injection
```python
import asyncio
import random

FILLERS = ["Umm...", "Let me see...", "Oh yeah, so...", "Gotcha..."]

async def respond_with_filler_if_slow(user_input, llm, tts):
    """Only inject filler if LLM takes >300ms"""
    llm_task = asyncio.create_task(llm.generate(user_input))

    try:
        # Wait 300ms for LLM response
        response = await asyncio.wait_for(llm_task, timeout=0.3)
    except asyncio.TimeoutError:
        # LLM is slow - inject filler while waiting
        await tts.speak(random.choice(FILLERS))
        response = await llm_task

    await tts.speak(response)
```

### 4. Groq Setup
```python
from livekit.plugins import groq

llm = groq.LLM(
    model="llama-3.1-70b-versatile",  # Or "llama-3.1-8b-instant" for faster
    api_key="your_groq_api_key",
)
```

### 5. Cartesia with Emotion & Speed (CONFIRMED WORKING)
```python
from livekit.plugins import cartesia

tts = cartesia.TTS(
    model="sonic-2",  # or "sonic-3" for latest
    voice="your_voice_id",
    speed=1.0,  # Range: 0.6 to 1.5 (or -1.0 to 1.0 for granular)
    emotion=["positivity:medium", "curiosity:low"],  # Format: "emotion:level"
)

# Available emotion levels: lowest, low, medium, high, highest
# Primary emotions (best results): neutral, angry, excited, content, sad, scared
# Full list: happy, excited, enthusiastic, curious, content, calm, friendly,
#            angry, frustrated, sad, anxious, confident, sarcastic, and many more
```

### 6. Cartesia SSML Tags (IN TRANSCRIPT)
```python
# Speed control
transcript = '<speed ratio="0.9"/>I want to speak a bit slower here.'

# Emotion control
transcript = '<emotion value="excited"/>Wow, that sounds great!'

# Pause control (via Pipecat helper)
transcript = f"That's great!{CartesiaTTSService.PAUSE_TAG(0.5)}Let me check on that."
```

### 7. Updated System Prompt
```python
AIDEN_CORE_PROMPT = """
You are Aiden, a friendly appointment setter for [IMO Name].

# Voice Style (CRITICAL)
- Sound like a neighbor, NOT a salesperson
- Use contractions: gonna, wanna, lemme, gotta
- Include fillers: umm, yeah, so, oh
- Example: "Oh yeah, so... they've got Mike in your area tomorrow."

# Response Rules (CRITICAL)
- MAX 2 sentences per response
- MAX 25 words per response
- ALWAYS end with a question
- Use commas and periods for natural pauses

# Example Good Responses
- "Umm... let me check here. Morning or afternoon work better?"
- "Oh gotcha, gotcha. And you're still at 123 Oak Street, right?"
- "Yeah so... they've got availability tomorrow. Does 10am work?"
"""
```

---

## Cartesia Feature Summary (VERIFIED)

| Feature | Supported | How to Use |
|---------|-----------|------------|
| Speed Control | ✅ YES | `speed=1.0` param or `<speed ratio="1.5"/>` SSML |
| Emotion Control | ✅ YES | `emotion=["excited:high"]` param or `<emotion value="excited"/>` SSML |
| Pause/Break | ✅ YES | Via Pipecat `PAUSE_TAG()` or punctuation |
| Standard SSML `<break>` | ⚠️ Limited | Use Cartesia-specific tags instead |

**Best emotions for sales voice:** content, friendly, curious, confident, enthusiastic

---

## Done Criteria

You're done when:
- [ ] Total latency consistently <500ms
- [ ] Turn 2+ TTFT is faster than Turn 1
- [ ] Responses sound natural (pass the "friend test")
- [ ] Responses are short (under 25 words)
- [ ] Filler injection working when LLM is slow
- [ ] 10+ test calls with good metrics

---

## Appendix: Cartesia SSML & Emotion Support (Full Reference)

### Overview

Cartesia Sonic-3 provides rich controls for speed, volume, and emotion. You can use these via:
1. **API Parameters** - Pass in `speed` and `emotion` when initializing TTS
2. **SSML Tags** - Embed tags directly in the transcript text
3. **Playground UI** - Test in play.cartesia.ai before coding

**Important:** Sonic-3 interprets these as *guidance* (like directing an actor), not strict commands. The emotion must be consistent with the transcript content to work well.

---

### Speed Control

**API Parameter:**
```python
from livekit.plugins import cartesia

tts = cartesia.TTS(
    model="sonic-2",
    voice="your_voice_id",
    speed=1.0,  # Range: 0.6 (slow) to 1.5 (fast)
)

# Granular control: -1.0 to 1.0
# -1.0 = slowest, 0.0 = default, 1.0 = fastest
```

**SSML Tag (in transcript):**
```python
transcript = '<speed ratio="1.2"/>I want to speak faster here.'
transcript = '<speed ratio="0.8"/>Now I am speaking more slowly.'
```

**Preset Options:** "slowest", "slow", "normal", "fast", "fastest"

---

### Volume Control

**API Parameter:**
```python
tts = cartesia.TTS(
    volume=1.0,  # Range: 0.5 (quiet) to 2.0 (loud)
)
```

**SSML Tag (in transcript):**
```python
transcript = '<volume level="1.5"/>This part is louder!'
transcript = '<volume level="0.7"/>This part is softer.'
```

---

### Emotion Control

**API Parameter:**
```python
tts = cartesia.TTS(
    model="sonic-2",
    voice="your_voice_id",
    emotion=["positivity:medium", "curiosity:low"],
)

# Format: "emotion_name:level"
# Levels: lowest, low, medium, high, highest
```

**SSML Tag (in transcript):**
```python
transcript = '<emotion value="excited"/>Wow, that sounds amazing!'
transcript = '<emotion value="content"/>Oh yeah, that works perfectly for me.'
```

**Important Notes:**
- Emotion controls are ADDITIVE - they add emotion, they cannot remove it
- `anger:low` adds a small amount of anger, it doesn't make the voice less angry
- Emotion must match the transcript content (sad emotion + excited words = bad results)

---

### Primary Emotions (Best Results)

These have the most training data and produce the most reliable results:

| Emotion | Best For |
|---------|----------|
| `neutral` | Default, professional |
| `content` | Satisfied, friendly |
| `excited` | Enthusiasm, good news |
| `angry` | Frustration (use carefully) |
| `sad` | Empathy, bad news |
| `scared` | Urgency, concern |

---

### Full Emotion List

**Positive Emotions:**
- happy, excited, enthusiastic, elated, euphoric, triumphant
- amazed, surprised, flirtatious, joking/comedic
- curious, content, peaceful, serene, calm
- grateful, affectionate, trust, sympathetic
- anticipation, proud, confident

**Negative Emotions:**
- angry, mad, outraged, frustrated, agitated, threatened
- disgusted, contempt, envious, sarcastic, ironic
- sad, dejected, melancholic, disappointed, hurt, guilty
- bored, tired, rejected, nostalgic, wistful
- apologetic, hesitant, insecure, confused, resigned
- anxious, panicked, alarmed, scared

**Neutral/Other:**
- neutral, mysterious, distant, skeptical, contemplative, determined

---

### Best Voices for Emotion

Cartesia recommends using voices tagged 'Emotive' in their Voice Library for best results:

**Top Emotive Voice:**
- **Marian** - ID: `26403c37-80c1-4a1a-8692-540551ca2ae5`

Browse more at: https://play.cartesia.ai (filter by 'Emotive' tag)

---

### Recommended Settings for Insurance Sales (AIDN)

For a friendly, trustworthy appointment setter:

```python
tts = cartesia.TTS(
    model="sonic-2",  # or "sonic-3"
    voice="your_voice_id",  # Use an emotive-tagged voice
    speed=1.0,              # Normal speed (don't rush)
    emotion=[
        "content:medium",   # Satisfied, relaxed tone
        "confident:low",    # Slight confidence without arrogance
    ],
)
```

**Alternative emotion combos to test:**
- `["friendly:medium"]` - Warm and approachable
- `["enthusiastic:low", "content:medium"]` - Upbeat but not pushy
- `["calm:medium", "confident:low"]` - Trustworthy and professional

---

### SSML Tags Reference (Cartesia-Specific)

| Tag | Example | Effect |
|-----|---------|--------|
| Speed | `<speed ratio="1.2"/>text` | Speak 20% faster |
| Volume | `<volume level="1.5"/>text` | Speak 50% louder |
| Emotion | `<emotion value="excited"/>text` | Add excitement |

**Using with Pipecat (if applicable):**
```python
from pipecat.services.cartesia import CartesiaTTSService, CartesiaEmotion

# Pause tag
text = f"Great!{CartesiaTTSService.PAUSE_TAG(0.5)}Let me check on that."

# Emotion tag
text = CartesiaTTSService.EMOTION_TAG(CartesiaEmotion.SARCASM) + "Oh wonderful."

# Speed tag
text = CartesiaTTSService.SPEED_TAG(1.2) + "I'm speaking quickly now."

# Volume tag
text = CartesiaTTSService.VOLUME_TAG(1.5) + "This is louder!"
```

---

### Prosody Tips (No SSML Required)

If you don't want to use SSML tags, you can improve naturalness through text alone:

1. **Punctuation creates pauses:**
   - Period (.) = full pause
   - Comma (,) = short pause
   - Ellipsis (...) = hesitation pause
   - Dash (—) = quick pause

2. **Example:**
   ```
   "Oh yeah... so they've got Mike in your area tomorrow. Morning, or afternoon?"
   ```
   The ellipsis creates a thinking pause, the comma before "or" creates a natural break.

3. **Short sentences = better prosody:**
   ```
   Bad:  "I wanted to let you know that we have availability tomorrow morning or afternoon if either of those times works for you"

   Good: "We've got availability tomorrow. Morning or afternoon work better?"
   ```

---

### Testing Your Settings

1. **Playground first:** Test at https://play.cartesia.ai before coding
2. **Record test calls:** Listen back for naturalness
3. **A/B test:** Try different emotion combos, measure which converts better
4. **Get feedback:** Ask someone who doesn't know it's AI

---

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Emotion not working | Make sure emotion matches transcript content |
| Voice sounds unstable | Reduce number of emotion tags or lower intensity |
| Speed sounds unnatural | Stay between 0.8-1.2, avoid extremes |
| SSML tags being spoken | Check syntax, ensure tags are properly formatted |
| Inconsistent results | Use emotive-tagged voices from Cartesia library |
