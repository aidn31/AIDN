"""Agent models for AIDN."""

from datetime import time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AgentProfileBase(BaseModel):
    """Base agent profile model."""
    agent_name: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    physical_description: Optional[str] = None
    car_description: Optional[str] = None
    google_calendar_id: Optional[str] = Field(None, max_length=255)
    earliest_appointment_time: time = time(9, 0)  # 9:00 AM
    latest_appointment_time: time = time(18, 0)   # 6:00 PM
    slot_gap_hours: int = Field(2, ge=1, le=8)


class AgentProfile(AgentProfileBase):
    """Complete agent profile model."""
    id: UUID
    is_active: bool = True

    class Config:
        from_attributes = True


class AgentAvailabilityBase(BaseModel):
    """Base agent availability model."""
    day_of_week: int = Field(..., ge=0, le=6)  # 0 = Sunday
    is_available: bool = False
    calling_start_time: Optional[time] = None
    calling_end_time: Optional[time] = None
    max_appointments: int = Field(0, ge=0)
    first_appointment_time: Optional[time] = None


class AgentAvailability(AgentAvailabilityBase):
    """Complete agent availability model."""
    id: UUID
    agent_id: UUID

    class Config:
        from_attributes = True


class AgentTerritoryBase(BaseModel):
    """Base agent territory model."""
    county: Optional[str] = Field(None, max_length=100)
    state: str = Field(..., max_length=10)
    zip_code: Optional[str] = Field(None, max_length=10)
    lead_types: List[str] = Field(default_factory=list)


class AgentTerritory(AgentTerritoryBase):
    """Complete agent territory model."""
    id: UUID
    agent_id: UUID

    class Config:
        from_attributes = True