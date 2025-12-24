"""
AIDN Script Knowledge Base
==========================

Knowledge base system that stores and retrieves scripts for different lead types
and call scenarios, enabling the voice agent to use appropriate scripts based on
lead context and conversation flow.
"""

import logging
from typing import Dict, Optional, List
from enum import Enum
from dataclasses import dataclass

from ..shared.models import Lead

logger = logging.getLogger(__name__)


class ScriptType(Enum):
    """Types of scripts available in the knowledge base."""
    GREETING = "greeting"
    MAIN_FLOW = "main_flow"
    OBJECTION = "objection"
    APPOINTMENT_SETTING = "appointment_setting"
    CONFIRMATION = "confirmation"


class LeadType(Enum):
    """Lead types for script targeting."""
    FINAL_EXPENSE = "final_expense"
    TERM_LIFE = "term_life"
    WHOLE_LIFE = "whole_life"
    MORTGAGE_PROTECTION = "mortgage_protection"
    GENERAL = "general"


@dataclass
class Script:
    """Script data structure."""
    script_type: ScriptType
    lead_type: LeadType
    content: str
    usage_context: str
    priority: int = 1  # Higher number = higher priority


class ScriptKnowledgeBase:
    """Knowledge base for call scripts organized by lead type and scenario."""

    def __init__(self):
        self.scripts: Dict[str, List[Script]] = {}
        self._load_default_scripts()

    def _load_default_scripts(self):
        """Load default scripts based on the new casual, friendly persona."""

        # Main greeting scripts by lead type
        greeting_scripts = [
            Script(
                script_type=ScriptType.GREETING,
                lead_type=LeadType.FINAL_EXPENSE,
                content="""Hey {first_name}! This is {agent_name}, umm, I'm calling from the benefits center here in {county}...

So we've got this package of info ready to go out to ya about the final expense programs, and I was just making sure you still live at {address}, is that right?""",
                usage_context="Opening greeting for final expense leads",
                priority=10
            ),

            Script(
                script_type=ScriptType.GREETING,
                lead_type=LeadType.TERM_LIFE,
                content="""Hey {first_name}! This is {agent_name} calling from the benefits center here in {county}...

We've got that info package ready for ya about the term life coverage options, just wanted to make sure you're still at {address}?""",
                usage_context="Opening greeting for term life leads",
                priority=10
            ),

            Script(
                script_type=ScriptType.GREETING,
                lead_type=LeadType.WHOLE_LIFE,
                content="""Hey {first_name}! This is {agent_name}, calling from the benefits center here in {county}...

So we've got this whole life insurance info ready to send out to ya, and I was just double-checking you're still at {address}?""",
                usage_context="Opening greeting for whole life leads",
                priority=10
            ),

            Script(
                script_type=ScriptType.GREETING,
                lead_type=LeadType.MORTGAGE_PROTECTION,
                content="""Hey {first_name}! This is {agent_name} from the benefits center here in {county}...

We've got that mortgage protection info ready for ya, just wanted to make sure you still live at {address}, that right?""",
                usage_context="Opening greeting for mortgage protection leads",
                priority=10
            ),

            Script(
                script_type=ScriptType.GREETING,
                lead_type=LeadType.GENERAL,
                content="""Hey {first_name}! This is {agent_name}, calling from the benefits center here in {county}...

So we've got this package of insurance info ready to go out to ya, and I was just making sure you still live at {address}?""",
                usage_context="Generic greeting for all lead types",
                priority=5
            )
        ]

        # Main flow scripts
        main_flow_scripts = [
            Script(
                script_type=ScriptType.MAIN_FLOW,
                lead_type=LeadType.GENERAL,
                content="""Great, well my job is pretty simple - get you the info on the new {lead_type} programs and go over it with ya.

Let me see here... they have me out there tomorrow around 8-9am and later around 3-4pm... which one works better for you?""",
                usage_context="Main appointment setting flow",
                priority=10
            )
        ]

        # Appointment confirmation scripts
        confirmation_scripts = [
            Script(
                script_type=ScriptType.CONFIRMATION,
                lead_type=LeadType.GENERAL,
                content="""Ok great, so that's {day} at {time} at {address}.

My name is {agent_name}, I'll be in a {car_description}, and I am {physical_description}.

I appreciate you and look forward to seeing you {day} at {time}. Take care, thank you, bye!""",
                usage_context="Final appointment confirmation",
                priority=10
            )
        ]

        # Store scripts organized by type and lead type
        for script in greeting_scripts + main_flow_scripts + confirmation_scripts:
            key = f"{script.script_type.value}_{script.lead_type.value}"
            if key not in self.scripts:
                self.scripts[key] = []
            self.scripts[key].append(script)

        logger.info(f"Loaded {len(greeting_scripts + main_flow_scripts + confirmation_scripts)} default scripts")

    def get_script(self, script_type: ScriptType, lead_type: Optional[LeadType] = None,
                   lead: Optional[Lead] = None) -> Optional[Script]:
        """Get the most appropriate script for the given context."""

        # Determine lead type from lead object if not provided
        if not lead_type and lead:
            lead_type_map = {
                "final_expense": LeadType.FINAL_EXPENSE,
                "term_life": LeadType.TERM_LIFE,
                "whole_life": LeadType.WHOLE_LIFE,
                "mortgage_protection": LeadType.MORTGAGE_PROTECTION
            }
            lead_type = lead_type_map.get(lead.lead_type, LeadType.GENERAL)
        elif not lead_type:
            lead_type = LeadType.GENERAL

        # Look for specific script first
        specific_key = f"{script_type.value}_{lead_type.value}"
        if specific_key in self.scripts:
            # Return highest priority script
            return max(self.scripts[specific_key], key=lambda s: s.priority)

        # Fall back to general script
        general_key = f"{script_type.value}_{LeadType.GENERAL.value}"
        if general_key in self.scripts:
            return max(self.scripts[general_key], key=lambda s: s.priority)

        return None

    def format_script(self, script: Script, lead: Optional[Lead] = None,
                     agent_info: Optional[Dict] = None, **kwargs) -> str:
        """Format script with lead and agent information."""
        if not script:
            return ""

        # Prepare formatting context
        format_context = {}

        # Add lead information
        if lead:
            format_context.update({
                'first_name': lead.first_name,
                'last_name': lead.last_name,
                'address': lead.address,
                'city': lead.city,
                'county': lead.county,
                'state': lead.state,
                'zip_code': lead.zip_code,
                'lead_type': lead.lead_type.replace('_', ' ') if lead.lead_type else 'insurance'
            })

        # Add agent information
        if agent_info:
            format_context.update(agent_info)

        # Add any additional context
        format_context.update(kwargs)

        # Format the script
        try:
            return script.content.format(**format_context)
        except KeyError as e:
            logger.warning(f"Missing format key in script: {e}")
            return script.content
        except Exception as e:
            logger.error(f"Error formatting script: {e}")
            return script.content

    def add_script(self, script: Script) -> bool:
        """Add a new script to the knowledge base."""
        try:
            key = f"{script.script_type.value}_{script.lead_type.value}"
            if key not in self.scripts:
                self.scripts[key] = []
            self.scripts[key].append(script)
            logger.info(f"Added script: {script.script_type.value} for {script.lead_type.value}")
            return True
        except Exception as e:
            logger.error(f"Error adding script: {e}")
            return False

    def get_objection_response(self, objection_type: str, lead: Optional[Lead] = None) -> str:
        """Get casual objection responses based on new persona."""

        # Updated objection responses with casual tone
        objection_responses = {
            "what_is_it": """It's about the cash benefit programs for {state} residents in your age group and my job is simply to get you the info and go over it with you.

They have me out there tomorrow for a ton of stops. Would you be home in the morning or would you be home in the afternoon?""",

            "what_is_it_second": """It's the updated 2024 cash benefit programs for your age group, and I've got your date of birth here as {date_of_birth}.

My job is simple - get you the info and they have me out there tomorrow. Would the morning around 9-10 work or would the afternoon 1-2pm be better?""",

            "not_interested": """Yeah, I get it... umm, can I ask - is it the timing that's not good, or are you pretty well set with your current situation?""",

            "busy_right_now": """Oh sure, no problem... this'll just take like 30 seconds. They've got me running around tomorrow and I was just trying to see if you'd be around in the morning or afternoon?""",

            "how_did_you_get_number": """Ya know, you had filled out one of those cards asking about coverage... do ya remember doing that recently? Anyway, that's why I'm calling - to get you that info you requested.""",

            "already_have_insurance": """Oh that's great! Yeah, a lot of folks we help already have something... they just wanna make sure they're getting the best deal or haven't missed anything new. Would it hurt to just take a quick look?""",

            "send_me_info": """Yeah, I wish I could just drop it in the mail, but honestly these programs are so specific to your situation - ya know, your age, income level and all that... that's why they like me to just go over it real quick with ya. Would tomorrow morning or afternoon work better?"""
        }

        response = objection_responses.get(objection_type, objection_responses.get("not_interested", ""))

        # Format with lead info if available
        if lead and response:
            try:
                format_context = {
                    'state': lead.state,
                    'first_name': lead.first_name,
                    'date_of_birth': 'your age group'  # Would be actual DOB in production
                }
                response = response.format(**format_context)
            except:
                pass  # Use unformatted response if formatting fails

        return response

    def get_all_scripts(self, script_type: Optional[ScriptType] = None,
                       lead_type: Optional[LeadType] = None) -> List[Script]:
        """Get all scripts matching the criteria."""
        all_scripts = []

        for scripts_list in self.scripts.values():
            for script in scripts_list:
                if script_type and script.script_type != script_type:
                    continue
                if lead_type and script.lead_type != lead_type:
                    continue
                all_scripts.append(script)

        return sorted(all_scripts, key=lambda s: s.priority, reverse=True)