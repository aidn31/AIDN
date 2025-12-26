#!/usr/bin/env python3
"""
AIDN API Server with Twilio-LiveKit Audio Bridge
=================================================

API server that connects Twilio phone calls to LiveKit voice agent via WebSocket audio streaming.
"""

import asyncio
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
    generate_stream_twiml
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
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/twilio-webhook",
            "audio_stream": "/twilio-audio-stream",
            "test_call": "/test-call"
        }
    }


@app.post("/twilio-webhook")
async def twilio_webhook(request: Request):
    """
    Twilio webhook endpoint that connects calls to LiveKit voice agent.
    
    This returns TwiML that:
    1. Creates a LiveKit room for the call
    2. Returns <Stream> TwiML to connect audio via WebSocket
    3. Voice agent joins the room and handles the conversation
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
        
        # Create LiveKit room for this call
        room_created = await create_livekit_room_for_call(room_name, lead_id, agent_id)
        
        if not room_created:
            print("⚠️ Failed to create LiveKit room, falling back to static response")
            # Fallback to static TwiML if room creation fails
            twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">We're experiencing technical difficulties. Please try again later.</Say>
    <Hangup/>
</Response>"""
            return Response(content=twiml_response, media_type="text/xml")
        
        # Get WebSocket URL for audio streaming
        webhook_base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL", "")
        
        # Convert https to wss for WebSocket
        if webhook_base_url.startswith("https://"):
            ws_base_url = webhook_base_url.replace("https://", "wss://")
        elif webhook_base_url.startswith("http://"):
            ws_base_url = webhook_base_url.replace("http://", "ws://")
        else:
            ws_base_url = f"wss://{webhook_base_url}"
        
        websocket_url = f"{ws_base_url}/twilio-audio-stream"
        
        print(f"🔊 WebSocket URL: {websocket_url}")
        
        # Enable full AI streaming with LiveKit voice agent
        USE_STREAM_TWIML = True  # Enable for full AI conversation
        
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
    
    Optionally accepts JSON body with lead info:
    {
        "phone": "+19086197628",
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
        first_name = lead_info.get("first_name", "Test")
        last_name = lead_info.get("last_name", "User")
        address = lead_info.get("address", "123 Test Street")
        city = lead_info.get("city", "Tampa")
        state = lead_info.get("state", "FL")
        zip_code = lead_info.get("zip_code", "33544")
        county = lead_info.get("county", "Pasco")
        
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
        webhook_url = f"{webhook_base_url}/twilio-webhook?{lead_params}"
        
        print(f"📞 Creating test call...")
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
            "message": f"Test call initiated for {first_name} {last_name}!"
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
