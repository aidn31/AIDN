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
from .script_knowledge_base import ScriptKnowledgeBase, ScriptType, LeadType

logger = logging.getLogger(__name__)


class AIDNVoiceAgent(Agent):
    """AIDN Voice Agent for insurance appointment booking."""

    def __init__(self, db_manager: DatabaseManager):
        # Initialize with new casual, friendly persona
        super().__init__(
            instructions="""You are calling on behalf of an insurance benefits center. You have a casual, friendly personality - like someone they already know.

CRITICAL PERSONA CHARACTERISTICS:
- Speak SLOWLY and relaxed, not rushed
- Sound busy but friendly - like you're squeezing them in as a favor
- Use casual language: "gonna", "ya", "umm", "let me see here"
- Add natural speech patterns and filler words
- Assume familiarity - greet like you know them already
- NOT professional or corporate sounding - this is a casual conversation

SPEECH PATTERNS TO USE:
- "Hey [Name]!" (not "Hello, am I speaking with...")
- "umm", "hmm", "ya know", "let me see here"
- "gonna" instead of "going to"
- "wanna" instead of "want to"
- "ya" instead of "you"

CONVERSATION FLOW:
1. Casual greeting with their name
2. Say you're calling from benefits center in their county
3. Mention you have info ready to go out to them
4. Verify their address casually
5. Set appointment for tomorrow (morning or afternoon options)
6. Confirm with agent description and car info

TONE EXAMPLE:
"Hey Joe! This is Mike, umm, I'm calling from the benefits center here in Cook County... so we've got this package of info ready to go out to ya, and I was just making sure you still live at 123 Main Street, is that right?"

OBJECTION HANDLING:
- "What is it?" → Explain cash benefit programs for their age group, offer morning/afternoon
- If they ask "What is it?" again → Mention updated 2024 programs, still offer times
- Stay casual and friendly throughout

NEVER discuss specific policy details or give insurance advice. Your only job is to book the appointment."""
        )

        self.db_manager = db_manager
        self.lead_repo = LeadRepository(db_manager)
        self.appointment_repo = AppointmentRepository(db_manager)
        self.objection_handler = ObjectionHandler()
        self.script_kb = ScriptKnowledgeBase()

        # Current call context
        self.current_lead: Optional[Lead] = None
        self.current_agent_id: Optional[UUID] = None
        self.agent_info: Optional[dict] = None

    async def set_call_context(self, lead: Lead, agent_id: UUID, agent_info: dict = None):
        """Set the current lead and agent for the call."""
        self.current_lead = lead
        self.current_agent_id = agent_id
        self.agent_info = agent_info or {}
        logger.info(f"Set call context for lead {lead.id} with agent {agent_id}")

    @function_tool
    async def get_greeting_script(self, context: RunContext) -> str:
        """Get the appropriate greeting script based on lead type."""
        if not self.current_lead:
            return "Hey there! This is calling from the benefits center..."

        # Get script from knowledge base
        script = self.script_kb.get_script(
            script_type=ScriptType.GREETING,
            lead=self.current_lead
        )

        if script:
            return self.script_kb.format_script(
                script=script,
                lead=self.current_lead,
                agent_info=self.agent_info
            )

        # Fallback greeting
        return f"Hey {self.current_lead.first_name}! This is calling from the benefits center here in {self.current_lead.county}..."

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

            # Use casual tone for appointment options
            morning_slot = None
            afternoon_slot = None

            for slot in slots:
                hour = slot.time.hour
                if not morning_slot and 8 <= hour <= 11:
                    morning_slot = slot
                elif not afternoon_slot and 13 <= hour <= 17:
                    afternoon_slot = slot

                if morning_slot and afternoon_slot:
                    break

            if morning_slot and afternoon_slot:
                return "Great, well my job is pretty simple - get you the info and go over it with ya. Let me see here... they have me out there tomorrow around 8-9am and later around 3-4pm... which one works better for you?"
            elif morning_slot:
                return "Let me see here... I've got tomorrow morning around 8-9am available. Would that work for ya?"
            elif afternoon_slot:
                return "Looks like I've got tomorrow afternoon around 3-4pm open. Would that work for ya?"
            else:
                return "Umm, let me check the schedule... looks pretty tight tomorrow. Would the next day work better for ya?"

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

                    # Format confirmation using script knowledge base
                    script = self.script_kb.get_script(ScriptType.CONFIRMATION, lead=self.current_lead)

                    if script and self.agent_info:
                        day_name = slot.date.strftime("%A")
                        time_str = slot.time.strftime("%I:%M %p")

                        confirmation = self.script_kb.format_script(
                            script=script,
                            lead=self.current_lead,
                            agent_info=self.agent_info,
                            day=day_name,
                            time=time_str,
                            address=self.current_lead.address if self.current_lead else "your address"
                        )
                        return confirmation
                    else:
                        # Fallback casual confirmation
                        day_name = slot.date.strftime("%A")
                        time_str = slot.time.strftime("%I:%M %p")
                        agent_name = self.agent_info.get('agent_name', 'the agent') if self.agent_info else 'the agent'

                        return f"Ok great, so that's {day_name} at {time_str} at your place. My name is {agent_name}, and I appreciate you and look forward to seeing you {day_name} at {time_str}. Take care, thank you, bye!"
                else:
                    return "That time slot just got taken. Let me find another option for you."
            else:
                return "I don't see any available times right now. Let me have someone call you back with options that work."

        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            return "Let me have someone call you back to get that scheduled for you."

    @function_tool
    async def handle_objection(self, context: RunContext, objection_type: str, customer_response: str) -> str:
        """Handle common objections with new casual responses."""

        # Use the knowledge base for objection responses first
        response = self.script_kb.get_objection_response(objection_type, self.current_lead)

        if not response:
            # Fall back to original objection handler
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