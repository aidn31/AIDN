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
        return """I completely understand. Since you did request information about life insurance,
I just wanted to make sure you had a chance to learn about your options.
Would it help if I mentioned this would just be a quick 15-minute conversation
to see if there's anything that might benefit your family?
If not, that's totally fine - I can remove your number from our list."""

    async def _handle_how_did_you_get_number(self, response: str, lead: Optional[Lead]) -> str:
        """Handle 'How did you get my number?' objection."""
        lead_source = "online" if not lead or not lead.lead_source else lead.lead_source

        return f"""You actually filled out a form requesting information about life insurance.
It was {lead_source} - you were looking into coverage options for your family.
That's why we're calling, to help answer any questions you might have.
Does that ring a bell?"""

    async def _handle_is_this_scam(self, response: str, lead: Optional[Lead]) -> str:
        """Handle 'Is this a scam?' objection."""
        return """I totally understand your concern - there are a lot of scam calls these days.
This is completely legitimate though. You requested information about life insurance coverage,
and we're just following up to see if you'd like to speak with one of our licensed agents.
We're not asking for any personal information over the phone or trying to sell you anything right now.
This would just be scheduling a brief appointment to go over your options. Does that sound reasonable?"""

    async def _handle_busy_right_now(self, response: str, lead: Optional[Lead]) -> str:
        """Handle 'I'm busy right now' objection."""
        return """Of course, I don't want to keep you. This will just take about 30 seconds -
I'm calling because you requested information about life insurance, and I wanted to see
if we could set up a quick 15-minute appointment for you to learn about your options.
Would tomorrow evening or Thursday afternoon work better for you?"""

    async def _handle_already_have_insurance(self, response: str, lead: Optional[Lead]) -> str:
        """Handle 'I already have insurance' objection."""
        return """That's great that you're already covered! A lot of people we talk to
find out their current coverage might not be quite enough for their family's needs,
or they discover they could get the same coverage for less money.
Since you already requested the information, would it hurt to have someone
take a quick look at what you have and see if there are any gaps?
It's just a 15-minute conversation - no pressure at all."""

    async def _handle_send_information(self, response: str, lead: Optional[Lead]) -> str:
        """Handle 'Just send me information' objection."""
        return """I wish I could just mail you something, but honestly, insurance is so personal -
your age, health, family situation - it all affects what makes sense for you.
That's why our agent likes to spend just 15 minutes going over your specific situation
to make sure you get information that's actually relevant.
Plus, if you have questions, they can answer them right there.
Would tomorrow evening or Thursday work for a quick conversation?"""

    async def _handle_unknown_objection(self, response: str, lead: Optional[Lead]) -> str:
        """Handle unknown or unclassified objections."""
        logger.warning(f"Unknown objection type: {response}")

        return """I understand your concern. Since you did request information about life insurance,
I just wanted to make sure you had the opportunity to learn about your options.
Would you prefer I have someone call you back at a better time,
or would you like me to remove your number from our list?"""

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