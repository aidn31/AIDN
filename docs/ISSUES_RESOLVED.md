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

## Resolved Issues

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