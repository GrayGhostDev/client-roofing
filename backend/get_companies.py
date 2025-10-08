#!/usr/bin/env python3
"""
Fetch CallRail Companies for Account
"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.getenv('CALLRAIL_API_KEY')
account_id = 'ACC0199bb04fc0c7b269e869723c32c226a'  # iSwitch-Roofs

headers = {
    'Authorization': f'Token token={api_key}',
    'Accept': 'application/json'
}

print("🔍 Fetching companies for iSwitch-Roofs account...")
print()

response = requests.get(
    f'https://api.callrail.com/v3/a/{account_id}/companies.json',
    headers=headers,
    timeout=10
)

if response.status_code == 200:
    companies = response.json().get('companies', [])
    print(f"✅ Found {len(companies)} company(ies):\n")
    for company in companies:
        print(f"Company Name: {company.get('name')}")
        print(f"Company ID: {company.get('id')}")
        print(f"Status: {company.get('status')}")
        print(f"Time Zone: {company.get('time_zone')}")
        print(f"Created: {company.get('created_at')}")
        print("-" * 60)
else:
    print(f"❌ Error: Status {response.status_code}")
    print(response.text)
