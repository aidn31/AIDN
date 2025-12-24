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

## 🟢 Recently Resolved Issues

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
- End-to-end call test
- Audio quality verification
- Voice agent response testing

---

### Dashboard "Call" Button Not Wired Up

**Status:** 🟡 PARTIAL - Code exists but not connected
**Discovered:** December 24, 2025
**Impact:** Cannot easily initiate calls from dashboard

**Problem:**
The "Call" button in the leads table exists but has no `onClick` handler. The `/calls/initiate` API endpoint works, but the button doesn't call it.

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
1. **Input Format**: Function defined as `async def twilio_webhook(request: dict)` which tells FastAPI to expect JSON body. Twilio sends `application/x-www-form-urlencoded` data, causing FastAPI to return 422 Unprocessable Entity.
2. **Output Format**: Returning plain string `return twiml_response` sets Content-Type to `text/plain`. Twilio expects `text/xml` for TwiML.

**Solution:**
```python
# BEFORE (broken):
@app.post("/twilio-webhook")
async def twilio_webhook(request: dict):
    return twiml_response

# AFTER (fixed):
from fastapi import Request
from fastapi.responses import Response

@app.post("/twilio-webhook")
async def twilio_webhook(request: Request):
    form_data = await request.form()  # Parse form data, not JSON
    return Response(content=twiml_response, media_type="text/xml")
```

**Files Changed:**
- `simple_api_server.py` - Added imports, fixed function signature, body parsing, and return type
- `api_server.py` - Same fixes applied

**Prevention:**
- Always use `Request` object for Twilio webhooks (they send form data, not JSON)
- Always return `Response` with `media_type="text/xml"` for TwiML
- Test webhooks with `curl -X POST -H "Content-Type: application/x-www-form-urlencoded" -d "key=value"`

---

### [December 24, 2025] - API Server Using Simulated Calls Instead of Real Twilio

**Problem:** The `/calls/initiate` endpoint was returning fake call IDs instead of actually calling through Twilio. Phone never rang.

**Root Cause:** The API server was not using the actual `CallManager` class. It was returning simulated responses for testing.

**Solution:**
```python
# Import and initialize the real CallManager
from src.voice_agent.call_manager import CallManager

call_manager = CallManager(db_manager)

# Use it in the endpoint
call_sid = await call_manager.initiate_call(lead, lead.agent_id)
```

**Files Changed:**
- `api_server.py` - Import CallManager, initialize it, use in `/calls/initiate`

**Prevention:**
- Always use real integration classes, not simulated responses
- Test with actual phone numbers to verify calls go through

---

### [December 24, 2025] - Phone Number Validation Rejecting Valid Numbers

**Problem:** Some test phone numbers were being rejected as invalid.

**Root Cause:** Phone numbers needed to be exactly 10 or 11 digits for US validation. Some test numbers were shorter.

**Solution:** Use proper 10-digit US phone numbers (e.g., `9086197628` not `555-1234`).

**Prevention:**
- Always use real phone number format in test data
- Validate phone numbers before inserting into database

---

### [December 24, 2025] - Tailwind CSS v4 Compatibility Issues

**Problem:** Dashboard styles not applying correctly, build errors with Tailwind.

**Root Cause:** Tailwind v4.x has breaking changes from v3.x. Project had mixed configurations.

**Solution:** Downgraded to stable Tailwind v3.x with proper PostCSS configuration.

**Files Changed:**
- `web-dashboard/tailwind.config.js`
- `web-dashboard/postcss.config.js`
- `web-dashboard/package.json`

**Prevention:**
- Pin Tailwind version in package.json
- Test CSS changes after any dependency updates
