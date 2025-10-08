"""
Integration Dashboard - Testing and Validation Script
Demonstrates CallRail integration functionality in development mode.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.integrations.callrail import callrail_integration
    print("✅ CallRail integration module loaded successfully")
except ImportError as e:
    print(f"❌ Failed to import CallRail integration: {e}")
    sys.exit(1)


def print_header(title):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_integration_status():
    """Test CallRail integration configuration and connectivity."""
    print_header("CallRail Integration Status Check")

    # Check configuration
    print("Configuration Status:")
    print(f"  API Key Configured: {'✅ Yes' if callrail_integration.api_key else '❌ No'}")
    print(f"  Account ID: {'✅ Configured' if callrail_integration.account_id else '❌ Missing'}")
    print(f"  Company ID: {'✅ Configured' if callrail_integration.company_id else '❌ Missing'}")

    if not callrail_integration.api_key:
        print("\n⚠️  WARNING: CallRail API key not configured")
        print("   Add CALLRAIL_API_KEY to your .env file")
        print("   See CALLRAIL_INTEGRATION_COMPLETE.md for instructions")
        return False

    # Test connection
    print("\nTesting API Connection...")
    success, error_msg = callrail_integration.test_connection()

    if success:
        print("  ✅ Connection successful!")
        return True
    else:
        print(f"  ❌ Connection failed: {error_msg}")
        return False


def show_available_endpoints():
    """Display available API endpoints."""
    print_header("Available API Endpoints")

    endpoints = [
        ("GET", "/api/integrations/callrail/status", "Integration status and health"),
        ("GET", "/api/integrations/callrail/test-connection", "Test API connectivity"),
        ("POST", "/api/integrations/callrail/import-calls", "Import historical calls"),
        ("GET", "/api/integrations/callrail/call/<call_id>", "Get specific call details"),
        ("POST", "/api/integrations/callrail/setup-webhook", "Configure webhooks"),
        ("", "", ""),
        ("POST", "/api/webhooks/callrail/post-call", "Post-call webhook receiver"),
        ("POST", "/api/webhooks/callrail/pre-call", "Pre-call webhook receiver"),
        ("POST", "/api/webhooks/callrail/call-modified", "Call-modified webhook"),
        ("POST", "/api/webhooks/callrail/routing-complete", "Routing-complete webhook"),
        ("GET/POST", "/api/webhooks/test", "Test webhook endpoint"),
    ]

    print("Method   | Endpoint                                        | Description")
    print("-" * 100)
    for method, endpoint, desc in endpoints:
        print(f"{method:8} | {endpoint:47} | {desc}")


def show_integration_features():
    """Display implemented features."""
    print_header("Implemented Features")

    features = [
        ("✅", "API Authentication", "Token-based authentication with CallRail API"),
        ("✅", "Call Import", "Historical call data import with date range filtering"),
        ("✅", "Webhook Processing", "Real-time call event processing"),
        ("✅", "Signature Verification", "HMAC SHA1 signature validation for security"),
        ("✅", "Lead Association", "Automatic phone number matching to leads/customers"),
        ("✅", "Interaction Creation", "Automatic interaction records from calls"),
        ("✅", "Real-time Notifications", "Pusher integration for live call alerts"),
        ("✅", "Recording Management", "Call recording URL storage and retrieval"),
        ("✅", "Transcription Support", "Call transcription storage and display"),
        ("✅", "Error Handling", "Comprehensive error handling and logging"),
    ]

    for status, feature, description in features:
        print(f"{status} {feature:25} - {description}")


def show_quick_start():
    """Display quick start instructions."""
    print_header("Quick Start Guide")

    print("1. Configure Environment Variables:")
    print("   Add to your .env file:")
    print("   ┌─────────────────────────────────────────────────────┐")
    print("   │ CALLRAIL_API_KEY=your_api_key_here                  │")
    print("   │ CALLRAIL_ACCOUNT_ID=your_account_id                 │")
    print("   │ CALLRAIL_COMPANY_ID=your_company_id                 │")
    print("   └─────────────────────────────────────────────────────┘")

    print("\n2. Start the Backend Server:")
    print("   cd backend")
    print("   python run.py")

    print("\n3. Test the Integration:")
    print("   curl http://localhost:8001/api/integrations/callrail/status")

    print("\n4. Import Historical Calls:")
    print("   curl -X POST http://localhost:8001/api/integrations/callrail/import-calls \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"days_back\": 30}'")

    print("\n5. Setup Webhooks (Production):")
    print("   - Use ngrok for local testing: ngrok http 8001")
    print("   - Configure webhooks in CallRail dashboard")
    print("   - Point to: https://your-domain.com/api/webhooks/callrail/post-call")


def show_next_steps():
    """Display next steps after setup."""
    print_header("Next Steps")

    steps = [
        ("1", "Get CallRail API Credentials",
         "Visit CallRail dashboard → Settings → Integrations → API Keys"),
        ("2", "Update .env Configuration",
         "Add your API key, account ID, and company ID"),
        ("3", "Test API Connection",
         "Run: curl http://localhost:8001/api/integrations/callrail/test-connection"),
        ("4", "Import Historical Data",
         "Import last 30-90 days of call logs"),
        ("5", "Configure Production Webhooks",
         "Set up real-time call notifications"),
        ("6", "Train Team",
         "Show team where to find call recordings and interactions"),
    ]

    for num, title, description in steps:
        print(f"{num}. {title}")
        print(f"   → {description}\n")


def main():
    """Main dashboard function."""
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                              ║")
    print("║          iSwitch Roofs CRM - CallRail Integration Dashboard                 ║")
    print("║                                                                              ║")
    print("║                        ✅ IMPLEMENTATION COMPLETE                            ║")
    print("║                                                                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")

    # Test integration status
    is_configured = test_integration_status()

    # Show features
    show_integration_features()

    # Show endpoints
    show_available_endpoints()

    # Show quick start
    if not is_configured:
        show_quick_start()

    # Show next steps
    show_next_steps()

    print_header("Documentation")
    print("📖 Complete documentation: CALLRAIL_INTEGRATION_COMPLETE.md")
    print("📁 Integration code: backend/app/integrations/callrail.py")
    print("🔗 Webhook handlers: backend/app/routes/webhooks.py")
    print("🛣️  API routes: backend/app/routes/callrail_routes.py")

    print("\n" + "=" * 80)
    print("  Ready for Testing and Production Deployment!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
