#!/usr/bin/env python3
"""
Simple test script to create a lead and initiate a call
"""

import os
import asyncio
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('/Users/thomasroldan/Documents/GitHub/AIDN')

async def test_phone_call():
    """Create a test lead and initiate a call"""

    try:
        # Import database components
        from src.shared.database.connection import DatabaseManager
        from src.shared.models.lead import Lead
        from uuid import uuid4

        # Initialize database
        db = DatabaseManager()
        await db.connect()

        # Create test lead for Thomas
        print("🔍 Creating test lead for Thomas Roldan...")

        lead_id = await db.fetchval("""
            INSERT INTO leads (
                first_name, last_name, phone, address, city, county, state, zip_code,
                lead_type, lead_source, agent_id, created_at, uploaded_at, call_outcome
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                      (SELECT id FROM agent_profiles WHERE is_active = true LIMIT 1),
                      $11, $12, $13)
            RETURNING id
        """,
        'Thomas', 'Roldan', '+19086197628',
        '123 Test Street', 'Wesley Chapel', 'Pasco', 'FL', '33543',
        'final_expense', 'test_call', datetime.now(), datetime.now(), 'fresh'
        )

        print(f"✅ Created test lead with ID: {lead_id}")

        # Get the agent assigned to this lead
        agent = await db.fetchrow('SELECT * FROM agent_profiles WHERE is_active = true LIMIT 1')
        print(f"📋 Assigned to agent: {agent['agent_name']}")

        # Now try to initiate a call using Twilio directly
        from twilio.rest import Client

        # Initialize Twilio client
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

        if not all([account_sid, auth_token, twilio_number]):
            print("❌ Missing Twilio configuration!")
            return

        print(f"📞 Using Twilio number: {twilio_number}")

        twilio_client = Client(account_sid, auth_token)

        # Create a simple test call (we'll configure the webhook later)
        webhook_url = "https://webhook.site/unique-id"  # Temporary webhook for testing

        print(f"🔄 Initiating call to +19086197628...")

        call = twilio_client.calls.create(
            url=webhook_url,
            to="+19086197628",
            from_=twilio_number,
            timeout=20,  # Ring timeout in seconds
            record=False,  # Disable recording for test
            method="POST"
        )

        print(f"✅ Call initiated successfully!")
        print(f"📞 Call SID: {call.sid}")
        print(f"📱 Calling: +19086197628")
        print(f"🔗 Webhook URL: {webhook_url}")
        print(f"📊 Status: {call.status}")

        # Log the call in database
        await db.execute("""
            INSERT INTO call_logs (
                lead_id, agent_id, call_sid, started_at, outcome
            ) VALUES ($1, $2, $3, $4, $5)
        """, lead_id, agent['id'], call.sid, datetime.now(), 'initiated')

        print(f"💾 Logged call in database")

        await db.close()

        return call.sid

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 AIDN Test Call System")
    print("=" * 40)

    result = asyncio.run(test_phone_call())

    if result:
        print(f"\n🎉 Test completed successfully!")
        print(f"Call ID: {result}")
        print(f"\n📱 Check your phone for the incoming call!")
        print(f"Note: This is a test call with a simple webhook.")
        print(f"For full voice agent functionality, the LiveKit integration needs to be configured.")
    else:
        print(f"\n❌ Test failed. Please check the error messages above.")