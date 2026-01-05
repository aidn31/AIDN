#!/usr/bin/env python3
"""
Test Call Script
================
Dispatches a test outbound call to the AIDN voice agent.
"""

import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from livekit import api

load_dotenv()


async def dispatch_test_call(phone_number: str):
    """Dispatch a test call to the specified phone number."""

    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not all([livekit_url, api_key, api_secret]):
        print("❌ Missing LIVEKIT_URL, LIVEKIT_API_KEY, or LIVEKIT_API_SECRET")
        sys.exit(1)

    print(f"📞 Dispatching test call to {phone_number}")
    print(f"📡 LiveKit URL: {livekit_url}")

    # Create LiveKit API client
    lk_api = api.LiveKitAPI(
        url=livekit_url,
        api_key=api_key,
        api_secret=api_secret,
    )

    # Create a room for the call
    room_name = f"test-call-{phone_number.replace('+', '')}"

    try:
        # Create room first
        await lk_api.room.create_room(
            api.CreateRoomRequest(name=room_name)
        )
        print(f"✅ Created room: {room_name}")
    except Exception as e:
        print(f"⚠️ Room may already exist: {e}")

    # Dispatch the agent with call metadata
    try:
        dispatch = await lk_api.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                room=room_name,
                agent_name="aidn-outbound",
                metadata=json.dumps({
                    "phone_number": phone_number,
                    "lead_id": None,  # No lead for test call
                    "agent_id": None,
                })
            )
        )
        print(f"✅ Agent dispatched!")
        print(f"   Dispatch ID: {dispatch.id}")
        print(f"   Room: {room_name}")
        print(f"\n🎙️ The agent should now dial {phone_number}...")

    except Exception as e:
        print(f"❌ Failed to dispatch agent: {e}")
        raise

    await lk_api.aclose()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_call.py <phone_number>")
        print("Example: python test_call.py +19086197628")
        sys.exit(1)

    phone = sys.argv[1]
    asyncio.run(dispatch_test_call(phone))
