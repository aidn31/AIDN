"""
Simple synchronous database helper for Streamlit dashboard.
Avoids async/sync conflicts in Streamlit.
"""

import psycopg2
import psycopg2.extras
import os
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class StreamlitDatabase:
    """Simple synchronous database connection for Streamlit."""

    def __init__(self):
        self.connection_string = os.getenv("DATABASE_URL")
        if not self.connection_string:
            raise ValueError("DATABASE_URL environment variable is required")

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dicts."""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(query, params or ())
                    if cur.description:  # Query returns results
                        return [dict(row) for row in cur.fetchall()]
                    return []
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise

    def execute_single(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute a query and return single result as dict."""
        results = self.execute_query(query, params)
        return results[0] if results else None

    def get_agents(self) -> List[Dict[str, Any]]:
        """Get all active agents."""
        query = """
        SELECT id, agent_name, phone, email, physical_description, car_description
        FROM agent_profiles
        WHERE is_active = true
        """
        return self.execute_query(query)

    def get_leads_for_agent(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get leads for an agent."""
        query = """
        SELECT id, first_name, last_name, phone, city, state, county,
               lead_type, lead_source, call_outcome, call_count,
               created_at, last_called_at, next_call_at
        FROM leads
        WHERE agent_id = %s AND is_active = true
        ORDER BY
            CASE call_outcome
                WHEN 'fresh' THEN 1
                WHEN 'callback' THEN 2
                WHEN 'no_answer' THEN 3
                ELSE 4
            END,
            created_at DESC
        LIMIT %s
        """
        return self.execute_query(query, (agent_id, limit))

    def get_appointments_for_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get appointments for an agent."""
        query = """
        SELECT a.id, a.date, a.time, a.status,
               l.first_name, l.last_name, l.phone
        FROM appointment_slots a
        LEFT JOIN leads l ON a.lead_id = l.id
        WHERE a.agent_id = %s AND a.status != 'available'
        ORDER BY a.date, a.time
        """
        return self.execute_query(query, (agent_id,))

    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            self.execute_query("SELECT 1")
            return True
        except:
            return False