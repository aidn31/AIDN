"""
AIDN Shared Models
==================

Pydantic models for database tables and API schemas.
"""

from .lead import Lead, LeadCreate, LeadUpdate, CallOutcome, LeadType
from .agent import AgentProfile, AgentAvailability, AgentTerritory
from .appointment import AppointmentSlot, AppointmentCreate, AppointmentStatus
from .call import CallLog, CallCreate

__all__ = [
    "Lead",
    "LeadCreate",
    "LeadUpdate",
    "CallOutcome",
    "LeadType",
    "AgentProfile",
    "AgentAvailability",
    "AgentTerritory",
    "AppointmentSlot",
    "AppointmentCreate",
    "AppointmentStatus",
    "CallLog",
    "CallCreate",
]