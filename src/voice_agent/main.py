"""
AIDN Voice Agent Main Entry Point
=================================

LiveKit Agents entry point for AIDN voice agent.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import WorkerOptions, cli

from .aidn_agent import AIDNVoiceAgent, create_aidn_session
from ..shared.database import DatabaseManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database manager
db_manager = None


async def prewarm(proc: agents.JobProcess):
    """Prewarm function to initialize global resources."""
    global db_manager

    logger.info("Prewarming AIDN voice agent...")

    # Initialize database connection
    db_manager = DatabaseManager()
    await db_manager.connect()

    logger.info("AIDN voice agent prewarm complete")


async def entrypoint(ctx: agents.JobContext):
    """Main entry point for the AIDN voice agent."""
    global db_manager

    if not db_manager:
        # Fallback if prewarm didn't run
        db_manager = DatabaseManager()
        await db_manager.connect()

    logger.info(f"AIDN Voice Agent started in room: {ctx.room.name}")

    # Create AIDN session with optimized configuration
    session = await create_aidn_session(db_manager)

    # Create the AIDN agent
    agent = AIDNVoiceAgent(db_manager)

    # In production, this would be set based on the incoming call context
    # For now, using environment variables for testing
    test_lead_id = os.getenv("TEST_LEAD_ID")
    test_agent_id = os.getenv("TEST_AGENT_ID")

    if test_lead_id and test_agent_id:
        from uuid import UUID
        from ..shared.database import LeadRepository

        lead_repo = LeadRepository(db_manager)
        lead = await lead_repo.get_lead_by_id(UUID(test_lead_id))

        if lead:
            await agent.set_call_context(lead, UUID(test_agent_id))

    # Start the session
    await session.start(room=ctx.room, agent=agent)


def main():
    """Main function to run the AIDN voice agent."""

    # Verify required environment variables
    required_vars = [
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "DEEPGRAM_API_KEY"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return

    # Configure worker options
    worker_options = WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm,
    )

    # Run the agent
    cli.run_app(worker_options)


if __name__ == "__main__":
    main()