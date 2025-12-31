"""
AIDN Voice Agent Main Entry Point
=================================

LiveKit Agents entry point for AIDN voice agent.
Handles incoming call rooms and bridges with Twilio audio.
"""

import asyncio
import json
import logging
import os
from uuid import UUID

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import WorkerOptions, cli, JobContext, JobRequest

from .aidn_agent import AIDNVoiceAgent, create_aidn_session
from ..shared.database import DatabaseManager, LeadRepository, AgentRepository

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global database manager
db_manager = None


async def get_db_manager() -> DatabaseManager:
    """Get or create the database manager."""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
        await db_manager.connect()
    return db_manager


async def prewarm(proc: agents.JobProcess):
    """Prewarm function to initialize global resources."""
    logger.info("🔥 Prewarming AIDN voice agent...")
    
    # Initialize database connection
    await get_db_manager()
    
    logger.info("✅ AIDN voice agent prewarm complete")


async def request_handler(req: JobRequest) -> None:
    """
    Handle incoming job requests.
    
    This decides whether to accept incoming room connections.
    We accept all rooms that start with 'aidn-' as these are our call rooms.
    """
    room_name = req.room.name
    
    if room_name.startswith("aidn-"):
        logger.info(f"📞 Accepting call room: {room_name}")
        await req.accept()
    else:
        logger.info(f"🚫 Rejecting non-AIDN room: {room_name}")
        await req.reject()  # Reject non-AIDN rooms


async def entrypoint(ctx: JobContext):
    """
    Main entry point for the AIDN voice agent.
    
    Called when we join a LiveKit room (after Twilio audio bridge connects).
    """
    db = await get_db_manager()
    
    room_name = ctx.room.name
    logger.info(f"🎤 AIDN Voice Agent joining room: {room_name}")
    
    # Wait for the room to be ready
    await ctx.connect()
    
    # Extract lead and agent info from room metadata or participant attributes
    lead = None
    agent_info = None
    lead_id = None
    agent_id = None

    try:
        # Method 1: Try room-level metadata first
        room_metadata = ctx.room.metadata
        if room_metadata:
            metadata = json.loads(room_metadata)
            lead_id = metadata.get("lead_id")
            agent_id = metadata.get("agent_id")
            logger.info(f"📋 Found room metadata - Lead: {lead_id}, Agent: {agent_id}")

        # Method 2: If no room metadata, check for bridge participant with metadata
        if not lead_id or not agent_id:
            logger.info("🔍 No room metadata found, checking participant metadata...")
            for participant in ctx.room.remote_participants.values():
                if participant.metadata:
                    try:
                        participant_meta = json.loads(participant.metadata)
                        if participant_meta.get("type") == "twilio_bridge":
                            lead_id = participant_meta.get("lead_id", lead_id)
                            agent_id = participant_meta.get("agent_id", agent_id)
                            logger.info(f"📋 Found participant metadata - Lead: {lead_id}, Agent: {agent_id}")
                            break
                    except json.JSONDecodeError:
                        continue

        # Method 3: Extract from room name as fallback (if room name contains IDs)
        if not lead_id or not agent_id:
            logger.warning("❌ No metadata found in room or participants")
            logger.info(f"🏠 Room name: {room_name}")
            # Could extract from room name if it contains the IDs

    except json.JSONDecodeError:
        logger.warning("Could not parse room metadata")
    except Exception as e:
        logger.error(f"Error reading room metadata: {e}")

    # Log final extraction results
    if lead_id and agent_id:
        logger.info(f"✅ Successfully extracted - Lead: {lead_id}, Agent: {agent_id}")
    else:
        logger.warning(f"⚠️ Incomplete metadata extraction - Lead: {lead_id}, Agent: {agent_id}")
    
    # Load lead from database
    if lead_id:
        try:
            lead_repo = LeadRepository(db)
            lead = await lead_repo.get_lead_by_id(UUID(lead_id))
            if lead:
                logger.info(f"👤 Loaded lead: {lead.first_name} {lead.last_name} from {lead.county}, {lead.state}")
        except Exception as e:
            logger.error(f"Error loading lead: {e}")
    
    # Load agent info from database
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
    
    # Create the AIDN voice agent session
    session = await create_aidn_session(db)
    
    # Create the AIDN agent
    agent = AIDNVoiceAgent(db)
    
    # Set call context if we have lead info
    if lead:
        await agent.set_call_context(lead, UUID(agent_id) if agent_id else None, agent_info)
        logger.info(f"✅ Call context set for {lead.first_name}")
    else:
        logger.warning("⚠️ No lead found - using generic greeting")
    
    # Wait for audio tracks from the Twilio bridge
    logger.info("🔊 Waiting for Twilio audio bridge...")
    
    # Give the bridge time to publish its audio track
    await asyncio.sleep(1)
    
    # Set up track published listener BEFORE starting session
    @ctx.room.on("track_published")
    def on_local_track_published(publication, participant):
        logger.info(f"📢 Track published: {publication.sid}, kind: {publication.kind}, by: {participant.identity}")

    # Start the session
    logger.info("🚀 Starting AIDN voice agent session...")
    try:
        await session.start(room=ctx.room, agent=agent)
        logger.info("✅ Session started successfully")

        # Log local participant info
        local_participant = ctx.room.local_participant
        logger.info(f"🎤 Local participant: {local_participant.identity}")
    except Exception as e:
        logger.error(f"❌ Session start failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

    # Keep the session alive until the room closes
    logger.info("🎙️ Voice agent is now active on the call")
    
    # Wait for room to close by monitoring room events
    # The session will stay alive as long as the room is active
    room = ctx.room
    disconnected = asyncio.Event()
    
    @room.on("disconnected")
    def on_disconnect():
        disconnected.set()
    
    # Wait until room disconnects
    await disconnected.wait()
    
    logger.info(f"📴 Call ended in room: {room_name}")


def main():
    """Main function to run the AIDN voice agent."""
    
    # Verify required environment variables
    required_vars = [
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "DEEPGRAM_API_KEY",
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these in your .env file")
        return
    
    logger.info("🚀 Starting AIDN Voice Agent Worker")
    logger.info(f"📡 LiveKit URL: {os.getenv('LIVEKIT_URL')}")
    
    # Configure worker options
    worker_options = WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm,
        request_fnc=request_handler,
    )
    
    # Run the agent
    cli.run_app(worker_options)


if __name__ == "__main__":
    main()
