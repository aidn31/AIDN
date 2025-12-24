#!/usr/bin/env python3
"""
Simple AIDN API Server (No Voice Agent Dependencies)
===================================================

Lightweight API server with just the webhook endpoint for testing Twilio integration.
"""

import asyncio
import os
import sys
from datetime import datetime
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('/Users/thomasroldan/Documents/GitHub/AIDN')

app = FastAPI(
    title="AIDN Simple API",
    description="Simple API server for Twilio webhook testing",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "AIDN Simple API is running", "webhook": "/twilio-webhook"}


@app.post("/twilio-webhook")
async def twilio_webhook(request: Request):
    """
    Twilio webhook endpoint that provides a voice response.
    This is called by Twilio when a call is answered.
    
    CRITICAL: Twilio sends form-urlencoded data, NOT JSON!
    We must use Request object and return Response with text/xml content type.
    """
    try:
        # Parse Twilio's form-urlencoded data (NOT JSON!)
        form_data = await request.form()
        
        print(f"📞 Twilio webhook called at {datetime.now()}")
        print(f"📥 CallSid: {form_data.get('CallSid')}")
        print(f"📱 To: {form_data.get('To')}")
        print(f"📱 From: {form_data.get('From')}")
        print(f"📊 CallStatus: {form_data.get('CallStatus')}")

        # Return TwiML response with a professional greeting
        twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Hello! Thank you for calling A-I-D-N Insurance Services. My name is Sarah, and I'll be your insurance benefits specialist today.</Say>
    <Pause length="1"/>
    <Say voice="Polly.Joanna">I see that you recently requested information about final expense insurance coverage. Is that correct?</Say>
    <Pause length="3"/>
    <Say voice="Polly.Joanna">Based on your request, I have some excellent coverage options available in your area. Let me review those with you quickly.</Say>
    <Pause length="1"/>
    <Say voice="Polly.Joanna">Our final expense insurance starts as low as fifteen dollars per month and can provide up to fifty thousand dollars in coverage for burial and final expenses.</Say>
    <Pause length="2"/>
    <Say voice="Polly.Joanna">I'd love to schedule a brief appointment to go over these options with you in person. Are you available tomorrow afternoon or would evening work better for you?</Say>
    <Pause length="5"/>
    <Say voice="Polly.Joanna">Thank you for your time today. A local agent will be in touch to schedule your appointment. Have a wonderful day!</Say>
    <Hangup/>
</Response>"""

        print(f"✅ Webhook processed successfully - returning TwiML response")

        # CRITICAL: Return Response with text/xml content type for Twilio
        return Response(content=twiml_response, media_type="text/xml")

    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()

        # Return error TwiML with proper content type
        error_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">We apologize, but we are experiencing technical difficulties. Please try calling back in a few minutes.</Say>
    <Hangup/>
</Response>"""
        return Response(content=error_twiml, media_type="text/xml")


@app.post("/test-call")
async def test_call():
    """Create a test call to verify the system works end-to-end."""
    try:
        from twilio.rest import Client

        # Initialize Twilio client
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        webhook_base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL")

        if not all([account_sid, auth_token, twilio_number, webhook_base_url]):
            return {"error": "Missing Twilio or webhook configuration"}

        # Create the webhook URL
        webhook_url = f"{webhook_base_url}/twilio-webhook"
        target_phone = "+19086197628"

        print(f"📞 Creating test call...")
        print(f"🔗 Webhook URL: {webhook_url}")
        print(f"📱 Calling: {target_phone}")

        twilio_client = Client(account_sid, auth_token)

        # Create the call
        call = twilio_client.calls.create(
            url=webhook_url,
            to=target_phone,
            from_=twilio_number,
            timeout=20,
            record=False,
            method="POST"
        )

        return {
            "success": True,
            "call_sid": call.sid,
            "webhook_url": webhook_url,
            "target_phone": target_phone,
            "status": call.status,
            "message": "Test call initiated successfully!"
        }

    except Exception as e:
        print(f"❌ Test call error: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("🚀 Starting AIDN Simple API Server")
    print("🔌 Health Check: http://localhost:8000/")
    print("📞 Twilio Webhook: /twilio-webhook")
    print("🧪 Test Call Endpoint: /test-call")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )