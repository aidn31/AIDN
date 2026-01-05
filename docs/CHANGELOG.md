# AIDN Changelog

## [2.1.0] - January 3, 2026

### NEW: Aiden Persona & Low-Latency Voice

Complete voice agent persona rebuild with optimized latency settings.

#### Added
- **Aiden Persona** - Full conversational persona for insurance appointment setting
  - Casual, warm personality ("gonna", "ya", "wanna", "lemme")
  - Complete conversation flow from greeting to appointment tie-down
  - 12 objection handling scripts (not interested, what is it, scam, busy, etc.)
  - Decision maker confirmation flow
  - 5-digit confirmation code system per call
  - 11 guardrails to prevent unwanted behaviors
- **Cartesia TTS** - Low-latency text-to-speech (~100-150ms vs 300-500ms OpenAI)
- **Optimized VAD Settings** - Faster turn detection (300ms silence threshold)
- **Dynamic System Prompt** - `build_system_prompt()` injects lead/agent data at runtime
- **Confirmation Code Generator** - `generate_confirmation_code()` creates random 5-digit codes
- **Test Call Script** - `scripts/test_call.py` for easy call dispatching

#### Changed
- `src/voice_agent/aidn_agent.py` - Complete rewrite with Aiden persona (~400 lines)
- `src/voice_agent/main.py` - Cartesia TTS, optimized VAD, Aiden greeting
- `src/voice_agent/script_knowledge_base.py` - Cleared for persona rebuild
- `src/voice_agent/objection_handler.py` - Cleared (LLM handles via persona)
- `.env` - Added `CARTESIA_API_KEY`

#### Latency Improvements
| Component | Before | After |
|-----------|--------|-------|
| TTS | OpenAI (~300-500ms) | Cartesia (~100-150ms) |
| VAD silence | 550ms | 300ms |
| Turn detection | Default | Optimized |

---

## [2.0.0] - January 2, 2026

### MAJOR: LiveKit SIP + Telnyx Migration

Complete migration from custom Twilio bridge to LiveKit SIP with Telnyx.

#### Added
- LiveKit SIP outbound calling via `ctx.api.sip.create_sip_participant()`
- Telnyx as phone provider
- `SIP_OUTBOUND_TRUNK_ID` environment variable
- Greeting delivered after call is answered
- Participant disconnect detection

#### Removed
- `simple_websocket_test.py` - Custom Twilio WebSocket bridge
- `simple_api_server.py` - FastAPI with Twilio webhooks
- `api_server.py` - Alternative API server
- `src/voice_agent/twilio_audio_bridge.py` - Audio converter
- `src/voice_agent/call_manager.py` - Twilio call manager
- Railway configuration files (Procfile, railway.json, etc.)
- Twilio test files
- `twilio` package from requirements.txt

#### Changed
- `src/voice_agent/main.py` - Complete rewrite for LiveKit SIP
- `src/voice_agent/aidn_agent.py` - Removed on_enter greeting
- `src/voice_agent/__init__.py` - Removed deleted exports
- `.env.example` - Updated for Telnyx/SIP
- `docker-compose.yml` - Removed Twilio env vars
- `docker-compose.prod.yml` - Removed Twilio env vars
- `pyproject.toml` - Removed twilio dependency

#### Stats
- **Lines removed:** 3,728
- **Lines added:** 120
- **Net reduction:** 3,608 lines

---

## [1.x] - December 2025

### Previous Development (Archived)

The following features were built with the custom Twilio bridge architecture:

- React dashboard with Linear/Vercel aesthetic
- FastAPI backend with full REST API
- PostgreSQL database with lead management
- Voice agent with casual persona
- Objection handling system
- Appointment booking logic

These features remain intact after the migration. Only the phone integration layer changed.

---

## Migration Commits

| Commit | Description |
|--------|-------------|
| `cae4a1d` | Backup before migration |
| `965efb1` | Phase 2: Delete old bridge (-3,728 lines) |
| `ac5c2a5` | Phase 3: Rewrite agent code for LiveKit SIP |
| `7c6fced` | Phase 4: Update environment variables |
| `4ddc8b6` | Phase 5: Final cleanup and verification |
