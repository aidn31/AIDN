#!/usr/bin/env python3
"""
AIDN API Server with Twilio-LiveKit Audio Bridge
=================================================

API server that connects Twilio phone calls to LiveKit voice agent via WebSocket audio streaming.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, '/Users/thomasroldan/Documents/GitHub/AIDN')

from src.voice_agent.twilio_audio_bridge import (
    TwilioAudioBridge,
    create_livekit_room_for_call,
    generate_stream_twiml,
)

app = FastAPI(
    title="AIDN API Server",
    description="AI-Powered Insurance Distribution Network - Voice Agent API",
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

# Store active audio bridges (room_name -> TwilioAudioBridge)
active_bridges: dict[str, TwilioAudioBridge] = {}


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "AIDN API Server is running",
        "version": "1.0.2",
        "endpoints": {
            "webhook": "/twilio-webhook",
            "audio_stream": "/twilio-audio-stream",
            "test_call": "/test-call",
            "ws_test": "/ws-test",
            "simple_webhook": "/simple-webhook",
            "stream_test": "/stream-test-webhook",
            "minimal_stream": "/minimal-stream-webhook",
            "echo_stream": "/echo-stream-webhook",
            "stream_with_params": "/stream-with-params-webhook",
            "stream_both_tracks": "/stream-both-tracks-webhook"
        },
        "track_tests": {
            "track_inbound": "/track-inbound-webhook",
            "track_outbound": "/track-outbound-webhook",
            "track_default": "/track-default-webhook",
            "track_comparison": "/track-comparison-webhook"
        },
        "phase2_tests": {
            "stream_no_livekit": "/stream-no-livekit-webhook",
            "stream_delayed_livekit": "/stream-delayed-livekit-webhook"
        }
    }


@app.post("/simple-webhook")
async def simple_webhook(request: Request):
    """Ultra-simple webhook for testing - just returns basic TwiML."""
    print("📞 Simple webhook called!")
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Hello! This is a simple test. The webhook is working correctly. Goodbye!</Say>
</Response>"""
    return Response(content=twiml, media_type="text/xml")


@app.post("/stream-test-webhook")
async def stream_test_webhook(request: Request):
    """Test webhook with Stream but NO LiveKit room creation."""
    print("📞 Stream test webhook called!")
    
    # Get the WebSocket URL (no LiveKit room creation)
    webhook_base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL", "https://aidn-production.up.railway.app")
    ws_url = webhook_base_url.replace("https://", "wss://").replace("http://", "ws://")
    stream_url = f"{ws_url}/twilio-audio-stream?room=stream-test&lead_id=test&agent_id=test"
    
    print(f"🔗 Stream URL: {stream_url}")
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Testing the stream connection now.</Say>
    <Start>
        <Stream url="{stream_url}" track="both_tracks"/>
    </Start>
    <Pause length="30"/>
    <Say voice="Polly.Matthew">Stream test complete.</Say>
</Response>"""
    
    print(f"📄 TwiML: {twiml}")
    return Response(content=twiml, media_type="text/xml")


@app.post("/minimal-stream-webhook")
async def minimal_stream_webhook(request: Request):
    """Ultra-minimal Stream test - no query params, just the bare essentials."""
    print("📞 Minimal stream webhook called!")
    
    # Get the simplest possible WebSocket URL
    webhook_base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL", "https://aidn-production.up.railway.app")
    ws_url = webhook_base_url.replace("https://", "wss://").replace("http://", "ws://")
    
    # Just the endpoint, no query params
    stream_url = f"{ws_url}/twilio-audio-stream"
    
    print(f"🔗 Minimal Stream URL: {stream_url}")
    
    # Simplest possible TwiML with Stream - try inbound_track only
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Start>
        <Stream url="{stream_url}"/>
    </Start>
    <Say voice="Polly.Matthew">Stream started. You should hear this after the stream connects.</Say>
    <Pause length="60"/>
</Response>"""
    
    print(f"📄 Minimal TwiML: {twiml}")
    return Response(content=twiml, media_type="text/xml")


@app.post("/echo-stream-webhook")
async def echo_stream_webhook(request: Request):
    """Test with Twilio's own echo server to verify Stream TwiML works at all."""
    print("📞 Echo stream webhook called - using Twilio's echo server!")
    
    # Twilio provides a public echo WebSocket for testing
    # If this works, it confirms our TwiML is correct and issue is our WebSocket
    echo_url = "wss://media-streams-echo.twilio.com/echo"
    
    print(f"🔗 Echo URL: {echo_url}")
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Testing with Twilio echo server. Speak and you should hear yourself.</Say>
    <Start>
        <Stream url="{echo_url}"/>
    </Start>
    <Pause length="30"/>
    <Say voice="Polly.Matthew">Echo test complete.</Say>
</Response>"""
    
    print(f"📄 Echo TwiML: {twiml}")
    return Response(content=twiml, media_type="text/xml")


@app.post("/stream-with-params-webhook")
async def stream_with_params_webhook(request: Request):
    """Test Stream with query params but NO track=both_tracks."""
    print("📞 Stream with params webhook called!")
    
    # Get room info from query params
    room_name = request.query_params.get("room", "test-room")
    lead_id = request.query_params.get("lead_id", "test-lead")
    agent_id = request.query_params.get("agent_id", "test-agent")
    
    webhook_base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL", "https://aidn-production.up.railway.app")
    ws_url = webhook_base_url.replace("https://", "wss://").replace("http://", "ws://")
    
    # Include query params but NO track attribute (uses default inbound_track)
    stream_url = f"{ws_url}/twilio-audio-stream?room={room_name}&lead_id={lead_id}&agent_id={agent_id}"
    
    print(f"🔗 Stream URL (with params, no track attr): {stream_url}")
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Testing stream with query parameters.</Say>
    <Start>
        <Stream url="{stream_url}"/>
    </Start>
    <Pause length="60"/>
    <Say voice="Polly.Matthew">Stream test complete.</Say>
</Response>"""
    
    print(f"📄 TwiML: {twiml}")
    return Response(content=twiml, media_type="text/xml")


@app.post("/stream-both-tracks-webhook")
async def stream_both_tracks_webhook(request: Request):
    """Test Stream with track=both_tracks but NO query params."""
    print("📞 Stream both tracks webhook called!")
    
    webhook_base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL", "https://aidn-production.up.railway.app")
    ws_url = webhook_base_url.replace("https://", "wss://").replace("http://", "ws://")
    
    # No query params but HAS track="both_tracks"
    stream_url = f"{ws_url}/twilio-audio-stream"
    
    print(f"🔗 Stream URL (no params, with both_tracks): {stream_url}")
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Testing stream with both tracks attribute.</Say>
    <Start>
        <Stream url="{stream_url}" track="both_tracks"/>
    </Start>
    <Pause length="60"/>
    <Say voice="Polly.Matthew">Stream test complete.</Say>
</Response>"""
    
    print(f"📄 TwiML: {twiml}")
    return Response(content=twiml, media_type="text/xml")


# === TRACK CONFIGURATION ISOLATION TESTS ===
# These endpoints test each track configuration systematically

@app.post("/track-inbound-webhook")
async def track_inbound_webhook(request: Request):
    """Test Stream with track=inbound (default) - should receive caller audio only."""
    print("📞 Track INBOUND webhook called!")

    webhook_base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL", "https://aidn-production.up.railway.app")
    ws_url = webhook_base_url.replace("https://", "wss://").replace("http://", "ws://")
    stream_url = f"{ws_url}/twilio-audio-stream"

    print(f"🔗 Stream URL (inbound track): {stream_url}")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Testing inbound track - we should receive your voice only.</Say>
    <Start>
        <Stream url="{stream_url}" track="inbound"/>
    </Start>
    <Pause length="30"/>
    <Say voice="Polly.Matthew">Inbound track test complete.</Say>
</Response>"""

    print(f"📄 Inbound Track TwiML: {twiml}")
    return Response(content=twiml, media_type="text/xml")


@app.post("/track-outbound-webhook")
async def track_outbound_webhook(request: Request):
    """Test Stream with track=outbound - should receive Twilio generated audio only."""
    print("📞 Track OUTBOUND webhook called!")

    webhook_base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL", "https://aidn-production.up.railway.app")
    ws_url = webhook_base_url.replace("https://", "wss://").replace("http://", "ws://")
    stream_url = f"{ws_url}/twilio-audio-stream"

    print(f"🔗 Stream URL (outbound track): {stream_url}")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Testing outbound track - we should receive Twilio audio only.</Say>
    <Start>
        <Stream url="{stream_url}" track="outbound"/>
    </Start>
    <Say voice="Polly.Matthew">You should hear this message through the stream.</Say>
    <Pause length="20"/>
    <Say voice="Polly.Matthew">Outbound track test complete.</Say>
</Response>"""

    print(f"📄 Outbound Track TwiML: {twiml}")
    return Response(content=twiml, media_type="text/xml")


@app.post("/track-default-webhook")
async def track_default_webhook(request: Request):
    """Test Stream with no track attribute (defaults to inbound)."""
    print("📞 Track DEFAULT (no attribute) webhook called!")

    webhook_base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL", "https://aidn-production.up.railway.app")
    ws_url = webhook_base_url.replace("https://", "wss://").replace("http://", "ws://")
    stream_url = f"{ws_url}/twilio-audio-stream"

    print(f"🔗 Stream URL (default track): {stream_url}")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Testing default track - no track attribute specified.</Say>
    <Start>
        <Stream url="{stream_url}"/>
    </Start>
    <Pause length="30"/>
    <Say voice="Polly.Matthew">Default track test complete.</Say>
</Response>"""

    print(f"📄 Default Track TwiML: {twiml}")
    return Response(content=twiml, media_type="text/xml")


@app.post("/track-comparison-webhook")
async def track_comparison_webhook(request: Request):
    """Test track=both_tracks with LiveKit bridge to compare with working configuration."""
    print("📞 Track COMPARISON (both_tracks + LiveKit) webhook called!")

    # Get query parameters
    room_name = request.query_params.get("room", f"aidn-test-{datetime.now().strftime('%H%M%S')}")
    lead_id = request.query_params.get("lead_id", str(uuid4()))
    agent_id = request.query_params.get("agent_id", str(uuid4()))

    print(f"🏠 Room: {room_name}")
    print(f"👤 Lead ID: {lead_id}")
    print(f"🤖 Agent ID: {agent_id}")

    # Create LiveKit room for this test
    room_created = await create_livekit_room_for_call(
        room_name=room_name,
        lead_id=lead_id,
        agent_id=agent_id
    )

    if not room_created:
        print("❌ Failed to create LiveKit room for comparison test")
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Room creation failed for comparison test.</Say>
    <Hangup/>
</Response>"""
        return Response(content=twiml, media_type="text/xml")

    # Generate WebSocket URL with room info
    webhook_base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL", "https://aidn-production.up.railway.app")
    ws_url = webhook_base_url.replace("https://", "wss://").replace("http://", "ws://")
    stream_url = f"{ws_url}/twilio-audio-stream?room={room_name}&lead_id={lead_id}&agent_id={agent_id}"

    print(f"🔗 Stream URL (comparison test): {stream_url}")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Testing both tracks with LiveKit bridge enabled.</Say>
    <Start>
        <Stream url="{stream_url}" track="both_tracks"/>
    </Start>
    <Pause length="60"/>
    <Say voice="Polly.Matthew">Comparison test complete.</Say>
</Response>"""

    print(f"📄 Comparison TwiML: {twiml}")
    return Response(content=twiml, media_type="text/xml")


# === PHASE 2: LIVEKIT INTEGRATION SIMPLIFICATION ===

@app.post("/stream-no-livekit-webhook")
async def stream_no_livekit_webhook(request: Request):
    """Test Stream connection WITHOUT any LiveKit integration - pure WebSocket test."""
    print("📞 STREAM NO-LIVEKIT webhook called!")

    # Get query parameters (for logging, but won't use for room creation)
    room_name = request.query_params.get("room", f"aidn-test-{datetime.now().strftime('%H%M%S')}")
    lead_id = request.query_params.get("lead_id", str(uuid4()))
    agent_id = request.query_params.get("agent_id", str(uuid4()))

    print(f"🏠 Room (for WebSocket only): {room_name}")
    print(f"👤 Lead ID: {lead_id}")
    print(f"🤖 Agent ID: {agent_id}")

    # Generate WebSocket URL with room info (but no LiveKit room will be created)
    webhook_base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL", "https://aidn-production.up.railway.app")
    ws_url = webhook_base_url.replace("https://", "wss://").replace("http://", "ws://")
    stream_url = f"{ws_url}/twilio-audio-stream-simple?room={room_name}&lead_id={lead_id}&agent_id={agent_id}"

    print(f"🔗 Stream URL (no LiveKit): {stream_url}")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Testing stream connection without LiveKit integration.</Say>
    <Start>
        <Stream url="{stream_url}" track="both_tracks"/>
    </Start>
    <Pause length="30"/>
    <Say voice="Polly.Matthew">Stream test without LiveKit complete.</Say>
</Response>"""

    print(f"📄 No-LiveKit TwiML: {twiml}")
    return Response(content=twiml, media_type="text/xml")


@app.post("/stream-delayed-livekit-webhook")
async def stream_delayed_livekit_webhook(request: Request):
    """Test Stream connection FIRST, then create LiveKit room after stream establishes."""
    print("📞 STREAM DELAYED-LIVEKIT webhook called!")

    # Get query parameters
    room_name = request.query_params.get("room", f"aidn-test-{datetime.now().strftime('%H%M%S')}")
    lead_id = request.query_params.get("lead_id", str(uuid4()))
    agent_id = request.query_params.get("agent_id", str(uuid4()))

    print(f"🏠 Room: {room_name}")
    print(f"👤 Lead ID: {lead_id}")
    print(f"🤖 Agent ID: {agent_id}")

    # DON'T create LiveKit room yet - let the stream establish first
    # The room creation will happen in the WebSocket handler after "start" event

    # Generate WebSocket URL with room info
    webhook_base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL", "https://aidn-production.up.railway.app")
    ws_url = webhook_base_url.replace("https://", "wss://").replace("http://", "ws://")
    stream_url = f"{ws_url}/twilio-audio-stream-delayed?room={room_name}&lead_id={lead_id}&agent_id={agent_id}"

    print(f"🔗 Stream URL (delayed LiveKit): {stream_url}")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Testing stream first, then LiveKit room creation.</Say>
    <Start>
        <Stream url="{stream_url}" track="both_tracks"/>
    </Start>
    <Pause length="60"/>
    <Say voice="Polly.Matthew">Delayed LiveKit test complete.</Say>
</Response>"""

    print(f"📄 Delayed-LiveKit TwiML: {twiml}")
    return Response(content=twiml, media_type="text/xml")


@app.websocket("/ws-test")
async def websocket_test(websocket: WebSocket):
    """Simple WebSocket test endpoint to verify WS works on Railway."""
    await websocket.accept()
    print("✅ WebSocket test connection accepted!")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"📥 Received: {data}")
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print("🔌 WebSocket test disconnected")


@app.post("/twilio-webhook")
async def twilio_webhook(request: Request):
    """
    Twilio webhook endpoint that connects calls to LiveKit voice agent using DELAYED approach.

    This returns TwiML that:
    1. Returns <Stream> TwiML immediately (no room creation during webhook)
    2. Connects audio via WebSocket to delayed endpoint
    3. LiveKit room created AFTER stream establishes (avoids webhook timeout)
    4. Voice agent joins the room and handles the conversation
    """
    try:
        # Parse Twilio's form-urlencoded data
        form_data = await request.form()
        
        call_sid = form_data.get("CallSid", "unknown")
        to_number = form_data.get("To", "")
        from_number = form_data.get("From", "")
        call_status = form_data.get("CallStatus", "")
        
        print(f"📞 Twilio webhook called at {datetime.now()}")
        print(f"📥 CallSid: {call_sid}")
        print(f"📱 To: {to_number}")
        print(f"📱 From: {from_number}")
        print(f"📊 CallStatus: {call_status}")
        
        # Get lead_id and agent_id from query params (passed from CallManager)
        lead_id = request.query_params.get("lead_id", str(uuid4()))
        agent_id = request.query_params.get("agent_id", str(uuid4()))
        room_name = request.query_params.get("room", f"aidn-call-{call_sid}")
        
        print(f"🔗 Room: {room_name}")
        print(f"👤 Lead ID: {lead_id}")
        print(f"👔 Agent ID: {agent_id}")
        
        # DON'T create LiveKit room during webhook - use delayed approach to avoid timeout
        # Room creation will happen in WebSocket handler after stream establishes
        print("🕐 Using DELAYED LiveKit room creation to avoid webhook timeout")

        # Get WebSocket URL for delayed audio streaming
        webhook_base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL", "https://aidn-production.up.railway.app")

        # Convert https to wss for WebSocket
        if webhook_base_url.startswith("https://"):
            ws_base_url = webhook_base_url.replace("https://", "wss://")
        elif webhook_base_url.startswith("http://"):
            ws_base_url = webhook_base_url.replace("http://", "ws://")
        else:
            ws_base_url = f"wss://{webhook_base_url}"

        # Use delayed WebSocket endpoint - let generate_stream_twiml add query params
        websocket_url = f"{ws_base_url}/twilio-audio-stream-delayed"
        
        print(f"🔊 WebSocket URL: {websocket_url}")
        
        # Enable full AI streaming with LiveKit voice agent
        USE_STREAM_TWIML = True  # ✅ PHASE 2 FIX: Delayed LiveKit integration solves application error
        
        if USE_STREAM_TWIML:
            # Generate TwiML with <Stream> to connect audio
            twiml_response = generate_stream_twiml(
                websocket_url=websocket_url,
                room_name=room_name,
                lead_id=lead_id,
                agent_id=agent_id
            )
            print(f"✅ Returning Stream TwiML - audio will be bridged to LiveKit")
        else:
            # Simple TTS response for testing
            twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">
        Hey there! This is the AI calling from the benefits center. 
        Our AI voice agent system is now working and ready to help you with insurance appointments.
        This is a test call to verify the audio is working correctly.
        Thank you for your time, and have a great day!
    </Say>
</Response>"""
            print(f"✅ Returning simple Say TwiML for testing")
        
        return Response(content=twiml_response, media_type="text/xml")
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        
        # Return error TwiML
        error_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">We apologize, but we are experiencing technical difficulties.</Say>
    <Hangup/>
</Response>"""
        return Response(content=error_twiml, media_type="text/xml")


@app.websocket("/twilio-audio-stream-simple")
async def twilio_audio_stream_simple(websocket: WebSocket):
    """
    SIMPLIFIED WebSocket endpoint - NO LiveKit integration, just log audio events.

    This tests pure Twilio Stream functionality without any LiveKit complexity.
    """
    await websocket.accept()
    print("✅ Simple audio stream WebSocket connected!")

    try:
        while True:
            # Receive message from Twilio
            message = await websocket.receive_text()
            data = json.loads(message)
            event = data.get("event", "unknown")

            if event == "connected":
                print("🔌 Twilio WebSocket connected")

            elif event == "start":
                start_info = data.get("start", {})
                stream_sid = start_info.get("streamSid")
                call_sid = start_info.get("callSid")
                print(f"🎬 Stream started: {stream_sid}, call: {call_sid}")

            elif event == "media":
                media = data.get("media", {})
                sequence = media.get("sequenceNumber", 0)
                if sequence % 100 == 0:  # Log every 100th media packet
                    print(f"🎵 Media packet #{sequence}")

            elif event == "stop":
                print("🛑 Stream stopped")
                break

            elif event == "mark":
                mark_name = data.get("mark", {}).get("name", "")
                print(f"📍 Mark: {mark_name}")

            else:
                print(f"❓ Unknown event: {event}")

    except WebSocketDisconnect:
        print("🔌 Simple audio stream disconnected")
    except Exception as e:
        print(f"❌ Simple audio stream error: {e}")
        import traceback
        traceback.print_exc()


@app.websocket("/twilio-audio-stream-delayed")
async def twilio_audio_stream_delayed(websocket: WebSocket):
    """
    WebSocket endpoint that creates LiveKit room AFTER stream starts (not during webhook).

    This tests delayed LiveKit integration to avoid webhook timeouts.
    """
    await websocket.accept()
    print("✅ Delayed LiveKit audio stream WebSocket connected!")

    # Extract room info from query params
    query_params = dict(websocket.query_params)
    room_name = query_params.get("room", "unknown")
    lead_id = query_params.get("lead_id", "unknown")
    agent_id = query_params.get("agent_id", "unknown")

    print(f"🏠 Room for delayed creation: {room_name}")
    print(f"👤 Lead: {lead_id}")
    print(f"🤖 Agent: {agent_id}")

    bridge = None

    try:
        while True:
            # Receive message from Twilio
            message = await websocket.receive_text()
            data = json.loads(message)
            event = data.get("event", "unknown")

            if event == "connected":
                print("🔌 Delayed LiveKit WebSocket connected")

            elif event == "start":
                start_info = data.get("start", {})
                stream_sid = start_info.get("streamSid")
                call_sid = start_info.get("callSid")
                print(f"🎬 Stream started: {stream_sid}, call: {call_sid}")

                # NOW create the LiveKit room and bridge (after stream is established)
                print("⏰ Creating LiveKit room after stream start...")

                room_created = await create_livekit_room_for_call(
                    room_name=room_name,
                    lead_id=lead_id,
                    agent_id=agent_id
                )

                if room_created:
                    print("✅ LiveKit room created successfully")

                    # Create the bridge
                    bridge = TwilioAudioBridge(
                        room_name=room_name,
                        lead_id=lead_id,
                        agent_id=agent_id
                    )

                    # Connect to LiveKit
                    if await bridge.connect_to_livekit():
                        print("✅ TwilioAudioBridge connected to LiveKit")
                        active_bridges[room_name] = bridge
                    else:
                        print("❌ Failed to connect TwilioAudioBridge to LiveKit")
                        bridge = None
                else:
                    print("❌ Failed to create LiveKit room")

            elif event == "media" and bridge:
                # Process media through bridge if it exists
                response = await bridge.process_twilio_message(message)
                if response:
                    await websocket.send_text(response)

            elif event == "stop":
                print("🛑 Delayed LiveKit stream stopped")
                if bridge:
                    await bridge.disconnect()
                    if room_name in active_bridges:
                        del active_bridges[room_name]
                break

            elif event == "mark":
                mark_name = data.get("mark", {}).get("name", "")
                print(f"📍 Mark: {mark_name}")

            else:
                print(f"❓ Unknown event: {event}")

    except WebSocketDisconnect:
        print("🔌 Delayed LiveKit stream disconnected")
        if bridge:
            await bridge.disconnect()
            if room_name in active_bridges:
                del active_bridges[room_name]
    except Exception as e:
        print(f"❌ Delayed LiveKit stream error: {e}")
        import traceback
        traceback.print_exc()
        if bridge:
            await bridge.disconnect()
            if room_name in active_bridges:
                del active_bridges[room_name]


@app.websocket("/twilio-audio-stream")
async def twilio_audio_stream(websocket: WebSocket):
    """
    WebSocket endpoint for Twilio audio streaming.

    This is where the magic happens:
    1. Twilio connects via WebSocket and streams audio
    2. We bridge the audio to/from a LiveKit room
    3. The AIDN voice agent in the room handles the conversation
    """
    await websocket.accept()
    
    # Get parameters from query string
    room_name = websocket.query_params.get("room", f"aidn-call-{uuid4()}")
    lead_id = websocket.query_params.get("lead_id", str(uuid4()))
    agent_id = websocket.query_params.get("agent_id", str(uuid4()))
    
    print(f"🎤 WebSocket connected for room: {room_name}")
    print(f"👤 Lead: {lead_id}, Agent: {agent_id}")
    
    # Create audio bridge
    bridge = TwilioAudioBridge(
        room_name=room_name,
        lead_id=lead_id,
        agent_id=agent_id
    )
    
    # Store bridge for potential external access
    active_bridges[room_name] = bridge
    
    try:
        # Create tasks for bidirectional audio
        receive_task = asyncio.create_task(
            _handle_incoming_audio(websocket, bridge)
        )
        send_task = asyncio.create_task(
            _handle_outgoing_audio(websocket, bridge)
        )
        
        # Wait for either task to complete (one will finish when connection closes)
        done, pending = await asyncio.wait(
            [receive_task, send_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
                
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected for room: {room_name}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        await bridge.disconnect()
        if room_name in active_bridges:
            del active_bridges[room_name]
        print(f"🧹 Cleaned up bridge for room: {room_name}")


async def _handle_incoming_audio(websocket: WebSocket, bridge: TwilioAudioBridge):
    """Handle incoming audio from Twilio."""
    try:
        while True:
            # Receive message from Twilio
            message = await websocket.receive_text()
            
            # Process the message (audio, start, stop, etc.)
            response = await bridge.process_twilio_message(message)
            
            # Send response if any
            if response:
                await websocket.send_text(response)
                
    except WebSocketDisconnect:
        raise
    except Exception as e:
        print(f"Error in incoming audio handler: {e}")
        raise


async def _handle_outgoing_audio(websocket: WebSocket, bridge: TwilioAudioBridge):
    """Handle outgoing audio to Twilio (from voice agent)."""
    try:
        # Keep running as long as we haven't explicitly disconnected
        # The bridge connects to LiveKit asynchronously after receiving "start" event
        # So we need to wait patiently for it to become ready
        max_wait_for_connect = 30  # seconds
        waited = 0
        
        # Wait for bridge to connect (receives "start" event from Twilio first)
        while not bridge.is_connected and waited < max_wait_for_connect:
            await asyncio.sleep(0.1)
            waited += 0.1
        
        if not bridge.is_connected:
            print("⚠️ Bridge never connected to LiveKit, exiting outgoing handler")
            return
        
        print("✅ Bridge connected, starting outgoing audio loop")
        
        # Now stream audio as long as connected
        while bridge.is_connected:
            # Get audio to send to Twilio
            message = await bridge.get_outgoing_audio()
            
            if message:
                await websocket.send_text(message)
            else:
                # Small delay if no audio ready
                await asyncio.sleep(0.01)
        
        # Drain any remaining audio after disconnect
        while not bridge.outgoing_audio_queue.empty():
            message = await bridge.get_outgoing_audio()
            if message:
                await websocket.send_text(message)
                
    except WebSocketDisconnect:
        raise
    except Exception as e:
        print(f"Error in outgoing audio handler: {e}")
        raise


@app.post("/test-call")
async def test_call(request: Request):
    """Create a test call to verify the audio bridge works end-to-end.
    
    Accepts JSON body with optional lead info and webhook:
    {
        "phone": "+19086197628",
        "webhook": "twilio-webhook",  // Options: twilio-webhook, simple-webhook, echo-stream-webhook, minimal-stream-webhook
        "first_name": "Tommy",
        "last_name": "Roldan",
        "address": "123 Main Street",
        "city": "Tampa",
        "state": "FL",
        "zip_code": "33544",
        "county": "Pasco"
    }
    """
    try:
        from twilio.rest import Client
        
        # Try to get lead info from request body
        lead_info = {}
        try:
            lead_info = await request.json()
        except:
            pass  # No body or invalid JSON, use defaults
        
        # Initialize Twilio client
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        webhook_base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL")
        
        if not all([account_sid, auth_token, twilio_number, webhook_base_url]):
            return {"error": "Missing Twilio or webhook configuration"}
        
        # Extract lead details (with defaults for testing)
        target_phone = lead_info.get("phone", "+19086197628")
        webhook_type = lead_info.get("webhook", "twilio-webhook")  # Default to main webhook
        first_name = lead_info.get("first_name", "Test")
        last_name = lead_info.get("last_name", "User")
        address = lead_info.get("address", "123 Test Street")
        city = lead_info.get("city", "Tampa")
        state = lead_info.get("state", "FL")
        zip_code = lead_info.get("zip_code", "33544")
        county = lead_info.get("county", "Pasco")
        
        # Map webhook types to endpoints
        webhook_endpoints = {
            "twilio-webhook": "/twilio-webhook",
            "simple-webhook": "/simple-webhook",
            "echo-stream-webhook": "/echo-stream-webhook",
            "minimal-stream-webhook": "/minimal-stream-webhook",
            "stream-test-webhook": "/stream-test-webhook",
            "stream-with-params-webhook": "/stream-with-params-webhook",
            "stream-both-tracks-webhook": "/stream-both-tracks-webhook",
            # Track configuration tests
            "track-inbound-webhook": "/track-inbound-webhook",
            "track-outbound-webhook": "/track-outbound-webhook",
            "track-default-webhook": "/track-default-webhook",
            "track-comparison-webhook": "/track-comparison-webhook",
            # Phase 2: LiveKit integration tests
            "stream-no-livekit-webhook": "/stream-no-livekit-webhook",
            "stream-delayed-livekit-webhook": "/stream-delayed-livekit-webhook"
        }
        webhook_path = webhook_endpoints.get(webhook_type, "/twilio-webhook")
        
        # Generate unique identifiers for this call
        lead_id = str(uuid4())
        agent_id = str(uuid4())
        room_name = f"aidn-test-{datetime.now().strftime('%H%M%S')}"
        
        # Create the webhook URL with parameters including lead info
        import urllib.parse
        lead_params = urllib.parse.urlencode({
            "room": room_name,
            "lead_id": lead_id,
            "agent_id": agent_id,
            "first_name": first_name,
            "last_name": last_name,
            "address": address,
            "city": city,
            "state": state,
            "county": county
        })
        webhook_url = f"{webhook_base_url}{webhook_path}?{lead_params}"
        
        print(f"📞 Creating test call...")
        print(f"📌 Webhook: {webhook_path}")
        print(f"👤 Lead: {first_name} {last_name}")
        print(f"📍 Address: {address}, {city}, {state} {zip_code}")
        print(f"🏠 County: {county}")
        print(f"📱 Calling: {target_phone}")
        print(f"🔗 Room: {room_name}")
        
        twilio_client = Client(account_sid, auth_token)
        
        # Create the call
        call = twilio_client.calls.create(
            url=webhook_url,
            to=target_phone,
            from_=twilio_number,
            timeout=30,
            record=False,
            method="POST"
        )
        
        return {
            "success": True,
            "call_sid": call.sid,
            "room_name": room_name,
            "lead_id": lead_id,
            "agent_id": agent_id,
            "webhook_type": webhook_type,
            "webhook_path": webhook_path,
            "lead_info": {
                "first_name": first_name,
                "last_name": last_name,
                "address": address,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "county": county,
                "phone": target_phone
            },
            "webhook_url": webhook_url,
            "status": call.status,
            "message": f"Test call initiated for {first_name} {last_name} using {webhook_type}!"
        }
        
    except Exception as e:
        print(f"❌ Test call error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.get("/active-calls")
async def get_active_calls():
    """Get list of active audio bridges/calls."""
    return {
        "active_calls": len(active_bridges),
        "rooms": list(active_bridges.keys())
    }


if __name__ == "__main__":
    print("🚀 Starting AIDN API Server with Audio Bridge")
    print("🔌 Health Check: http://localhost:8000/")
    print("📞 Twilio Webhook: /twilio-webhook")
    print("🎤 Audio Stream: /twilio-audio-stream (WebSocket)")
    print("🧪 Test Call: /test-call")
    
    uvicorn.run(
        "simple_api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
