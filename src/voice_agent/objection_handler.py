"""
AIDN Objection Handler
======================

Handles the 5 core objection scenarios for insurance appointment booking.
"""

import logging
from typing import Optional

from ..shared.models import Lead

logger = logging.getLogger(__name__)


class ObjectionHandler:
    """Handles common objections during insurance lead calls."""

    async def handle_objection(self, objection_type: str, customer_response: str, lead: Optional[Lead] = None) -> str:
        """Handle objections. Currently returns empty - LLM handles naturally via persona."""
        # Objection handling cleared for persona rebuild
        # The LLM will handle objections naturally based on its system prompt
        logger.info(f"Objection detected: {objection_type}")
        return ""

    def classify_objection(self, customer_response: str) -> str:
        """Classify customer response into objection types."""
        response_lower = customer_response.lower()

        # Simple keyword-based classification (would be ML-based in production)
        if any(word in response_lower for word in ["not interested", "no thanks", "don't want"]):
            return "not_interested"
        elif any(word in response_lower for word in ["how did you get", "where did you get", "how did you find"]):
            return "how_did_you_get_my_number"
        elif any(word in response_lower for word in ["scam", "fraud", "legitimate", "real"]):
            return "is_this_a_scam"
        elif any(word in response_lower for word in ["busy", "bad time", "can't talk"]):
            return "im_busy_right_now"
        elif any(word in response_lower for word in ["already have", "already covered", "have insurance"]):
            return "i_already_have_insurance"
        elif any(word in response_lower for word in ["send me", "mail me", "email me"]):
            return "send_me_information"
        else:
            return "unknown"