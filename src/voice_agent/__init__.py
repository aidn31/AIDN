"""
AIDN Voice Agent
================

LiveKit-powered voice agent for insurance appointment booking.
Uses LiveKit SIP + Telnyx for phone calls.
"""

# Lazy imports to avoid loading heavy dependencies when not needed
__all__ = [
    "AIDNVoiceAgent",
    "ObjectionHandler",
]


def __getattr__(name):
    """Lazy import heavy modules only when accessed."""
    if name == "AIDNVoiceAgent":
        from .aidn_agent import AIDNVoiceAgent
        return AIDNVoiceAgent
    elif name == "ObjectionHandler":
        from .objection_handler import ObjectionHandler
        return ObjectionHandler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
