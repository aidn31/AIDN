"""
Test database functionality for AIDN.
"""

import pytest
import asyncio
from datetime import datetime, date, timedelta
from uuid import uuid4

from src.shared.database import DatabaseManager, LeadRepository, AgentRepository
from src.shared.models import Lead, LeadCreate, AgentProfile


@pytest.fixture
async def db_manager():
    """Create a test database manager."""
    # Use a test database or in-memory database for testing
    db_manager = DatabaseManager("postgresql://test:test@localhost:5432/aidn_test")
    await db_manager.connect()
    yield db_manager
    await db_manager.disconnect()


@pytest.fixture
async def sample_agent_id(db_manager):
    """Create a sample agent for testing."""
    query = """
    INSERT INTO agent_profiles (
        agent_name, phone, email
    ) VALUES ($1, $2, $3) RETURNING id
    """

    result = await db_manager.fetchrow(
        query, "Test Agent", "+1-555-TEST", "test@example.com"
    )
    return result['id']


class TestDatabaseConnection:
    """Test database connection and basic operations."""

    @pytest.mark.asyncio
    async def test_connection(self, db_manager):
        """Test that we can connect to the database."""
        result = await db_manager.fetchval("SELECT 1")
        assert result == 1

    @pytest.mark.asyncio
    async def test_schema_exists(self, db_manager):
        """Test that main tables exist."""
        tables_to_check = ['leads', 'agent_profiles', 'appointment_slots']

        for table in tables_to_check:
            query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = $1
            )
            """
            exists = await db_manager.fetchval(query, table)
            assert exists, f"Table {table} does not exist"


class TestLeadRepository:
    """Test lead repository operations."""

    @pytest.mark.asyncio
    async def test_create_lead(self, db_manager, sample_agent_id):
        """Test creating a new lead."""
        lead_repo = LeadRepository(db_manager)

        lead_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1-555-0123",
            "city": "Chicago",
            "state": "IL",
            "lead_type": "final_expense",
            "agent_id": sample_agent_id,
            "created_at": datetime.now()
        }

        lead = await lead_repo.create_lead(lead_data)

        assert lead.first_name == "John"
        assert lead.last_name == "Doe"
        assert lead.phone == "+1-555-0123"
        assert lead.agent_id == sample_agent_id

    @pytest.mark.asyncio
    async def test_get_lead_by_id(self, db_manager, sample_agent_id):
        """Test retrieving a lead by ID."""
        lead_repo = LeadRepository(db_manager)

        # Create a lead first
        lead_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+1-555-0456",
            "agent_id": sample_agent_id
        }

        created_lead = await lead_repo.create_lead(lead_data)

        # Retrieve the lead
        retrieved_lead = await lead_repo.get_lead_by_id(created_lead.id)

        assert retrieved_lead is not None
        assert retrieved_lead.id == created_lead.id
        assert retrieved_lead.first_name == "Jane"

    @pytest.mark.asyncio
    async def test_update_lead_outcome(self, db_manager, sample_agent_id):
        """Test updating lead call outcome."""
        lead_repo = LeadRepository(db_manager)

        # Create a lead
        lead_data = {
            "first_name": "Bob",
            "last_name": "Wilson",
            "phone": "+1-555-0789",
            "agent_id": sample_agent_id
        }

        lead = await lead_repo.create_lead(lead_data)

        # Update outcome
        success = await lead_repo.update_lead_outcome(
            lead_id=lead.id,
            outcome="booked"
        )

        assert success

        # Verify the update
        updated_lead = await lead_repo.get_lead_by_id(lead.id)
        assert updated_lead.call_outcome == "booked"
        assert updated_lead.call_count == 1

    @pytest.mark.asyncio
    async def test_get_leads_for_calling(self, db_manager, sample_agent_id):
        """Test getting leads ready for calling."""
        lead_repo = LeadRepository(db_manager)

        # Create several leads with different statuses
        test_leads = [
            {"first_name": "Fresh", "last_name": "Lead", "phone": "+1-555-1111"},
            {"first_name": "Callback", "last_name": "Lead", "phone": "+1-555-2222"},
        ]

        created_leads = []
        for lead_data in test_leads:
            lead_data["agent_id"] = sample_agent_id
            lead = await lead_repo.create_lead(lead_data)
            created_leads.append(lead)

        # Set one lead to callback status
        await lead_repo.update_lead_outcome(
            lead_id=created_leads[1].id,
            outcome="callback",
            next_call_at=datetime.now() - timedelta(minutes=10)  # Past time, ready to call
        )

        # Get leads for calling
        leads_to_call = await lead_repo.get_leads_for_calling(sample_agent_id, limit=10)

        assert len(leads_to_call) >= 2
        # Fresh leads should come first
        assert leads_to_call[0].call_outcome in ["fresh", "callback"]


class TestAgentRepository:
    """Test agent repository operations."""

    @pytest.mark.asyncio
    async def test_get_agent_by_id(self, db_manager, sample_agent_id):
        """Test retrieving an agent by ID."""
        agent_repo = AgentRepository(db_manager)

        agent = await agent_repo.get_agent_by_id(sample_agent_id)

        assert agent is not None
        assert agent.id == sample_agent_id
        assert agent.agent_name == "Test Agent"

    @pytest.mark.asyncio
    async def test_get_active_agents(self, db_manager):
        """Test getting all active agents."""
        agent_repo = AgentRepository(db_manager)

        agents = await agent_repo.get_active_agents()

        assert len(agents) >= 1  # At least our test agent
        assert all(agent.is_active for agent in agents)