"""
AIDN Voice Agent
================

LiveKit-powered voice agent for insurance appointment booking.

Note: Heavy imports (AIDNVoiceAgent) are done lazily to avoid loading
LiveKit plugins when not needed (e.g., when just using the audio bridge).
"""

# Lazy imports to avoid loading heavy dependencies when not needed
__all__ = [
    "AIDNVoiceAgent",
    "ObjectionHandler",
    "CallManager",
    "TwilioAudioBridge",
]


def __getattr__(name):
    """Lazy import heavy modules only when accessed."""
    if name == "AIDNVoiceAgent":
        from .aidn_agent import AIDNVoiceAgent
        return AIDNVoiceAgent
    elif name == "ObjectionHandler":
        from .objection_handler import ObjectionHandler
        return ObjectionHandler
    elif name == "CallManager":
        from .call_manager import CallManager
        return CallManager
    elif name == "TwilioAudioBridge":
        from .twilio_audio_bridge import TwilioAudioBridge
        return TwilioAudioBridge
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
