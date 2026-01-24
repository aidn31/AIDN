"""
AIDN Voice Agent v2 - With RAG
==============================

Optimized voice agent using:
- Slim core prompt (~60 lines, ~1200 tokens)
- RAG-based objection handling (retrieved on-demand)
- Expected latency improvement: 3-4s → <1s
"""

import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import UUID

from livekit.agents import Agent, RunContext, function_tool

from .core_prompt import build_core_prompt
from ..shared.database import DatabaseManager, LeadRepository, AppointmentRepository
from ..shared.models import Lead

logger = logging.getLogger(__name__)


# =============================================================================
# OBJECTION KNOWLEDGE BASE (RAG)
# =============================================================================

class ObjectionKB:
    """Simple RAG system for objection handling."""
    
    def __init__(self, kb_path: Optional[str] = None):
        """Load objection knowledge base from JSON."""
        if kb_path is None:
            # Default to same directory as this file
            kb_path = Path(__file__).parent / "objection_kb.json"
        
        with open(kb_path, 'r') as f:
            data = json.load(f)
        
        self.objections = data.get("objections", [])
        self.fallback = data.get("fallback", {})
        
        # Build trigger index for fast lookup
        self._trigger_index = {}
        for obj in self.objections:
            for trigger in obj.get("triggers", []):
                self._trigger_index[trigger.lower()] = obj
        
        logger.info(f"Loaded {len(self.objections)} objection handlers")
    
    def find_objection(self, user_input: str) -> dict:
        """
        Find the best matching objection handler for user input.
        
        Args:
            user_input: What the user said
            
        Returns:
            Objection dict with id, name, strategy, response
        """
        user_lower = user_input.lower()
        
        # Check each trigger phrase
        for trigger, obj in self._trigger_index.items():
            if trigger in user_lower:
                logger.info(f"Matched objection: {obj['id']} (trigger: {trigger})")
                return obj
        
        # No match - return fallback
        logger.info(f"No objection match for: {user_input[:50]}...")
        return {
            "id": "fallback",
            "name": "Fallback",
            "strategy": self.fallback.get("strategy", "Redirect to scheduling"),
            "response": self.fallback.get("response", "Would morning or afternoon work better?")
        }
    
    def format_response(self, objection: dict, lead_info: dict) -> str:
        """Format the objection response with lead info."""
        response = objection.get("response", "")
        
        # Replace placeholders
        replacements = {
            "{first_name}": lead_info.get("first_name", "there"),
            "{last_name}": lead_info.get("last_name", ""),
            "{address}": lead_info.get("address", "your address"),
            "{county}": lead_info.get("county", "your area"),
            "{dob}": lead_info.get("dob", "on file"),
            "{agent_name}": lead_info.get("agent_name", "our agent"),
        }
        
        for placeholder, value in replacements.items():
            response = response.replace(placeholder, str(value))
        
        return response


def generate_confirmation_code() -> str:
    """Generate a random 5-digit confirmation code."""
    return str(random.randint(10000, 99999))


# =============================================================================
# AIDN VOICE AGENT v2
# =============================================================================

class AIDNVoiceAgent(Agent):
    """
    AIDN Voice Agent with RAG-based objection handling.
    
    Architecture:
    - Slim core prompt (~1200 tokens) loaded on init
    - Objection handlers retrieved via tool call when needed
    - Expected latency: <1 second response time
    """

    def __init__(self, db_manager=None):
        """Initialize with slim core prompt."""
        # Start with default prompt - updated when call context is set
        super().__init__(
            instructions=build_core_prompt()
        )
        
        self.db_manager = db_manager
        self.objection_kb = ObjectionKB()
        
        # These would be initialized from db_manager in production
        # self.lead_repo = LeadRepository(db_manager) if db_manager else None
        # self.appointment_repo = AppointmentRepository(db_manager) if db_manager else None
        
        # Current call context
        self.current_lead = None
        self.current_agent_id: Optional[UUID] = None
        self.agent_info: Optional[dict] = None
        self.confirmation_code: Optional[str] = None
        
        logger.info("AIDNVoiceAgent initialized with slim prompt + RAG")

    async def set_call_context(self, lead, agent_id: UUID, agent_info: dict = None):
        """Set the current lead and agent, rebuild slim prompt."""
        self.current_lead = lead
        self.current_agent_id = agent_id
        self.agent_info = agent_info or {}
        self.confirmation_code = generate_confirmation_code()
        
        # Rebuild slim prompt with lead info
        self.instructions = build_core_prompt(
            first_name=getattr(lead, 'first_name', 'there'),
            last_name=getattr(lead, 'last_name', ''),
            address=getattr(lead, 'address', 'your address'),
            county=getattr(lead, 'county', 'your area'),
            dob=getattr(lead, 'date_of_birth', 'on file'),
            agent_name=self.agent_info.get('agent_name', 'our agent'),
            car_description=self.agent_info.get('car_description', 'a company car'),
            confirmation_code=self.confirmation_code
        )
        
        logger.info(f"Call context set for lead {getattr(lead, 'id', 'unknown')}")
        logger.info(f"Confirmation code: {self.confirmation_code}")

    def _get_lead_info_dict(self) -> dict:
        """Get lead info as dict for response formatting."""
        if self.current_lead:
            return {
                "first_name": getattr(self.current_lead, 'first_name', 'there'),
                "last_name": getattr(self.current_lead, 'last_name', ''),
                "address": getattr(self.current_lead, 'address', 'your address'),
                "county": getattr(self.current_lead, 'county', 'your area'),
                "dob": getattr(self.current_lead, 'date_of_birth', 'on file'),
                "agent_name": self.agent_info.get('agent_name', 'our agent') if self.agent_info else 'our agent',
            }
        return {
            "first_name": "there",
            "last_name": "",
            "address": "your address",
            "county": "your area",
            "dob": "on file",
            "agent_name": "our agent",
        }

    # =========================================================================
    # RAG TOOL - This is the key optimization!
    # =========================================================================
    
    @function_tool
    async def get_objection_response(
        self,
        context: RunContext,
        what_they_said: str
    ) -> str:
        """
        Get the appropriate response for an objection.
        
        Use this when the lead raises an objection like:
        - "What is it?" / "What's this about?"
        - "Not interested" / "No thanks"
        - "I'm busy" / "Bad time"
        - "How did you get my number?"
        - "Is this a scam?"
        - "Just mail it to me"
        - "I already have insurance"
        - "Need to talk to spouse"
        - "I'm at work"
        - "Call me back later"
        
        Args:
            what_they_said: The objection or concern the lead expressed
            
        Returns:
            The response you should give, personalized with lead info
        """
        # Find matching objection handler
        objection = self.objection_kb.find_objection(what_they_said)
        
        # Format with lead info
        lead_info = self._get_lead_info_dict()
        response = self.objection_kb.format_response(objection, lead_info)
        
        logger.info(f"RAG objection lookup: '{what_they_said[:30]}...' → {objection['id']}")
        
        return response

    # =========================================================================
    # OTHER TOOLS (unchanged from v1)
    # =========================================================================
    
    @function_tool
    async def get_available_times(self, context: RunContext, day: str = "tomorrow") -> str:
        """
        Get available appointment times.

        Args:
            day: Which day to check availability for (default: tomorrow)
        """
        agent_name = self.agent_info.get('agent_name', 'our agent') if self.agent_info else 'our agent'

        # In production, this would query real availability
        # For now, return standard morning/afternoon options
        return f"They have {agent_name} out there {day} around 10am and around 2pm. Which works better for ya?"

    @function_tool
    async def confirm_appointment(
        self,
        context: RunContext,
        time_slot: str,
        parking: str = "",
        house_color: str = ""
    ) -> str:
        """
        Confirm the appointment with tie-down details.
        
        Args:
            time_slot: The confirmed time (e.g., "10am", "2pm")
            parking: Where to park (driveway/street)
            house_color: Color of the house
        """
        first_name = self._get_lead_info_dict()["first_name"]
        agent_name = self._get_lead_info_dict()["agent_name"]
        car = self.agent_info.get('car_description', 'a company car') if self.agent_info else 'a company car'
        
        # Build confirmation
        confirmation = f"Alright {first_name}, so {agent_name} will be there tomorrow at {time_slot}"
        
        if car:
            confirmation += f", {car}"
        if parking:
            confirmation += f", parking in the {parking}"
        if house_color:
            confirmation += f", {house_color} house"
        
        confirmation += f". Your confirmation code is {self.confirmation_code}. I appreciate ya, take care now!"
        
        logger.info(f"Appointment confirmed: {time_slot}, code: {self.confirmation_code}")
        
        return confirmation

    @function_tool
    async def schedule_callback(self, context: RunContext, callback_time: str) -> str:
        """Schedule a callback for later."""
        first_name = self._get_lead_info_dict()["first_name"]
        
        logger.info(f"Callback scheduled for: {callback_time}")
        
        return f"Sounds good, I'll give you a call back {callback_time}. Talk to you then {first_name}!"

    @function_tool
    async def end_call_politely(self, context: RunContext, reason: str = "") -> str:
        """End the call politely (only for deceased or firm DNC)."""
        if "passed" in reason.lower() or "died" in reason.lower():
            return "I'm so sorry for your loss. Please take care of yourself."
        
        first_name = self._get_lead_info_dict()["first_name"]
        return f"No problem at all {first_name}, you take care now!"

    # =========================================================================
    # LIFECYCLE
    # =========================================================================
    
    async def on_enter(self):
        """Called when agent becomes active."""
        logger.info("🎤 AIDNVoiceAgent session started (slim prompt + RAG)")

    async def on_exit(self):
        """Called when agent session ends."""
        logger.info("AIDN Voice Agent session ended")
        if self.current_lead:
            logger.info(f"Call completed for lead {getattr(self.current_lead, 'id', 'unknown')}")


# =============================================================================
# QUICK TEST
# =============================================================================

if __name__ == "__main__":
    # Test the objection KB
    kb = ObjectionKB()
    
    test_inputs = [
        "What is this about?",
        "I'm not interested",
        "How did you get my number?",
        "Is this some kind of scam?",
        "Just mail me the information",
        "I already have life insurance",
        "I need to ask my wife first",
        "I'm at work right now",
        "Something random that won't match",
    ]
    
    lead_info = {
        "first_name": "John",
        "last_name": "Smith",
        "address": "123 Oak Street",
        "county": "Cook County",
        "dob": "03/15/1955",
        "agent_name": "Mike Johnson",
    }
    
    print("=" * 60)
    print("OBJECTION KB TEST")
    print("=" * 60)
    
    for user_input in test_inputs:
        print(f"\nUser: \"{user_input}\"")
        objection = kb.find_objection(user_input)
        response = kb.format_response(objection, lead_info)
        print(f"Matched: {objection['id']}")
        print(f"Response: {response[:100]}...")
