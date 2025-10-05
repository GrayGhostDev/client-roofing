#!/usr/bin/env python3
"""
Environment Configuration Checker
Verify Supabase and other critical environment variables are set
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_environment():
    """Check critical environment variables"""
    print("🔍 Environment Configuration Check")
    print("=" * 50)

    # Critical Supabase variables
    supabase_vars = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
        "SUPABASE_SERVICE_KEY": os.getenv("SUPABASE_SERVICE_KEY"),
        "DATABASE_URL": os.getenv("DATABASE_URL"),
    }

    # Flask/API variables
    api_vars = {
        "SECRET_KEY": os.getenv("SECRET_KEY"),
        "FLASK_APP": os.getenv("FLASK_APP"),
        "FLASK_ENV": os.getenv("FLASK_ENV"),
    }

    print("📋 Supabase Configuration:")
    for key, value in supabase_vars.items():
        if value:
            # Show first 20 chars for security
            masked_value = f"{value[:20]}{'...' if len(value) > 20 else ''}"
            print(f"✅ {key}: {masked_value}")
        else:
            print(f"❌ {key}: NOT SET")

    print("\n📋 Flask Configuration:")
    for key, value in api_vars.items():
        if value:
            if key == "SECRET_KEY":
                print(f"✅ {key}: {'*' * min(len(value), 20)}")
            else:
                print(f"✅ {key}: {value}")
        else:
            print(f"❌ {key}: NOT SET")

    # Check .env file exists
    env_file = Path(__file__).parent.parent / ".env"
    print("\n📄 Environment File:")
    if env_file.exists():
        print(f"✅ .env file exists at: {env_file}")
    else:
        print(f"❌ .env file missing at: {env_file}")
        print("📋 Copy .env.example to .env and configure values")

    # Summary
    missing_critical = []
    for key in ["SUPABASE_URL", "SUPABASE_KEY", "SECRET_KEY"]:
        if not os.getenv(key):
            missing_critical.append(key)

    print("\n📊 Status Summary:")
    if not missing_critical:
        print("✅ All critical environment variables are set")
        print("🚀 Ready to create database tables")
        return True
    else:
        print(f"❌ Missing critical variables: {', '.join(missing_critical)}")
        print("🔧 Configure these variables in .env file before proceeding")
        return False


if __name__ == "__main__":
    success = check_environment()
    if not success:
        print("\n⚠️ Next Steps:")
        print("1. Copy .env.example to .env")
        print("2. Get Supabase credentials from dashboard")
        print("3. Set all required environment variables")
        print("4. Run this script again to verify")
    else:
        print("\n✅ Environment Ready!")
        print("Now execute the database creation via Supabase dashboard")
        print("See DATABASE_SETUP_MANUAL.md for complete instructions")
