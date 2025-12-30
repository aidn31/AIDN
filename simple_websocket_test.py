#!/usr/bin/env python3
# Build version: 2025-12-29-v2
"""
PIECE 2: Twilio WebSocket to LiveKit Audio Bridge
===============================================

PIECE 1 (STILL WORKING): Connect to Twilio's audio stream and count packages.
PIECE 2 (COMPLETE): Convert audio format and publish to LiveKit room for voice agent processing.

NO return audio yet (Piece 4).
"""

import json
import asyncio
import base64
import os
import audioop
from datetime import datetime
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import Response
import uvicorn

# LiveKit imports (new for Piece 2)
try:
    from livekit import api, rtc
    LIVEKIT_AVAILABLE = True
    print("✅ LiveKit imports successful")
except ImportError as e:
    LIVEKIT_AVAILABLE = False
    print(f"⚠️ LiveKit not available: {e}")

app = FastAPI()

# Global counter for audio packages (Piece 1 - unchanged)
audio_package_count = 0

# LiveKit room management (NEW for Piece 2)
active_rooms = {}  # Track active LiveKit rooms per call
livekit_api_client = None

# Initialize LiveKit API client (NEW for Piece 2)
async def init_livekit_async():
    global livekit_api_client
    if not LIVEKIT_AVAILABLE:
        print("⚠️ LiveKit not available - skipping initialization")
        return False

    livekit_url = os.getenv("LIVEKIT_URL")
    livekit_api_key = os.getenv("LIVEKIT_API_KEY")
    livekit_secret = os.getenv("LIVEKIT_SECRET")

    if not all([livekit_url, livekit_api_key, livekit_secret]):
        print("⚠️ Missing LiveKit environment variables")
        print("   Required: LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_SECRET")
        return False

    try:
        livekit_api_client = api.LiveKitAPI(livekit_url, livekit_api_key, livekit_secret)
        print("✅ LiveKit API client initialized")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize LiveKit: {e}")
        return False

# Initialize LiveKit on startup
livekit_ready = False

@app.on_event("startup")
async def startup_event():
    global livekit_ready
    livekit_ready = await init_livekit_async()

@app.post("/twilio-webhook")
async def twilio_webhook(request: Request):
    """
    PIECE 1 (UNCHANGED): Twilio calls this when phone rings
    PIECE 2 (NEW): Also creates LiveKit room for the call
    """
    form_data = await request.form()
    call_sid = form_data.get('CallSid', 'unknown')
    from_number = form_data.get('From', 'unknown')

    print(f"📞 Phone call started from {from_number}, CallSid: {call_sid}")

    # NEW PIECE 2: Create LiveKit room for this call
    if livekit_ready and livekit_api_client:
        try:
            room_name = f"aidn-call-{call_sid}-{int(datetime.now().timestamp())}"
            room_request = api.CreateRoomRequest(name=room_name)
            await livekit_api_client.room.create_room(room_request)

            # Store the room for this call
            active_rooms[call_sid] = room_name
            print(f"🏠 Created LiveKit room: {room_name}")

        except Exception as e:
            print(f"❌ Failed to create LiveKit room: {e}")

    # UNCHANGED: This XML tells Twilio to send audio to our WebSocket
    # NEW: Added call_sid parameter to identify the call
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Start>
        <Stream url="wss://aidn-production.up.railway.app/twilio-stream?call_sid={call_sid}" />
    </Start>
    <Say>Connecting you to our AI agent. Please wait a moment.</Say>
    <Pause length="15"/>
    <Hangup/>
</Response>"""

    return Response(content=twiml_response, media_type="text/xml")


@app.websocket("/twilio-stream")
async def twilio_stream(websocket: WebSocket):
    """
    PIECE 1 (UNCHANGED): Count audio packages from Twilio
    PIECE 2 (NEW): Forward audio to LiveKit room
    """
    global audio_package_count

    print("🚀 WebSocket connection attempt started")
    await websocket.accept()
    print("🔌 Twilio connected to WebSocket!")

    # NEW PIECE 2: Get call_sid and connect to LiveKit room
    query_params = websocket.query_params
    call_sid = query_params.get('call_sid', 'unknown')
    livekit_room = None
    livekit_connection = None
    audio_source = None

    print(f"📞 WebSocket connected for call: {call_sid}")

    # DEBUG: Log call_sid and active_rooms for diagnosis
    print(f"🐛 DEBUG call_sid received: '{call_sid}'")
    print(f"🐛 DEBUG active_rooms keys: {list(active_rooms.keys())}")
    print(f"🐛 DEBUG livekit_ready: {livekit_ready}")
    print(f"🐛 DEBUG call_sid in active_rooms: {call_sid in active_rooms}")

    # NEW PIECE 2: Connect to LiveKit room if available
    if livekit_ready and call_sid in active_rooms:
        try:
            room_name = active_rooms[call_sid]
            livekit_url = os.getenv("LIVEKIT_URL")
            livekit_api_key = os.getenv("LIVEKIT_API_KEY")
            livekit_secret = os.getenv("LIVEKIT_SECRET")

            # Create access token for the room
            token = api.AccessToken(livekit_api_key, livekit_secret)
            token.with_identity(f"twilio-caller-{call_sid}")
            token.with_name("Twilio Caller")
            token.with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True
            ))
            access_token = token.to_jwt()

            # Connect to LiveKit room
            livekit_room = rtc.Room()
            await livekit_room.connect(livekit_url, access_token)
            livekit_connection = livekit_room

            # Create audio source for publishing caller audio
            audio_source = rtc.AudioSource(
                sample_rate=8000,  # Twilio sends 8kHz audio
                num_channels=1     # Mono audio
            )

            # Publish audio track to the room
            track = rtc.LocalAudioTrack.create_audio_track("caller-audio", audio_source)
            options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
            await livekit_room.local_participant.publish_track(track, options)

            print(f"🔗 Connected to LiveKit room: {room_name}")
            print(f"🎵 Audio track published: caller-audio")

        except Exception as e:
            print(f"❌ Failed to connect to LiveKit room: {e}")
            livekit_connection = None

    try:
        while True:
            # Get the next audio package from Twilio (UNCHANGED)
            message = await websocket.receive_text()
            data = json.loads(message)

            # Twilio sends different types of messages (UNCHANGED)
            event_type = data.get('event')

            if event_type == 'start':
                print("🎬 Stream started - audio packages coming soon!")

            elif event_type == 'media':
                # PIECE 1 (UNCHANGED): Count the audio packages
                audio_package_count += 1

                # NEW PIECE 2: Actually send audio to LiveKit
                if livekit_connection and audio_source:
                    try:
                        media_data = data.get('media', {})
                        audio_payload = media_data.get('payload', '')

                        if audio_payload:
                            # Decode the base64 μ-law audio from Twilio
                            ulaw_bytes = base64.b64decode(audio_payload)

                            # Convert μ-law to PCM (16-bit signed integers)
                            pcm_bytes = audioop.ulaw2lin(ulaw_bytes, 2)

                            # Create audio frame with proper format for LiveKit
                            audio_frame = rtc.AudioFrame.create(
                                sample_rate=8000,
                                num_channels=1,
                                samples_per_channel=len(pcm_bytes) // 2  # 2 bytes per sample (16-bit)
                            )

                            # Copy PCM data to the frame
                            audio_frame.data[:len(pcm_bytes)] = pcm_bytes

                            # Push audio frame to LiveKit
                            await audio_source.capture_frame(audio_frame)

                            # Log actual audio publishing (not just "ready")
                            if audio_package_count % 10 == 0:
                                print(f"📦 Received {audio_package_count} audio packages")
                                print(f"🎵 Audio published to LiveKit ({len(pcm_bytes)} PCM bytes)")

                    except Exception as e:
                        print(f"❌ Error publishing audio to LiveKit: {e}")
                else:
                    # PIECE 1 (UNCHANGED): Original logging when no LiveKit
                    if audio_package_count % 10 == 0:
                        print(f"📦 Received {audio_package_count} audio packages")

            elif event_type == 'stop':
                print(f"🛑 Stream ended. Total packages: {audio_package_count}")
                break

    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        # NEW PIECE 2: Cleanup LiveKit connection
        if livekit_connection:
            try:
                await livekit_connection.disconnect()
                print(f"🔌 Disconnected from LiveKit room for call {call_sid}")
            except Exception as e:
                print(f"❌ Error disconnecting from LiveKit: {e}")

        # NEW PIECE 2: Remove from active rooms
        if call_sid in active_rooms:
            del active_rooms[call_sid]

        print("📞 Call ended")


if __name__ == "__main__":
    print("🚀 Starting Piece 2: Twilio WebSocket to LiveKit Bridge")
    print("📍 WebSocket endpoint: /twilio-stream")
    print("📞 Webhook endpoint: /twilio-webhook")
    print()
    print("✅ PIECE 1: WebSocket audio reception (verified working)")
    print("✅ PIECE 2: LiveKit room creation and audio publishing")
    print()
    print("📊 Status:")
    print(f"  LiveKit Available: {LIVEKIT_AVAILABLE}")
    print(f"  LiveKit Configured: {livekit_ready}")
    print()
    if not livekit_ready:
        print("⚠️  LiveKit not configured - audio will only be counted (Piece 1 mode)")
        print("   To enable Piece 2, set: LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_SECRET")
    else:
        print("✅ LiveKit ready - audio will be forwarded to rooms")

    uvicorn.run(app, host="0.0.0.0", port=8000)