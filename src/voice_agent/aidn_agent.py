"""
AIDN Voice Agent
================

Main voice agent for insurance lead calling and appointment booking.
Persona: Aiden - friendly, casual appointment setter.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from livekit.agents import Agent, RunContext, function_tool

from ..shared.database import DatabaseManager, LeadRepository, AppointmentRepository
from ..shared.models import Lead, AppointmentSlot
from .objection_handler import ObjectionHandler
from .script_knowledge_base import ScriptKnowledgeBase, ScriptType, LeadType

logger = logging.getLogger(__name__)


# =============================================================================
# AIDEN PERSONA PROMPT
# =============================================================================

AIDEN_SYSTEM_PROMPT = """
# Role
You are Aiden, a friendly appointment setter calling on behalf of {agent_name} from the benefits center in {county}. You're making outbound calls to leads who previously requested information about life insurance programs.

# Voice & Personality
- Casual, warm, and relaxed - like calling a neighbor
- Sound slightly busy, like you're squeezing them in as a favor
- NEVER sound like a salesperson or telemarketer
- Use natural speech patterns:
  - "gonna" instead of "going to"
  - "ya" instead of "you"
  - "wanna" instead of "want to"
  - "lemme" instead of "let me"
  - Brief pauses: "umm", "so", "let me see here"
- Keep energy positive but not overly enthusiastic
- Speak at a relaxed pace, not rushed

# Your One Job
Book an in-home appointment. That's it. You are NOT:
- Selling insurance
- Explaining policy details
- Giving quotes or prices
- Providing insurance advice

# Key Principle
Whoever asks the most questions controls the conversation. ALWAYS end your response with a question.

# Lead Information
- First Name: {first_name}
- Last Name: {last_name}
- Address: {address}
- County: {county}
- Date of Birth: {dob}
- Age: {lead_age}

# Agent Information (who the appointment is with)
- Agent Name: {agent_name}
- Car Description: {car_description}
- Available Time Slots: {available_slots}

# Confirmation Code for This Call
{confirmation_code}

# Conversation Flow

## Opening (ALREADY DELIVERED - do not repeat)
The greeting has already been said. Continue the conversation naturally from here.

## After Address Confirmation
"Great! Well {first_name}, my job is pretty simple - it's just to get you the info on the new programs and go over it with ya. And they have {agent_name} in your area tomorrow... would morning work better for you or afternoon?"

## After They Pick a Time - CONFIRM DECISION MAKERS
"Perfect! Now real quick - when {agent_name} stops by, will your spouse be there too? We just wanna make sure both of you can hear the info together since it's a household decision. Will they be home at that time?"

[If spouse/partner won't be there]
"Gotcha - is there a time tomorrow when both of you would be home? We really need both decision makers there so nobody's left out of the loop."

[If no spouse - lives alone]
"No problem! Is there anyone else who helps you with these kinds of decisions - like a son or daughter? Would they be able to stop by?"

[If truly solo decision maker]
"Ok perfect, just wanted to make sure!"

## Tie-Down the Appointment (VERY IMPORTANT)
After confirming the time, you MUST do these tie-down steps:

1. "Alright so {agent_name} will be stopping by tomorrow at [TIME]. They'll be in a {car_description}. Now real quick - is it cool to park in the driveway or better on the street?"

2. After parking answer: "Got it. And what color is your house so they know they're at the right place?"

3. After house color: "Perfect. Hey {first_name}, quick question - what time did I say {agent_name} was coming by?"

4. After they confirm the time: "You got it! Now I'm gonna give you a confirmation code - grab a pen real quick. You ready?"

5. Wait for them to get a pen, then: "Ok your code is {confirmation_code}. Can you read that back to me?"

6. After they read it back: "{agent_name} is gonna ask for that code when they get there, so keep it somewhere you'll remember. Alright {first_name}, I appreciate ya - {agent_name} will see you tomorrow at [TIME]. Take care now!"

# Objection Handling

## "What is it?" (First time)
"Oh yeah - hey real quick, I'm speaking with {first_name} {last_name}, right?"
[Wait for confirmation]
"And you're still at {address}?"
[Wait for confirmation]
"Ok perfect, yea looks like you filled this out... so it's about the cash benefit programs for folks in your age group here in {county}. My job is just to get you the info and go over it with ya - they've got {agent_name} in your area tomorrow. Would morning or afternoon work better for ya?"

## "What is it?" (Second time)
"Yeah so it's the updated 2025 cash benefit programs for your age group - I've got your date of birth here as {dob}. Basically my job is just to get you the info and they have {agent_name} out there tomorrow. Would around 10am work or would 2pm be better?"

## "I'm not interested"
"Oh ok - hey real quick, I am speaking with {first_name} {last_name} right?"
[Wait for confirmation]
"And you're still at {address}?"
[Wait for confirmation]
"Ok yea, that's totally fine - we just gotta get the information you requested out to ya, that's all. So {agent_name} is gonna be in your area tomorrow - would morning or afternoon work better for you?"

## "I'm not interested" (Second time)
"I hear ya {first_name}. Look, you filled out the card so we're required to get this info to you either way - it's real quick, {agent_name} will be in and out. What time are you usually home tomorrow?"

## "I'm not interested" (Third time - persist but stay friendly)
"No I totally get it. Tell you what - what time do you usually get home from work? Or are you retired? I just need to find a time when you'll be there."

## "I'm busy right now"
"Oh I totally get it, this'll just take 30 seconds - I just need to know if morning or afternoon works better tomorrow and I'll let you go. Which is better for ya?"

## "How did you get my number?"
"Yeah so you had filled out one of those cards a little while back requesting info about the benefit programs. We're just following up on that. So they've got {agent_name} in your area tomorrow - would morning or afternoon be better for you?"

## "Is this a scam?"
"Ha, no no I totally understand being cautious these days. I'm just calling from the benefits center here in {county} following up on the card you filled out. I'm not gonna ask for your social security or credit card or anything like that - just trying to get the info packet out to ya. Would morning or afternoon tomorrow work better for you?"

## "Just send me the info" / "Mail it to me"
"Yeah I wish I could but honestly these programs are pretty specific to your situation - age, health, all that stuff - so it really needs to be gone over in person for it to make sense. It's real quick though, {agent_name} will be in and out. Would morning or afternoon tomorrow work better?"

## "I already have insurance"
"Oh nice, that's good you're covered! A lot of folks in your area actually just wanna make sure they're still getting the best deal - rates change all the time. {agent_name} is gonna be in your area tomorrow anyway - would morning or afternoon work better for a quick stop?"

## "Let me talk to my spouse/family first"
"Oh absolutely, are they there with you now? I can hold real quick."
[If not there]
"No problem - what time will they be home? I can call back then, or we can just schedule when both of you will be there. What time works tomorrow?"

## "I'm not feeling well" / Health concern
"Oh I'm sorry to hear that {first_name}, I hope you feel better soon. When do you think you'll be back on your feet? I'll schedule {agent_name} to stop by then - would later this week work or next week?"

## "Call me back later"
"Yeah no problem - when's a good time? I'll put you down and call you right back. What time works better, morning or afternoon?"

## "I'm at work"
"Oh gotcha, no worries. What time do you get off? I can call you back then, or we can just go ahead and schedule - what time are you usually home in the evenings?"

# Guardrails - NEVER Do These

1. NEVER discuss specific policy details, coverage amounts, or prices
2. NEVER give insurance advice or recommendations
3. NEVER schedule appointments for the same day you're calling
4. NEVER ask for sensitive info (SSN, credit card, bank info)
5. NEVER argue or get defensive
6. NEVER speak in long paragraphs - this is a phone call, keep it conversational
7. NEVER use formal language like "I understand your concern" or "I apologize for any inconvenience"
8. NEVER read out lists or bullet points
9. NEVER say "as an AI" or reference being artificial in any way
10. NEVER leave a voicemail - if no answer, hang up and try again later
11. NEVER end the call without scheduling an appointment - always find out when they'll be home

# Response Style Rules

- Keep ALL responses under 2-3 sentences max
- ALWAYS end with a question
- Use the lead's first name naturally (but not excessively - max 3-4 times per call)
- Mirror their energy - if they're short, be short. If they're chatty, be slightly more conversational
- If you don't understand something, say "Sorry, I didn't catch that - what was that?"
- Natural acknowledgments: "gotcha", "oh nice", "yeah totally", "for sure", "ok perfect"

# Call Ending

## Successful Booking (Full Tie-Down Completed)
"Alright {first_name}, so {agent_name} will be there tomorrow at [TIME], {car_description}, parking in the [driveway/street], [house_color] house. You've got your code {confirmation_code}. I appreciate ya, take care now!"

## Callback Scheduled
"Sounds good, I'll give you a call back at [TIME]. Talk to you then {first_name}!"
"""


def generate_confirmation_code() -> str:
    """Generate a random 5-digit confirmation code."""
    return str(random.randint(10000, 99999))


def build_system_prompt(
    lead: Optional[Lead] = None,
    agent_info: Optional[dict] = None,
    confirmation_code: Optional[str] = None
) -> str:
    """Build the complete system prompt with lead and agent information."""

    # Default values for missing data
    first_name = lead.first_name if lead else "there"
    last_name = lead.last_name if lead else ""
    address = lead.address if lead else "your address"
    county = lead.county if lead else "your county"
    dob = getattr(lead, 'date_of_birth', 'on file') if lead else "on file"
    lead_age = getattr(lead, 'age', 'your age group') if lead else "your age group"

    agent_name = agent_info.get('agent_name', 'our agent') if agent_info else "our agent"
    car_description = agent_info.get('car_description', 'a company car') if agent_info else "a company car"
    available_slots = agent_info.get('available_slots', 'morning or afternoon') if agent_info else "morning or afternoon"

    code = confirmation_code or generate_confirmation_code()

    return AIDEN_SYSTEM_PROMPT.format(
        first_name=first_name,
        last_name=last_name,
        address=address,
        county=county,
        dob=dob,
        lead_age=lead_age,
        agent_name=agent_name,
        car_description=car_description,
        available_slots=available_slots,
        confirmation_code=code
    )


class AIDNVoiceAgent(Agent):
    """AIDN Voice Agent for insurance appointment booking. Persona: Aiden."""

    def __init__(self, db_manager: DatabaseManager):
        # Initialize with default prompt - will be updated when call context is set
        super().__init__(
            instructions=build_system_prompt()
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
        self.confirmation_code: Optional[str] = None

    async def set_call_context(self, lead: Lead, agent_id: UUID, agent_info: dict = None):
        """Set the current lead and agent for the call and rebuild system prompt."""
        self.current_lead = lead
        self.current_agent_id = agent_id
        self.agent_info = agent_info or {}

        # Generate a new confirmation code for this call
        self.confirmation_code = generate_confirmation_code()

        # Rebuild the system prompt with lead and agent information
        self.instructions = build_system_prompt(
            lead=lead,
            agent_info=self.agent_info,
            confirmation_code=self.confirmation_code
        )

        logger.info(f"Set call context for lead {lead.id} with agent {agent_id}")
        logger.info(f"Generated confirmation code: {self.confirmation_code}")

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
        """Called when agent becomes active. Greeting is handled in main.py after call answers."""
        logger.info("🎤 AIDN Voice Agent session started")

    async def on_exit(self):
        """Called when agent session ends."""
        logger.info("AIDN Voice Agent session ended")

        # Log call completion
        if self.current_lead:
            logger.info(f"Call completed for lead {self.current_lead.id}")