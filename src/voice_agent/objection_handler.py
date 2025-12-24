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
        """Handle objections based on type and provide appropriate response."""

        objection_handlers = {
            "not_interested": self._handle_not_interested,
            "how_did_you_get_my_number": self._handle_how_did_you_get_number,
            "is_this_a_scam": self._handle_is_this_scam,
            "im_busy_right_now": self._handle_busy_right_now,
            "i_already_have_insurance": self._handle_already_have_insurance,
            "send_me_information": self._handle_send_information
        }

        handler = objection_handlers.get(objection_type, self._handle_unknown_objection)
        return await handler(customer_response, lead)

    async def _handle_not_interested(self, response: str, lead: Optional[Lead]) -> str:
        """Handle 'I'm not interested' objection."""
        return """Yeah, I get it... umm, can I ask - is it the timing that's not good, or are you pretty well set with your current situation?

Because ya know, you did fill out that card asking about coverage... I was just trying to get you the info you requested."""

    async def _handle_how_did_you_get_number(self, response: str, lead: Optional[Lead]) -> str:
        """Handle 'How did you get my number?' objection."""
        lead_source = "online" if not lead or not lead.lead_source else lead.lead_source

        return f"""Ya know, you had filled out one of those cards asking about coverage... do ya remember doing that recently? Anyway, that's why I'm calling - to get you that info you requested."""

    async def _handle_is_this_scam(self, response: str, lead: Optional[Lead]) -> str:
        """Handle 'Is this a scam?' objection."""
        return """Oh no, I totally get that... there's so many scam calls these days, right? Nah, this is legit - you filled out that card asking about insurance coverage, and that's why I'm calling. I'm not asking for your social security or credit card or anything like that... just trying to set up a quick appointment to go over the info you requested. Does that make sense?"""

    async def _handle_busy_right_now(self, response: str, lead: Optional[Lead]) -> str:
        """Handle 'I'm busy right now' objection."""
        return """Oh sure, no problem... this'll just take like 30 seconds. They've got me running around tomorrow and I was just trying to see if you'd be around in the morning or afternoon?"""

    async def _handle_already_have_insurance(self, response: str, lead: Optional[Lead]) -> str:
        """Handle 'I already have insurance' objection."""
        return """Oh that's great! Yeah, a lot of folks we help already have something... they just wanna make sure they're getting the best deal or haven't missed anything new. Would it hurt to just take a quick look?"""

    async def _handle_send_information(self, response: str, lead: Optional[Lead]) -> str:
        """Handle 'Just send me information' objection."""
        return """Yeah, I wish I could just drop it in the mail, but honestly these programs are so specific to your situation - ya know, your age, income level and all that... that's why they like me to just go over it real quick with ya. Would tomorrow morning or afternoon work better?"""

    async def _handle_unknown_objection(self, response: str, lead: Optional[Lead]) -> str:
        """Handle unknown or unclassified objections."""
        logger.warning(f"Unknown objection type: {response}")

        return """I hear ya... umm, since you did request information about coverage, I was just trying to get you that info. Would you rather I have someone call ya back at a better time, or just take your number off the list?"""

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