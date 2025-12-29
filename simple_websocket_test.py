#!/usr/bin/env python3
"""
PIECE 1: Simple Twilio WebSocket Connection Test
==============================================

Just connect to Twilio's audio stream and count the packages.
NO LiveKit, NO audio processing, NO sending back audio.
"""

import json
import asyncio
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import Response
import uvicorn

app = FastAPI()

# Global counter for audio packages
audio_package_count = 0

@app.post("/twilio-webhook")
async def twilio_webhook(request: Request):
    """
    WHAT THIS DOES: Twilio calls this when phone rings
    TELLS TWILIO: Connect your audio stream to our WebSocket
    """
    form_data = await request.form()
    print(f"📞 Phone call started from {form_data.get('From')}")

    # This XML tells Twilio to send audio to our WebSocket
    twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Start>
        <Stream url="wss://aidn-production.up.railway.app/twilio-stream" />
    </Start>
    <Say>Connecting you to our test system. Please say hello.</Say>
    <Pause length="10"/>
    <Hangup/>
</Response>"""

    return Response(content=twiml_response, media_type="text/xml")


@app.websocket("/twilio-stream")
async def twilio_stream(websocket: WebSocket):
    """
    WHAT THIS DOES: This is where Twilio sends the audio packages
    PIECE 1 GOAL: Just count the packages and print updates
    """
    global audio_package_count

    await websocket.accept()
    print("🔌 Twilio connected to WebSocket!")

    try:
        while True:
            # Get the next audio package from Twilio
            message = await websocket.receive_text()
            data = json.loads(message)

            # Twilio sends different types of messages
            event_type = data.get('event')

            if event_type == 'start':
                print("🎬 Stream started - audio packages coming soon!")

            elif event_type == 'media':
                # This is an actual audio package!
                audio_package_count += 1
                if audio_package_count % 10 == 0:  # Print every 10th package
                    print(f"📦 Received {audio_package_count} audio packages")

            elif event_type == 'stop':
                print(f"🛑 Stream ended. Total packages: {audio_package_count}")
                break

    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        print("📞 Call ended")


if __name__ == "__main__":
    print("🚀 Starting Simple WebSocket Test")
    print("📍 WebSocket endpoint: /twilio-stream")
    print("📞 Webhook endpoint: /twilio-webhook")
    print()
    print("⚠️  IMPORTANT: Update the webhook URL in the TwiML above!")

    uvicorn.run(app, host="0.0.0.0", port=8000)