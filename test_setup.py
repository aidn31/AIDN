#!/usr/bin/env python3
"""
AIDN Setup Test Script
======================

Basic test to verify AIDN setup is working correctly.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.shared.database import DatabaseManager
from src.shared.database.migration import AIDNMigration
from src.voice_agent.objection_handler import ObjectionHandler


async def test_database_connection():
    """Test database connection."""
    print("🔍 Testing database connection...")

    # Use a test database URL or default
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set. Using default test URL.")
        db_url = "postgresql://aidnuser:aidnpass123@localhost:5432/aidn"

    try:
        db_manager = DatabaseManager(db_url)
        await db_manager.connect()

        # Test basic query
        result = await db_manager.fetchval("SELECT 1")
        assert result == 1

        await db_manager.disconnect()
        print("✅ Database connection successful")
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_migration():
    """Test database migration."""
    print("🔍 Testing database migration...")

    try:
        migration = AIDNMigration()
        status = await migration.check_migration_status()

        if status.get("migrated"):
            print("✅ Database migration already completed")
            print(f"   - Tables exist: {status.get('tables_exist')}")
            print(f"   - Sample data: {status.get('sample_data')}")
            print(f"   - Lead count: {status.get('lead_count')}")
            print(f"   - Agent count: {status.get('agent_count')}")
        else:
            print("⚠️  Database not migrated. Run migration with:")
            print("   python -m src.shared.database.migration")

        return True

    except Exception as e:
        print(f"❌ Migration check failed: {e}")
        return False


def test_objection_handler():
    """Test objection handler."""
    print("🔍 Testing objection handler...")

    try:
        handler = ObjectionHandler()

        # Test classification
        test_cases = [
            "I'm not interested",
            "How did you get my number?",
            "Is this a scam?",
            "I'm busy right now",
            "I already have insurance"
        ]

        for test_case in test_cases:
            classification = handler.classify_objection(test_case)
            print(f"   '{test_case}' → {classification}")

        print("✅ Objection handler working correctly")
        return True

    except Exception as e:
        print(f"❌ Objection handler test failed: {e}")
        return False


def test_imports():
    """Test that all imports work."""
    print("🔍 Testing imports...")

    try:
        # Test core imports
        from src.shared.models import Lead, AgentProfile, AppointmentSlot
        from src.shared.database import DatabaseManager, LeadRepository
        from src.voice_agent.aidn_agent import AIDNVoiceAgent
        from src.voice_agent.objection_handler import ObjectionHandler

        print("✅ All imports successful")
        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during imports: {e}")
        return False


def test_environment():
    """Test environment configuration."""
    print("🔍 Testing environment configuration...")

    required_vars = [
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "DEEPGRAM_API_KEY"
    ]

    optional_vars = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER",
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET"
    ]

    missing_required = []
    missing_optional = []

    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)

    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)

    if missing_required:
        print(f"❌ Missing required environment variables: {', '.join(missing_required)}")
        return False
    else:
        print("✅ All required environment variables present")

    if missing_optional:
        print(f"⚠️  Missing optional environment variables: {', '.join(missing_optional)}")
        print("   These are needed for full functionality but not required for testing")

    return True


async def main():
    """Run all tests."""
    print("🚀 AIDN Setup Test\n")

    tests = [
        ("Environment", test_environment),
        ("Imports", test_imports),
        ("Objection Handler", test_objection_handler),
        ("Database Connection", test_database_connection),
        ("Migration Status", test_migration),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*50)
    print("AIDN SETUP TEST SUMMARY")
    print("="*50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
        if result:
            passed += 1

    print(f"\nResult: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! AIDN setup is working correctly.")
        print("\nNext steps:")
        print("1. If migration not completed, run: python -m src.shared.database.migration")
        print("2. Start dashboard: streamlit run src/dashboard-agent/streamlit_app.py")
        print("3. Test voice agent: python -m src.voice_agent.main console")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        return 1

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)