import asyncio
import websockets

async def test_ws():
    try:
        uri = "wss://aidn-production.up.railway.app/twilio-audio-stream-delayed?room=test&lead_id=test&agent_id=test"
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to delayed WebSocket!")
            await websocket.send("test")
            response = await websocket.recv()
            print(f"📥 Response: {response}")
    except Exception as e:
        print(f"❌ Error: {e}")

asyncio.run(test_ws())
