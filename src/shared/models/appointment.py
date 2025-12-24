"""Appointment models for AIDN."""

from datetime import date, datetime, time
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AppointmentStatus(str, Enum):
    """Appointment slot status."""
    AVAILABLE = "available"
    BOOKED = "booked"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"


class AppointmentSlotBase(BaseModel):
    """Base appointment slot model."""
    agent_id: UUID
    date: date
    time: time
    status: AppointmentStatus = AppointmentStatus.AVAILABLE


class AppointmentCreate(AppointmentSlotBase):
    """Model for creating appointment slots."""
    pass


class AppointmentSlot(AppointmentSlotBase):
    """Complete appointment slot model."""
    id: UUID
    lead_id: Optional[UUID] = None
    booked_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

    @property
    def is_available(self) -> bool:
        """Check if slot is available for booking."""
        return self.status == AppointmentStatus.AVAILABLE

    @property
    def is_booked(self) -> bool:
        """Check if slot is booked."""
        return self.status == AppointmentStatus.BOOKED