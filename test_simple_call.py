#!/usr/bin/env python3
"""
Simple Test Call for WebSocket Audio Counting
"""

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

def make_test_call():
    """Make a test call to verify WebSocket audio counting"""

    # Twilio credentials
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

    if not all([account_sid, auth_token, twilio_number]):
        print("❌ Missing Twilio environment variables")
        return

    # Create Twilio client
    client = Client(account_sid, auth_token)

    # The webhook URL (Railway deployment)
    webhook_url = "https://aidn-production.up.railway.app/twilio-webhook"
    target_phone = "+19086197628"

    print(f"🚀 Making test call for WebSocket audio counting...")
    print(f"📞 Calling: {target_phone}")
    print(f"🔗 Webhook: {webhook_url}")

    # Make the call
    call = client.calls.create(
        url=webhook_url,
        to=target_phone,
        from_=twilio_number,
        timeout=20
    )

    print(f"✅ Call initiated!")
    print(f"📱 Call SID: {call.sid}")
    print(f"📊 Status: {call.status}")
    print()
    print("📋 What should happen:")
    print("1. Your phone should ring")
    print("2. You'll hear: 'Connecting you to our test system. Please say hello.'")
    print("3. Say 'Hello' or 'Testing' a few times")
    print("4. Call will hang up after ~10 seconds")
    print()
    print("📊 Check Railway logs to see audio package counting!")

if __name__ == "__main__":
    make_test_call()