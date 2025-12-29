#!/usr/bin/env python3
"""
AIDN API Server
==============

FastAPI backend to serve the React dashboard with real database data.
Provides REST endpoints for the professional React dashboard.
"""

import asyncio
import csv
import io
import os
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import AIDN modules
from src.dashboard_agent.streamlit_db import StreamlitDatabase
from src.shared.database.connection import DatabaseManager
from src.shared.territory_manager import TerritoryManager
from src.voice_agent.call_manager import CallManager
from src.shared.models.lead import Lead

app = FastAPI(
    title="AIDN API",
    description="AI-Powered Insurance Distribution Network API",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and territory manager
db = StreamlitDatabase()
db_manager = DatabaseManager()
territory_manager = TerritoryManager(db_manager)

# Initialize call manager for voice agent functionality
call_manager = CallManager(db_manager)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "AIDN API is running", "version": "1.0.0"}


@app.get("/agents")
async def get_agents():
    """Get all active agents."""
    try:
        agents = db.get_agents()
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent by ID."""
    try:
        agent = db.execute_single(
            "SELECT * FROM agent_profiles WHERE id = %s AND is_active = true",
            (agent_id,)
        )
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leads")
async def get_leads(
    agent_id: str = Query(..., description="Agent ID"),
    status: Optional[str] = Query(None, description="Filter by call outcome"),
    county: Optional[str] = Query(None, description="Filter by county"),
    lead_type: Optional[str] = Query(None, description="Filter by lead type"),
    limit: int = Query(100, description="Maximum number of leads")
):
    """Get leads for an agent with optional filters."""
    try:
        # Build dynamic query based on filters
        query = """
            SELECT l.*, a.agent_name
            FROM leads l
            JOIN agent_profiles a ON l.agent_id = a.id
            WHERE l.agent_id = %s AND l.is_active = true
        """
        params = [agent_id]

        if status:
            query += " AND l.call_outcome = %s"
            params.append(status)

        if county:
            query += " AND l.county ILIKE %s"
            params.append(f"%{county}%")

        if lead_type:
            query += " AND l.lead_type = %s"
            params.append(lead_type)

        query += " ORDER BY l.created_at DESC LIMIT %s"
        params.append(limit)

        leads = db.execute_query(query, tuple(params))
        return leads
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leads/{lead_id}")
async def get_lead(lead_id: str):
    """Get specific lead by ID."""
    try:
        lead = db.execute_single(
            "SELECT l.*, a.agent_name FROM leads l JOIN agent_profiles a ON l.agent_id = a.id WHERE l.id = %s",
            (lead_id,)
        )
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        return lead
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/appointment-slots")
async def get_appointment_slots(
    agent_id: str = Query(..., description="Agent ID"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)")
):
    """Get appointment slots for an agent."""
    try:
        query = """
            SELECT s.*, l.first_name, l.last_name, l.phone
            FROM appointment_slots s
            LEFT JOIN leads l ON s.lead_id = l.id
            WHERE s.agent_id = %s
        """
        params = [agent_id]

        if date:
            query += " AND s.date = %s"
            params.append(date)
        else:
            # Default to next 7 days
            query += " AND s.date >= CURRENT_DATE AND s.date <= CURRENT_DATE + INTERVAL '7 days'"

        query += " ORDER BY s.date, s.time"

        slots = db.execute_query(query, tuple(params))
        return slots
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/appointments/book")
async def book_appointment(booking_data: dict):
    """Book an appointment slot for a lead."""
    try:
        slot_id = booking_data.get("slot_id")
        lead_id = booking_data.get("lead_id")

        if not slot_id or not lead_id:
            raise HTTPException(status_code=400, detail="slot_id and lead_id are required")

        # Use the database function to book appointment atomically
        result = db.execute_single(
            "SELECT book_appointment(%s, %s) as success",
            (slot_id, lead_id)
        )

        if result and result['success']:
            # Get the booked appointment details
            appointment = db.execute_single(
                """SELECT s.*, l.first_name, l.last_name, l.phone
                   FROM appointment_slots s
                   JOIN leads l ON s.lead_id = l.id
                   WHERE s.id = %s""",
                (slot_id,)
            )
            return {"success": True, "appointment": appointment}
        else:
            return {"success": False, "error": "Appointment slot no longer available"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/calls/initiate")
async def initiate_call(call_data: dict):
    """Initiate a call to a lead."""
    try:
        lead_id = call_data.get("lead_id")
        if not lead_id:
            raise HTTPException(status_code=400, detail="lead_id is required")

        # Get lead details
        lead_data = db.execute_single("SELECT * FROM leads WHERE id = %s", (lead_id,))
        if not lead_data:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Convert to Lead model
        from uuid import UUID
        from datetime import datetime
        lead = Lead(
            id=UUID(lead_data['id']) if isinstance(lead_data['id'], str) else lead_data['id'],
            first_name=lead_data['first_name'],
            last_name=lead_data['last_name'],
            phone=lead_data['phone'],
            address=lead_data.get('address'),
            city=lead_data.get('city'),
            county=lead_data.get('county'),
            state=lead_data.get('state'),
            zip_code=lead_data.get('zip_code'),
            agent_id=UUID(lead_data['agent_id']) if isinstance(lead_data['agent_id'], str) else lead_data['agent_id'],
            lead_type=lead_data.get('lead_type', 'general'),
            source=lead_data.get('lead_source', 'manual'),
            call_outcome=lead_data.get('call_outcome', 'fresh'),
            call_count=lead_data.get('call_count', 0),
            needs_retry=lead_data.get('needs_retry', False),
            is_active=lead_data.get('is_active', True),
            created_at=lead_data.get('created_at', datetime.now()),
            uploaded_at=lead_data.get('uploaded_at', datetime.now())
        )

        # Initiate the actual call using CallManager
        try:
            call_sid = await call_manager.initiate_call(lead, lead.agent_id)

            if call_sid:
                return {
                    "success": True,
                    "call_id": call_sid,
                    "message": f"Calling {lead.first_name} {lead.last_name} at {lead.phone}"
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to initiate call - no call_sid returned")
        except Exception as call_error:
            print(f"Call initiation error: {call_error}")
            raise HTTPException(status_code=500, detail=f"Call initiation failed: {str(call_error)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/stats")
async def get_dashboard_stats(agent_id: str = Query(..., description="Agent ID")):
    """Get dashboard statistics for an agent."""
    try:
        # Total leads
        total_leads = db.execute_single(
            "SELECT COUNT(*) as count FROM leads WHERE agent_id = %s AND is_active = true",
            (agent_id,)
        )['count']

        # Fresh leads (never called)
        fresh_leads = db.execute_single(
            "SELECT COUNT(*) as count FROM leads WHERE agent_id = %s AND call_outcome = 'fresh'",
            (agent_id,)
        )['count']

        # Appointments today
        appointments_today = db.execute_single(
            "SELECT COUNT(*) as count FROM appointment_slots WHERE agent_id = %s AND date = CURRENT_DATE AND status = 'booked'",
            (agent_id,)
        )['count']

        # Calls in progress (simulate)
        calls_in_progress = 0  # Would be calculated from active call sessions

        # Conversion rate (appointments booked / total calls made)
        total_calls = db.execute_single(
            "SELECT COUNT(*) as count FROM leads WHERE agent_id = %s AND call_count > 0",
            (agent_id,)
        )['count'] or 1  # Avoid division by zero

        booked_appointments = db.execute_single(
            "SELECT COUNT(*) as count FROM leads WHERE agent_id = %s AND call_outcome = 'booked'",
            (agent_id,)
        )['count']

        conversion_rate = round((booked_appointments / total_calls) * 100, 1) if total_calls > 0 else 0

        # Show rate (simulate - would be calculated from completed appointments)
        show_rate = 75.5  # Example

        return {
            "totalLeads": total_leads,
            "freshLeads": fresh_leads,
            "appointmentsToday": appointments_today,
            "callsInProgress": calls_in_progress,
            "conversionRate": conversion_rate,
            "showRate": show_rate
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/call-logs")
async def get_call_logs(
    agent_id: str = Query(..., description="Agent ID"),
    limit: int = Query(50, description="Maximum number of call logs")
):
    """Get call logs for an agent."""
    try:
        logs = db.execute_query("""
            SELECT cl.*, l.first_name, l.last_name, l.phone
            FROM call_logs cl
            JOIN leads l ON cl.lead_id = l.id
            WHERE cl.agent_id = %s
            ORDER BY cl.started_at DESC
            LIMIT %s
        """, (agent_id, limit))

        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Territory Management Endpoints
@app.post("/agents")
async def create_agent(agent_data: dict):
    """Create a new agent profile."""
    try:
        required_fields = ["agent_name", "email", "phone"]
        for field in required_fields:
            if field not in agent_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Ensure database manager is connected
        await db_manager.connect()

        agent_id = await db_manager.fetchval("""
            INSERT INTO agent_profiles (
                agent_name, email, phone, physical_description, car_description
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """,
        agent_data["agent_name"],
        agent_data["email"],
        agent_data["phone"],
        agent_data.get("physical_description", ""),
        agent_data.get("car_description", "")
        )

        return {"success": True, "agent_id": str(agent_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/territories")
async def get_all_territories():
    """Get all agent territories."""
    try:
        await db_manager.connect()
        territories = await db_manager.fetch("""
            SELECT t.*, a.agent_name
            FROM agent_territories t
            JOIN agent_profiles a ON t.agent_id = a.id
            WHERE a.is_active = true
            ORDER BY a.agent_name, t.county
        """)

        return [dict(t) for t in territories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}/territories")
async def get_agent_territories(agent_id: str):
    """Get territories for a specific agent."""
    try:
        territories = await territory_manager.get_agent_territories(agent_id)
        return territories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_id}/territories")
async def create_agent_territory(agent_id: str, territory_data: dict):
    """Create a territory assignment for an agent."""
    try:
        territory_id = await territory_manager.create_agent_territory(
            agent_id=agent_id,
            county=territory_data.get("county"),
            state=territory_data.get("state", "IL"),
            zip_code=territory_data.get("zip_code"),
            lead_types=territory_data.get("lead_types", [])
        )

        return {"success": True, "territory_id": territory_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/leads/{lead_id}/assign")
async def assign_lead_to_agent(lead_id: str):
    """Assign a lead to the best matching agent based on territory."""
    try:
        result = await territory_manager.assign_lead_to_agent(lead_id)
        return {
            "success": result.assigned_agent_id is not None,
            "lead_id": result.lead_id,
            "assigned_agent_id": result.assigned_agent_id,
            "assigned_agent_name": result.assigned_agent_name,
            "reason": result.reason,
            "conflicts": result.conflicts or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/territories/coverage-report")
async def get_territory_coverage_report():
    """Get territory coverage analysis."""
    try:
        report = await territory_manager.get_territory_coverage_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/leads/bulk-assign")
async def bulk_assign_unassigned_leads():
    """Bulk assign all unassigned leads to appropriate agents."""
    try:
        results = await territory_manager.bulk_reassign_unassigned_leads()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/leads/upload")
async def upload_leads(file: UploadFile = File(...)):
    """Upload leads from CSV or PDF files with OCR processing."""
    try:

        # Validate file size (max 10MB)
        if file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

        # Read file content
        content = await file.read()

        leads_data = []
        errors = []

        if file.filename.lower().endswith('.csv'):
            # Process CSV file
            try:
                # Try different encodings
                for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                    try:
                        content_str = content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    errors.append("Unable to decode file. Please ensure it's a valid CSV file.")
                    return {"success": False, "imported": 0, "errors": errors}

                # Parse CSV
                csv_reader = csv.DictReader(io.StringIO(content_str))

                for row_idx, row in enumerate(csv_reader, start=2):
                    try:
                        lead_data = process_lead_row(row, row_idx)
                        if lead_data:
                            leads_data.append(lead_data)
                    except Exception as e:
                        errors.append(f"Row {row_idx}: {str(e)}")

            except Exception as e:
                errors.append(f"CSV parsing error: {str(e)}")

        elif file.filename.lower().endswith('.pdf'):
            # Process PDF file (with OCR)
            try:
                # For now, return error message about PDF support
                # TODO: Implement PDF/OCR processing once packages are installed
                errors.append("PDF processing is not yet implemented. Please use CSV files for now.")
                return {"success": False, "imported": 0, "errors": errors}

                # Future implementation:
                # leads_data = await process_pdf_file(content)

            except Exception as e:
                errors.append(f"PDF processing error: {str(e)}")
        else:
            errors.append("Unsupported file type. Please upload CSV or PDF files only.")
            return {"success": False, "imported": 0, "errors": errors}

        # Insert leads into database
        imported_count = 0
        if leads_data:
            try:
                for lead_data in leads_data:
                    # Insert lead into database
                    result = db.execute_single("""
                        INSERT INTO leads (
                            first_name, last_name, phone, address, city, county, state, zip_code,
                            lead_type, lead_source, agent_id, created_at, uploaded_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        lead_data['first_name'], lead_data['last_name'], lead_data['phone'],
                        lead_data.get('address', ''), lead_data.get('city', ''),
                        lead_data.get('county', ''), lead_data.get('state', 'IL'),
                        lead_data.get('zip_code', ''), lead_data.get('lead_type', 'final_expense'),
                        lead_data.get('lead_source', 'upload'), lead_data.get('agent_id'),
                        datetime.now(), datetime.now()
                    ))

                    if result:
                        imported_count += 1

            except Exception as e:
                errors.append(f"Database insertion error: {str(e)}")

        return {
            "success": True,
            "imported": imported_count,
            "errors": errors,
            "total_processed": len(leads_data) + len(errors)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")


def process_lead_row(row: Dict[str, str], row_idx: int) -> Dict[str, Any]:
    """Process a single lead row from CSV and validate/normalize data."""

    # Clean and normalize field names (case-insensitive mapping)
    field_map = {
        'first_name': ['first_name', 'firstname', 'first', 'fname'],
        'last_name': ['last_name', 'lastname', 'last', 'lname'],
        'phone': ['phone', 'phone_number', 'telephone', 'mobile'],
        'address': ['address', 'street', 'street_address'],
        'city': ['city'],
        'county': ['county'],
        'state': ['state', 'st'],
        'zip_code': ['zip', 'zip_code', 'zipcode', 'postal_code'],
        'lead_type': ['lead_type', 'type', 'insurance_type', 'product'],
        'lead_source': ['lead_source', 'source', 'campaign', 'referral']
    }

    # Normalize row keys (lowercase, no spaces)
    normalized_row = {k.lower().strip().replace(' ', '_'): v.strip() for k, v in row.items() if v and v.strip()}

    # Map fields
    lead_data = {}
    for field, aliases in field_map.items():
        value = None
        for alias in aliases:
            if alias in normalized_row:
                value = normalized_row[alias]
                break
        lead_data[field] = value

    # Validate required fields
    if not lead_data.get('first_name'):
        raise ValueError("Missing required field: first_name")
    if not lead_data.get('last_name'):
        raise ValueError("Missing required field: last_name")
    if not lead_data.get('phone'):
        raise ValueError("Missing required field: phone")

    # Clean and validate phone number
    phone = re.sub(r'[^\d+]', '', lead_data['phone'])
    if not phone:
        raise ValueError("Invalid phone number")

    # Ensure phone starts with + or 1
    if not phone.startswith('+'):
        if phone.startswith('1') and len(phone) == 11:
            phone = '+' + phone
        elif len(phone) == 10:
            phone = '+1' + phone
        else:
            phone = '+1' + phone

    lead_data['phone'] = phone

    # Validate lead type
    valid_lead_types = ['final_expense', 'term_life', 'whole_life', 'mortgage_protection']
    lead_type = lead_data.get('lead_type', '').lower().replace(' ', '_')
    if lead_type not in valid_lead_types:
        lead_data['lead_type'] = 'final_expense'  # Default
    else:
        lead_data['lead_type'] = lead_type

    # Default values
    lead_data['lead_source'] = lead_data.get('lead_source') or 'upload'
    lead_data['state'] = lead_data.get('state') or 'IL'

    return lead_data


@app.post("/twilio-webhook")
async def twilio_webhook(request: Request):
    """
    Twilio webhook endpoint that connects incoming calls to LiveKit voice agent.
    This is called by Twilio when a call is answered.

    CRITICAL: Twilio sends form-urlencoded data, NOT JSON!
    We must use Request object and return Response with text/xml content type.
    """
    try:
        # Parse Twilio's form-urlencoded data (NOT JSON!)
        form_data = await request.form()

        # Extract query parameters from URL (room, lead_id, agent_id come via query string)
        query_params = request.query_params
        room_name = query_params.get("room")
        lead_id = query_params.get("lead_id")
        agent_id = query_params.get("agent_id")

        # Log Twilio's form data
        print(f"📞 Twilio webhook called")
        print(f"🏠 Room: {room_name}, Lead: {lead_id}, Agent: {agent_id}")
        print(f"📥 CallSid: {form_data.get('CallSid')}")
        print(f"📱 To: {form_data.get('To')}")
        print(f"📱 From: {form_data.get('From')}")
        print(f"📊 CallStatus: {form_data.get('CallStatus')}")

        # Create LiveKit room for the call
        if room_name and lead_id and agent_id:
            from src.voice_agent.twilio_audio_bridge import create_livekit_room_for_call, generate_stream_twiml

            print(f"🏠 Creating LiveKit room: {room_name}")
            room_created = await create_livekit_room_for_call(room_name, lead_id, agent_id)

            if room_created:
                print(f"✅ LiveKit room created successfully")

                # Generate WebSocket URL for audio streaming
                # This will connect to our WebSocket handler that bridges Twilio ↔ LiveKit
                import os
                base_url = os.getenv("LIVEKIT_WEBHOOK_BASE_URL", "https://aidn-production.up.railway.app")
                websocket_url = f"{base_url.replace('https://', 'wss://').replace('http://', 'ws://')}/twilio-stream"

                print(f"🔗 WebSocket URL: {websocket_url}")

                # Generate TwiML that streams audio to our WebSocket
                twiml_response = generate_stream_twiml(
                    websocket_url=websocket_url,
                    room_name=room_name,
                    lead_id=lead_id,
                    agent_id=agent_id
                )

                print(f"✅ Generated TwiML with Stream for LiveKit integration")
            else:
                print(f"❌ Failed to create LiveKit room")
                # Fallback to simple message
                twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">We are experiencing technical difficulties. Please try calling back in a few minutes.</Say>
    <Hangup/>
</Response>"""
        else:
            print(f"❌ Missing required parameters: room={room_name}, lead_id={lead_id}, agent_id={agent_id}")
            # Fallback to simple message
            twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Hello, please hold while we connect you to your insurance benefits specialist.</Say>
    <Pause length="2"/>
    <Say voice="Polly.Joanna">We are currently setting up your call. This will take just a moment.</Say>
    <Hangup/>
</Response>"""

        # Log the webhook call
        print(f"✅ Webhook processed successfully for lead {lead_id}")

        # CRITICAL: Return Response with text/xml content type for Twilio
        return Response(content=twiml_response, media_type="text/xml")

    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()

        # Return error TwiML with proper content type
        error_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">We apologize, but we are experiencing technical difficulties. Please try calling back in a few minutes.</Say>
    <Hangup/>
</Response>"""
        return Response(content=error_twiml, media_type="text/xml")


@app.websocket("/twilio-stream")
async def twilio_stream_handler(websocket):
    """
    WebSocket endpoint that bridges Twilio audio streams to LiveKit voice agent.

    This is where the real-time audio magic happens!
    """
    from fastapi import WebSocket
    from src.voice_agent.twilio_audio_bridge import TwilioAudioBridge

    await websocket.accept()
    print(f"🔗 Twilio WebSocket connection accepted")

    # Extract room/lead/agent info from WebSocket query parameters
    query_params = dict(websocket.query_params)
    room_name = query_params.get("room")
    lead_id = query_params.get("lead_id")
    agent_id = query_params.get("agent_id")

    print(f"🔗 WebSocket params - Room: {room_name}, Lead: {lead_id}, Agent: {agent_id}")

    if not all([room_name, lead_id, agent_id]):
        print(f"❌ Missing WebSocket parameters")
        await websocket.close(code=1000)
        return

    # Create audio bridge
    bridge = TwilioAudioBridge(
        room_name=room_name,
        lead_id=lead_id,
        agent_id=agent_id
    )

    try:
        # Process WebSocket messages in a loop
        while True:
            # Handle incoming messages from Twilio
            message = await websocket.receive_text()
            await bridge.process_twilio_message(message)

            # Send any queued audio back to Twilio
            outgoing_audio = await bridge.get_outgoing_audio()
            if outgoing_audio:
                await websocket.send_text(outgoing_audio)

    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"🔗 WebSocket disconnected")
        await bridge.disconnect()


if __name__ == "__main__":
    print("🚀 Starting AIDN API Server")
    print("📊 Dashboard: http://localhost:3000")
    print("🔌 API Docs: http://localhost:8000/docs")
    print("📞 Twilio Webhook: /twilio-webhook")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )