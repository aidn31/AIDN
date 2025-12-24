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

## 🔴 Known Issues (Not Yet Resolved)

### Twilio ↔ LiveKit Audio Bridge Not Implemented

**Status:** 🔴 CRITICAL - NOT STARTED
**Discovered:** December 24, 2025
**Impact:** Voice agent cannot speak on phone calls

**Problem:**
The `/twilio-webhook` endpoint returns static TwiML `<Say>` messages. The AI voice agent (AIDNVoiceAgent) exists but is never connected to actual phone calls. Users hear a pre-recorded message instead of having a conversation with the AI.

**Current Behavior:**
```
Twilio initiates call → Phone rings → Webhook returns <Say> TwiML
→ User hears static message → Call hangs up
→ AI voice agent never participates
```

**Required Behavior:**
```
Twilio initiates call → Phone rings → Webhook returns <Stream> TwiML
→ Audio streams via WebSocket to server → Server bridges to LiveKit room
→ AIDNVoiceAgent joins room → Real-time AI conversation
→ AI handles objections, books appointments
```

**Blocked Features:**
- Real-time AI conversation on phone calls
- Objection handling during live calls
- Appointment booking during calls
- Casual persona speaking to customers

**Required Solution:**
1. Implement WebSocket handler for Twilio `<Stream>`
2. Bridge audio bidirectionally to/from LiveKit room
3. Auto-join AIDNVoiceAgent when call connects
4. Pass lead context for personalization

**Estimated Effort:** 2-3 days

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
