# AIDN Architecture

**Last Updated:** December 23, 2025

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DASHBOARD UI                              │
│                    (React / Next.js)                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DASHBOARD AGENT (Pydantic AI)                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SUPABASE DATABASE                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AIDN VOICE AGENT (LiveKit)                     │
│         Twilio + Deepgram + ElevenLabs + OpenAI                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Component | Technology | Why |
|-----------|------------|-----|
| Voice Agent | LiveKit | Real-time audio processing, proven voice agent architecture |
| Phone Calls | Twilio | Industry standard for telephony, reliable call routing |
| Speech-to-Text | Deepgram | Fast, accurate transcription for real-time conversations |
| Text-to-Speech | ElevenLabs | Natural-sounding voices, better than standard TTS |
| LLM | OpenAI/Claude | Advanced conversation handling and reasoning |
| Database | Supabase | PostgreSQL with real-time features, easy to use |
| Dashboard Agent | Pydantic AI | Structured tools for lead and agent management |
| Frontend | TBD | To be determined based on repo analysis |

---

## Key Architectural Decisions

### December 23, 2025 - Consolidation Architecture
**Decision:** Unify 3 existing AIDN implementations into single codebase
- **Source:** workshops/livekit-rag-voice-agent + workshops/aidn-dashboard-agent + workshops/aidn-lead-management-agent
- **Target:** Single AIDN/ repository with voice-agent/ and dashboard-agent/ modules
- **Database:** AIDN_SPECIFICATION.md schema as master, migrate existing data

### December 23, 2025 - Voice Technology Stack (Keep Existing)
- **Voice Agent:** LiveKit (don't change working configuration)
- **Phone Calls:** Twilio (keep existing integration)
- **Speech-to-Text:** Deepgram (proven working)
- **Text-to-Speech:** ElevenLabs/OpenAI (keep existing config)
- **LLM:** OpenAI (working in existing implementation)

### December 23, 2025 - Prototype vs Product Technology Choices
**Prototype:**
- **Database:** Supabase (existing integration)
- **Dashboard UI:** Streamlit (fast development, working code exists)
- **Agent Framework:** Pydantic AI (existing implementation)
- **Deployment:** Simple Docker (existing setup)

**Product (After YC):**
- **Dashboard UI:** React/Next.js (from ai-agent-mastery/9_Agent_SaaS)
- **Deployment:** Production Docker + Caddy (from ai-agent-mastery/6_Agent_Deployment)
- **Monitoring:** Production logging and metrics
- **Multi-tenancy:** Support for multiple IMOs

### Database Schema Evolution
**Current State:** 3 different schemas across repositories
**Target State:** Single unified schema based on AIDN_SPECIFICATION.md
**Migration Strategy:** Create migration script to transform existing data to new schema

### Integration Approach
**Voice Agent ↔ Dashboard Agent Communication:**
- Shared database layer for real-time updates
- Event-driven updates (lead status changes, appointment bookings)
- Unified configuration management

### Objection Handling Architecture
**Prototype:** 5 core objections with keyword-based responses
**Product:** Advanced conversation intelligence with context awareness
- Pattern recognition for objection types
- Dynamic response generation
- Conversation memory and context