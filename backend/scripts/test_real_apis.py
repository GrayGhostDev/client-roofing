#!/usr/bin/env python3
"""
Real Data API Testing Script
Tests all configured data sources and reports connectivity, data quality, and sample outputs
"""

import os
import sys
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import requests
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.intelligence.real_data_sources import (
    WeatherDataCollector,
    NOAAStormDataCollector,
    PublicPropertyDataCollector,
    SocialMediaDataCollector
)

# =============================================================================
# Test Configuration
# =============================================================================

TEST_LOCATIONS = [
    {"city": "Bloomfield Hills", "state": "MI", "zip": "48304"},
    {"city": "Birmingham", "state": "MI", "zip": "48009"},
    {"city": "Grosse Pointe", "state": "MI", "zip": "48230"},
]

# =============================================================================
# Test Functions
# =============================================================================

def print_header(text: str):
    """Print formatted section header"""
    print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{text.center(80)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

def print_error(text: str):
    """Print error message"""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")

def print_info(text: str):
    """Print info message"""
    print(f"{Fore.BLUE}ℹ {text}{Style.RESET_ALL}")

async def test_weather_api():
    """Test Weather.gov API (no auth required)"""
    print_header("Testing Weather.gov API")

    collector = WeatherDataCollector()
    success = False
    alert_count = 0
    sample_alerts = []

    try:
        print_info("Fetching severe weather alerts for Michigan...")
        alerts = await collector.get_severe_weather_alerts("MI")

        if alerts:
            alert_count = len(alerts)
            sample_alerts = alerts[:3]  # First 3 alerts
            success = True
            print_success(f"Retrieved {alert_count} active weather alerts")

            for i, alert in enumerate(sample_alerts, 1):
                print(f"\n  Alert {i}:")
                print(f"    Event: {alert.get('event', 'Unknown')}")
                print(f"    Severity: {alert.get('severity', 'Unknown')}")
                print(f"    Area: {alert.get('area_desc', 'Unknown')}")
                print(f"    Headline: {alert.get('headline', 'No headline')[:100]}...")
        else:
            print_warning("No active alerts (this is normal if weather is calm)")
            success = True  # Not an error, just no alerts

    except Exception as e:
        print_error(f"Weather.gov API test failed: {str(e)}")
        print_info("This usually indicates SSL certificate issues")

    return {
        "service": "Weather.gov API",
        "success": success,
        "data_count": alert_count,
        "sample_data": sample_alerts,
        "cost": "FREE",
        "auth_required": False
    }

async def test_noaa_api():
    """Test NOAA Storm Events API"""
    print_header("Testing NOAA Storm Events API")

    api_token = os.getenv('NOAA_API_TOKEN')

    if not api_token or api_token == 'your-key-here':
        print_warning("NOAA API token not configured")
        print_info("Register at: https://www.ncdc.noaa.gov/cdo-web/token")
        return {
            "service": "NOAA API",
            "success": False,
            "error": "API token not configured",
            "cost": "FREE",
            "auth_required": True
        }

    collector = NOAAStormDataCollector()
    success = False
    storm_count = 0
    sample_storms = []

    try:
        print_info("Fetching recent storm events for Michigan...")
        storms = await collector.get_recent_storms("MICHIGAN", days_back=90)

        if storms:
            storm_count = len(storms)
            sample_storms = storms[:3]
            success = True
            print_success(f"Retrieved {storm_count} storm events (last 90 days)")

            for i, storm in enumerate(sample_storms, 1):
                print(f"\n  Storm {i}:")
                print(f"    Type: {storm.get('event_type', 'Unknown')}")
                print(f"    Date: {storm.get('begin_date', 'Unknown')}")
                print(f"    Location: {storm.get('location', 'Unknown')}")
                print(f"    Damage: ${storm.get('damage_property', 0):,.0f}")
        else:
            print_warning("No recent storms found")
            success = True

    except Exception as e:
        print_error(f"NOAA API test failed: {str(e)}")

    return {
        "service": "NOAA Storm Events API",
        "success": success,
        "data_count": storm_count,
        "sample_data": sample_storms,
        "cost": "FREE",
        "auth_required": True
    }

async def test_zillow_api():
    """Test Zillow Property Data API"""
    print_header("Testing Zillow API")

    api_key = os.getenv('ZILLOW_API_KEY')

    if not api_key or api_key == 'your-key-here':
        print_warning("Zillow API key not configured")
        print_info("Register at: https://www.zillow.com/howto/api/APIOverview.htm")
        return {
            "service": "Zillow API",
            "success": False,
            "error": "API key not configured",
            "cost": "FREE (1,000 calls/day)",
            "auth_required": True
        }

    collector = PublicPropertyDataCollector()
    success = False
    property_count = 0
    sample_properties = []

    try:
        print_info(f"Fetching property data for {TEST_LOCATIONS[0]['city']}...")
        properties = await collector.get_premium_properties(
            TEST_LOCATIONS[0]['city'],
            TEST_LOCATIONS[0]['state'],
            min_value=500000
        )

        if properties:
            property_count = len(properties)
            sample_properties = properties[:3]
            success = True
            print_success(f"Retrieved {property_count} premium properties")

            for i, prop in enumerate(sample_properties, 1):
                print(f"\n  Property {i}:")
                print(f"    Address: {prop.get('address', 'Unknown')}")
                print(f"    Value: ${prop.get('estimated_value', 0):,.0f}")
                print(f"    Bedrooms: {prop.get('bedrooms', 'N/A')}")
                print(f"    Year Built: {prop.get('year_built', 'N/A')}")
        else:
            print_warning("No properties found")

    except Exception as e:
        print_error(f"Zillow API test failed: {str(e)}")

    return {
        "service": "Zillow API",
        "success": success,
        "data_count": property_count,
        "sample_data": sample_properties,
        "cost": "FREE (1,000 calls/day)",
        "auth_required": True
    }

async def test_social_media_apis():
    """Test Twitter and Facebook APIs"""
    print_header("Testing Social Media APIs")

    twitter_token = os.getenv('TWITTER_BEARER_TOKEN')
    facebook_token = os.getenv('FACEBOOK_ACCESS_TOKEN')

    results = []

    # Test Twitter
    if not twitter_token or twitter_token == 'your-key-here':
        print_warning("Twitter API token not configured")
        print_info("Register at: https://developer.twitter.com/")
        results.append({
            "service": "Twitter API",
            "success": False,
            "error": "API token not configured",
            "cost": "FREE (500K tweets/month)"
        })
    else:
        collector = SocialMediaDataCollector()
        try:
            print_info("Searching Twitter for roofing mentions...")
            tweets = await collector.search_twitter_mentions(
                keywords=["roof repair", "roof damage"],
                location="Michigan"
            )

            if tweets:
                print_success(f"Retrieved {len(tweets)} tweets")
                for i, tweet in enumerate(tweets[:2], 1):
                    print(f"\n  Tweet {i}:")
                    print(f"    Author: {tweet.get('author', 'Unknown')}")
                    print(f"    Text: {tweet.get('text', 'No text')[:100]}...")
                    print(f"    Engagement: {tweet.get('engagement_score', 0)}/100")

                results.append({
                    "service": "Twitter API",
                    "success": True,
                    "data_count": len(tweets),
                    "sample_data": tweets[:2],
                    "cost": "FREE (500K tweets/month)"
                })
            else:
                print_warning("No recent tweets found")
                results.append({
                    "service": "Twitter API",
                    "success": True,
                    "data_count": 0,
                    "cost": "FREE (500K tweets/month)"
                })

        except Exception as e:
            print_error(f"Twitter API test failed: {str(e)}")
            results.append({
                "service": "Twitter API",
                "success": False,
                "error": str(e),
                "cost": "FREE (500K tweets/month)"
            })

    # Test Facebook
    if not facebook_token or facebook_token == 'your-key-here':
        print_warning("\nFacebook API token not configured")
        print_info("Register at: https://developers.facebook.com/")
        results.append({
            "service": "Facebook API",
            "success": False,
            "error": "API token not configured",
            "cost": "FREE (basic access)"
        })
    else:
        print_info("\nSearching Facebook for roofing groups...")
        # Facebook Graph API test would go here
        print_warning("Facebook Graph API requires app review for full access")
        results.append({
            "service": "Facebook API",
            "success": False,
            "error": "Requires app review",
            "cost": "FREE (basic access)"
        })

    return results

async def test_county_assessors():
    """Test county assessor APIs"""
    print_header("Testing County Assessor APIs")

    print_info("Testing Oakland County assessor data...")

    # Oakland County has public API (no auth)
    try:
        url = "https://gis.oakgov.com/arcgis/rest/services/base/PropertyInformation/MapServer/0/query"
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "json",
            "resultRecordCount": 5
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])

            if features:
                print_success(f"Retrieved {len(features)} property records")

                for i, feature in enumerate(features[:2], 1):
                    attrs = feature.get('attributes', {})
                    print(f"\n  Property {i}:")
                    print(f"    Parcel ID: {attrs.get('PARCEL_ID', 'Unknown')}")
                    print(f"    Address: {attrs.get('SITE_ADDR', 'Unknown')}")
                    print(f"    Value: ${attrs.get('TAXABLE_VALUE', 0):,.0f}")

                return {
                    "service": "County Assessor APIs",
                    "success": True,
                    "data_count": len(features),
                    "sample_data": [f.get('attributes') for f in features[:2]],
                    "cost": "FREE",
                    "auth_required": False
                }

        print_warning("No data returned from assessor API")
        return {
            "service": "County Assessor APIs",
            "success": False,
            "error": "No data returned",
            "cost": "FREE"
        }

    except Exception as e:
        print_error(f"County assessor API test failed: {str(e)}")
        return {
            "service": "County Assessor APIs",
            "success": False,
            "error": str(e),
            "cost": "FREE"
        }

# =============================================================================
# Main Test Runner
# =============================================================================

async def run_all_tests():
    """Run all API tests and generate report"""
    print_header("iSwitch Roofs - Real Data API Testing")
    print(f"{Fore.BLUE}Testing all configured data sources...{Style.RESET_ALL}")
    print(f"{Fore.BLUE}Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}\n")

    results = []

    # Test each data source
    results.append(await test_weather_api())
    results.append(await test_noaa_api())
    results.append(await test_zillow_api())

    social_results = await test_social_media_apis()
    results.extend(social_results)

    results.append(await test_county_assessors())

    # Generate summary report
    print_header("Test Summary Report")

    total_tests = len(results)
    successful_tests = sum(1 for r in results if r.get('success'))
    failed_tests = total_tests - successful_tests

    print(f"{Fore.BLUE}Total Tests:{Style.RESET_ALL} {total_tests}")
    print(f"{Fore.GREEN}Successful:{Style.RESET_ALL} {successful_tests}")
    print(f"{Fore.RED}Failed:{Style.RESET_ALL} {failed_tests}")
    print()

    # Detailed results
    print(f"{Fore.CYAN}{'Service':<30} {'Status':<15} {'Data Count':<15} {'Cost'}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'-' * 80}{Style.RESET_ALL}")

    for result in results:
        service = result['service']
        status = f"{Fore.GREEN}✓ SUCCESS{Style.RESET_ALL}" if result['success'] else f"{Fore.RED}✗ FAILED{Style.RESET_ALL}"
        data_count = result.get('data_count', 'N/A')
        cost = result.get('cost', 'Unknown')

        print(f"{service:<30} {status:<24} {str(data_count):<15} {cost}")

        if not result['success'] and 'error' in result:
            print(f"  {Fore.RED}Error: {result['error']}{Style.RESET_ALL}")

    print()

    # Recommendations
    print_header("Recommendations")

    if failed_tests == 0:
        print_success("All data sources configured and operational!")
        print_info("You can now generate real leads using the Live Data Generator")
        print_info("Expected lead volume: 500-800 per month")
    else:
        print_warning(f"{failed_tests} data source(s) need configuration")
        print()

        # Check what needs configuration
        needs_config = [r for r in results if not r['success'] and 'not configured' in r.get('error', '')]

        if needs_config:
            print(f"{Fore.YELLOW}Priority: Register for these FREE APIs:{Style.RESET_ALL}")
            for result in needs_config:
                print(f"  • {result['service']}")
            print()

        print(f"{Fore.BLUE}Next Steps:{Style.RESET_ALL}")
        print("  1. Register for missing API keys")
        print("  2. Add keys to backend/.env file")
        print("  3. Run this test script again")
        print("  4. Start generating real leads!")

    # Save detailed report
    report_file = "api_test_report.json"
    with open(report_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "successful": successful_tests,
                "failed": failed_tests
            },
            "results": results
        }, f, indent=2)

    print()
    print_info(f"Detailed report saved to: {report_file}")
    print()

    return successful_tests == total_tests

# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    try:
        all_passed = asyncio.run(run_all_tests())
        sys.exit(0 if all_passed else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Test failed with error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)
