"""Database repositories for AIDN."""

import logging
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from ..models import Lead, AgentProfile, AppointmentSlot, CallLog
from .connection import DatabaseManager

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository class with common functionality."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager


class LeadRepository(BaseRepository):
    """Repository for lead operations."""

    async def get_lead_by_id(self, lead_id: UUID) -> Optional[Lead]:
        """Get a lead by ID."""
        query = """
        SELECT * FROM leads WHERE id = $1 AND is_active = true
        """
        row = await self.db.fetchrow(query, lead_id)
        return Lead.model_validate(dict(row)) if row else None

    async def get_leads_for_calling(self, agent_id: UUID, limit: int = 10) -> List[Lead]:
        """Get leads ready for calling by an agent."""
        query = """
        SELECT * FROM leads
        WHERE agent_id = $1
          AND is_active = true
          AND call_outcome IN ('fresh', 'no_answer', 'callback')
          AND (next_call_at IS NULL OR next_call_at <= NOW())
        ORDER BY
          CASE call_outcome
            WHEN 'fresh' THEN 1
            WHEN 'callback' THEN 2
            WHEN 'no_answer' THEN 3
          END,
          created_at ASC
        LIMIT $2
        """
        rows = await self.db.fetch(query, agent_id, limit)
        return [Lead.model_validate(dict(row)) for row in rows]

    async def update_lead_outcome(self, lead_id: UUID, outcome: str, next_call_at: Optional[datetime] = None) -> bool:
        """Update lead call outcome and next call time."""
        query = """
        UPDATE leads
        SET call_outcome = $2,
            last_called_at = NOW(),
            call_count = call_count + 1,
            next_call_at = $3
        WHERE id = $1
        """
        result = await self.db.execute(query, lead_id, outcome, next_call_at)
        return "UPDATE 1" in result

    async def create_lead(self, lead_data: dict) -> Lead:
        """Create a new lead."""
        query = """
        INSERT INTO leads (
            first_name, last_name, phone, address, city, county, state,
            zip_code, lead_type, lead_source, agent_id, created_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
        ) RETURNING *
        """
        row = await self.db.fetchrow(
            query,
            lead_data['first_name'],
            lead_data['last_name'],
            lead_data['phone'],
            lead_data.get('address'),
            lead_data.get('city'),
            lead_data.get('county'),
            lead_data.get('state'),
            lead_data.get('zip_code'),
            lead_data.get('lead_type'),
            lead_data.get('lead_source'),
            lead_data.get('agent_id'),
            lead_data.get('created_at', datetime.now())
        )
        return Lead.model_validate(dict(row))


class AgentRepository(BaseRepository):
    """Repository for agent operations."""

    async def get_agent_by_id(self, agent_id: UUID) -> Optional[AgentProfile]:
        """Get an agent by ID."""
        query = """
        SELECT * FROM agent_profiles WHERE id = $1 AND is_active = true
        """
        row = await self.db.fetchrow(query, agent_id)
        return AgentProfile.model_validate(dict(row)) if row else None

    async def get_active_agents(self) -> List[AgentProfile]:
        """Get all active agents."""
        query = """
        SELECT * FROM agent_profiles WHERE is_active = true ORDER BY agent_name
        """
        rows = await self.db.fetch(query)
        return [AgentProfile.model_validate(dict(row)) for row in rows]

    async def is_agent_available_for_calling(self, agent_id: UUID) -> bool:
        """Check if agent is available for calling now."""
        query = """
        SELECT av.is_available, av.calling_start_time, av.calling_end_time
        FROM agent_availability av
        WHERE av.agent_id = $1
          AND av.day_of_week = EXTRACT(DOW FROM NOW())
          AND av.is_available = true
          AND NOW()::time BETWEEN av.calling_start_time AND av.calling_end_time
        """
        row = await self.db.fetchrow(query, agent_id)
        return row is not None

    async def get_agent_daily_appointment_limit(self, agent_id: UUID) -> int:
        """Get agent's appointment limit for today."""
        query = """
        SELECT max_appointments
        FROM agent_availability
        WHERE agent_id = $1
          AND day_of_week = EXTRACT(DOW FROM NOW())
          AND is_available = true
        """
        result = await self.db.fetchval(query, agent_id)
        return result or 0


class AppointmentRepository(BaseRepository):
    """Repository for appointment operations."""

    async def get_available_slots(self, agent_id: UUID, start_date: date, end_date: date) -> List[AppointmentSlot]:
        """Get available appointment slots for an agent in date range."""
        query = """
        SELECT * FROM appointment_slots
        WHERE agent_id = $1
          AND date BETWEEN $2 AND $3
          AND status = 'available'
        ORDER BY date, time
        """
        rows = await self.db.fetch(query, agent_id, start_date, end_date)
        return [AppointmentSlot.model_validate(dict(row)) for row in rows]

    async def book_slot(self, slot_id: UUID, lead_id: UUID) -> bool:
        """Book an appointment slot for a lead (atomic operation)."""
        query = """
        SELECT success, slot_id FROM book_appointment($1, $2)
        """
        result = await self.db.fetchrow(query, slot_id, lead_id)
        return result['success'] if result else False

    async def get_agent_appointments_today(self, agent_id: UUID) -> int:
        """Get count of booked appointments for agent today."""
        query = """
        SELECT COUNT(*) FROM appointment_slots
        WHERE agent_id = $1
          AND date = CURRENT_DATE
          AND status IN ('booked', 'completed')
        """
        return await self.db.fetchval(query, agent_id) or 0

    async def generate_slots_for_agent(self, agent_id: UUID, start_date: date, end_date: date) -> int:
        """Generate appointment slots for an agent using database function."""
        query = """
        SELECT generate_appointment_slots($1, $2, $3)
        """
        return await self.db.fetchval(query, agent_id, start_date, end_date) or 0


class CallLogRepository(BaseRepository):
    """Repository for call log operations."""

    async def create_call_log(self, call_data: dict) -> CallLog:
        """Create a new call log entry."""
        query = """
        INSERT INTO call_logs (
            lead_id, agent_id, call_sid, started_at, ended_at,
            duration_seconds, outcome, recording_url, transcript, notes
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
        ) RETURNING *
        """
        row = await self.db.fetchrow(
            query,
            call_data['lead_id'],
            call_data['agent_id'],
            call_data.get('call_sid'),
            call_data.get('started_at', datetime.now()),
            call_data.get('ended_at'),
            call_data.get('duration_seconds'),
            call_data.get('outcome'),
            call_data.get('recording_url'),
            call_data.get('transcript'),
            call_data.get('notes')
        )
        return CallLog.model_validate(dict(row))

    async def update_call_log(self, call_id: UUID, update_data: dict) -> bool:
        """Update an existing call log."""
        # Build dynamic update query based on provided fields
        update_fields = []
        values = []
        param_count = 1

        for field, value in update_data.items():
            if field in ['ended_at', 'duration_seconds', 'outcome', 'recording_url', 'transcript', 'notes']:
                update_fields.append(f"{field} = ${param_count + 1}")
                values.append(value)
                param_count += 1

        if not update_fields:
            return False

        query = f"""
        UPDATE call_logs
        SET {', '.join(update_fields)}
        WHERE id = $1
        """
        result = await self.db.execute(query, call_id, *values)
        return "UPDATE 1" in result

    async def get_call_logs_for_lead(self, lead_id: UUID) -> List[CallLog]:
        """Get all call logs for a lead."""
        query = """
        SELECT * FROM call_logs
        WHERE lead_id = $1
        ORDER BY started_at DESC
        """
        rows = await self.db.fetch(query, lead_id)
        return [CallLog.model_validate(dict(row)) for row in rows]

    async def get_call_logs_by_sid(self, call_sid: str) -> List[CallLog]:
        """Get call logs by Twilio SID."""
        query = """
        SELECT * FROM call_logs
        WHERE call_sid = $1
        ORDER BY started_at DESC
        """
        rows = await self.db.fetch(query, call_sid)
        return [CallLog.model_validate(dict(row)) for row in rows]