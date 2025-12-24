"""
AIDN Database Migration Script
==============================

Migrates existing database schemas to the unified AIDN specification.
"""

import asyncio
import logging
import os
from datetime import datetime, time
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .connection import DatabaseManager

logger = logging.getLogger(__name__)


class AIDNMigration:
    """Handles database migrations for AIDN."""

    def __init__(self, database_url: Optional[str] = None):
        self.db_manager = DatabaseManager(database_url)

    async def run_migration(self, drop_existing: bool = False):
        """Run the complete migration process."""
        logger.info("Starting AIDN database migration...")

        try:
            await self.db_manager.connect()

            if drop_existing:
                logger.warning("Dropping existing tables...")
                await self._drop_existing_tables()

            # Create new schema
            logger.info("Creating AIDN schema...")
            await self.db_manager.initialize_schema()

            # Create sample data for testing
            logger.info("Creating sample data...")
            await self._create_sample_data()

            logger.info("Migration completed successfully!")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            await self.db_manager.disconnect()

    async def _drop_existing_tables(self):
        """Drop existing tables (use with caution)."""
        drop_queries = [
            "DROP TABLE IF EXISTS call_logs CASCADE",
            "DROP TABLE IF EXISTS appointment_slots CASCADE",
            "DROP TABLE IF EXISTS agent_territories CASCADE",
            "DROP TABLE IF EXISTS agent_availability CASCADE",
            "DROP TABLE IF EXISTS leads CASCADE",
            "DROP TABLE IF EXISTS agent_profiles CASCADE",
            "DROP FUNCTION IF EXISTS book_appointment(UUID, UUID) CASCADE",
            "DROP FUNCTION IF EXISTS generate_appointment_slots(UUID, DATE, DATE) CASCADE"
        ]

        for query in drop_queries:
            await self.db_manager.execute(query)

    async def _create_sample_data(self):
        """Create sample data for testing and demo."""
        # Create sample agent
        agent_id = await self._create_sample_agent()

        # Create sample leads
        await self._create_sample_leads(agent_id)

        # Create agent availability
        await self._create_agent_availability(agent_id)

        # Generate appointment slots
        await self._generate_sample_slots(agent_id)

    async def _create_sample_agent(self):
        """Create a sample agent profile."""
        query = """
        INSERT INTO agent_profiles (
            agent_name, phone, email, physical_description, car_description,
            earliest_appointment_time, latest_appointment_time, slot_gap_hours
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8
        ) RETURNING id
        """

        result = await self.db_manager.fetchrow(
            query,
            "John Smith",
            "+1-555-0123",
            "john.smith@aidn.demo",
            "Male, 6 feet tall, brown hair, wearing a dark suit",
            "Silver Honda Accord, license plate ABC-1234",
            time(9, 0),
            time(18, 0),
            2
        )

        agent_id = result['id']
        logger.info(f"Created sample agent with ID: {agent_id}")
        return agent_id

    async def _create_sample_leads(self, agent_id):
        """Create sample leads for testing."""
        sample_leads = [
            {
                "first_name": "Mary",
                "last_name": "Johnson",
                "phone": "+1-555-0001",
                "address": "123 Main St",
                "city": "Chicago",
                "county": "Cook",
                "state": "IL",
                "zip_code": "60601",
                "lead_type": "final_expense",
                "lead_source": "online_form"
            },
            {
                "first_name": "Robert",
                "last_name": "Davis",
                "phone": "+1-555-0002",
                "address": "456 Oak Ave",
                "city": "Springfield",
                "county": "Sangamon",
                "state": "IL",
                "zip_code": "62701",
                "lead_type": "term_life",
                "lead_source": "referral"
            },
            {
                "first_name": "Jennifer",
                "last_name": "Wilson",
                "phone": "+1-555-0003",
                "address": "789 Pine St",
                "city": "Peoria",
                "county": "Peoria",
                "state": "IL",
                "zip_code": "61601",
                "lead_type": "whole_life",
                "lead_source": "mail_campaign"
            },
            {
                "first_name": "Michael",
                "last_name": "Brown",
                "phone": "+1-555-0004",
                "address": "321 Elm Dr",
                "city": "Rockford",
                "county": "Winnebago",
                "state": "IL",
                "zip_code": "61101",
                "lead_type": "mortgage_protection",
                "lead_source": "online_form"
            },
            {
                "first_name": "Sarah",
                "last_name": "Miller",
                "phone": "+1-555-0005",
                "address": "654 Maple Ln",
                "city": "Naperville",
                "county": "DuPage",
                "state": "IL",
                "zip_code": "60540",
                "lead_type": "final_expense",
                "lead_source": "telemarketing"
            }
        ]

        query = """
        INSERT INTO leads (
            first_name, last_name, phone, address, city, county, state,
            zip_code, lead_type, lead_source, agent_id, created_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
        )
        """

        for lead in sample_leads:
            await self.db_manager.execute(
                query,
                lead["first_name"],
                lead["last_name"],
                lead["phone"],
                lead["address"],
                lead["city"],
                lead["county"],
                lead["state"],
                lead["zip_code"],
                lead["lead_type"],
                lead["lead_source"],
                agent_id,
                datetime.now()
            )

        logger.info(f"Created {len(sample_leads)} sample leads")

    async def _create_agent_availability(self, agent_id):
        """Create agent availability schedule."""
        # Monday through Friday, 9 AM to 12 PM calling, max 4 appointments
        availability_data = [
            (1, True, time(9, 0), time(12, 0), 4, time(9, 0)),  # Monday
            (2, True, time(9, 0), time(12, 0), 4, time(9, 0)),  # Tuesday
            (3, False, None, None, 0, None),                     # Wednesday (off)
            (4, True, time(9, 0), time(12, 0), 5, time(9, 0)),  # Thursday
            (5, True, time(9, 0), time(12, 0), 3, time(9, 0)),  # Friday
            (6, True, time(10, 0), time(13, 0), 2, time(10, 0)), # Saturday
            (0, False, None, None, 0, None)                      # Sunday (off)
        ]

        query = """
        INSERT INTO agent_availability (
            agent_id, day_of_week, is_available, calling_start_time,
            calling_end_time, max_appointments, first_appointment_time
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7
        )
        """

        for day_data in availability_data:
            await self.db_manager.execute(query, agent_id, *day_data)

        logger.info("Created agent availability schedule")

    async def _generate_sample_slots(self, agent_id):
        """Generate appointment slots for the next week."""
        from datetime import date, timedelta

        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        # Use the database function to generate slots
        query = "SELECT generate_appointment_slots($1, $2, $3)"
        slots_created = await self.db_manager.fetchval(query, agent_id, start_date, end_date)

        logger.info(f"Generated {slots_created} appointment slots")

    async def check_migration_status(self):
        """Check if migration has been completed."""
        try:
            await self.db_manager.connect()

            # Check if main tables exist
            query = """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name IN ('leads', 'agent_profiles', 'appointment_slots')
            """
            table_count = await self.db_manager.fetchval(query)

            if table_count >= 3:
                # Check if sample data exists
                lead_count = await self.db_manager.fetchval("SELECT COUNT(*) FROM leads")
                agent_count = await self.db_manager.fetchval("SELECT COUNT(*) FROM agent_profiles")

                return {
                    "migrated": True,
                    "tables_exist": True,
                    "sample_data": lead_count > 0 and agent_count > 0,
                    "lead_count": lead_count,
                    "agent_count": agent_count
                }
            else:
                return {
                    "migrated": False,
                    "tables_exist": False,
                    "sample_data": False,
                    "lead_count": 0,
                    "agent_count": 0
                }

        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            return {
                "migrated": False,
                "error": str(e)
            }
        finally:
            await self.db_manager.disconnect()


async def main():
    """Main migration function."""
    import argparse

    parser = argparse.ArgumentParser(description="AIDN Database Migration")
    parser.add_argument("--drop", action="store_true", help="Drop existing tables before migration")
    parser.add_argument("--check", action="store_true", help="Check migration status")
    parser.add_argument("--database-url", help="Database URL (overrides environment)")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    migration = AIDNMigration(args.database_url)

    if args.check:
        status = await migration.check_migration_status()
        print("Migration Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
    else:
        await migration.run_migration(drop_existing=args.drop)


if __name__ == "__main__":
    asyncio.run(main())