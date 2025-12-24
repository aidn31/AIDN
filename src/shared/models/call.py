"""Call log models for AIDN."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CallLogBase(BaseModel):
    """Base call log model."""
    lead_id: UUID
    agent_id: UUID
    call_sid: Optional[str] = None  # Twilio Call SID
    outcome: Optional[str] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    notes: Optional[str] = None


class CallCreate(CallLogBase):
    """Model for creating a new call log."""
    started_at: datetime = datetime.now()
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None


class CallLog(CallLogBase):
    """Complete call log model."""
    id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    class Config:
        from_attributes = True

    @property
    def is_completed(self) -> bool:
        """Check if call is completed."""
        return self.ended_at is not None

    @property
    def call_duration_minutes(self) -> Optional[float]:
        """Get call duration in minutes."""
        if self.duration_seconds:
            return self.duration_seconds / 60.0
        return None