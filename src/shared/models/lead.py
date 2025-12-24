"""Lead models for AIDN."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LeadType(str, Enum):
    """Types of insurance leads."""
    FINAL_EXPENSE = "final_expense"
    TERM_LIFE = "term_life"
    WHOLE_LIFE = "whole_life"
    MORTGAGE_PROTECTION = "mortgage_protection"


class CallOutcome(str, Enum):
    """Possible outcomes of a call attempt."""
    FRESH = "fresh"
    NO_ANSWER = "no_answer"
    NOT_INTERESTED = "not_interested"
    BOOKED = "booked"
    CALLBACK = "callback"
    DISCONNECTED = "disconnected"
    WRONG_NUMBER = "wrong_number"
    DNC = "dnc"  # Do Not Call


class LeadBase(BaseModel):
    """Base lead model with common fields."""
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    phone: str = Field(..., max_length=20)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    county: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=10)
    zip_code: Optional[str] = Field(None, max_length=10)
    lead_type: Optional[LeadType] = None
    lead_source: Optional[str] = Field(None, max_length=100)


class LeadCreate(LeadBase):
    """Model for creating a new lead."""
    agent_id: Optional[UUID] = None
    created_at: Optional[datetime] = None


class LeadUpdate(BaseModel):
    """Model for updating an existing lead."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    county: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=10)
    zip_code: Optional[str] = Field(None, max_length=10)
    lead_type: Optional[LeadType] = None
    lead_source: Optional[str] = Field(None, max_length=100)
    agent_id: Optional[UUID] = None
    call_outcome: Optional[CallOutcome] = None
    next_call_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class Lead(LeadBase):
    """Complete lead model with all database fields."""
    id: UUID
    agent_id: Optional[UUID] = None
    created_at: datetime
    uploaded_at: datetime
    last_called_at: Optional[datetime] = None
    next_call_at: Optional[datetime] = None
    call_count: int = 0
    call_outcome: CallOutcome = CallOutcome.FRESH
    is_active: bool = True

    class Config:
        from_attributes = True

    @property
    def full_name(self) -> str:
        """Return the lead's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def lead_age_days(self) -> int:
        """Return the age of the lead in days."""
        return (datetime.now() - self.created_at).days

    @property
    def needs_retry(self) -> bool:
        """Check if lead needs to be called again."""
        if not self.is_active or self.call_outcome in [CallOutcome.DNC, CallOutcome.DISCONNECTED, CallOutcome.WRONG_NUMBER]:
            return False

        if self.call_outcome == CallOutcome.FRESH:
            return True

        if self.next_call_at and datetime.now() >= self.next_call_at:
            return True

        return False