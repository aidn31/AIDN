"""
Google Calendar Integration for AIDN
=====================================

Creates calendar events for booked appointments.
Fire-and-forget: failures are logged but don't block booking.
"""

import logging
import os
from datetime import date, time, datetime, timedelta
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Google Calendar API scope
SCOPES = ['https://www.googleapis.com/auth/calendar.events']


def create_calendar_service():
    """
    Create and return a Google Calendar API service.

    Returns:
        Google Calendar service object, or None if setup fails
    """
    credentials_path = os.getenv('GOOGLE_CALENDAR_CREDENTIALS_PATH')

    if not credentials_path:
        logger.warning("GOOGLE_CALENDAR_CREDENTIALS_PATH not set")
        return None

    if not os.path.exists(credentials_path):
        logger.warning(f"Credentials file not found: {credentials_path}")
        return None

    try:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES
        )
        service = build('calendar', 'v3', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Failed to create calendar service: {e}")
        return None


def create_appointment_event(
    lead_name: str,
    lead_phone: str,
    lead_address: str,
    appointment_date: date,
    appointment_time: time,
    agent_name: str,
    confirmation_code: str,
    duration_hours: int = 1
) -> Optional[str]:
    """
    Create a Google Calendar event for an appointment.

    Args:
        lead_name: Full name of the lead
        lead_phone: Lead's phone number
        lead_address: Full address for the appointment
        appointment_date: Date of appointment
        appointment_time: Time of appointment
        agent_name: Name of the agent attending
        confirmation_code: AIDN confirmation code
        duration_hours: Length of appointment in hours (default: 1)

    Returns:
        Event ID if successful, None if failed
    """
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID')

    if not calendar_id:
        logger.warning("GOOGLE_CALENDAR_ID not set - skipping calendar event")
        return None

    service = create_calendar_service()
    if not service:
        return None

    try:
        # Combine date and time into datetime
        start_datetime = datetime.combine(appointment_date, appointment_time)
        end_datetime = start_datetime + timedelta(hours=duration_hours)

        # Format for Google Calendar API (ISO format with timezone)
        # Using local timezone assumption - adjust if needed
        event = {
            'summary': f'AIDN: {lead_name}',
            'location': lead_address,
            'description': (
                f'AIDN Appointment\n'
                f'─────────────────\n'
                f'Lead: {lead_name}\n'
                f'Phone: {lead_phone}\n'
                f'Agent: {agent_name}\n'
                f'Confirmation Code: {confirmation_code}\n'
                f'─────────────────\n'
                f'Booked by AIDN Voice Agent'
            ),
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'America/Chicago',  # Adjust to your timezone
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/Chicago',
            },
            'reminders': {
                'useDefault': True,
            },
        }

        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()

        event_id = created_event.get('id')
        event_link = created_event.get('htmlLink')

        logger.info(f"Calendar event created: {event_id}")
        logger.debug(f"Calendar event link: {event_link}")

        return event_id

    except HttpError as e:
        logger.error(f"Google Calendar API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to create calendar event: {e}")
        return None
