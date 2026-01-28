# AIDN Development Rules

You are helping build AIDN - an AI voice agent platform for life insurance lead calling and appointment scheduling.

## Mission
Build YC-caliber outbound sales AI voice agent. Automate lead calling + appointment scheduling with natural conversation, Google Calendar integration, and <800ms voice latency.

## Current Capabilities (What Works Now)
- ✅ Single call at a time (manual initiation via dashboard)
- ✅ Dashboard → API → LiveKit → Phone → Calendar flow
- ✅ Voice latency: 700-800ms (Deepgram + Groq + Cartesia)
- ✅ Natural conversation with Aiden persona (casual, friendly)
- ✅ Objection handling (16 scenarios via RAG)
- ✅ Appointment booking with Google Calendar integration
- ✅ PostgreSQL database with leads, agents, appointments

## Tech Stack
**Voice:** LiveKit + Deepgram (STT) + Groq Llama 3.1 8B (LLM) + Cartesia Sonic 2 (TTS)
**Backend:** FastAPI + Python + PostgreSQL
**Frontend:** Next.js + React + TypeScript + Tailwind CSS
**Infrastructure:** Docker + Railway (planned)
**Calendar:** Google Calendar API (service account)

## Project Structure
```
src/
├── voice_agent/      # LiveKit agent (Aiden) - aidn-outbound
├── api/              # FastAPI backend (ports 8000)
├── dashboard_agent/  # Streamlit admin (legacy, being replaced)
└── shared/           # Database, models, utilities

web-dashboard/        # Next.js React frontend (port 3000)
docs/                 # Project documentation
.cursor/              # AI development workflows
```

## Start Services
```bash
# Terminal 1: Voice Agent
python -m src.voice_agent.main dev

# Terminal 2: API Server
uvicorn src.api.server:app --reload --port 8000

# Terminal 3: Dashboard
cd web-dashboard && npm run dev
```

## Development Workflow
1. **Start session:** `/prime` - Load all context
2. **Planning:** Discuss feature → `/plan` → Creates structured plan doc
3. **Execution:** NEW chat → `/execute <plan_path>` (context reset)
4. **Evolution:** After bugs → `/evolve` to improve system

## Code Conventions
- **Python:** Type hints required, async/await for I/O, Pydantic validation
- **TypeScript:** Strict mode, explicit types, functional components
- **Database:** Repository pattern only (no raw SQL in endpoints)
- **Git:** Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`)

## Testing Requirements
- **Voice:** Test with real phone calls, log latency per component (STT/LLM/TTS)
- **API:** Test with curl/Postman before dashboard integration
- **Frontend:** Manual testing in browser
- **E2E:** Full flow (Dashboard → Call button → Phone → Calendar event)

## Core KPIs (Monitor Always)
- Voice latency: <800ms total (STT ~350ms, LLM 300-500ms, TTS ~320ms)
- Persona: Aiden (casual, friendly, NOT corporate)
- Compliance: TCPA compliant, no policy advice
- Call flow: Dashboard → API → LiveKit → Phone → Calendar
- YC Deadline: February 9, 2026

## Reference Documentation (Load Only When Working On)
- **Voice Agent:** @.cursor/reference/voice_agent_rules.md
- **API Development:** @.cursor/reference/api_rules.md
- **Frontend:** @.cursor/reference/frontend_rules.md
- **Database:** @.cursor/reference/database_rules.md
- **Monitoring:** @.cursor/reference/monitoring_rules.md
- **Deployment:** @.cursor/reference/deployment_rules.md

## Critical Context Files
- **PRD:** AIDN_SPECIFICATION.md
- **Status:** docs/PROJECT_STATUS.md
- **Next Steps:** docs/NEXT_STEPS.md
- **Architecture:** docs/ARCHITECTURE.md
- **Roadmap:** docs/YC_DEADLINE_ROADMAP.md

## Critical Rules for Voice Agent
- Core prompt must stay <1500 tokens (use RAG for objections)
- Always log latency per component (STT, LLM TTFT, TTS TTFB)
- Test with real phone numbers, not simulators
- Never hardcode phone numbers or API keys
- Calendar booking must succeed even if Google API fails (fire-and-forget)
- 3-layer architecture: Slim prompt + RAG tools + Knowledge base

## Critical Rules for API
- Use async/await for all I/O operations
- Validate all inputs with Pydantic models
- Use repository pattern (src/shared/database/repository.py)
- Return consistent error responses
- Never expose database errors to clients

## Critical Rules for Frontend
- Follow Linear/Vercel/Stripe aesthetic (Slate + Emerald design)
- Fetch data from API, never direct database access
- Handle loading/error states for all async operations
- Use TypeScript strict mode, no `any` types

## Common Pitfalls (Avoid These)
- ❌ Don't bloat voice prompts (kills latency)
- ❌ Don't skip E2E testing (Dashboard → Phone)
- ❌ Don't make database changes without migrations
- ❌ Don't forget context reset (planning ≠ execution)
- ❌ Don't deploy without testing full call flow
- ❌ Don't commit secrets (.env, credentials.json)

## Environment Variables Required
```bash
# Database
DATABASE_URL=postgresql://...

# Voice Agent
DEEPGRAM_API_KEY=...
CARTESIA_API_KEY=sk_car_...
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
SIP_OUTBOUND_TRUNK_ID=ST_...

# LLM
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.1-8b-instant

# Calendar
GOOGLE_CALENDAR_CREDENTIALS_PATH=./google-calendar-credentials.json
GOOGLE_CALENDAR_ID=your-calendar-id@gmail.com
```

---

*Last Updated: January 27, 2026 | Lines: 145 | Voice Agent: Aiden | Current: 1 call at a time*
