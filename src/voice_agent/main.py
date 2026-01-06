"""
AIDN Voice Agent Main Entry Point
=================================

LiveKit Agents entry point for AIDN outbound voice agent.
Uses LiveKit SIP + Telnyx for phone calls (no custom bridge needed).
"""

import asyncio
import json
import logging
import os
import time
from uuid import UUID

from dotenv import load_dotenv
from livekit import api
from livekit.agents import AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import deepgram, openai, silero, cartesia

from .aidn_agent_v2 import AIDNVoiceAgent
from ..shared.database import DatabaseManager, LeadRepository, AgentRepository

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("aidn")

# Global database manager
db_manager = None


async def get_db_manager() -> DatabaseManager:
    """Get or create the database manager."""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
        await db_manager.connect()
    return db_manager


async def entrypoint(ctx: JobContext):
    """
    AIDN Outbound Call Entrypoint

    Flow:
    1. Receive dispatch with phone_number and lead_id in metadata
    2. Connect to room
    3. Load lead info from database
    4. Create SIP participant (dials the lead via Telnyx)
    5. Wait for call to be answered
    6. Greet lead by name
    7. Conversation happens via agent
    """
    await ctx.connect()

    room_name = ctx.room.name
    logger.info(f"🎤 AIDN Voice Agent starting in room: {room_name}")

    # Extract call info from dispatch metadata
    metadata = json.loads(ctx.job.metadata) if ctx.job.metadata else {}
    phone_number = metadata.get("phone_number")
    lead_id = metadata.get("lead_id")
    agent_id = metadata.get("agent_id")

    if not phone_number:
        logger.error("❌ No phone_number in job metadata. Cannot place call.")
        return

    logger.info(f"📞 Preparing outbound call to {phone_number}")

    # Load lead and agent info from database
    db = await get_db_manager()
    lead = None
    agent_info = None

    if lead_id:
        try:
            lead_repo = LeadRepository(db)
            lead = await lead_repo.get_lead_by_id(UUID(lead_id))
            if lead:
                logger.info(f"👤 Loaded lead: {lead.first_name} {lead.last_name} from {lead.county}, {lead.state}")
        except Exception as e:
            logger.error(f"Error loading lead: {e}")

    if agent_id:
        try:
            agent_repo = AgentRepository(db)
            agent_profile = await agent_repo.get_agent_by_id(UUID(agent_id))
            if agent_profile:
                agent_info = {
                    "agent_name": agent_profile.agent_name,
                    "physical_description": agent_profile.physical_description,
                    "car_description": agent_profile.car_description,
                    "phone": agent_profile.phone,
                    "email": agent_profile.email
                }
                logger.info(f"👔 Loaded agent: {agent_profile.agent_name}")
        except Exception as e:
            logger.error(f"Error loading agent: {e}")

    # Create the AIDN voice agent
    agent = AIDNVoiceAgent(db)

    # Set call context if we have lead info
    if lead:
        await agent.set_call_context(lead, UUID(agent_id) if agent_id else None, agent_info)
        logger.info(f"✅ Call context set for {lead.first_name}")

    # Create the agent session with ULTRA LOW LATENCY settings
    #
    # TTS Options (fastest to slowest):
    #   1. Cartesia - ~100-150ms latency, streaming, high quality
    #   2. Deepgram - ~150-200ms latency
    #   3. OpenAI TTS - ~300-500ms latency
    #
    # VAD Settings for natural conversation:
    #   - min_silence_duration: How long silence before end-of-turn (lower = faster, but may cut off)
    #   - speech_pad: Padding around speech detection
    #
    # Endpointing delays (KEY FOR LATENCY):
    #   - min_endpointing_delay: How long after speech stops before responding (default 0.5s)
    #   - max_endpointing_delay: Maximum wait before forcing response (default 3.0s)
    #
    session = AgentSession(
        stt=deepgram.STT(
            model="nova-2",
            language="en-US",
            endpointing_ms=25,  # 25ms endpointing (fast turn detection)
        ),
        llm=openai.LLM(
            model="gpt-4o-mini",  # Fast model, good for conversation
            temperature=0.7,
        ),
        # Cartesia TTS - fastest option with streaming support
        tts=cartesia.TTS(
            model="sonic-2-2025-03-07",
            voice="a5136bf9-224c-4d76-b823-52bd5efcffcc",
            speed=1.0,  # Normal speed, natural pacing
            emotion=["positivity:high", "curiosity:medium"],  # Friendly tone
        ),
        vad=silero.VAD.load(
            min_silence_duration=0.2,  # 200ms silence = end of turn (was 0.3)
            prefix_padding_duration=0.05,  # 50ms padding (was 0.1)
            min_speech_duration=0.05,  # Detect speech quickly
            activation_threshold=0.4,  # Slightly more sensitive (was 0.5)
        ),
        # KEY LATENCY SETTINGS - respond faster after user stops speaking
        min_endpointing_delay=0.1,  # 100ms min delay (default 0.5s)
        max_endpointing_delay=0.8,  # 800ms max delay (default 3.0s)
    )

    # Add timing metrics for debugging latency
    speech_end_time = None

    @session.on("user_speech_committed")
    def on_user_speech_committed(msg):
        nonlocal speech_end_time
        speech_end_time = time.time()
        logger.info(f"⏱️ USER_SPEECH_END: {msg.transcript[:50]}...")

    @session.on("agent_started_speaking")
    def on_agent_started():
        if speech_end_time:
            latency = (time.time() - speech_end_time) * 1000
            logger.info(f"⏱️ RESPONSE_LATENCY: {latency:.0f}ms (speech_end -> agent_start)")

    # Start the session BEFORE dialing
    await session.start(room=ctx.room, agent=agent)
    logger.info("✅ Agent session started")

    # Dial the lead via SIP (Telnyx)
    sip_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")

    if not sip_trunk_id:
        logger.error("❌ SIP_OUTBOUND_TRUNK_ID not set. Cannot place call.")
        return

    try:
        logger.info(f"📱 Dialing {phone_number} via SIP trunk...")

        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=sip_trunk_id,
                sip_call_to=phone_number,
                room_name=ctx.room.name,
                participant_identity=f"lead-{phone_number}",
                wait_until_answered=True,
            )
        )

        logger.info("✅ Call answered!")

        # Build personalized Aiden greeting
        if lead:
            county = lead.county or "your area"
            address = lead.address or "your address"
            greeting = (
                f"Hey {lead.first_name}! This is Aiden, umm, I'm calling from the "
                f"benefits center here in {county}... so we've got this package of "
                f"info ready to go out to ya about the final expense programs, and "
                f"I was just making sure you still live at {address}. Is that right?"
            )
        else:
            greeting = (
                "Hey there! This is Aiden calling from the benefits center. "
                "We've got some info ready to go out to ya, do you have a quick second?"
            )

        # Greet the lead AFTER call is answered
        await session.say(greeting)
        logger.info("🗣️ Greeting delivered")

    except Exception as e:
        logger.error(f"❌ Failed to connect call: {e}")
        return

    # Keep session alive until call ends
    logger.info("🎙️ Voice agent is now active on the call")

    disconnected = asyncio.Event()

    @ctx.room.on("disconnected")
    def on_disconnect():
        disconnected.set()

    @ctx.room.on("participant_disconnected")
    def on_participant_left(participant):
        logger.info(f"👋 Participant left: {participant.identity}")
        if participant.identity.startswith("lead-"):
            logger.info("📴 Lead hung up - ending call")
            disconnected.set()

    await disconnected.wait()
    logger.info(f"📴 Call ended in room: {room_name}")


def main():
    """Main function to run the AIDN voice agent."""

    # Verify required environment variables
    required_vars = [
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "DEEPGRAM_API_KEY",
        "CARTESIA_API_KEY",  # For low-latency TTS
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "SIP_OUTBOUND_TRUNK_ID",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these in your .env file")
        return

    logger.info("🚀 Starting AIDN Voice Agent (LiveKit SIP + Telnyx)")
    logger.info(f"📡 LiveKit URL: {os.getenv('LIVEKIT_URL')}")

    # Configure worker options
    worker_options = WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="aidn-outbound",
    )

    # Run the agent
    cli.run_app(worker_options)


if __name__ == "__main__":
    main()
