# AIDN Issues Resolved

This document tracks bugs and issues that have been fixed.
**Check here before debugging** - the solution may already exist!

---

## Issue Template

### [DATE] - [Issue Title]
**Problem:** [What was happening]
**Root Cause:** [Why it was happening]
**Solution:** [How we fixed it]
**Files Changed:** [List of files]
**Prevention:** [How to avoid this in future]

---

## 🔴 Active Issues (Under Investigation)

### [December 26, 2025] - Twilio Stream TwiML "Application Error"

**Status:** 🔴 ACTIVE - UNDER INVESTIGATION
**Discovered:** December 26, 2025 - 9:00 PM EST
**Worked By:** Claude (AI Assistant) with Tommy Roldan
**Impact:** Cannot use AI voice agent on calls - Twilio Stream not connecting

**Problem:**
When the webhook returns TwiML with `<Start><Stream>`, user hears "We are sorry, an application error has occurred" and the call ends. Simple `<Say>` TwiML works perfectly.

**What We've Verified:**
1. ✅ Simple `<Say>` TwiML works (user hears message)
2. ✅ WebSocket endpoint works (Python client connects successfully)
3. ✅ Railway supports WebSocket (tested with `/ws-test`)
4. ✅ TwiML is valid XML with correct content-type
5. ❌ Twilio never connects to the WebSocket (no connection logs)

**TwiML That Fails:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Please hold while I connect you.</Say>
    <Start>
        <Stream url="wss://aidn-production.up.railway.app/twilio-audio-stream?room=test" track="both_tracks"/>
    </Start>
    <Pause length="120"/>
</Response>
```

**TwiML That Works:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Hello! This is a simple test.</Say>
</Response>
```

**Debugging Steps Taken:**
1. Added `/ws-test` endpoint - WebSocket works ✅
2. Added `/simple-webhook` - Basic TwiML works ✅
3. Tested WebSocket with Python client - Connects successfully ✅
4. Checked Railway HTTP logs - No WebSocket connection from Twilio
5. Tried `<Connect><Stream>` instead of `<Start><Stream>` - Same error

**Next Steps:**
1. [ ] Check Twilio call logs for detailed error message
2. [ ] Test `/stream-test-webhook` (Stream without LiveKit room creation)
3. [ ] Verify Twilio account has Media Streams enabled
4. [ ] Consider deploying voice agent to Railway as second service

---

## 🟢 Recently Resolved Issues

### [December 26, 2025] - LiveKit Async Callback Error

**Status:** 🟢 RESOLVED
**Resolved:** December 26, 2025 - 4:00 PM EST
**Worked By:** Claude (AI Assistant) with Tommy Roldan
**Impact:** Voice agent can now register callbacks without errors

**Problem:**
Railway logs showed: "Failed to connect to LiveKit: Cannot register an async callback with `.on()`. Use `asyncio.create_task` within your synchronous callback instead."

**Root Cause:**
LiveKit SDK's `.on()` method requires synchronous callbacks, but we were passing async methods directly:
```python
# BROKEN:
self.room.on("track_subscribed", self._on_track_subscribed)  # async method
```

**Solution:**
Changed to synchronous wrappers that use `asyncio.create_task`:
```python
# FIXED:
@self.room.on("track_subscribed")
def on_track_subscribed(track, publication, participant):
    asyncio.create_task(self._on_track_subscribed(track, publication, participant))
```

**Files Changed:**
- `src/voice_agent/twilio_audio_bridge.py` - Lines 234-246

**Prevention:**
- Always use sync wrappers with `asyncio.create_task` for LiveKit event handlers
- Check LiveKit SDK documentation for callback requirements

---

### [December 26, 2025] - Voice Agent SDK Compatibility Issues

**Status:** 🟢 RESOLVED
**Resolved:** December 26, 2025 - 4:30 PM EST
**Worked By:** Claude (AI Assistant) with Tommy Roldan
**Impact:** Voice agent worker now starts without errors

**Problem:**
Voice agent worker failed with multiple errors:
1. `AttributeError: module 'livekit.agents' has no attribute 'AutoAccept'`
2. `AttributeError: 'JobContext' object has no attribute 'wait_for_disconnect'`

**Root Cause:**
The code was written for an older version of the `livekit-agents` SDK (v1.3.10 has different API).

**Solution:**
Updated `main.py` to use current SDK patterns:

```python
# BEFORE (broken):
async def request_handler(req: JobRequest) -> agents.AutoAccept:
    return agents.AutoAccept()

# AFTER (fixed):
async def request_handler(req: JobRequest) -> None:
    await req.accept()

# BEFORE (broken):
await ctx.wait_for_disconnect()

# AFTER (fixed):
room = ctx.room
disconnected = asyncio.Event()

@room.on("disconnected")
def on_disconnect():
    disconnected.set()

await disconnected.wait()
```

**Files Changed:**
- `src/voice_agent/main.py` - request_handler and entrypoint functions

**Prevention:**
- Check SDK version and API before using methods
- Test locally before deploying

---

### [December 25, 2025] - Twilio ↔ LiveKit Audio Bridge Implemented

**Status:** 🟢 RESOLVED - TESTING REQUIRED
**Resolved:** December 25, 2025
**Impact:** Voice agent can now speak on phone calls (pending testing)

**Problem:**
The `/twilio-webhook` endpoint was returning static TwiML `<Say>` messages. The AI voice agent (AIDNVoiceAgent) existed but was never connected to actual phone calls.

**Solution Implemented:**

1. **Created TwilioAudioBridge class** (`src/voice_agent/twilio_audio_bridge.py`)
   - Handles WebSocket connection from Twilio
   - Bridges audio to/from LiveKit room
   - Manages bidirectional streaming

2. **Created AudioConverter class** (numpy-based, Python 3.14 compatible)
   - μ-law to PCM16 conversion
   - PCM16 to μ-law encoding
   - Sample rate conversion (8kHz ↔ 16kHz)

3. **Added WebSocket endpoint** `/twilio-audio-stream`
   - Receives Twilio stream events
   - Creates TwilioAudioBridge per call
   - Handles incoming/outgoing audio

4. **Updated webhook** to return `<Stream>` TwiML
   - Creates LiveKit room for each call
   - Returns WebSocket URL for audio streaming

5. **Updated voice agent main.py**
   - Added room request handler
   - Loads lead/agent context from metadata
   - Auto-joins voice agent to room

**Files Changed:**
- `src/voice_agent/twilio_audio_bridge.py` (NEW)
- `src/voice_agent/__init__.py` (lazy imports)
- `src/voice_agent/main.py` (room handler)
- `simple_api_server.py` (WebSocket endpoint)

**Testing Required:**
- End-to-end call test (blocked by Stream TwiML issue)

---

### Dashboard "Call" Button Not Wired Up

**Status:** 🟡 PARTIAL - Code exists but not connected
**Discovered:** December 24, 2025
**Impact:** Cannot easily initiate calls from dashboard

**Problem:**
The "Call" button in the leads table exists but has no `onClick` handler.

**Location:** `web-dashboard/app/leads/page.tsx` line ~225

**Required Solution:**
```typescript
const handleCallLead = async (leadId: string) => {
  const response = await fetch(`http://localhost:8000/calls/initiate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lead_id: leadId })
  });
  // Handle response, show status
};
```

**Estimated Effort:** 2-4 hours

---

## ✅ Resolved Issues

### [December 24, 2025] - Twilio Webhook 422 Error / "Application Error" Message

**Problem:** When Twilio called a user's phone, they heard "We are sorry, another application error has occurred" and the call hung up.

**Root Cause:** TWO bugs in the `/twilio-webhook` endpoint:
1. **Input Format**: Function defined as `async def twilio_webhook(request: dict)` which tells FastAPI to expect JSON body. Twilio sends `application/x-www-form-urlencoded` data.
2. **Output Format**: Returning plain string sets Content-Type to `text/plain`. Twilio expects `text/xml`.

**Solution:**
```python
# AFTER (fixed):
from fastapi import Request
from fastapi.responses import Response

@app.post("/twilio-webhook")
async def twilio_webhook(request: Request):
    form_data = await request.form()
    return Response(content=twiml_response, media_type="text/xml")
```

**Files Changed:**
- `simple_api_server.py`
- `api_server.py`

**Prevention:**
- Always use `Request` object for Twilio webhooks
- Always return `Response` with `media_type="text/xml"` for TwiML

---

### [December 24, 2025] - API Server Using Simulated Calls Instead of Real Twilio

**Problem:** The `/calls/initiate` endpoint was returning fake call IDs instead of actually calling through Twilio.

**Root Cause:** The API server was not using the actual `CallManager` class.

**Solution:** Import and use real CallManager for call initiation.

**Files Changed:**
- `api_server.py`

---

### [December 24, 2025] - Phone Number Validation Rejecting Valid Numbers

**Problem:** Some test phone numbers were being rejected as invalid.

**Root Cause:** Phone numbers needed to be exactly 10 or 11 digits for US validation.

**Solution:** Use proper 10-digit US phone numbers.

---

### [December 24, 2025] - Tailwind CSS v4 Compatibility Issues

**Problem:** Dashboard styles not applying correctly.

**Root Cause:** Tailwind v4.x has breaking changes from v3.x.

**Solution:** Downgraded to stable Tailwind v3.x.

**Files Changed:**
- `web-dashboard/tailwind.config.js`
- `web-dashboard/postcss.config.js`
- `web-dashboard/package.json`
