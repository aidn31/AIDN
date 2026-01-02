# AIDN Migration Plan: Custom Bridge → LiveKit SIP + Telnyx

## STATUS: ✅ COMPLETE (January 2, 2026)

---

## 📋 Overview

**Mission:** Migrate AIDN from a broken custom Twilio WebSocket bridge to LiveKit's native SIP integration with Telnyx.

**Result:** Successfully completed. Simpler code, no Railway hosting, working audio, lower costs.

---

## ✅ COMPLETED CHECKLIST

### Phase 1: Discovery ✅
- [x] List all files in the project
- [x] Identify bridge-related files (to DELETE)
- [x] Identify agent files (to KEEP and SIMPLIFY)
- [x] Review requirements.txt

### Phase 2: Delete Old Bridge ✅
- [x] Delete `simple_websocket_test.py`
- [x] Delete `simple_api_server.py`
- [x] Delete `api_server.py`
- [x] Delete `src/voice_agent/twilio_audio_bridge.py`
- [x] Delete `src/voice_agent/call_manager.py`
- [x] Delete Railway config files (`railway.json`, `Procfile`, etc.)
- [x] Delete Twilio test files
- [x] Remove Twilio packages from requirements.txt

### Phase 3: Update Dependencies ✅
- [x] Ensure `livekit-agents>=1.0` in requirements.txt
- [x] Ensure `livekit-plugins-deepgram` in requirements.txt
- [x] Ensure `livekit-plugins-openai` in requirements.txt
- [x] Ensure `livekit-plugins-silero` in requirements.txt
- [x] Add `livekit-plugins-cartesia` to requirements.txt
- [x] Add `livekit-plugins-turn-detector` to requirements.txt

### Phase 4: Rewrite main.py ✅
- [x] Remove all Twilio-specific logic
- [x] Remove custom room creation logic
- [x] Remove manual participant linking
- [x] Remove wait_for_participant workarounds
- [x] Implement new outbound calling pattern
- [x] Add SIP participant creation for dialing
- [x] Move greeting to AFTER call is answered

### Phase 5: Simplify aidn_agent.py ✅
- [x] Remove session.say() from on_enter()
- [x] Remove create_aidn_session() function
- [x] Clean up unused imports
- [x] Keep: instructions, personality, tools
- [x] Keep: appointment booking logic

### Phase 6: Environment Variables ✅
- [x] Add SIP_OUTBOUND_TRUNK_ID to .env.example
- [x] Remove TWILIO_* variables from .env.example
- [x] Update docker-compose.yml
- [x] Update docker-compose.prod.yml
- [x] Remove twilio from pyproject.toml

### Phase 7: Final Verification ✅
- [x] No Python files reference "twilio"
- [x] No files reference "simple_websocket" or "bridge"
- [x] No files reference "railway"
- [x] No manual audio conversion code exists
- [x] Agent can be run with `python -m src.voice_agent.main dev`
- [x] Test calls completed successfully

---

## 📊 Migration Results

| Metric | Value |
|--------|-------|
| Lines deleted | 3,728 |
| Lines added | 120 |
| Net reduction | 3,608 lines |
| Files deleted | 14 |
| Test calls | 5+ successful |

---

## 🔗 Key Commits

| Commit | Description |
|--------|-------------|
| `cae4a1d` | Backup before migration |
| `965efb1` | Phase 2: Delete old bridge |
| `ac5c2a5` | Phase 3: Rewrite agent code |
| `7c6fced` | Phase 4: Update env vars |
| `4ddc8b6` | Phase 5: Final cleanup |

---

## 📐 Final Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LIVEKIT SIP + TELNYX                         │
│  Outbound calls via SIP trunk • No custom bridge needed        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 AIDN VOICE AGENT (LiveKit)                      │
│  Stack: Deepgram STT + GPT-4o-mini + OpenAI TTS                │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Lessons Learned

1. LiveKit SIP is much simpler than custom bridges
2. Don't greet in on_enter() - wait for call answer
3. Telnyx trial accounts require verified numbers
4. Keep bridge code simple - let LiveKit handle audio
