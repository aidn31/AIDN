"""
Test AIDN voice agent functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime

from src.voice_agent.aidn_agent import AIDNVoiceAgent
from src.voice_agent.objection_handler import ObjectionHandler
from src.shared.models import Lead, LeadType, CallOutcome


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager."""
    return Mock()


@pytest.fixture
def mock_lead():
    """Create a mock lead for testing."""
    return Lead(
        id=uuid4(),
        first_name="John",
        last_name="Doe",
        phone="+1-555-0123",
        city="Chicago",
        state="IL",
        lead_type=LeadType.FINAL_EXPENSE,
        lead_source="online_form",
        created_at=datetime.now(),
        uploaded_at=datetime.now(),
        call_count=0,
        call_outcome=CallOutcome.FRESH,
        is_active=True
    )


@pytest.fixture
def mock_agent_id():
    """Create a mock agent ID."""
    return uuid4()


class TestAIDNVoiceAgent:
    """Test AIDN voice agent functionality."""

    def test_agent_initialization(self, mock_db_manager):
        """Test that the agent initializes correctly."""
        agent = AIDNVoiceAgent(mock_db_manager)

        assert agent.db_manager == mock_db_manager
        assert agent.current_lead is None
        assert agent.current_agent_id is None
        assert "insurance" in agent.instructions.lower()

    @pytest.mark.asyncio
    async def test_set_call_context(self, mock_db_manager, mock_lead, mock_agent_id):
        """Test setting call context."""
        agent = AIDNVoiceAgent(mock_db_manager)

        await agent.set_call_context(mock_lead, mock_agent_id)

        assert agent.current_lead == mock_lead
        assert agent.current_agent_id == mock_agent_id

    @pytest.mark.asyncio
    async def test_mark_do_not_call(self, mock_db_manager, mock_lead, mock_agent_id):
        """Test marking a lead as do not call."""
        # Mock the lead repository
        mock_lead_repo = AsyncMock()
        mock_lead_repo.update_lead_outcome = AsyncMock(return_value=True)

        agent = AIDNVoiceAgent(mock_db_manager)
        agent.lead_repo = mock_lead_repo
        agent.current_lead = mock_lead

        # Mock the run context
        mock_context = Mock()

        result = await agent.mark_do_not_call(mock_context)

        # Verify the outcome was updated
        mock_lead_repo.update_lead_outcome.assert_called_once_with(
            lead_id=mock_lead.id,
            outcome="dnc"
        )

        assert "removed" in result.lower()

    @pytest.mark.asyncio
    async def test_get_available_appointments_no_agent(self, mock_db_manager):
        """Test getting appointments when no agent is set."""
        agent = AIDNVoiceAgent(mock_db_manager)
        mock_context = Mock()

        result = await agent.get_available_appointments(mock_context)

        assert "trouble accessing" in result.lower()

    @pytest.mark.asyncio
    async def test_book_appointment_success(self, mock_db_manager, mock_lead, mock_agent_id):
        """Test successful appointment booking."""
        # Mock repositories
        mock_appointment_repo = AsyncMock()
        mock_lead_repo = AsyncMock()

        # Mock available slot
        mock_slot = Mock()
        mock_slot.id = uuid4()
        mock_slot.date = datetime.now().date()
        mock_slot.time = datetime.now().time()

        mock_appointment_repo.get_available_slots = AsyncMock(return_value=[mock_slot])
        mock_appointment_repo.book_slot = AsyncMock(return_value=True)
        mock_lead_repo.update_lead_outcome = AsyncMock(return_value=True)

        agent = AIDNVoiceAgent(mock_db_manager)
        agent.appointment_repo = mock_appointment_repo
        agent.lead_repo = mock_lead_repo
        agent.current_lead = mock_lead
        agent.current_agent_id = mock_agent_id

        mock_context = Mock()

        result = await agent.book_appointment(mock_context, "tomorrow", "2pm")

        # Verify appointment was booked
        mock_appointment_repo.book_slot.assert_called_once()
        mock_lead_repo.update_lead_outcome.assert_called_once()

        assert "scheduled" in result.lower()


class TestObjectionHandler:
    """Test objection handling functionality."""

    def test_objection_handler_initialization(self):
        """Test objection handler initializes correctly."""
        handler = ObjectionHandler()
        assert handler is not None

    @pytest.mark.asyncio
    async def test_handle_not_interested(self, mock_lead):
        """Test handling 'not interested' objection."""
        handler = ObjectionHandler()

        response = await handler.handle_objection(
            "not_interested",
            "I'm not interested",
            mock_lead
        )

        assert "understand" in response.lower()
        assert "options" in response.lower()

    @pytest.mark.asyncio
    async def test_handle_how_did_you_get_number(self, mock_lead):
        """Test handling 'how did you get my number' objection."""
        handler = ObjectionHandler()

        response = await handler.handle_objection(
            "how_did_you_get_my_number",
            "How did you get my number?",
            mock_lead
        )

        assert "filled out a form" in response.lower()
        assert "requesting information" in response.lower()

    @pytest.mark.asyncio
    async def test_handle_is_this_scam(self, mock_lead):
        """Test handling 'is this a scam' objection."""
        handler = ObjectionHandler()

        response = await handler.handle_objection(
            "is_this_a_scam",
            "Is this a scam?",
            mock_lead
        )

        assert "legitimate" in response.lower()
        assert "understand your concern" in response.lower()

    @pytest.mark.asyncio
    async def test_handle_busy_right_now(self, mock_lead):
        """Test handling 'busy right now' objection."""
        handler = ObjectionHandler()

        response = await handler.handle_objection(
            "im_busy_right_now",
            "I'm busy right now",
            mock_lead
        )

        assert "30 seconds" in response.lower()
        assert "appointment" in response.lower()

    @pytest.mark.asyncio
    async def test_handle_already_have_insurance(self, mock_lead):
        """Test handling 'already have insurance' objection."""
        handler = ObjectionHandler()

        response = await handler.handle_objection(
            "i_already_have_insurance",
            "I already have insurance",
            mock_lead
        )

        assert "great" in response.lower()
        assert "gaps" in response.lower()

    def test_classify_objection(self):
        """Test objection classification."""
        handler = ObjectionHandler()

        # Test various objection classifications
        test_cases = [
            ("I'm not interested", "not_interested"),
            ("How did you get my number?", "how_did_you_get_my_number"),
            ("Is this a scam?", "is_this_a_scam"),
            ("I'm busy right now", "im_busy_right_now"),
            ("I already have insurance", "i_already_have_insurance"),
            ("Just send me information", "send_me_information"),
            ("Something random", "unknown")
        ]

        for response, expected_classification in test_cases:
            classification = handler.classify_objection(response)
            assert classification == expected_classification


class TestLeadModel:
    """Test Lead model functionality."""

    def test_lead_full_name(self, mock_lead):
        """Test lead full name property."""
        assert mock_lead.full_name == "John Doe"

    def test_lead_age_days(self, mock_lead):
        """Test lead age calculation."""
        # Lead was just created, so age should be 0
        assert mock_lead.lead_age_days == 0

    def test_lead_needs_retry_fresh(self, mock_lead):
        """Test that fresh leads need retry."""
        assert mock_lead.needs_retry is True

    def test_lead_needs_retry_dnc(self, mock_lead):
        """Test that DNC leads don't need retry."""
        mock_lead.call_outcome = CallOutcome.DNC
        assert mock_lead.needs_retry is False

    def test_lead_needs_retry_disconnected(self, mock_lead):
        """Test that disconnected leads don't need retry."""
        mock_lead.call_outcome = CallOutcome.DISCONNECTED
        assert mock_lead.needs_retry is False

    def test_lead_needs_retry_inactive(self, mock_lead):
        """Test that inactive leads don't need retry."""
        mock_lead.is_active = False
        assert mock_lead.needs_retry is False