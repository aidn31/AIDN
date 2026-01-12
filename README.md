# AIDN - AI-Powered Insurance Distribution Network

A YC-caliber AI voice agent platform designed specifically for Life Insurance Independent Marketing Organizations (IMOs). AIDN automates outbound lead calling and appointment scheduling, allowing human agents to focus on what they do best—closing sales.

## 🎯 Mission

Eliminate the manual lead-calling burden for life insurance agents while maximizing appointment show rates and lead conversion.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DASHBOARD UI                              │
│                    (Streamlit / React)                          │
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
│         LiveKit SIP + Telnyx + Deepgram + GPT-4o-mini + Cartesia│
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or later
- PostgreSQL database
- API Keys:
  - OpenAI API key
  - Deepgram API key
  - Cartesia API key (for low-latency TTS)
  - LiveKit Cloud account (for SIP + Telnyx integration)

### 1. Install Dependencies

```bash
# Install dependencies using UV
uv sync
```

### 2. Set Up Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key
- `DEEPGRAM_API_KEY` - Deepgram API key
- `CARTESIA_API_KEY` - Cartesia API key (for low-latency TTS)
- `LIVEKIT_URL` - LiveKit Cloud WebSocket URL
- `LIVEKIT_API_KEY` - LiveKit API key
- `LIVEKIT_API_SECRET` - LiveKit API secret
- `SIP_OUTBOUND_TRUNK_ID` - LiveKit SIP trunk ID (configured with Telnyx)

### 3. Initialize Database

```bash
# Create database schema
uv run python -c "
from src.shared.database import DatabaseManager
import asyncio
async def init():
    db = DatabaseManager()
    await db.connect()
    await db.initialize_schema()
    print('Database initialized!')
asyncio.run(init())
"
```

### 4. Run the Dashboard

```bash
# Start the Streamlit dashboard
streamlit run src/dashboard-agent/streamlit_app.py
```

### 5. Run the Voice Agent (Optional)

```bash
# Console mode for testing
uv run python -m src.voice_agent.main console

# Development mode (connects to LiveKit)
uv run python -m src.voice_agent.main dev
```

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f voice-agent
```

## 🎤 Voice Agent Features

- **Natural Conversations**: AI that sounds human and builds rapport
- **Insurance-Specific**: Built for life insurance sales workflows
- **Objection Handling**: Handles 12+ objection scenarios via RAG
- **Compliance-First**: TCPA compliant, never discusses policy details
- **Smart Scheduling**: Atomic appointment booking with calendar sync

## 📊 Dashboard Features

- **Lead Management**: Upload, categorize, and track leads
- **Call Queue**: Prioritized calling queue with retry logic
- **Real-time Analytics**: Conversion rates, call volume, performance metrics
- **Agent Control**: Full visibility and control over calling activity

## 🏃‍♂️ Development Status

**Current Phase:** PRODUCTION READY - Voice Optimization Phase

### Completed ✅
- [x] Unified project structure
- [x] Database schema and models
- [x] Voice agent core architecture
- [x] Basic dashboard interface
- [x] Docker deployment configuration

### In Progress 🚧
- [ ] Voice optimization (reduce latency from 1400-2400ms → <500ms)
- [ ] Dashboard integration (wire up call button)
- [ ] End-to-end appointment booking flow
- [ ] YC demo preparation

### Next Steps 📋
- [ ] Appointment slot generation logic
- [ ] Lead prioritization queue
- [ ] End-to-end integration testing
- [ ] YC demo preparation

## 🎯 YC Demo Goals

**Timeline:** Working prototype by January 19th for YC application (February 9th deadline)

**Demo Flow (60 seconds):**
1. Dashboard shows 5 test leads
2. Click "Call Lead" button
3. AIDN calls live phone number
4. Natural conversation + objection handling
5. Appointment booked, appears in dashboard

## 🤝 Contributing

This is currently a private project for YC application development. After YC application, we'll open source appropriate components.

## 📄 License

Private - All rights reserved during YC application phase.

---

**AIDN - Turning leads into appointments, automatically.**