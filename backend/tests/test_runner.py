"""
Test Runner and Configuration for iSwitch Roofs CRM
Orchestrates comprehensive testing suite with proper configuration
"""

import json
import os
import sys
import time
from datetime import datetime

import pytest


class TestSuiteRunner:
    """Comprehensive test suite runner with reporting."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.results = {}

    def run_unit_tests(self):
        """Run unit tests."""
        print("🧪 Running Unit Tests...")
        self.start_time = time.time()

        # Run unit tests with coverage
        exit_code = pytest.main(
            [
                "-v",
                "--tb=short",
                "--cov=app",
                "--cov-report=html:htmlcov/unit",
                "--cov-report=xml:coverage_unit.xml",
                "--cov-report=term-missing",
                "--junit-xml=reports/unit_tests.xml",
                "-m",
                "unit",
                "tests/unit/",
                "--disable-warnings",
            ]
        )

        self.results["unit"] = {"exit_code": exit_code, "duration": time.time() - self.start_time}

        return exit_code == 0

    def run_integration_tests(self):
        """Run integration tests."""
        print("🔗 Running Integration Tests...")
        self.start_time = time.time()

        exit_code = pytest.main(
            [
                "-v",
                "--tb=short",
                "--cov=app",
                "--cov-report=html:htmlcov/integration",
                "--cov-report=xml:coverage_integration.xml",
                "--junit-xml=reports/integration_tests.xml",
                "-m",
                "integration",
                "tests/test_api_endpoints.py",
                "tests/test_frontend_integration.py",
                "--disable-warnings",
            ]
        )

        self.results["integration"] = {
            "exit_code": exit_code,
            "duration": time.time() - self.start_time,
        }

        return exit_code == 0

    def run_security_tests(self):
        """Run security tests."""
        print("🔒 Running Security Tests...")
        self.start_time = time.time()

        exit_code = pytest.main(
            [
                "-v",
                "--tb=short",
                "--junit-xml=reports/security_tests.xml",
                "-m",
                "security",
                "tests/test_security.py",
                "--disable-warnings",
            ]
        )

        self.results["security"] = {
            "exit_code": exit_code,
            "duration": time.time() - self.start_time,
        }

        return exit_code == 0

    def run_performance_tests(self):
        """Run performance tests."""
        print("⚡ Running Performance Tests...")
        self.start_time = time.time()

        exit_code = pytest.main(
            [
                "-v",
                "--tb=short",
                "--junit-xml=reports/performance_tests.xml",
                "-m",
                "performance",
                "tests/test_performance.py",
                "--disable-warnings",
            ]
        )

        self.results["performance"] = {
            "exit_code": exit_code,
            "duration": time.time() - self.start_time,
        }

        return exit_code == 0

    def run_e2e_tests(self):
        """Run end-to-end tests."""
        print("🎯 Running End-to-End Tests...")
        self.start_time = time.time()

        exit_code = pytest.main(
            [
                "-v",
                "--tb=short",
                "--junit-xml=reports/e2e_tests.xml",
                "-m",
                "e2e",
                "tests/test_e2e_workflows.py",
                "--disable-warnings",
            ]
        )

        self.results["e2e"] = {"exit_code": exit_code, "duration": time.time() - self.start_time}

        return exit_code == 0

    def run_all_tests(self):
        """Run complete test suite."""
        print("🚀 Starting Comprehensive Test Suite...")
        suite_start = time.time()

        # Create reports directory
        os.makedirs("reports", exist_ok=True)

        # Run test suites in order
        test_suites = [
            ("Unit Tests", self.run_unit_tests),
            ("Integration Tests", self.run_integration_tests),
            ("Security Tests", self.run_security_tests),
            ("Performance Tests", self.run_performance_tests),
            ("E2E Tests", self.run_e2e_tests),
        ]

        results_summary = {}
        overall_success = True

        for suite_name, test_function in test_suites:
            print(f"\n{'=' * 60}")
            print(f"Running {suite_name}")
            print(f"{'=' * 60}")

            try:
                success = test_function()
                results_summary[suite_name] = "PASSED" if success else "FAILED"
                if not success:
                    overall_success = False
            except Exception as e:
                print(f"❌ Error running {suite_name}: {e}")
                results_summary[suite_name] = "ERROR"
                overall_success = False

        # Generate summary report
        total_duration = time.time() - suite_start
        self.generate_summary_report(results_summary, total_duration, overall_success)

        return overall_success

    def generate_summary_report(self, results_summary, total_duration, overall_success):
        """Generate comprehensive test summary report."""
        print(f"\n{'=' * 80}")
        print("📊 TEST SUITE SUMMARY REPORT")
        print(f"{'=' * 80}")

        print(f"⏱️  Total Duration: {total_duration:.2f} seconds")
        print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Overall Result: {'✅ PASSED' if overall_success else '❌ FAILED'}")

        print("\n📋 Test Suite Results:")
        for suite_name, result in results_summary.items():
            emoji = "✅" if result == "PASSED" else "❌" if result == "FAILED" else "⚠️"
            duration = self.results.get(suite_name.lower().split()[0], {}).get("duration", 0)
            print(f"  {emoji} {suite_name:<20} {result:<8} ({duration:.2f}s)")

        # Generate JSON report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "overall_success": overall_success,
            "total_duration": total_duration,
            "results": results_summary,
            "detailed_results": self.results,
        }

        with open("reports/test_summary.json", "w") as f:
            json.dump(report_data, f, indent=2)

        print("\n📄 Detailed reports saved to:")
        print("  - HTML Coverage: htmlcov/index.html")
        print("  - XML Reports: reports/*.xml")
        print("  - JSON Summary: reports/test_summary.json")

        if not overall_success:
            print("\n⚠️  Some tests failed. Check individual reports for details.")

        print(f"{'=' * 80}")

    def run_quick_tests(self):
        """Run a quick subset of tests for development."""
        print("⚡ Running Quick Test Suite...")

        exit_code = pytest.main(
            [
                "-v",
                "--tb=short",
                "--maxfail=5",  # Stop after 5 failures
                "--disable-warnings",
                "tests/unit/",
                "tests/test_api_endpoints.py",
                "-m",
                "not slow",  # Skip slow tests
            ]
        )

        return exit_code == 0

    def run_smoke_tests(self):
        """Run smoke tests to verify basic functionality."""
        print("💨 Running Smoke Tests...")

        # Define critical test paths for smoke testing
        smoke_tests = [
            "tests/test_api_endpoints.py::TestLeadsAPI::test_get_leads_success",
            "tests/test_api_endpoints.py::TestAuthAPI::test_login_success",
            "tests/test_security.py::TestAuthentication::test_login_with_valid_credentials",
        ]

        exit_code = pytest.main(["-v", "--tb=short", "--disable-warnings"] + smoke_tests)

        return exit_code == 0


def main():
    """Main entry point for test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="iSwitch Roofs CRM Test Runner")
    parser.add_argument(
        "--suite",
        choices=["all", "unit", "integration", "security", "performance", "e2e", "quick", "smoke"],
        default="all",
        help="Test suite to run",
    )
    parser.add_argument(
        "--coverage-fail-under", type=int, default=80, help="Minimum coverage percentage required"
    )

    args = parser.parse_args()

    runner = TestSuiteRunner()

    # Set coverage fail-under in pytest.ini or environment
    os.environ["COVERAGE_FAIL_UNDER"] = str(args.coverage_fail_under)

    success = False

    if args.suite == "all":
        success = runner.run_all_tests()
    elif args.suite == "unit":
        success = runner.run_unit_tests()
    elif args.suite == "integration":
        success = runner.run_integration_tests()
    elif args.suite == "security":
        success = runner.run_security_tests()
    elif args.suite == "performance":
        success = runner.run_performance_tests()
    elif args.suite == "e2e":
        success = runner.run_e2e_tests()
    elif args.suite == "quick":
        success = runner.run_quick_tests()
    elif args.suite == "smoke":
        success = runner.run_smoke_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
