# AIDN Changelog

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
