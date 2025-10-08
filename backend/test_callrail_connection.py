#!/usr/bin/env python3
"""
Test CallRail API Connection
Validates credentials and tests basic API connectivity
"""

import os
import sys
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

def test_callrail_connection():
    """Test CallRail API connection with configured credentials."""

    print("=" * 80)
    print("CallRail API Connection Test")
    print("=" * 80)
    print()

    # Get credentials from environment
    api_key = os.getenv('CALLRAIL_API_KEY')
    account_id = os.getenv('CALLRAIL_ACCOUNT_ID')
    company_id = os.getenv('CALLRAIL_COMPANY_ID')

    # Display configuration
    print("📋 Configuration:")
    print(f"  API Key: {'✅ Set' if api_key else '❌ Missing'} ({api_key[:20]}... if api_key else '')")
    print(f"  Account ID: {account_id if account_id else '❌ Missing'}")
    print(f"  Company ID: {company_id if company_id else '❌ Missing'}")
    print()

    if not api_key:
        print("❌ ERROR: CALLRAIL_API_KEY not found in environment")
        print("   Please add your API key to the .env file")
        return False

    if not company_id:
        print("❌ ERROR: CALLRAIL_COMPANY_ID not found in environment")
        return False

    # Test 1: Get Account Information
    print("🔍 Test 1: Fetching Account Information...")
    try:
        headers = {
            'Authorization': f'Token token={api_key}',
            'Accept': 'application/json'
        }

        # Try to get account details
        response = requests.get(
            'https://api.callrail.com/v3/a.json',
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            accounts = response.json().get('accounts', [])
            print(f"  ✅ SUCCESS: Found {len(accounts)} account(s)")
            for account in accounts:
                print(f"     • {account.get('name')} (ID: {account.get('id')})")
        elif response.status_code == 401:
            print("  ❌ FAILED: Invalid API key (401 Unauthorized)")
            print(f"     Response: {response.text}")
            return False
        else:
            print(f"  ⚠️  WARNING: Unexpected status code: {response.status_code}")
            print(f"     Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"  ❌ ERROR: Request failed - {str(e)}")
        return False

    print()

    # Test 2: Get Company Information
    print(f"🔍 Test 2: Fetching Company Information (ID: {company_id})...")
    try:
        response = requests.get(
            f'https://api.callrail.com/v3/a/{account_id}/companies/{company_id}.json',
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            company = response.json()
            print(f"  ✅ SUCCESS: Company found")
            print(f"     • Name: {company.get('name', 'N/A')}")
            print(f"     • Status: {company.get('status', 'N/A')}")
            print(f"     • Time Zone: {company.get('time_zone', 'N/A')}")
        elif response.status_code == 404:
            print(f"  ⚠️  WARNING: Company ID {company_id} not found")
            print("     This might be okay if account_id needs adjustment")
        else:
            print(f"  ⚠️  Status code: {response.status_code}")
            print(f"     Response: {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️  WARNING: Request failed - {str(e)}")

    print()

    # Test 3: List Recent Calls (if company access works)
    print(f"🔍 Test 3: Fetching Recent Calls...")
    try:
        response = requests.get(
            f'https://api.callrail.com/v3/a/{account_id}/calls.json',
            headers=headers,
            params={'per_page': 5},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            calls = data.get('calls', [])
            total = data.get('total_records', 0)
            print(f"  ✅ SUCCESS: Found {total} total calls")
            print(f"     Showing {len(calls)} most recent:")
            for call in calls[:3]:
                print(f"     • {call.get('formatted_customer_phone')} - {call.get('formatted_business_phone')}")
                print(f"       Duration: {call.get('duration')}s | Status: {call.get('answered', False) and 'Answered' or 'Missed'}")
        elif response.status_code == 404:
            print(f"  ⚠️  WARNING: Calls endpoint returned 404")
            print("     Account ID might need adjustment")
        else:
            print(f"  ⚠️  Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️  WARNING: Request failed - {str(e)}")

    print()
    print("=" * 80)
    print("✅ CallRail API connection test completed!")
    print()
    print("📝 Next Steps:")
    print("   1. If Account ID needs updating, check CallRail dashboard")
    print("   2. Start backend server: cd backend && python run.py")
    print("   3. Test integration endpoint: curl http://localhost:8001/api/integrations/callrail/status")
    print("=" * 80)

    return True


if __name__ == '__main__':
    success = test_callrail_connection()
    sys.exit(0 if success else 1)
