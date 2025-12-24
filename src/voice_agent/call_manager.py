"""
AIDN Call Manager
=================

Manages outbound calls using Twilio and LiveKit integration.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from ..shared.database import DatabaseManager, LeadRepository, CallLogRepository
from ..shared.models import Lead, CallOutcome

logger = logging.getLogger(__name__)


class CallManager:
    """Manages outbound calling for AIDN."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.lead_repo = LeadRepository(db_manager)
        self.call_log_repo = CallLogRepository(db_manager)

        # Initialize Twilio client
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

        if not all([account_sid, auth_token, self.twilio_number]):
            raise ValueError("Missing required Twilio configuration")

        self.twilio_client = Client(account_sid, auth_token)

    async def get_next_lead_to_call(self, agent_id: UUID) -> Optional[Lead]:
        """Get the next lead that should be called for an agent."""
        leads = await self.lead_repo.get_leads_for_calling(agent_id, limit=1)
        return leads[0] if leads else None

    async def initiate_call(self, lead: Lead, agent_id: UUID) -> Optional[str]:
        """Initiate outbound call using Twilio."""
        try:
            # Validate phone number format (basic check)
            phone = self._format_phone_number(lead.phone)
            if not phone:
                logger.error(f"Invalid phone number for lead {lead.id}: {lead.phone}")
                return None

            # Create LiveKit room for the call
            room_name = f"aidn-call-{lead.id}-{datetime.now().timestamp()}"

            # Configure Twilio call with LiveKit webhook
            livekit_webhook_url = self._get_livekit_webhook_url(room_name, lead.id, agent_id)

            call = self.twilio_client.calls.create(
                url=livekit_webhook_url,
                to=phone,
                from_=self.twilio_number,
                timeout=20,  # Ring timeout in seconds
                record=True,  # Enable call recording
                method="POST"
            )

            # Log call initiation
            await self.call_log_repo.create_call_log({
                "lead_id": lead.id,
                "agent_id": agent_id,
                "call_sid": call.sid,
                "started_at": datetime.now(),
                "outcome": "initiated"
            })

            logger.info(f"Initiated call {call.sid} to {phone} for lead {lead.id}")
            return call.sid

        except TwilioRestException as e:
            logger.error(f"Twilio error calling lead {lead.id}: {e}")
            await self._handle_call_failure(lead.id, agent_id, "twilio_error")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling lead {lead.id}: {e}")
            await self._handle_call_failure(lead.id, agent_id, "system_error")
            return None

    async def handle_call_completed(self, call_sid: str, outcome: str, duration: Optional[int] = None):
        """Handle call completion and update lead status."""
        try:
            # Find the call log
            call_logs = await self.call_log_repo.get_call_logs_by_sid(call_sid)
            if not call_logs:
                logger.warning(f"No call log found for call_sid {call_sid}")
                return

            call_log = call_logs[0]
            lead = await self.lead_repo.get_lead_by_id(call_log.lead_id)
            if not lead:
                logger.error(f"Lead not found for call {call_sid}")
                return

            # Update call log
            await self.call_log_repo.update_call_log(call_log.id, {
                "ended_at": datetime.now(),
                "duration_seconds": duration,
                "outcome": outcome
            })

            # Update lead based on outcome
            await self._update_lead_after_call(lead, outcome)

            logger.info(f"Call {call_sid} completed with outcome: {outcome}")

        except Exception as e:
            logger.error(f"Error handling call completion for {call_sid}: {e}")

    async def retry_lead_if_needed(self, lead: Lead) -> bool:
        """Check if lead should be retried and schedule next call."""
        if not lead.needs_retry:
            return False

        # Implement 3-attempt retry logic
        if lead.call_count < 3 and lead.call_outcome in [CallOutcome.FRESH, CallOutcome.NO_ANSWER]:
            # Immediate retry for fresh leads or first no answers
            if lead.call_count == 0:
                next_call_time = datetime.now()
            else:
                # Wait 2 hours between retries
                next_call_time = datetime.now() + timedelta(hours=2)

            await self.lead_repo.update_lead_outcome(
                lead_id=lead.id,
                outcome=CallOutcome.NO_ANSWER,
                next_call_at=next_call_time
            )
            return True

        elif lead.call_outcome == CallOutcome.NOT_INTERESTED:
            # Retry not interested leads after 7 days
            next_call_time = datetime.now() + timedelta(days=7)
            await self.lead_repo.update_lead_outcome(
                lead_id=lead.id,
                outcome=CallOutcome.NOT_INTERESTED,
                next_call_at=next_call_time
            )
            return True

        return False

    def _format_phone_number(self, phone: str) -> Optional[str]:
        """Format phone number for Twilio (E.164 format)."""
        # Remove all non-digit characters
        digits = ''.join(c for c in phone if c.isdigit())

        # Handle US phone numbers
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        else:
            logger.warning(f"Unsupported phone number format: {phone}")
            return None

    def _get_livekit_webhook_url(self, room_name: str, lead_id: UUID, agent_id: UUID) -> str:
        """Generate LiveKit webhook URL for Twilio."""
        base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL", "https://your-webhook-url.com")
        return f"{base_url}/twilio-webhook?room={room_name}&lead_id={lead_id}&agent_id={agent_id}"

    async def _handle_call_failure(self, lead_id: UUID, agent_id: UUID, error_type: str):
        """Handle call failure scenarios."""
        # Log the failure
        await self.call_log_repo.create_call_log({
            "lead_id": lead_id,
            "agent_id": agent_id,
            "started_at": datetime.now(),
            "ended_at": datetime.now(),
            "outcome": f"failed_{error_type}"
        })

        # Update lead to retry later
        await self.lead_repo.update_lead_outcome(
            lead_id=lead_id,
            outcome=CallOutcome.NO_ANSWER,
            next_call_at=datetime.now() + timedelta(minutes=30)
        )

    async def _update_lead_after_call(self, lead: Lead, outcome: str):
        """Update lead status after call completion."""
        # Map call outcomes to lead outcomes
        outcome_mapping = {
            "no_answer": CallOutcome.NO_ANSWER,
            "busy": CallOutcome.NO_ANSWER,
            "failed": CallOutcome.NO_ANSWER,
            "completed": CallOutcome.BOOKED,  # Assume completed calls resulted in appointments
            "not_interested": CallOutcome.NOT_INTERESTED,
            "callback": CallOutcome.CALLBACK,
            "do_not_call": CallOutcome.DNC,
            "wrong_number": CallOutcome.WRONG_NUMBER,
            "disconnected": CallOutcome.DISCONNECTED
        }

        lead_outcome = outcome_mapping.get(outcome, CallOutcome.NO_ANSWER)

        # Set next call time based on outcome
        next_call_at = None
        if lead_outcome == CallOutcome.NO_ANSWER and lead.call_count < 3:
            next_call_at = datetime.now() + timedelta(hours=2)
        elif lead_outcome == CallOutcome.NOT_INTERESTED:
            next_call_at = datetime.now() + timedelta(days=7)
        elif lead_outcome == CallOutcome.CALLBACK:
            next_call_at = datetime.now() + timedelta(hours=4)  # Default callback time

        await self.lead_repo.update_lead_outcome(
            lead_id=lead.id,
            outcome=lead_outcome,
            next_call_at=next_call_at
        )