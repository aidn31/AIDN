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
        """Load default scripts. Currently empty - to be populated with new persona."""
        # Scripts cleared for persona rebuild
        # Add new scripts here using add_script() or by defining them in this method
        logger.info("Script knowledge base initialized (empty - awaiting new persona)")

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
        """Get objection responses. Currently empty - to be populated with new persona."""
        # Objection responses cleared for persona rebuild
        # Return empty string - agent will use LLM to handle objections naturally
        return ""

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