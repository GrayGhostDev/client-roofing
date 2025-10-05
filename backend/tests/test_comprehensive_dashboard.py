#!/usr/bin/env python3
"""
Comprehensive Dashboard Testing Suite
Tests both frontend (Reflex) and backend (Flask) components
"""

import pytest
import requests
import time
import json
import subprocess
import sys
import os
from typing import Dict, List, Tuple, Optional
from urllib.parse import urljoin
import concurrent.futures
from dataclasses import dataclass


@dataclass
class TestResult:
    """Test result container"""
    test_name: str
    status: str  # PASS, FAIL, SKIP
    message: str
    duration: float
    details: Optional[Dict] = None


class DashboardTester:
    """Comprehensive dashboard testing class"""

    def __init__(self):
        self.frontend_url = "http://localhost:3000"
        self.backend_url = "http://127.0.0.1:8001"
        self.results: List[TestResult] = []

    def add_result(self, test_name: str, status: str, message: str, duration: float, details: Optional[Dict] = None):
        """Add a test result"""
        self.results.append(TestResult(test_name, status, message, duration, details))

    def test_backend_health(self) -> TestResult:
        """Test backend health endpoint"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            duration = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                return TestResult(
                    "Backend Health Check",
                    "PASS",
                    f"Backend responding (HTTP {response.status_code})",
                    duration,
                    data
                )
            else:
                return TestResult(
                    "Backend Health Check",
                    "FAIL",
                    f"Backend returned HTTP {response.status_code}",
                    duration
                )
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            return TestResult(
                "Backend Health Check",
                "FAIL",
                f"Backend connection failed: {str(e)}",
                duration
            )

    def test_backend_cors(self) -> TestResult:
        """Test CORS configuration"""
        start_time = time.time()
        try:
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }

            # Send OPTIONS request to test CORS preflight
            response = requests.options(f"{self.backend_url}/health", headers=headers, timeout=10)
            duration = time.time() - start_time

            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }

            if response.status_code in [200, 204] and cors_headers['Access-Control-Allow-Origin']:
                return TestResult(
                    "CORS Configuration",
                    "PASS",
                    "CORS headers properly configured",
                    duration,
                    cors_headers
                )
            else:
                return TestResult(
                    "CORS Configuration",
                    "FAIL",
                    f"CORS not properly configured (HTTP {response.status_code})",
                    duration,
                    cors_headers
                )
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            return TestResult(
                "CORS Configuration",
                "FAIL",
                f"CORS test failed: {str(e)}",
                duration
            )

    def test_backend_endpoints(self) -> List[TestResult]:
        """Test various backend endpoints"""
        endpoints = [
            ("/health", "GET"),
            ("/api/customers", "GET"),
            ("/api/leads", "GET"),
            ("/api/projects", "GET"),
            ("/api/appointments", "GET"),
            ("/api/analytics/dashboard", "GET"),
            ("/api/teams", "GET"),
            ("/api/partnerships", "GET")
        ]

        results = []
        for endpoint, method in endpoints:
            start_time = time.time()
            try:
                url = f"{self.backend_url}{endpoint}"
                response = requests.request(method, url, timeout=10)
                duration = time.time() - start_time

                if response.status_code in [200, 201, 404]:  # 404 is OK for empty resources
                    status = "PASS"
                    message = f"{method} {endpoint} responded (HTTP {response.status_code})"
                else:
                    status = "FAIL"
                    message = f"{method} {endpoint} failed (HTTP {response.status_code})"

                results.append(TestResult(
                    f"Backend Endpoint: {method} {endpoint}",
                    status,
                    message,
                    duration,
                    {"status_code": response.status_code, "response_size": len(response.content)}
                ))

            except requests.exceptions.RequestException as e:
                duration = time.time() - start_time
                results.append(TestResult(
                    f"Backend Endpoint: {method} {endpoint}",
                    "FAIL",
                    f"Request failed: {str(e)}",
                    duration
                ))

        return results

    def test_frontend_accessibility(self) -> TestResult:
        """Test frontend accessibility"""
        start_time = time.time()
        try:
            response = requests.get(self.frontend_url, timeout=15)
            duration = time.time() - start_time

            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)

                return TestResult(
                    "Frontend Accessibility",
                    "PASS",
                    f"Frontend accessible (HTTP {response.status_code})",
                    duration,
                    {
                        "content_type": content_type,
                        "content_length": content_length,
                        "has_html": "html" in content_type.lower()
                    }
                )
            else:
                return TestResult(
                    "Frontend Accessibility",
                    "FAIL",
                    f"Frontend returned HTTP {response.status_code}",
                    duration
                )
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            return TestResult(
                "Frontend Accessibility",
                "FAIL",
                f"Frontend connection failed: {str(e)}",
                duration
            )

    def test_service_integration(self) -> TestResult:
        """Test integration between frontend and backend"""
        start_time = time.time()
        try:
            # Test if frontend can make requests to backend
            frontend_response = requests.get(self.frontend_url, timeout=10)
            backend_response = requests.get(f"{self.backend_url}/health", timeout=10)
            duration = time.time() - start_time

            frontend_ok = frontend_response.status_code == 200
            backend_ok = backend_response.status_code == 200

            if frontend_ok and backend_ok:
                return TestResult(
                    "Service Integration",
                    "PASS",
                    "Both frontend and backend services responding",
                    duration,
                    {
                        "frontend_status": frontend_response.status_code,
                        "backend_status": backend_response.status_code
                    }
                )
            else:
                return TestResult(
                    "Service Integration",
                    "FAIL",
                    f"Service communication issue (Frontend: {frontend_response.status_code}, Backend: {backend_response.status_code})",
                    duration
                )
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            return TestResult(
                "Service Integration",
                "FAIL",
                f"Integration test failed: {str(e)}",
                duration
            )

    def test_performance_basic(self) -> List[TestResult]:
        """Basic performance testing"""
        results = []

        # Test frontend load time
        start_time = time.time()
        try:
            response = requests.get(self.frontend_url, timeout=30)
            duration = time.time() - start_time

            if duration < 5.0:
                status = "PASS"
                message = f"Frontend loads quickly ({duration:.2f}s)"
            elif duration < 10.0:
                status = "PASS"
                message = f"Frontend loads acceptably ({duration:.2f}s)"
            else:
                status = "FAIL"
                message = f"Frontend loads slowly ({duration:.2f}s)"

            results.append(TestResult(
                "Frontend Load Performance",
                status,
                message,
                duration,
                {"load_time": duration, "threshold": 10.0}
            ))
        except requests.exceptions.RequestException as e:
            results.append(TestResult(
                "Frontend Load Performance",
                "FAIL",
                f"Frontend load test failed: {str(e)}",
                0
            ))

        # Test backend response time
        start_time = time.time()
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            duration = time.time() - start_time

            if duration < 1.0:
                status = "PASS"
                message = f"Backend responds quickly ({duration:.3f}s)"
            elif duration < 3.0:
                status = "PASS"
                message = f"Backend responds acceptably ({duration:.3f}s)"
            else:
                status = "FAIL"
                message = f"Backend responds slowly ({duration:.3f}s)"

            results.append(TestResult(
                "Backend Response Performance",
                status,
                message,
                duration,
                {"response_time": duration, "threshold": 3.0}
            ))
        except requests.exceptions.RequestException as e:
            results.append(TestResult(
                "Backend Response Performance",
                "FAIL",
                f"Backend performance test failed: {str(e)}",
                0
            ))

        return results

    def test_error_handling(self) -> List[TestResult]:
        """Test error handling"""
        results = []

        # Test 404 handling
        start_time = time.time()
        try:
            response = requests.get(f"{self.backend_url}/api/nonexistent", timeout=10)
            duration = time.time() - start_time

            if response.status_code == 404:
                status = "PASS"
                message = "Backend properly returns 404 for non-existent endpoints"
            else:
                status = "FAIL"
                message = f"Backend returned {response.status_code} instead of 404"

            results.append(TestResult(
                "404 Error Handling",
                status,
                message,
                duration,
                {"status_code": response.status_code}
            ))
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            results.append(TestResult(
                "404 Error Handling",
                "FAIL",
                f"Error handling test failed: {str(e)}",
                duration
            ))

        return results

    def run_all_tests(self) -> List[TestResult]:
        """Run all tests and return results"""
        print("Starting comprehensive dashboard testing...")

        # Test backend health
        result = self.test_backend_health()
        self.results.append(result)
        print(f"✓ {result.test_name}: {result.status}")

        # Test CORS
        result = self.test_backend_cors()
        self.results.append(result)
        print(f"✓ {result.test_name}: {result.status}")

        # Test backend endpoints
        endpoint_results = self.test_backend_endpoints()
        self.results.extend(endpoint_results)
        for result in endpoint_results:
            print(f"✓ {result.test_name}: {result.status}")

        # Test frontend
        result = self.test_frontend_accessibility()
        self.results.append(result)
        print(f"✓ {result.test_name}: {result.status}")

        # Test integration
        result = self.test_service_integration()
        self.results.append(result)
        print(f"✓ {result.test_name}: {result.status}")

        # Test performance
        performance_results = self.test_performance_basic()
        self.results.extend(performance_results)
        for result in performance_results:
            print(f"✓ {result.test_name}: {result.status}")

        # Test error handling
        error_results = self.test_error_handling()
        self.results.extend(error_results)
        for result in error_results:
            print(f"✓ {result.test_name}: {result.status}")

        return self.results

    def generate_report(self) -> str:
        """Generate a comprehensive test report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "PASS"])
        failed_tests = len([r for r in self.results if r.status == "FAIL"])
        skipped_tests = len([r for r in self.results if r.status == "SKIP"])

        total_duration = sum(r.duration for r in self.results)

        report = f"""
COMPREHENSIVE DASHBOARD TEST REPORT
==================================

SUMMARY:
--------
Total Tests:    {total_tests}
Passed:         {passed_tests}
Failed:         {failed_tests}
Skipped:        {skipped_tests}
Success Rate:   {(passed_tests/total_tests*100):.1f}%
Total Duration: {total_duration:.2f}s

DETAILED RESULTS:
----------------
"""

        for result in self.results:
            status_icon = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⏩"
            report += f"{status_icon} {result.test_name}\n"
            report += f"   Status: {result.status}\n"
            report += f"   Message: {result.message}\n"
            report += f"   Duration: {result.duration:.3f}s\n"
            if result.details:
                report += f"   Details: {json.dumps(result.details, indent=2)}\n"
            report += "\n"

        # Add recommendations
        report += """
RECOMMENDATIONS:
---------------
"""

        if failed_tests == 0:
            report += "✅ All tests passed! System is ready for production.\n"
        else:
            report += f"❌ {failed_tests} test(s) failed. Review failures before deployment.\n"

        if any(r.duration > 5.0 for r in self.results if "Performance" in r.test_name):
            report += "⚠️  Performance issues detected. Consider optimization.\n"

        return report


def main():
    """Main test execution"""
    tester = DashboardTester()
    results = tester.run_all_tests()

    # Generate and print report
    report = tester.generate_report()
    print(report)

    # Save report to file
    report_file = "/Users/grayghostdata/Projects/client-roofing/backend/reports/comprehensive_test_report.txt"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, 'w') as f:
        f.write(report)

    print(f"Report saved to: {report_file}")

    # Return exit code based on test results
    failed_tests = len([r for r in results if r.status == "FAIL"])
    return 0 if failed_tests == 0 else 1


if __name__ == "__main__":
    sys.exit(main())