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
from .latency_tracker import LatencyTracker, get_tracker, reset_tracker
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
    # Choose LLM: "groq" for speed, "openai" for quality
    # Groq Llama 3.1 70B: ~100-200ms TTFT (vs GPT-4o-mini: ~500-1700ms)
    llm_provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if llm_provider == "groq":
        # Use Groq via OpenAI-compatible API
        # Models: llama-3.3-70b-versatile (smart), llama-3.1-8b-instant (fastest)
        groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        llm = openai.LLM(
            model=groq_model,
            temperature=0.7,
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
        )
        logger.info(f"🚀 Using Groq {groq_model} (low latency)")
    else:
        llm = openai.LLM(
            model="gpt-4o-mini",
            temperature=0.7,
        )
        logger.info("🤖 Using OpenAI GPT-4o-mini")

    session = AgentSession(
        stt=deepgram.STT(
            model="nova-2",
            language="en-US",
            endpointing_ms=25,  # 25ms endpointing (fast turn detection)
        ),
        llm=llm,
        # Cartesia TTS - fastest option with streaming support
        tts=cartesia.TTS(
            model="sonic-2-2025-03-07",
            voice="a5136bf9-224c-4d76-b823-52bd5efcffcc",
            speed=1.0,  # Normal speed, natural pacing
            emotion=["positivity:high", "curiosity:medium"],  # Friendly tone
        ),
        vad=silero.VAD.load(
            min_silence_duration=0.15,  # 150ms silence = end of turn (was 0.2)
            prefix_padding_duration=0.03,  # 30ms padding (was 0.05)
            min_speech_duration=0.05,  # Detect speech quickly
            activation_threshold=0.35,  # More sensitive (was 0.4)
        ),
        # KEY LATENCY SETTINGS - respond faster after user stops speaking
        min_endpointing_delay=0.05,  # 50ms min delay (was 0.1)
        max_endpointing_delay=0.4,  # 400ms max delay (was 0.8)
    )

    # Initialize latency tracker for this call
    reset_tracker()
    tracker = get_tracker(call_id=room_name)

    # ==========================================================================
    # LATENCY TRACKING EVENTS
    # ==========================================================================
    #
    # Pipeline flow:
    #   1. User speaks -> VAD detects end of speech
    #   2. STT processes audio -> transcript ready
    #   3. LLM receives transcript -> generates response (TTFT = first token)
    #   4. TTS receives text -> generates audio (TTFB = first byte)
    #   5. Agent speaks -> audio plays
    #
    # We track each stage to identify bottlenecks.
    # ==========================================================================

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev):
        """Called when STT transcribes user speech."""
        if ev.is_final:
            # Final transcript - start tracking this turn
            tracker.on_speech_end()
            tracker.on_transcript_ready(ev.transcript)
            logger.info(f"USER: {ev.transcript[:60]}...")

    @session.on("speech_created")
    def on_speech_created(ev):
        """Called when agent starts generating a response."""
        if ev.user_initiated:
            # LLM is starting to generate response to user input
            tracker.on_llm_first_token()

    @session.on("agent_state_changed")
    def on_agent_state_changed(ev):
        """Called when agent state changes."""
        if ev.new_state == "speaking":
            # Agent is now speaking - TTS audio is playing
            tracker.on_tts_first_byte()
            tracker.on_agent_speaking()

    @session.on("metrics_collected")
    def on_metrics_collected(ev):
        """Log internal LiveKit metrics for additional insight."""
        logger.debug(f"METRICS: {ev}")

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

    # Log latency summary for this call
    tracker.log_summary()

    # Optionally save metrics to file for analysis
    try:
        metrics_dir = os.path.join(os.path.dirname(__file__), "../../logs/latency")
        os.makedirs(metrics_dir, exist_ok=True)
        metrics_file = os.path.join(metrics_dir, f"{room_name}_latency.json")
        with open(metrics_file, "w") as f:
            f.write(tracker.get_metrics_json())
        logger.info(f"📊 Latency metrics saved to: {metrics_file}")
    except Exception as e:
        logger.warning(f"Could not save latency metrics: {e}")


def main():
    """Main function to run the AIDN voice agent."""

    # Verify required environment variables
    llm_provider = os.getenv("LLM_PROVIDER", "groq").lower()

    required_vars = [
        "DATABASE_URL",
        "DEEPGRAM_API_KEY",
        "CARTESIA_API_KEY",  # For low-latency TTS
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "SIP_OUTBOUND_TRUNK_ID",
    ]

    # Add LLM-specific API key requirement
    if llm_provider == "groq":
        required_vars.append("GROQ_API_KEY")
    else:
        required_vars.append("OPENAI_API_KEY")

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
