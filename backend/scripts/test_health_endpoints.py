#!/usr/bin/env python3
"""
Health Endpoint Test Script
Verifies all monitoring endpoints are functioning correctly
"""

import json
import sys
import time
from typing import Dict, Any

import requests


def test_endpoint(url: str, endpoint: str, expected_status: int = 200) -> Dict[str, Any]:
    """
    Test a health endpoint

    Args:
        url: Base URL
        endpoint: Endpoint path
        expected_status: Expected HTTP status code

    Returns:
        Test result dictionary
    """
    full_url = f"{url}{endpoint}"

    try:
        start_time = time.time()
        response = requests.get(full_url, timeout=5)
        duration = (time.time() - start_time) * 1000

        return {
            "endpoint": endpoint,
            "status": "✅ PASS" if response.status_code == expected_status else "❌ FAIL",
            "http_status": response.status_code,
            "expected_status": expected_status,
            "response_time_ms": round(duration, 2),
            "response": response.json() if response.headers.get("content-type") == "application/json" else response.text,
        }
    except Exception as e:
        return {
            "endpoint": endpoint,
            "status": "❌ ERROR",
            "error": str(e),
        }


def main():
    """Run health endpoint tests"""
    # Configuration
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"

    print(f"Testing monitoring endpoints on {base_url}")
    print("=" * 80)
    print()

    # Define tests
    tests = [
        ("/health", 200, "Basic health check"),
        ("/health/live", 200, "Liveness probe"),
        ("/health/ready", 200, "Readiness probe"),
        ("/metrics", 200, "Metrics endpoint"),
    ]

    results = []

    for endpoint, expected_status, description in tests:
        print(f"Testing {description} ({endpoint})...")
        result = test_endpoint(base_url, endpoint, expected_status)
        results.append(result)

        # Print result
        print(f"  Status: {result['status']}")
        if "http_status" in result:
            print(f"  HTTP Status: {result['http_status']} (expected {result['expected_status']})")
            print(f"  Response Time: {result['response_time_ms']}ms")
        if "error" in result:
            print(f"  Error: {result['error']}")
        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    passed = sum(1 for r in results if r.get("status") == "✅ PASS")
    total = len(results)

    print(f"Tests Passed: {passed}/{total}")
    print(f"Pass Rate: {(passed/total)*100:.1f}%")
    print()

    # Detailed results
    print("Detailed Results:")
    print("-" * 80)

    for result in results:
        print(f"\n{result['endpoint']}:")
        print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        sys.exit(1)
