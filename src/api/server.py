"""
AIDN API Server
Minimal FastAPI backend for dashboard integration.
"""

import json
import os
from datetime import datetime
from uuid import UUID

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from pydantic import BaseModel
from typing import Optional, List

from ..shared.database import DatabaseManager, LeadRepository
from ..shared.models import Lead

load_dotenv()

app = FastAPI(title="AIDN API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

db_manager: DatabaseManager = None


class CallRequest(BaseModel):
    lead_id: str
    agent_id: Optional[str] = None


class CallResponse(BaseModel):
    status: str
    call_id: str
    lead_id: str


@app.on_event("startup")
async def startup():
    global db_manager
    db_manager = DatabaseManager()
    await db_manager.connect()


@app.get("/leads")
async def get_leads(agent_id: Optional[str] = None, limit: int = 100):
    """Get leads from database."""
    query = "SELECT * FROM leads WHERE is_active = true ORDER BY created_at DESC LIMIT $1"
    rows = await db_manager.fetch(query, limit)
    return [dict(row) for row in rows]


@app.post("/calls/initiate", response_model=CallResponse)
async def initiate_call(request: CallRequest):
    """Initiate an outbound call to a lead."""
    # 1. Validate and get lead from database
    try:
        lead_id = UUID(request.lead_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid lead_id format. Expected UUID, got: {request.lead_id}")

    lead_repo = LeadRepository(db_manager)
    lead = await lead_repo.get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # 2. Create LiveKit API client
    lk_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )

    # 3. Create room and dispatch agent
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    room_name = f"call-{request.lead_id[:8]}-{timestamp}"

    await lk_api.room.create_room(api.CreateRoomRequest(name=room_name))

    await lk_api.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            room=room_name,
            agent_name="aidn-outbound",
            metadata=json.dumps({
                "phone_number": lead.phone,
                "lead_id": request.lead_id,
                "agent_id": request.agent_id,
            }),
        )
    )

    await lk_api.aclose()

    return CallResponse(
        status="dispatched",
        call_id=room_name,
        lead_id=request.lead_id,
    )
