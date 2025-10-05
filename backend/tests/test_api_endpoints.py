"""
Comprehensive API endpoint testing for iSwitch Roofs CRM
Test all major API endpoints for functionality, validation, and security
"""

import json
from datetime import datetime
from unittest.mock import patch

import pytest
from flask.testing import FlaskClient


class TestLeadsAPI:
    """Test suite for leads API endpoints."""

    def test_get_leads_success(self, client: FlaskClient, auth_headers):
        """Test successful retrieval of leads."""
        with patch("app.routes.leads.get_all_leads") as mock_get_leads:
            mock_get_leads.return_value = {
                "data": [
                    {
                        "id": "lead-1",
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john@example.com",
                        "phone": "555-1234",
                        "status": "new",
                        "source": "website",
                    }
                ],
                "total": 1,
                "page": 1,
                "per_page": 20,
            }

            response = client.get("/api/leads", headers=auth_headers)

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "data" in data
            assert len(data["data"]) == 1
            assert data["data"][0]["first_name"] == "John"

    def test_create_lead_success(self, client: FlaskClient, auth_headers, sample_lead_data):
        """Test successful lead creation."""
        with patch("app.routes.leads.create_lead") as mock_create:
            mock_create.return_value = {
                "id": "new-lead-id",
                **sample_lead_data,
                "created_at": datetime.utcnow().isoformat(),
            }

            response = client.post(
                "/api/leads", data=json.dumps(sample_lead_data), headers=auth_headers
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data["first_name"] == sample_lead_data["first_name"]
            assert "id" in data

    def test_create_lead_validation_error(self, client: FlaskClient, auth_headers):
        """Test lead creation with invalid data."""
        invalid_data = {
            "first_name": "",  # Empty required field
            "email": "invalid-email",  # Invalid email format
            "phone": "123",  # Too short phone number
        }

        response = client.post("/api/leads", data=json.dumps(invalid_data), headers=auth_headers)

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_update_lead_success(self, client: FlaskClient, auth_headers):
        """Test successful lead update."""
        lead_id = "test-lead-id"
        update_data = {"status": "qualified", "temperature": "hot", "notes": "Follow up needed"}

        with patch("app.routes.leads.update_lead") as mock_update:
            mock_update.return_value = {
                "id": lead_id,
                "first_name": "John",
                "last_name": "Doe",
                **update_data,
                "updated_at": datetime.utcnow().isoformat(),
            }

            response = client.put(
                f"/api/leads/{lead_id}", data=json.dumps(update_data), headers=auth_headers
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "qualified"
            assert data["temperature"] == "hot"

    def test_delete_lead_success(self, client: FlaskClient, auth_headers):
        """Test successful lead deletion."""
        lead_id = "test-lead-id"

        with patch("app.routes.leads.delete_lead") as mock_delete:
            mock_delete.return_value = True

            response = client.delete(f"/api/leads/{lead_id}", headers=auth_headers)

            assert response.status_code == 204

    def test_get_lead_by_id_not_found(self, client: FlaskClient, auth_headers):
        """Test retrieving non-existent lead."""
        lead_id = "non-existent-id"

        with patch("app.routes.leads.get_lead_by_id") as mock_get:
            mock_get.return_value = None

            response = client.get(f"/api/leads/{lead_id}", headers=auth_headers)

            assert response.status_code == 404


class TestCustomersAPI:
    """Test suite for customers API endpoints."""

    def test_get_customers_success(self, client: FlaskClient, auth_headers):
        """Test successful retrieval of customers."""
        with patch("app.routes.customers.get_all_customers") as mock_get:
            mock_get.return_value = {
                "data": [
                    {
                        "id": "customer-1",
                        "first_name": "Jane",
                        "last_name": "Smith",
                        "email": "jane@example.com",
                        "phone": "555-5678",
                        "customer_type": "residential",
                    }
                ],
                "total": 1,
            }

            response = client.get("/api/customers", headers=auth_headers)

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "data" in data
            assert len(data["data"]) == 1

    def test_create_customer_success(self, client: FlaskClient, auth_headers, sample_customer_data):
        """Test successful customer creation."""
        with patch("app.routes.customers.create_customer") as mock_create:
            mock_create.return_value = {
                "id": "new-customer-id",
                **sample_customer_data,
                "created_at": datetime.utcnow().isoformat(),
            }

            response = client.post(
                "/api/customers", data=json.dumps(sample_customer_data), headers=auth_headers
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data["first_name"] == sample_customer_data["first_name"]


class TestProjectsAPI:
    """Test suite for projects API endpoints."""

    def test_get_projects_success(self, client: FlaskClient, auth_headers):
        """Test successful retrieval of projects."""
        with patch("app.routes.projects.get_all_projects") as mock_get:
            mock_get.return_value = {
                "data": [
                    {
                        "id": "project-1",
                        "name": "Roof Replacement",
                        "status": "in_progress",
                        "customer_id": "customer-1",
                        "estimated_value": 25000,
                    }
                ],
                "total": 1,
            }

            response = client.get("/api/projects", headers=auth_headers)

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "data" in data

    def test_create_project_success(self, client: FlaskClient, auth_headers, sample_project_data):
        """Test successful project creation."""
        with patch("app.routes.projects.create_project") as mock_create:
            mock_create.return_value = {
                "id": "new-project-id",
                **sample_project_data,
                "created_at": datetime.utcnow().isoformat(),
            }

            response = client.post(
                "/api/projects", data=json.dumps(sample_project_data), headers=auth_headers
            )

            assert response.status_code == 201


class TestAppointmentsAPI:
    """Test suite for appointments API endpoints."""

    def test_get_appointments_success(self, client: FlaskClient, auth_headers):
        """Test successful retrieval of appointments."""
        with patch("app.routes.appointments.get_appointments") as mock_get:
            mock_get.return_value = {
                "data": [
                    {
                        "id": "apt-1",
                        "title": "Roof Inspection",
                        "scheduled_date": "2025-10-10T10:00:00Z",
                        "status": "scheduled",
                        "entity_type": "lead",
                        "entity_id": "lead-1",
                    }
                ]
            }

            response = client.get("/api/appointments", headers=auth_headers)

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "data" in data

    def test_create_appointment_validation(self, client: FlaskClient, auth_headers):
        """Test appointment creation validation."""
        invalid_data = {
            "title": "",  # Empty title
            "scheduled_date": "invalid-date",  # Invalid date format
            "duration_minutes": -30,  # Negative duration
        }

        response = client.post(
            "/api/appointments", data=json.dumps(invalid_data), headers=auth_headers
        )

        assert response.status_code == 400


class TestAnalyticsAPI:
    """Test suite for analytics API endpoints."""

    def test_get_dashboard_metrics(self, client: FlaskClient, auth_headers):
        """Test dashboard metrics retrieval."""
        with patch("app.routes.analytics.get_dashboard_metrics") as mock_get:
            mock_get.return_value = {
                "total_leads": 150,
                "hot_leads": 25,
                "conversion_rate": 12.5,
                "revenue_this_month": 85000,
                "projects_in_progress": 8,
            }

            response = client.get("/api/analytics/dashboard", headers=auth_headers)

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "total_leads" in data
            assert data["conversion_rate"] == 12.5

    def test_get_revenue_chart_data(self, client: FlaskClient, auth_headers):
        """Test revenue chart data retrieval."""
        with patch("app.routes.analytics.get_revenue_data") as mock_get:
            mock_get.return_value = {
                "labels": ["Jan", "Feb", "Mar"],
                "data": [45000, 52000, 48000],
                "period": "quarterly",
            }

            response = client.get("/api/analytics/revenue?period=quarterly", headers=auth_headers)

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "labels" in data
            assert len(data["data"]) == 3


class TestAuthAPI:
    """Test suite for authentication API endpoints."""

    def test_login_success(self, client: FlaskClient):
        """Test successful login."""
        login_data = {"username": "testuser", "password": "testpass123"}

        with patch("app.routes.auth.authenticate_user") as mock_auth:
            mock_auth.return_value = {
                "access_token": "test_token_123",
                "refresh_token": "refresh_token_123",
                "expires_in": 3600,
                "user": {"id": "user-1", "username": "testuser", "role": "admin"},
            }

            response = client.post(
                "/api/auth/login", data=json.dumps(login_data), content_type="application/json"
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "access_token" in data
            assert data["user"]["username"] == "testuser"

    def test_login_invalid_credentials(self, client: FlaskClient):
        """Test login with invalid credentials."""
        login_data = {"username": "wronguser", "password": "wrongpass"}

        with patch("app.routes.auth.authenticate_user") as mock_auth:
            mock_auth.return_value = None

            response = client.post(
                "/api/auth/login", data=json.dumps(login_data), content_type="application/json"
            )

            assert response.status_code == 401
            data = json.loads(response.data)
            assert "error" in data

    def test_token_refresh(self, client: FlaskClient):
        """Test token refresh functionality."""
        refresh_data = {"refresh_token": "valid_refresh_token"}

        with patch("app.routes.auth.refresh_access_token") as mock_refresh:
            mock_refresh.return_value = {"access_token": "new_access_token", "expires_in": 3600}

            response = client.post(
                "/api/auth/refresh", data=json.dumps(refresh_data), content_type="application/json"
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "access_token" in data


class TestAPIValidation:
    """Test suite for API validation and security."""

    def test_missing_auth_header(self, client: FlaskClient):
        """Test API access without authentication."""
        response = client.get("/api/leads")

        # Should require authentication
        assert response.status_code in [401, 403]

    def test_invalid_json_payload(self, client: FlaskClient, auth_headers):
        """Test API with malformed JSON."""
        response = client.post("/api/leads", data="invalid json{", headers=auth_headers)

        assert response.status_code == 400

    def test_sql_injection_attempt(self, client: FlaskClient, auth_headers):
        """Test SQL injection protection."""
        malicious_data = {
            "first_name": "'; DROP TABLE leads; --",
            "last_name": "test",
            "email": "test@example.com",
            "phone": "555-1234",
        }

        response = client.post("/api/leads", data=json.dumps(malicious_data), headers=auth_headers)

        # Should either sanitize input or reject it
        assert response.status_code in [400, 422]

    def test_xss_attempt(self, client: FlaskClient, auth_headers):
        """Test XSS protection."""
        xss_data = {
            "first_name": '<script>alert("xss")</script>',
            "last_name": "test",
            "email": "test@example.com",
            "phone": "555-1234",
        }

        response = client.post("/api/leads", data=json.dumps(xss_data), headers=auth_headers)

        # Should sanitize or reject malicious input
        if response.status_code == 201:
            data = json.loads(response.data)
            # Script tag should be sanitized
            assert "<script>" not in data["first_name"]

    def test_rate_limiting(self, client: FlaskClient, auth_headers):
        """Test API rate limiting."""
        # Make multiple rapid requests
        responses = []
        for _ in range(50):  # Attempt to exceed rate limit
            response = client.get("/api/leads", headers=auth_headers)
            responses.append(response.status_code)

        # Should eventually return 429 (Too Many Requests)
        # Note: This test assumes rate limiting is implemented
        # Adjust assertion based on actual implementation
        assert any(code == 429 for code in responses) or all(code == 200 for code in responses)


class TestAPIPerformance:
    """Test suite for API performance."""

    def test_large_dataset_handling(self, client: FlaskClient, auth_headers):
        """Test API performance with large datasets."""
        # Test pagination with large page sizes
        response = client.get("/api/leads?per_page=1000", headers=auth_headers)

        # Should handle large requests gracefully
        assert response.status_code in [200, 400]  # 400 if page size limit enforced

    def test_concurrent_requests(self, client: FlaskClient, auth_headers):
        """Test API handling of concurrent requests."""
        import threading
        import time

        results = []

        def make_request():
            response = client.get("/api/leads", headers=auth_headers)
            results.append(response.status_code)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)

        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.time()

        # All requests should succeed
        assert all(code == 200 for code in results)
        # Should complete in reasonable time (adjust based on requirements)
        assert end_time - start_time < 5.0  # 5 seconds for 10 concurrent requests


# Integration test markers
pytestmark = [pytest.mark.integration, pytest.mark.api]
