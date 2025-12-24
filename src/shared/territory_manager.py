"""
AIDN Territory Management System
===============================

Handles multi-agent territory assignment, lead distribution, and conflict resolution.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from .database.connection import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class Territory:
    """Represents an agent's territory configuration."""
    id: str
    agent_id: str
    agent_name: str
    county: Optional[str]
    state: str
    zip_code: Optional[str]
    lead_types: List[str]
    priority: int = 1  # Higher number = higher priority in conflicts


@dataclass
class LeadAssignmentResult:
    """Result of lead assignment process."""
    lead_id: str
    assigned_agent_id: Optional[str]
    assigned_agent_name: Optional[str]
    reason: str
    conflicts: List[str] = None


class TerritoryManager:
    """Manages agent territories and lead assignments."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def assign_lead_to_agent(self, lead_id: str) -> LeadAssignmentResult:
        """
        Assign a lead to the best matching agent based on territory rules.

        Priority order:
        1. Exact county + state + lead_type match
        2. County + state match (any lead_type)
        3. State + lead_type match
        4. State match (any lead_type)
        5. Zip code match (if specified)
        6. Fallback to round-robin assignment
        """
        try:
            # Get lead details
            lead = await self.db.fetchrow("""
                SELECT id, county, state, zip_code, lead_type, first_name, last_name
                FROM leads WHERE id = $1
            """, lead_id)

            if not lead:
                return LeadAssignmentResult(
                    lead_id=lead_id,
                    assigned_agent_id=None,
                    assigned_agent_name=None,
                    reason="Lead not found"
                )

            # Get all active agent territories
            territories = await self.db.fetch("""
                SELECT t.id, t.agent_id, a.agent_name, t.county, t.state,
                       t.zip_code, t.lead_types
                FROM agent_territories t
                JOIN agent_profiles a ON t.agent_id = a.id
                WHERE a.is_active = true
                ORDER BY t.agent_id
            """)

            if not territories:
                return LeadAssignmentResult(
                    lead_id=lead_id,
                    assigned_agent_id=None,
                    assigned_agent_name=None,
                    reason="No active agents with territories found"
                )

            # Convert to Territory objects
            territory_objects = []
            for t in territories:
                territory_objects.append(Territory(
                    id=str(t['id']),
                    agent_id=str(t['agent_id']),
                    agent_name=t['agent_name'],
                    county=t['county'],
                    state=t['state'],
                    zip_code=t['zip_code'],
                    lead_types=t['lead_types'] or []
                ))

            # Find matching agents using priority rules
            matches = self._find_territory_matches(lead, territory_objects)

            if not matches:
                # Fallback: Round-robin assignment to any active agent
                agent = await self._get_next_round_robin_agent()
                if agent:
                    await self._assign_lead_to_agent_db(lead_id, agent['id'])
                    return LeadAssignmentResult(
                        lead_id=lead_id,
                        assigned_agent_id=str(agent['id']),
                        assigned_agent_name=agent['agent_name'],
                        reason="Round-robin assignment (no territory match)"
                    )
                else:
                    return LeadAssignmentResult(
                        lead_id=lead_id,
                        assigned_agent_id=None,
                        assigned_agent_name=None,
                        reason="No active agents available"
                    )

            # Handle conflicts and select best match
            best_match = self._resolve_territory_conflicts(matches)
            await self._assign_lead_to_agent_db(lead_id, best_match.agent_id)

            return LeadAssignmentResult(
                lead_id=lead_id,
                assigned_agent_id=best_match.agent_id,
                assigned_agent_name=best_match.agent_name,
                reason=f"Territory match: {best_match.county or 'N/A'}, {best_match.state}",
                conflicts=[m.agent_name for m in matches if m.agent_id != best_match.agent_id]
            )

        except Exception as e:
            logger.error(f"Error assigning lead {lead_id}: {e}")
            return LeadAssignmentResult(
                lead_id=lead_id,
                assigned_agent_id=None,
                assigned_agent_name=None,
                reason=f"Assignment error: {str(e)}"
            )

    def _find_territory_matches(self, lead: dict, territories: List[Territory]) -> List[Territory]:
        """Find territories that match the lead's location and type."""
        matches = []

        for territory in territories:
            match_score = 0
            reasons = []

            # County match (highest priority)
            if territory.county and lead['county']:
                if territory.county.lower() == lead['county'].lower():
                    match_score += 100
                    reasons.append("county")

            # State match
            if territory.state and lead['state']:
                if territory.state.lower() == lead['state'].lower():
                    match_score += 50
                    reasons.append("state")

            # Lead type match
            if territory.lead_types and lead['lead_type']:
                if lead['lead_type'] in territory.lead_types:
                    match_score += 75
                    reasons.append("lead_type")

            # Zip code match (if specified)
            if territory.zip_code and lead['zip_code']:
                if territory.zip_code == lead['zip_code']:
                    match_score += 25
                    reasons.append("zip_code")

            # Require at least state match for consideration
            if match_score >= 50:
                territory.priority = match_score
                matches.append(territory)

        return sorted(matches, key=lambda t: t.priority, reverse=True)

    def _resolve_territory_conflicts(self, matches: List[Territory]) -> Territory:
        """Resolve conflicts when multiple agents match a territory."""
        if len(matches) == 1:
            return matches[0]

        # Group by priority score
        best_score = matches[0].priority
        top_matches = [m for m in matches if m.priority == best_score]

        if len(top_matches) == 1:
            return top_matches[0]

        # For ties, use round-robin among the top matches
        # This could be enhanced with load balancing based on current lead count
        return top_matches[0]  # Simplified for now

    async def _get_next_round_robin_agent(self) -> Optional[dict]:
        """Get the next agent for round-robin assignment."""
        agent = await self.db.fetchrow("""
            SELECT id, agent_name
            FROM agent_profiles
            WHERE is_active = true
            ORDER BY
                (SELECT COUNT(*) FROM leads WHERE agent_id = agent_profiles.id AND is_active = true),
                agent_name
            LIMIT 1
        """)
        return dict(agent) if agent else None

    async def _assign_lead_to_agent_db(self, lead_id: str, agent_id: str) -> None:
        """Update the lead's agent assignment in the database."""
        await self.db.execute("""
            UPDATE leads
            SET agent_id = $1
            WHERE id = $2
        """, agent_id, lead_id)

    async def create_agent_territory(
        self,
        agent_id: str,
        county: Optional[str] = None,
        state: str = "IL",  # Default to Illinois
        zip_code: Optional[str] = None,
        lead_types: List[str] = None
    ) -> str:
        """Create a new territory assignment for an agent."""
        if lead_types is None:
            lead_types = ['final_expense', 'term_life', 'whole_life', 'mortgage_protection']

        territory_id = await self.db.fetchval("""
            INSERT INTO agent_territories (agent_id, county, state, zip_code, lead_types)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, agent_id, county, state, zip_code, lead_types)

        return str(territory_id)

    async def get_agent_territories(self, agent_id: str) -> List[dict]:
        """Get all territories for an agent."""
        territories = await self.db.fetch("""
            SELECT t.*, a.agent_name
            FROM agent_territories t
            JOIN agent_profiles a ON t.agent_id = a.id
            WHERE t.agent_id = $1
        """, agent_id)

        return [dict(t) for t in territories]

    async def get_territory_coverage_report(self) -> Dict[str, any]:
        """Generate a report of territory coverage and gaps."""
        # Get all unique counties from leads
        lead_counties = await self.db.fetch("""
            SELECT DISTINCT county, state, COUNT(*) as lead_count
            FROM leads
            WHERE is_active = true AND county IS NOT NULL
            GROUP BY county, state
            ORDER BY lead_count DESC
        """)

        # Get territory coverage
        territory_coverage = await self.db.fetch("""
            SELECT t.county, t.state, a.agent_name, t.lead_types
            FROM agent_territories t
            JOIN agent_profiles a ON t.agent_id = a.id
            WHERE a.is_active = true AND t.county IS NOT NULL
        """)

        # Analyze coverage gaps
        covered_counties = {(t['county'].lower(), t['state']) for t in territory_coverage if t['county']}
        lead_locations = {(lc['county'].lower(), lc['state']) for lc in lead_counties}

        uncovered_counties = lead_locations - covered_counties

        return {
            "total_counties_with_leads": len(lead_locations),
            "covered_counties": len(covered_counties),
            "uncovered_counties": len(uncovered_counties),
            "coverage_percentage": round((len(covered_counties) / len(lead_locations)) * 100, 1) if lead_locations else 0,
            "uncovered_details": [
                {"county": county.title(), "state": state, "lead_count": next(
                    lc['lead_count'] for lc in lead_counties
                    if lc['county'].lower() == county and lc['state'] == state
                )}
                for county, state in uncovered_counties
            ],
            "territory_assignments": [
                {
                    "agent_name": t['agent_name'],
                    "county": t['county'],
                    "state": t['state'],
                    "lead_types": t['lead_types']
                }
                for t in territory_coverage
            ]
        }

    async def bulk_reassign_unassigned_leads(self) -> Dict[str, int]:
        """Bulk reassign all unassigned leads to appropriate agents."""
        unassigned_leads = await self.db.fetch("""
            SELECT id FROM leads
            WHERE agent_id IS NULL AND is_active = true
        """)

        results = {
            "total_processed": len(unassigned_leads),
            "successfully_assigned": 0,
            "failed_assignments": 0
        }

        for lead in unassigned_leads:
            result = await self.assign_lead_to_agent(str(lead['id']))
            if result.assigned_agent_id:
                results["successfully_assigned"] += 1
            else:
                results["failed_assignments"] += 1

        return results