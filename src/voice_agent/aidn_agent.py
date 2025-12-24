"""
AIDN Voice Agent
================

Main voice agent for insurance lead calling and appointment booking.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from livekit import agents
from livekit.agents import Agent, AgentSession, RunContext, function_tool
from livekit.plugins import deepgram, openai, silero

from ..shared.database import DatabaseManager, LeadRepository, AppointmentRepository
from ..shared.models import Lead, AppointmentSlot
from .objection_handler import ObjectionHandler

logger = logging.getLogger(__name__)


class AIDNVoiceAgent(Agent):
    """AIDN Voice Agent for insurance appointment booking."""

    def __init__(self, db_manager: DatabaseManager):
        # Initialize with insurance-specific instructions
        super().__init__(
            instructions="""You are AIDN, a friendly AI voice assistant calling on behalf of an insurance agency.

Your role is to:
1. Call leads who requested insurance information
2. Qualify their interest in a warm, natural way
3. Book appointments with human agents
4. Handle objections professionally

Conversation Style:
- Sound like a warm, friendly person (not robotic)
- Use natural speech patterns with verbal affirmations
- Build rapport before transitioning to appointment booking
- Be conversational and empathetic

Key Rules:
- NEVER discuss specific policy details, prices, or coverage amounts
- NEVER provide insurance advice or recommendations
- Always redirect insurance questions to the human agent
- If someone says "Do Not Call", immediately respect that request
- Keep calls focused on appointment booking, not sales

Your goal is to book quality appointments where prospects are genuinely interested and likely to show up."""
        )

        self.db_manager = db_manager
        self.lead_repo = LeadRepository(db_manager)
        self.appointment_repo = AppointmentRepository(db_manager)
        self.objection_handler = ObjectionHandler()

        # Current call context
        self.current_lead: Optional[Lead] = None
        self.current_agent_id: Optional[UUID] = None

    async def set_call_context(self, lead: Lead, agent_id: UUID):
        """Set the current lead and agent for the call."""
        self.current_lead = lead
        self.current_agent_id = agent_id
        logger.info(f"Set call context for lead {lead.id} with agent {agent_id}")

    @function_tool
    async def get_available_appointments(self, context: RunContext, preferred_days: str = "this week") -> str:
        """Get available appointment slots for the assigned agent."""
        if not self.current_agent_id:
            return "I'm having trouble accessing the schedule right now. Let me transfer you to someone who can help."

        try:
            # Get available slots for next 2 days
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=2)

            slots = await self.appointment_repo.get_available_slots(
                agent_id=self.current_agent_id,
                start_date=start_date,
                end_date=end_date
            )

            if not slots:
                return "Let me check the schedule... I don't see any openings in the next couple days. Would next week work better for you?"

            # Format available times naturally
            formatted_slots = []
            for slot in slots[:3]:  # Limit to 3 options
                day_name = slot.date.strftime("%A")  # Monday, Tuesday, etc.
                time_str = slot.time.strftime("%I:%M %p")  # 2:00 PM
                formatted_slots.append(f"{day_name} at {time_str}")

            return f"I have some openings: {', '.join(formatted_slots[:2])} or {formatted_slots[2] if len(formatted_slots) > 2 else 'another time'}"

        except Exception as e:
            logger.error(f"Error getting appointments: {e}")
            return "Let me check on that and have someone call you right back with available times."

    @function_tool
    async def book_appointment(self, context: RunContext, day: str, time: str) -> str:
        """Book an appointment for the lead."""
        if not self.current_lead or not self.current_agent_id:
            return "I'm having trouble with the booking system. Let me have someone call you back to confirm."

        try:
            # Parse the day and time (simplified for prototype)
            # In production, would use more sophisticated parsing

            # Get available slots
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=7)

            slots = await self.appointment_repo.get_available_slots(
                agent_id=self.current_agent_id,
                start_date=start_date,
                end_date=end_date
            )

            if slots:
                # Book the first available slot (simplified)
                slot = slots[0]
                success = await self.appointment_repo.book_slot(
                    slot_id=slot.id,
                    lead_id=self.current_lead.id
                )

                if success:
                    # Update lead status
                    await self.lead_repo.update_lead_outcome(
                        lead_id=self.current_lead.id,
                        outcome="booked"
                    )

                    # Format confirmation
                    day_name = slot.date.strftime("%A, %B %d")
                    time_str = slot.time.strftime("%I:%M %p")

                    return f"Perfect! I've got you scheduled for {day_name} at {time_str}. The agent will call about 5 minutes before to confirm they're on their way."
                else:
                    return "That time slot just got taken. Let me find another option for you."
            else:
                return "I don't see any available times right now. Let me have someone call you back with options that work."

        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            return "Let me have someone call you back to get that scheduled for you."

    @function_tool
    async def handle_objection(self, context: RunContext, objection_type: str, customer_response: str) -> str:
        """Handle common objections with appropriate responses."""
        response = await self.objection_handler.handle_objection(
            objection_type=objection_type,
            customer_response=customer_response,
            lead=self.current_lead
        )

        # Log the objection for analytics
        logger.info(f"Handled objection: {objection_type} for lead {self.current_lead.id if self.current_lead else 'unknown'}")

        return response

    @function_tool
    async def mark_do_not_call(self, context: RunContext) -> str:
        """Mark lead as Do Not Call if requested."""
        if self.current_lead:
            await self.lead_repo.update_lead_outcome(
                lead_id=self.current_lead.id,
                outcome="dnc"
            )
            logger.info(f"Marked lead {self.current_lead.id} as DNC")

        return "I've removed your number from our calling list. Have a great day!"

    @function_tool
    async def request_callback(self, context: RunContext, preferred_time: str) -> str:
        """Schedule a callback for the lead."""
        if not self.current_lead:
            return "I'll make sure someone calls you back soon."

        try:
            # Set callback for later (simplified - would parse preferred_time in production)
            callback_time = datetime.now() + timedelta(hours=2)

            await self.lead_repo.update_lead_outcome(
                lead_id=self.current_lead.id,
                outcome="callback",
                next_call_at=callback_time
            )

            return f"I'll have someone call you back around {preferred_time}. Thanks for your time!"

        except Exception as e:
            logger.error(f"Error scheduling callback: {e}")
            return "I'll make sure someone calls you back soon."

    async def on_enter(self):
        """Called when agent becomes active."""
        logger.info("AIDN Voice Agent session started")

        # Generate personalized greeting if we have lead context
        if self.current_lead:
            greeting_instructions = f"""Greet {self.current_lead.first_name} warmly and naturally.

Reference that they requested information about {self.current_lead.lead_type.replace('_', ' ') if self.current_lead.lead_type else 'life insurance'}.

Example greeting: "Hi {self.current_lead.first_name}! This is [your name] calling about the insurance information you requested. Did I catch you at a good time?"

Be warm and conversational, not scripted."""
        else:
            greeting_instructions = "Greet the caller warmly and ask about the insurance information they requested."

        await self.session.generate_reply(instructions=greeting_instructions)

    async def on_exit(self):
        """Called when agent session ends."""
        logger.info("AIDN Voice Agent session ended")

        # Log call completion
        if self.current_lead:
            # This would typically be handled by the call manager
            logger.info(f"Call completed for lead {self.current_lead.id}")


async def create_aidn_session(db_manager: DatabaseManager) -> AgentSession:
    """Create AIDN voice agent session with proper configuration."""

    # Configure the voice pipeline optimized for phone calls
    session = AgentSession(
        # Speech-to-Text - optimized for phone quality audio
        stt=deepgram.STT(
            model="nova-2",
            language="en-US",
            smart_format=True,
            interim_results=True
        ),

        # Large Language Model - fast and cost-effective
        llm=openai.LLM(
            model="gpt-4.1-mini",
            temperature=0.7,  # Slightly more conversational
        ),

        # Text-to-Speech - natural voice for insurance context
        tts=openai.TTS(
            voice="echo",  # Professional but warm voice
            speed=1.1      # Slightly faster for efficiency
        ),

        # Voice Activity Detection
        vad=silero.VAD.load(),

        # Turn detection for natural conversation
        turn_detection="semantic"
    )

    return session