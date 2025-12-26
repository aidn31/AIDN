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


async def request_handler(req: JobRequest):
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
        await req.reject()


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
    
    # Extract lead and agent info from room metadata
    lead = None
    agent_info = None
    lead_id = None
    agent_id = None
    
    try:
        # Get room metadata
        room_metadata = ctx.room.metadata
        if room_metadata:
            metadata = json.loads(room_metadata)
            lead_id = metadata.get("lead_id")
            agent_id = metadata.get("agent_id")
            
            logger.info(f"📋 Room metadata - Lead: {lead_id}, Agent: {agent_id}")
    except json.JSONDecodeError:
        logger.warning("Could not parse room metadata")
    except Exception as e:
        logger.error(f"Error reading room metadata: {e}")
    
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
    
    # Wait for the bridge participant to join and publish audio
    max_wait = 30  # Wait up to 30 seconds for audio bridge
    waited = 0
    bridge_connected = False
    
    while waited < max_wait:
        # Check for remote participants with audio tracks
        for participant in ctx.room.remote_participants.values():
            if "twilio-bridge" in participant.identity:
                # Check if they have an audio track
                for track_pub in participant.track_publications.values():
                    if track_pub.kind.name == "KIND_AUDIO":
                        bridge_connected = True
                        logger.info(f"✅ Twilio audio bridge connected: {participant.identity}")
                        break
            if bridge_connected:
                break
        
        if bridge_connected:
            break
            
        await asyncio.sleep(0.5)
        waited += 0.5
        
        if waited % 5 == 0:
            logger.info(f"⏳ Still waiting for audio bridge... ({waited}s)")
    
    if not bridge_connected:
        logger.warning("⚠️ Audio bridge did not connect within timeout, proceeding anyway")
    
    # Small additional delay for audio track to be fully ready
    await asyncio.sleep(0.5)
    
    # Start the session
    logger.info("🚀 Starting AIDN voice agent session...")
    await session.start(room=ctx.room, agent=agent)
    
    # Keep the session alive until the room closes
    logger.info("🎙️ Voice agent is now active on the call")
    
    # Wait for the session to end (room will close when call ends)
    try:
        await session.drain()
    except Exception as e:
        logger.info(f"Session ended: {e}")
    
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
