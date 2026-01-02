# AIDN Migration Plan: Custom Bridge → LiveKit SIP + Telnyx

## 📋 Overview

**Mission:** Migrate AIDN from a broken custom Twilio WebSocket bridge to LiveKit's native SIP integration with Telnyx.

**Why:** The custom bridge has an audio bug (caller hears silence). LiveKit SIP handles audio automatically and correctly.

**Result:** Simpler code, no Railway hosting, working audio, lower costs.

---

## 🔑 Key Facts

- AIDN is an **OUTBOUND-only** voice agent (we call leads, they don't call us)
- Phone provider: **Telnyx** (not Twilio)
- Audio handling: **LiveKit SIP** (not custom bridge)
- Agent hosting: **LiveKit Cloud** (not Railway)

---

## ✅ CHECKLIST

### Phase 1: Discovery
- [ ] List all files in the project
- [ ] Identify bridge-related files (to DELETE)
- [ ] Identify agent files (to KEEP and SIMPLIFY)
- [ ] Review requirements.txt

### Phase 2: Delete Old Bridge
- [ ] Delete `simple_websocket_test.py` (or equivalent bridge file)
- [ ] Delete Railway config files (`railway.json`, `railway.toml`, `Procfile`)
- [ ] Delete any Twilio webhook handlers
- [ ] Remove Twilio packages from requirements.txt
- [ ] Remove audio codec packages only used for bridge (audioop, etc.)

### Phase 3: Update Dependencies
- [ ] Ensure `livekit-agents>=1.0` in requirements.txt
- [ ] Ensure `livekit-plugins-deepgram` in requirements.txt
- [ ] Ensure `livekit-plugins-openai` in requirements.txt
- [ ] Ensure `livekit-plugins-cartesia` in requirements.txt
- [ ] Ensure `livekit-plugins-silero` in requirements.txt
- [ ] Ensure `livekit-plugins-turn-detector` in requirements.txt

### Phase 4: Rewrite main.py
- [ ] Remove all Twilio-specific logic
- [ ] Remove custom room creation logic
- [ ] Remove manual participant linking
- [ ] Remove wait_for_participant workarounds
- [ ] Implement new outbound calling pattern (see REFERENCE section below)
- [ ] Add SIP participant creation for dialing
- [ ] Move greeting to AFTER call is answered

### Phase 5: Simplify aidn_agent.py
- [ ] Remove session.say() from on_enter()
- [ ] Remove any participant detection logic
- [ ] Remove any Twilio-specific handling
- [ ] Keep: instructions, personality, tools
- [ ] Keep: appointment booking logic

### Phase 6: Environment Variables
- [ ] Add SIP_OUTBOUND_TRUNK_ID to .env.example
- [ ] Remove any TWILIO_* variables
- [ ] Verify LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET exist
- [ ] Verify AI service keys exist (DEEPGRAM, OPENAI, CARTESIA)

### Phase 7: Final Verification
- [ ] No files reference "twilio" (search codebase)
- [ ] No files reference "simple_websocket" or "bridge"
- [ ] No files reference "railway"
- [ ] No manual audio conversion code exists (μ-law, PCM)
- [ ] Agent can be run with `python main.py dev`

---

## 📐 REFERENCE: New main.py Pattern
```python
import os
import json
import logging
from livekit import api
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.plugins import deepgram, openai, cartesia, silero
from livekit.plugins.turn_detector import MultilingualModel

from aidn_agent import AIDNVoiceAgent

logger = logging.getLogger("aidn")

async def entrypoint(ctx: JobContext):
    """
    AIDN Outbound Call Entrypoint
    
    Flow:
    1. Receive dispatch with phone_number in metadata
    2. Connect to room
    3. Create SIP participant (dials the lead)
    4. Wait for answer
    5. Greet lead
    6. Conversation happens
    """
    await ctx.connect()
    
    # Extract call info from dispatch metadata
    metadata = json.loads(ctx.job.metadata) if ctx.job.metadata else {}
    phone_number = metadata.get("phone_number")
    lead_name = metadata.get("lead_name", "")
    
    if not phone_number:
        logger.error("No phone_number in job metadata. Cannot place call.")
        return
    
    logger.info(f"Starting outbound call to {phone_number}")
    
    # Create agent and session
    agent = AIDNVoiceAgent()
    
    session = AgentSession(
        stt=deepgram.STT(model="nova-2"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=cartesia.TTS(voice="248be419-c632-4f23-adf1-5324ed7dbbd1"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )
    
    # Start session
    await session.start(room=ctx.room, agent=agent)
    
    # Dial the lead via SIP
    sip_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
    
    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=sip_trunk_id,
                sip_call_to=phone_number,
                room_name=ctx.room.name,
                participant_identity=f"lead-{phone_number}",
                wait_until_answered=True,
            )
        )
        
        # Call was answered - greet the lead
        greeting = f"Hi{' ' + lead_name if lead_name else ''}! This is AIDN calling about the life insurance information you requested. Do you have a quick moment?"
        
        await session.generate_reply(instructions=f"Say exactly: {greeting}")
        
    except Exception as e:
        logger.error(f"Failed to connect call: {e}")
        return


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="aidn-outbound",
        )
    )
```

---

## 📐 REFERENCE: Simplified aidn_agent.py Pattern
```python
from livekit.agents import Agent, RunContext, function_tool
import logging

logger = logging.getLogger("aidn-agent")


class AIDNVoiceAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""You are AIDN, a friendly appointment setter for life insurance.

VOICE STYLE:
- Warm, conversational, natural
- Use casual phrases: "Hey", "Gotcha", "Makes sense", "No worries"
- Speak at a relaxed pace, not rushed
- Use natural fillers: "um", "so", "well"
- Be empathetic and patient

YOUR GOAL:
- Schedule an appointment with a licensed insurance agent
- Get their preferred day and time
- Confirm their phone number

RULES:
- NEVER give insurance quotes or policy advice
- NEVER discuss specific coverage amounts
- ONLY schedule appointments
- Keep it brief - respect their time

HANDLING OBJECTIONS:
- "I'm busy": "Totally understand! When would be better for a quick 10-minute call?"
- "Not interested": "No problem at all! Thanks for your time. Have a great day!"
- "Is this a scam?": "Great question! You requested info through [source]. I'm just following up to schedule a call with a licensed agent. No pressure at all."
- "How long will it take?": "The appointment is just 10-15 minutes. They'll answer your questions and see if we can help."

ENDING CALLS:
- If appointment booked: "Perfect! You're all set for [day] at [time]. They'll call you at this number. Thanks so much!"
- If not interested: "No worries at all! Thanks for your time. Take care!"
"""
        )

    @function_tool
    async def book_appointment(
        self,
        context: RunContext,
        preferred_date: str,
        preferred_time: str,
        phone_number: str = None,
    ):
        """Book an appointment for the lead.
        
        Args:
            preferred_date: When they want the call (e.g., "tomorrow", "Monday")
            preferred_time: What time works (e.g., "2pm", "morning")
            phone_number: Callback number if different from current
        """
        logger.info(f"📅 Appointment booked: {preferred_date} at {preferred_time}")
        
        # TODO: Connect to your CRM/calendar system
        
        return {
            "success": True,
            "message": f"Appointment confirmed for {preferred_date} at {preferred_time}"
        }

    @function_tool
    async def end_call(
        self,
        context: RunContext,
        reason: str,
        notes: str = "",
    ):
        """End the call and log the outcome.
        
        Args:
            reason: One of: "appointment_booked", "not_interested", "callback_requested", "voicemail", "no_answer"
            notes: Any additional notes about the call
        """
        logger.info(f"📞 Call ended: {reason} - {notes}")
        
        # TODO: Log to your CRM
        
        return {"success": True}
```

---

## 🔗 Documentation Links

- LiveKit Outbound Calls: https://docs.livekit.io/agents/quickstarts/outbound-calls/
- LiveKit Telephony: https://docs.livekit.io/agents/start/telephony/
- Telnyx + LiveKit: https://docs.livekit.io/sip/quickstarts/configuring-telnyx-trunk/
- LiveKit Agents Framework: https://docs.livekit.io/agents/

---

## ⚠️ Common Mistakes to Avoid

1. **DON'T** keep any Twilio code - we're using Telnyx now
2. **DON'T** write audio conversion code - LiveKit SIP handles it
3. **DON'T** use wait_for_participant for SIP calls - participant is created by us
4. **DON'T** greet in on_enter() - greet AFTER call is answered
5. **DON'T** deploy to Railway - agents run on LiveKit Cloud

---

## 📊 Before vs After

| Aspect | Before (DELETE) | After (IMPLEMENT) |
|--------|-----------------|-------------------|
| Phone provider | Twilio | Telnyx |
| Phone → LiveKit | Custom bridge code | LiveKit SIP |
| Bridge hosting | Railway | None needed |
| Audio handling | Manual μ-law/PCM | Automatic |
| Participant linking | Manual with timing bugs | Automatic |
| Greeting timing | on_enter (broken) | After call answered |
| Lines of code | ~500+ | ~100 |