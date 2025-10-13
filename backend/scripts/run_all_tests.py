#!/usr/bin/env python3
"""
Comprehensive Test Runner for Week 9 Days 3-5 Implementation

Runs all tests for:
- Advanced Analytics module
- A/B Testing framework
- Revenue Forecasting models
- Flask API routes

Generates coverage reports and summary statistics.
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Test configurations
TEST_SUITES = {
    'advanced_analytics': {
        'path': 'tests/test_advanced_analytics.py',
        'description': 'Advanced Analytics Module Tests',
        'critical': True
    },
    'ab_testing': {
        'path': 'tests/test_ab_testing.py',
        'description': 'A/B Testing Framework Tests',
        'critical': True
    },
    'revenue_forecasting': {
        'path': 'tests/test_revenue_forecasting.py',
        'description': 'Revenue Forecasting Model Tests',
        'critical': True
    },
    'api_routes': {
        'path': 'tests/test_advanced_analytics_routes.py',
        'description': 'Flask API Integration Tests',
        'critical': True
    }
}

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_section(text):
    """Print formatted section."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{'-'*80}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{Colors.BOLD}{'-'*80}{Colors.ENDC}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def run_test_suite(suite_name, suite_config):
    """
    Run a single test suite.

    Args:
        suite_name: Name of the test suite
        suite_config: Configuration dictionary for the suite

    Returns:
        dict: Test results including passed, failed, duration
    """
    print_section(f"Running: {suite_config['description']}")

    test_path = backend_dir / suite_config['path']

    if not test_path.exists():
        print_error(f"Test file not found: {test_path}")
        return {
            'passed': False,
            'tests_run': 0,
            'failures': 1,
            'errors': 1,
            'duration': 0,
            'critical': suite_config['critical']
        }

    # Run pytest with verbose output and coverage
    cmd = [
        'pytest',
        str(test_path),
        '-v',
        '--tb=short',
        '--color=yes',
        f'--cov=app.ml',
        f'--cov=app.routes',
        '--cov-report=term-missing',
        '--durations=10'
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        output = result.stdout + result.stderr

        # Parse pytest output
        passed = result.returncode == 0

        # Extract statistics from output
        tests_run = 0
        failures = 0
        errors = 0
        duration = 0.0

        for line in output.split('\n'):
            if 'passed' in line.lower() or 'failed' in line.lower():
                # Extract test counts
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'passed' in part:
                        try:
                            tests_run += int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
                    if 'failed' in part:
                        try:
                            failures += int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
                    if 'error' in part:
                        try:
                            errors += int(parts[i-1])
                        except (ValueError, IndexError):
                            pass

            if 'seconds' in line.lower():
                # Extract duration
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'seconds' in part or 's' == part:
                            duration = float(parts[i-1].replace('s', ''))
                            break
                except (ValueError, IndexError):
                    pass

        # Print output
        print(output)

        if passed:
            print_success(f"{suite_config['description']} - ALL TESTS PASSED")
        else:
            print_error(f"{suite_config['description']} - TESTS FAILED")

        return {
            'passed': passed,
            'tests_run': tests_run if tests_run > 0 else (0 if passed else 1),
            'failures': failures,
            'errors': errors,
            'duration': duration,
            'critical': suite_config['critical'],
            'output': output
        }

    except subprocess.TimeoutExpired:
        print_error(f"Test suite timed out after 5 minutes")
        return {
            'passed': False,
            'tests_run': 0,
            'failures': 0,
            'errors': 1,
            'duration': 300,
            'critical': suite_config['critical'],
            'error': 'Timeout'
        }
    except Exception as e:
        print_error(f"Error running test suite: {str(e)}")
        return {
            'passed': False,
            'tests_run': 0,
            'failures': 0,
            'errors': 1,
            'duration': 0,
            'critical': suite_config['critical'],
            'error': str(e)
        }


def generate_summary(results):
    """
    Generate and print test summary.

    Args:
        results: Dictionary of test results
    """
    print_header("TEST SUMMARY")

    total_tests = sum(r['tests_run'] for r in results.values())
    total_failures = sum(r['failures'] for r in results.values())
    total_errors = sum(r['errors'] for r in results.values())
    total_duration = sum(r['duration'] for r in results.values())

    passed_suites = sum(1 for r in results.values() if r['passed'])
    total_suites = len(results)

    critical_failed = any(
        not r['passed'] and r['critical']
        for r in results.values()
    )

    # Print suite results
    print("\n📊 Test Suite Results:")
    print(f"{'Suite':<30} {'Tests':<10} {'Failures':<10} {'Errors':<10} {'Duration':<10} {'Status':<10}")
    print("-" * 90)

    for suite_name, result in results.items():
        status = "✓ PASS" if result['passed'] else "✗ FAIL"
        color = Colors.OKGREEN if result['passed'] else Colors.FAIL
        critical_marker = " [CRITICAL]" if result['critical'] and not result['passed'] else ""

        print(
            f"{color}{suite_name:<30}{Colors.ENDC} "
            f"{result['tests_run']:<10} "
            f"{result['failures']:<10} "
            f"{result['errors']:<10} "
            f"{result['duration']:<10.2f}s "
            f"{color}{status}{critical_marker}{Colors.ENDC}"
        )

    print("-" * 90)

    # Print totals
    print(f"\n📈 Overall Statistics:")
    print(f"  Total Test Suites: {total_suites}")
    print(f"  Passed Suites: {passed_suites}")
    print(f"  Failed Suites: {total_suites - passed_suites}")
    print(f"  Total Tests Run: {total_tests}")
    print(f"  Total Failures: {total_failures}")
    print(f"  Total Errors: {total_errors}")
    print(f"  Total Duration: {total_duration:.2f}s")

    # Print pass rate
    pass_rate = (passed_suites / total_suites * 100) if total_suites > 0 else 0
    if pass_rate == 100:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ SUCCESS: All test suites passed! ({pass_rate:.1f}%){Colors.ENDC}")
    elif critical_failed:
        print(f"\n{Colors.FAIL}{Colors.BOLD}✗ CRITICAL FAILURE: Critical test suites failed! ({pass_rate:.1f}%){Colors.ENDC}")
    else:
        print(f"\n{Colors.WARNING}⚠ PARTIAL SUCCESS: Some test suites failed ({pass_rate:.1f}%){Colors.ENDC}")

    return {
        'all_passed': passed_suites == total_suites,
        'critical_failed': critical_failed,
        'pass_rate': pass_rate,
        'total_tests': total_tests
    }


def check_dependencies():
    """Check if required dependencies are installed."""
    print_section("Checking Dependencies")

    required_packages = [
        'pytest',
        'pytest-asyncio',
        'pytest-cov',
        'flask',
        'sqlalchemy',
        'pandas',
        'numpy',
        'scikit-learn'
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_success(f"{package} - installed")
        except ImportError:
            print_error(f"{package} - MISSING")
            missing.append(package)

    if missing:
        print_warning(f"\nMissing packages: {', '.join(missing)}")
        print_warning("Run: pip install " + " ".join(missing))
        return False

    return True


def main():
    """Main test runner."""
    print_header(f"Week 9 Days 3-5 Test Suite Runner")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Check dependencies
    if not check_dependencies():
        print_error("\nDependency check failed. Please install missing packages.")
        return 1

    # Run all test suites
    results = {}
    for suite_name, suite_config in TEST_SUITES.items():
        results[suite_name] = run_test_suite(suite_name, suite_config)

    # Generate summary
    summary = generate_summary(results)

    # Print completion
    print(f"\n{Colors.BOLD}Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}\n")

    # Return exit code
    if summary['critical_failed']:
        return 2  # Critical failure
    elif not summary['all_passed']:
        return 1  # Some tests failed
    else:
        return 0  # All tests passed


if __name__ == '__main__':
    sys.exit(main())
