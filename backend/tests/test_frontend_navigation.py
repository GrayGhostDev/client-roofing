#!/usr/bin/env python3
"""
Frontend Navigation and Component Testing
Tests all dashboard pages and component rendering
"""

import pytest
import requests
import time
import json
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class NavigationTestResult:
    """Navigation test result container"""
    route: str
    status: str  # PASS, FAIL, SKIP
    status_code: int
    response_time: float
    content_size: int
    has_content: bool
    title_found: bool
    error_message: str = ""


class FrontendNavigationTester:
    """Test frontend page navigation and component rendering"""

    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.routes_to_test = [
            "/",
            "/kanban",
            "/leads",
            "/customers",
            "/projects",
            "/timeline",
            "/appointments",
            "/analytics",
            "/settings",
            "/login"
        ]

    def test_route(self, route: str) -> NavigationTestResult:
        """Test a specific route"""
        start_time = time.time()

        try:
            url = f"{self.base_url}{route}"
            response = requests.get(url, timeout=15)
            response_time = time.time() - start_time

            # Check basic response properties
            status_code = response.status_code
            content_size = len(response.content)
            content = response.text

            # Check for basic HTML content
            has_content = content_size > 100 and "html" in content.lower()

            # Check for title in content (basic validation)
            title_patterns = [
                r"iSwitch Roofs CRM",
                r"<title>.*iSwitch.*</title>",
                r"Dashboard",
                r"Kanban",
                r"Lead",
                r"Customer",
                r"Project",
                r"Appointment",
                r"Analytics",
                r"Settings",
                r"Login"
            ]

            title_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in title_patterns)

            # Determine status
            if status_code == 200 and has_content:
                status = "PASS"
                error_message = ""
            elif status_code == 200:
                status = "FAIL"
                error_message = "Page loads but has no content"
            else:
                status = "FAIL"
                error_message = f"HTTP {status_code} error"

        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            status = "FAIL"
            status_code = 0
            content_size = 0
            has_content = False
            title_found = False
            error_message = f"Request failed: {str(e)}"

        return NavigationTestResult(
            route=route,
            status=status,
            status_code=status_code,
            response_time=response_time,
            content_size=content_size,
            has_content=has_content,
            title_found=title_found,
            error_message=error_message
        )

    def test_all_routes(self) -> List[NavigationTestResult]:
        """Test all routes and return results"""
        results = []

        print("Testing frontend navigation...")

        for route in self.routes_to_test:
            print(f"Testing {route}...")
            result = self.test_route(route)
            results.append(result)

            status_icon = "✅" if result.status == "PASS" else "❌"
            print(f"{status_icon} {route}: {result.status} (HTTP {result.status_code}, {result.response_time:.3f}s)")

        return results

    def test_component_functionality(self) -> List[NavigationTestResult]:
        """Test specific component functionality"""
        print("\nTesting component-specific functionality...")

        component_tests = []

        # Test dashboard metrics loading
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            response_time = time.time() - start_time
            content = response.text

            # Check for dashboard-specific elements
            dashboard_elements = [
                "Total Leads",
                "Hot Leads",
                "Conversion Rate",
                "Kanban Board",
                "Lead Management",
                "Customer Management",
                "Project Management",
                "Analytics",
                "Recent Activity"
            ]

            elements_found = sum(1 for element in dashboard_elements if element in content)

            if elements_found >= 7:  # Most elements should be present
                status = "PASS"
                error_message = f"Found {elements_found}/{len(dashboard_elements)} dashboard elements"
            else:
                status = "FAIL"
                error_message = f"Only found {elements_found}/{len(dashboard_elements)} dashboard elements"

            component_tests.append(NavigationTestResult(
                route="/dashboard-components",
                status=status,
                status_code=response.status_code,
                response_time=response_time,
                content_size=len(content),
                has_content=True,
                title_found=True,
                error_message=error_message
            ))

        except requests.exceptions.RequestException as e:
            component_tests.append(NavigationTestResult(
                route="/dashboard-components",
                status="FAIL",
                status_code=0,
                response_time=0,
                content_size=0,
                has_content=False,
                title_found=False,
                error_message=f"Component test failed: {str(e)}"
            ))

        return component_tests

    def generate_report(self, results: List[NavigationTestResult]) -> str:
        """Generate comprehensive navigation test report"""
        total_tests = len(results)
        passed_tests = len([r for r in results if r.status == "PASS"])
        failed_tests = len([r for r in results if r.status == "FAIL"])

        avg_response_time = sum(r.response_time for r in results) / total_tests if total_tests > 0 else 0
        total_content_size = sum(r.content_size for r in results)

        report = f"""
FRONTEND NAVIGATION TEST REPORT
==============================

SUMMARY:
--------
Total Routes Tested: {total_tests}
Passed:              {passed_tests}
Failed:              {failed_tests}
Success Rate:        {(passed_tests/total_tests*100):.1f}%
Avg Response Time:   {avg_response_time:.3f}s
Total Content Size:  {total_content_size:,} bytes

DETAILED RESULTS:
----------------
"""

        for result in results:
            status_icon = "✅" if result.status == "PASS" else "❌"
            report += f"{status_icon} {result.route}\n"
            report += f"   Status: {result.status}\n"
            report += f"   HTTP Code: {result.status_code}\n"
            report += f"   Response Time: {result.response_time:.3f}s\n"
            report += f"   Content Size: {result.content_size:,} bytes\n"
            report += f"   Has Content: {result.has_content}\n"
            report += f"   Title Found: {result.title_found}\n"
            if result.error_message:
                report += f"   Error: {result.error_message}\n"
            report += "\n"

        # Performance analysis
        report += "PERFORMANCE ANALYSIS:\n"
        report += "--------------------\n"

        fast_routes = [r for r in results if r.response_time < 1.0 and r.status == "PASS"]
        slow_routes = [r for r in results if r.response_time > 3.0]

        report += f"Fast routes (<1s): {len(fast_routes)}\n"
        report += f"Slow routes (>3s): {len(slow_routes)}\n"

        if slow_routes:
            report += "Slow routes details:\n"
            for route in slow_routes:
                report += f"  - {route.route}: {route.response_time:.3f}s\n"

        # Content analysis
        report += "\nCONTENT ANALYSIS:\n"
        report += "-----------------\n"

        content_routes = [r for r in results if r.has_content]
        empty_routes = [r for r in results if not r.has_content and r.status_code == 200]

        report += f"Routes with content: {len(content_routes)}\n"
        report += f"Empty routes: {len(empty_routes)}\n"

        if empty_routes:
            report += "Empty routes:\n"
            for route in empty_routes:
                report += f"  - {route.route}\n"

        # Recommendations
        report += "\nRECOMMENDATIONS:\n"
        report += "---------------\n"

        if failed_tests == 0:
            report += "✅ All navigation tests passed! Frontend is ready for use.\n"
        else:
            report += f"❌ {failed_tests} navigation test(s) failed. Review failures.\n"

        if len(slow_routes) > 0:
            report += "⚠️  Some routes are slow. Consider optimization.\n"

        if len(empty_routes) > 0:
            report += "⚠️  Some routes return empty content. Check component rendering.\n"

        return report


def main():
    """Main test execution"""
    tester = FrontendNavigationTester()

    # Test all routes
    navigation_results = tester.test_all_routes()

    # Test component functionality
    component_results = tester.test_component_functionality()

    # Combine results
    all_results = navigation_results + component_results

    # Generate and print report
    report = tester.generate_report(all_results)
    print(report)

    # Save report to file
    import os
    report_file = "/Users/grayghostdata/Projects/client-roofing/backend/reports/frontend_navigation_report.txt"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, 'w') as f:
        f.write(report)

    print(f"Report saved to: {report_file}")

    # Return exit code based on test results
    failed_tests = len([r for r in all_results if r.status == "FAIL"])
    return 0 if failed_tests == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())