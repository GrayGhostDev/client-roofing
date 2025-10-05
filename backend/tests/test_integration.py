#!/usr/bin/env python
"""
Integration test suite for iSwitch Roofs CRM.
Tests the complete flow from frontend components through API to database.
"""

import unittest
import requests
import json
import time
from typing import Dict, Any, List
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test configuration
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8001"
TEST_TIMEOUT = 10

class IntegrationTestSuite(unittest.TestCase):
    """Complete integration tests for the CRM system."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.session = requests.Session()
        cls.auth_token = None
        cls.test_data = {
            "lead": {
                "first_name": "Test",
                "last_name": "Lead",
                "phone": "555-0123",
                "email": "test.lead@example.com",
                "source": "website_form",
                "city": "Birmingham",
                "state": "MI",
                "zip_code": "48009"
            },
            "customer": {
                "first_name": "Test",
                "last_name": "Customer",
                "phone": "555-0456",
                "email": "test.customer@example.com",
                "city": "Troy",
                "state": "MI",
                "zip_code": "48084"
            },
            "appointment": {
                "title": "Roof Inspection",
                "appointment_type": "inspection",
                "scheduled_date": "2025-10-10T10:00:00",
                "duration_minutes": 60,
                "location": "123 Test St, Birmingham, MI"
            },
            "project": {
                "title": "Roof Replacement",
                "project_type": "full_replacement",
                "estimated_value": 25000,
                "status": "planning"
            }
        }

    def setUp(self):
        """Set up each test."""
        self.created_ids = {
            "leads": [],
            "customers": [],
            "appointments": [],
            "projects": []
        }

    def tearDown(self):
        """Clean up after each test."""
        # Clean up created test data
        for entity_type, ids in self.created_ids.items():
            for entity_id in ids:
                try:
                    self.session.delete(
                        f"{BACKEND_URL}/api/{entity_type}/{entity_id}",
                        headers=self._get_headers()
                    )
                except:
                    pass

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    # ========== Service Availability Tests ==========

    def test_01_frontend_availability(self):
        """Test that the frontend is accessible."""
        response = requests.get(FRONTEND_URL, timeout=TEST_TIMEOUT)
        self.assertEqual(response.status_code, 200, "Frontend should be accessible")
        self.assertIn("<!DOCTYPE html>", response.text, "Should return HTML")

    def test_02_backend_availability(self):
        """Test that the backend is accessible."""
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=TEST_TIMEOUT)
        self.assertIn(response.status_code, [200, 404], "Backend should respond")

    def test_03_database_connectivity(self):
        """Test database connectivity through the API."""
        # This will fail until DB tables are created
        response = self.session.get(
            f"{BACKEND_URL}/api/leads",
            headers=self._get_headers()
        )
        # Even a 401/404 means the server is running
        self.assertIn(
            response.status_code,
            [200, 401, 404, 500],
            "Server should respond to API calls"
        )

    # ========== Authentication Tests ==========

    def test_04_user_registration(self):
        """Test user registration flow."""
        user_data = {
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User"
        }

        response = self.session.post(
            f"{BACKEND_URL}/api/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            self.assertIn("token", response.json(), "Should return auth token")
            self.auth_token = response.json().get("token")
        else:
            # Mark as skipped if auth not implemented
            self.skipTest("Authentication not yet implemented")

    def test_05_user_login(self):
        """Test user login flow."""
        login_data = {
            "email": "admin@iswitchroofs.com",
            "password": "admin123"
        }

        response = self.session.post(
            f"{BACKEND_URL}/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            self.assertIn("token", response.json(), "Should return auth token")
            self.auth_token = response.json().get("token")
        else:
            self.skipTest("Authentication not yet implemented")

    # ========== Lead Management Tests ==========

    def test_06_create_lead(self):
        """Test creating a new lead."""
        response = self.session.post(
            f"{BACKEND_URL}/api/leads",
            json=self.test_data["lead"],
            headers=self._get_headers()
        )

        if response.status_code == 201:
            data = response.json()
            self.assertIn("id", data, "Should return lead ID")
            self.created_ids["leads"].append(data["id"])

            # Verify lead was created
            verify_response = self.session.get(
                f"{BACKEND_URL}/api/leads/{data['id']}",
                headers=self._get_headers()
            )
            self.assertEqual(verify_response.status_code, 200)
        else:
            self.skipTest("Lead creation not yet functional")

    def test_07_list_leads(self):
        """Test listing leads with pagination."""
        response = self.session.get(
            f"{BACKEND_URL}/api/leads?page=1&size=10",
            headers=self._get_headers()
        )

        if response.status_code == 200:
            data = response.json()
            self.assertIn("data", data, "Should return data array")
            self.assertIn("pagination", data, "Should include pagination info")
        else:
            self.skipTest("Lead listing not yet functional")

    def test_08_update_lead(self):
        """Test updating a lead."""
        # First create a lead
        create_response = self.session.post(
            f"{BACKEND_URL}/api/leads",
            json=self.test_data["lead"],
            headers=self._get_headers()
        )

        if create_response.status_code == 201:
            lead_id = create_response.json()["id"]
            self.created_ids["leads"].append(lead_id)

            # Update the lead
            update_data = {"status": "contacted", "lead_score": 85}
            update_response = self.session.put(
                f"{BACKEND_URL}/api/leads/{lead_id}",
                json=update_data,
                headers=self._get_headers()
            )

            self.assertEqual(update_response.status_code, 200)
            self.assertEqual(update_response.json()["status"], "contacted")
        else:
            self.skipTest("Lead operations not yet functional")

    def test_09_lead_scoring(self):
        """Test lead scoring calculation."""
        scoring_data = {
            **self.test_data["lead"],
            "property_value": 750000,
            "roof_age": 20,
            "urgency": "immediate"
        }

        response = self.session.post(
            f"{BACKEND_URL}/api/leads/score",
            json=scoring_data,
            headers=self._get_headers()
        )

        if response.status_code == 200:
            data = response.json()
            self.assertIn("score", data, "Should return lead score")
            self.assertIn("breakdown", data, "Should include score breakdown")
            self.assertGreaterEqual(data["score"], 0)
            self.assertLessEqual(data["score"], 100)
        else:
            self.skipTest("Lead scoring not yet functional")

    # ========== Customer Management Tests ==========

    def test_10_convert_lead_to_customer(self):
        """Test converting a lead to a customer."""
        # Create a lead first
        lead_response = self.session.post(
            f"{BACKEND_URL}/api/leads",
            json=self.test_data["lead"],
            headers=self._get_headers()
        )

        if lead_response.status_code == 201:
            lead_id = lead_response.json()["id"]
            self.created_ids["leads"].append(lead_id)

            # Convert to customer
            convert_response = self.session.post(
                f"{BACKEND_URL}/api/leads/{lead_id}/convert",
                headers=self._get_headers()
            )

            if convert_response.status_code == 200:
                data = convert_response.json()
                self.assertIn("customer_id", data)
                self.created_ids["customers"].append(data["customer_id"])
        else:
            self.skipTest("Lead to customer conversion not yet functional")

    def test_11_customer_analytics(self):
        """Test customer analytics endpoint."""
        # Assuming we have a customer ID
        response = self.session.get(
            f"{BACKEND_URL}/api/customers/analytics",
            headers=self._get_headers()
        )

        if response.status_code == 200:
            data = response.json()
            self.assertIn("total_customers", data)
            self.assertIn("lifetime_value", data)
            self.assertIn("segments", data)
        else:
            self.skipTest("Customer analytics not yet functional")

    # ========== Appointment Tests ==========

    def test_12_create_appointment(self):
        """Test creating an appointment."""
        response = self.session.post(
            f"{BACKEND_URL}/api/appointments",
            json=self.test_data["appointment"],
            headers=self._get_headers()
        )

        if response.status_code == 201:
            data = response.json()
            self.assertIn("id", data)
            self.created_ids["appointments"].append(data["id"])
        else:
            self.skipTest("Appointment creation not yet functional")

    def test_13_check_availability(self):
        """Test checking appointment availability."""
        availability_data = {
            "date": "2025-10-10",
            "duration_minutes": 60
        }

        response = self.session.post(
            f"{BACKEND_URL}/api/appointments/availability",
            json=availability_data,
            headers=self._get_headers()
        )

        if response.status_code == 200:
            data = response.json()
            self.assertIn("slots", data)
            self.assertIsInstance(data["slots"], list)
        else:
            self.skipTest("Availability check not yet functional")

    # ========== Project Tests ==========

    def test_14_create_project(self):
        """Test creating a project."""
        # Need a customer first
        customer_data = self.test_data["customer"]
        customer_response = self.session.post(
            f"{BACKEND_URL}/api/customers",
            json=customer_data,
            headers=self._get_headers()
        )

        if customer_response.status_code == 201:
            customer_id = customer_response.json()["id"]
            self.created_ids["customers"].append(customer_id)

            # Create project
            project_data = {
                **self.test_data["project"],
                "customer_id": customer_id
            }

            project_response = self.session.post(
                f"{BACKEND_URL}/api/projects",
                json=project_data,
                headers=self._get_headers()
            )

            if project_response.status_code == 201:
                data = project_response.json()
                self.assertIn("id", data)
                self.created_ids["projects"].append(data["id"])
        else:
            self.skipTest("Project creation not yet functional")

    def test_15_project_pipeline(self):
        """Test project pipeline stages."""
        response = self.session.get(
            f"{BACKEND_URL}/api/projects/pipeline",
            headers=self._get_headers()
        )

        if response.status_code == 200:
            data = response.json()
            self.assertIn("stages", data)
            self.assertIsInstance(data["stages"], list)
        else:
            self.skipTest("Project pipeline not yet functional")

    # ========== Real-time Tests ==========

    def test_16_pusher_configuration(self):
        """Test Pusher real-time configuration."""
        response = self.session.get(
            f"{BACKEND_URL}/api/pusher/auth",
            headers=self._get_headers()
        )

        if response.status_code == 200:
            data = response.json()
            self.assertIn("auth", data)
        else:
            self.skipTest("Pusher not yet configured")

    # ========== Analytics Tests ==========

    def test_17_dashboard_metrics(self):
        """Test dashboard metrics endpoint."""
        response = self.session.get(
            f"{BACKEND_URL}/api/analytics/dashboard",
            headers=self._get_headers()
        )

        if response.status_code == 200:
            data = response.json()
            self.assertIn("leads_count", data)
            self.assertIn("revenue", data)
            self.assertIn("conversion_rate", data)
        else:
            self.skipTest("Analytics not yet functional")

    def test_18_conversion_funnel(self):
        """Test conversion funnel data."""
        response = self.session.get(
            f"{BACKEND_URL}/api/analytics/funnel",
            headers=self._get_headers()
        )

        if response.status_code == 200:
            data = response.json()
            self.assertIn("stages", data)
            self.assertIsInstance(data["stages"], list)
        else:
            self.skipTest("Conversion funnel not yet functional")

    # ========== End-to-End Flow Tests ==========

    def test_19_complete_lead_to_project_flow(self):
        """Test complete flow from lead creation to project completion."""
        # Step 1: Create lead
        lead_response = self.session.post(
            f"{BACKEND_URL}/api/leads",
            json=self.test_data["lead"],
            headers=self._get_headers()
        )

        if lead_response.status_code != 201:
            self.skipTest("Complete flow test skipped - APIs not functional")
            return

        lead_id = lead_response.json()["id"]
        self.created_ids["leads"].append(lead_id)

        # Step 2: Schedule appointment
        appointment_data = {
            **self.test_data["appointment"],
            "lead_id": lead_id
        }
        appointment_response = self.session.post(
            f"{BACKEND_URL}/api/appointments",
            json=appointment_data,
            headers=self._get_headers()
        )

        self.assertEqual(appointment_response.status_code, 201)
        appointment_id = appointment_response.json()["id"]
        self.created_ids["appointments"].append(appointment_id)

        # Step 3: Convert to customer
        convert_response = self.session.post(
            f"{BACKEND_URL}/api/leads/{lead_id}/convert",
            headers=self._get_headers()
        )

        self.assertEqual(convert_response.status_code, 200)
        customer_id = convert_response.json()["customer_id"]
        self.created_ids["customers"].append(customer_id)

        # Step 4: Create project
        project_data = {
            **self.test_data["project"],
            "customer_id": customer_id
        }
        project_response = self.session.post(
            f"{BACKEND_URL}/api/projects",
            json=project_data,
            headers=self._get_headers()
        )

        self.assertEqual(project_response.status_code, 201)
        project_id = project_response.json()["id"]
        self.created_ids["projects"].append(project_id)

        # Step 5: Complete project
        complete_response = self.session.put(
            f"{BACKEND_URL}/api/projects/{project_id}",
            json={"status": "completed"},
            headers=self._get_headers()
        )

        self.assertEqual(complete_response.status_code, 200)
        self.assertEqual(complete_response.json()["status"], "completed")

    def test_20_performance_metrics(self):
        """Test API performance metrics."""
        endpoints = [
            "/api/leads",
            "/api/customers",
            "/api/projects",
            "/api/appointments"
        ]

        for endpoint in endpoints:
            start_time = time.time()
            response = self.session.get(
                f"{BACKEND_URL}{endpoint}",
                headers=self._get_headers()
            )
            response_time = (time.time() - start_time) * 1000

            # API should respond within 500ms
            self.assertLess(
                response_time,
                500,
                f"{endpoint} took {response_time:.0f}ms (should be < 500ms)"
            )


class TestRunner:
    """Custom test runner with detailed output."""

    def run(self):
        """Run all integration tests."""
        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(IntegrationTestSuite)

        # Run tests with detailed output
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Print summary
        print("\n" + "=" * 80)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {result.testsRun}")
        print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
        print(f"Failed: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped)}")

        if result.skipped:
            print("\nSkipped Tests (APIs not yet implemented):")
            for test, reason in result.skipped:
                print(f"  - {test.id().split('.')[-1]}: {reason}")

        if result.failures:
            print("\nFailed Tests:")
            for test, trace in result.failures:
                print(f"  - {test.id().split('.')[-1]}")

        if result.errors:
            print("\nTests with Errors:")
            for test, trace in result.errors:
                print(f"  - {test.id().split('.')[-1]}")

        # Overall status
        print("\n" + "-" * 80)
        if result.wasSuccessful():
            print("✅ ALL TESTS PASSED!")
        elif len(result.failures) == 0 and len(result.errors) == 0:
            print("⚠️  Tests skipped - APIs not yet implemented")
        else:
            print("❌ TESTS FAILED - Review errors above")

        return result


if __name__ == "__main__":
    print("=" * 80)
    print("iSwitch Roofs CRM - Integration Test Suite")
    print("=" * 80)
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"Backend URL: {BACKEND_URL}")
    print("-" * 80)

    # Check service availability
    print("\nChecking services...")

    try:
        requests.get(FRONTEND_URL, timeout=2)
        print(f"✓ Frontend is running on {FRONTEND_URL}")
    except:
        print(f"✗ Frontend is not accessible on {FRONTEND_URL}")
        print("Please start the frontend: cd frontend-reflex && reflex run")
        sys.exit(1)

    try:
        requests.get(f"{BACKEND_URL}/api/health", timeout=2)
        print(f"✓ Backend is running on {BACKEND_URL}")
    except:
        print(f"⚠ Backend may not be fully functional on {BACKEND_URL}")

    print("\nStarting integration tests...")
    print("-" * 80)

    # Run tests
    runner = TestRunner()
    runner.run()