"""
AIDN API Server
Minimal FastAPI backend for dashboard integration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="AIDN API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


class CallRequest(BaseModel):
    lead_id: str
    agent_id: Optional[str] = None


class CallResponse(BaseModel):
    status: str
    call_id: str
    lead_id: str


@app.post("/calls/initiate", response_model=CallResponse)
async def initiate_call(request: CallRequest):
    """Initiate an outbound call to a lead."""
    return CallResponse(
        status="dispatched",
        call_id="test-123",
        lead_id=request.lead_id,
    )
