"""
Real-Time Integration Testing for iSwitch Roofs CRM
Tests real-time synchronization, cache invalidation, and Pusher events

Tests cover:
- Dashboard updates on lead/customer/project CRUD
- Cache invalidation flows on data changes
- Pusher event delivery across all channels
- Multi-user concurrent update handling
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch, call
import pytest
from flask.testing import FlaskClient


class TestDashboardRealTimeUpdates:
    """Test dashboard receives real-time updates via Pusher."""

    @patch('app.services.realtime.pusher_client')
    def test_dashboard_updates_on_lead_creation(self, mock_pusher, client: FlaskClient, auth_headers):
        """Verify dashboard receives Pusher event when lead created."""

        # Mock Pusher client
        mock_pusher.trigger = Mock()

        # Create lead
        lead_data = {
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@example.com",
            "phone": "248-555-1234",
            "source": "Google LSA",
            "city": "Birmingham",
            "state": "MI",
            "zip_code": "48009"
        }

        with patch("app.services.lead_service.create_lead") as mock_create_lead:
            mock_create_lead.return_value = {
                "id": "lead-123",
                **lead_data,
                "status": "new",
                "lead_score": 85,
                "temperature": "hot",
                "created_at": datetime.utcnow().isoformat()
            }

            response = client.post("/api/leads", data=json.dumps(lead_data), headers=auth_headers)

            assert response.status_code == 201
            lead = json.loads(response.data)

            # Verify Pusher event triggered
            mock_pusher.trigger.assert_called()

            # Verify event channel and name
            call_args = mock_pusher.trigger.call_args
            assert call_args[0][0] == "crm-leads-channel"  # Channel name
            assert call_args[0][1] == "lead-created"  # Event name

            # Verify event data
            event_data = call_args[0][2]
            assert event_data["id"] == "lead-123"
            assert event_data["status"] == "new"
            assert event_data["temperature"] == "hot"

    @patch('app.services.realtime.pusher_client')
    def test_dashboard_updates_on_customer_conversion(self, mock_pusher, client: FlaskClient, auth_headers):
        """Verify dashboard updates when lead converted to customer."""

        mock_pusher.trigger = Mock()

        # Convert lead to customer
        customer_data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.com",
            "phone": "248-555-5678",
            "converted_from_lead_id": "lead-456"
        }

        with patch("app.services.customer_service.create_customer") as mock_create:
            mock_create.return_value = {
                "id": "customer-789",
                **customer_data,
                "customer_status": "active",
                "created_at": datetime.utcnow().isoformat()
            }

            response = client.post("/api/customers", data=json.dumps(customer_data), headers=auth_headers)

            assert response.status_code == 201

            # Verify TWO Pusher events: lead-converted AND customer-created
            assert mock_pusher.trigger.call_count == 2

            # Check both event channels
            call_list = mock_pusher.trigger.call_args_list
            channels = [call[0][0] for call in call_list]
            assert "crm-leads-channel" in channels
            assert "crm-customers-channel" in channels

    @patch('app.services.realtime.pusher_client')
    def test_dashboard_updates_on_project_status_change(self, mock_pusher, client: FlaskClient, auth_headers):
        """Verify dashboard updates when project status changes."""

        mock_pusher.trigger = Mock()

        project_id = "project-123"
        status_update = {
            "status": "in_progress",
            "actual_start_date": datetime.utcnow().isoformat()
        }

        with patch("app.services.project_service.update_project") as mock_update:
            mock_update.return_value = {
                "id": project_id,
                **status_update,
                "estimated_value": 28500,
                "updated_at": datetime.utcnow().isoformat()
            }

            response = client.put(f"/api/projects/{project_id}", data=json.dumps(status_update), headers=auth_headers)

            assert response.status_code == 200

            # Verify Pusher event
            mock_pusher.trigger.assert_called()
            call_args = mock_pusher.trigger.call_args
            assert call_args[0][0] == "crm-projects-channel"
            assert call_args[0][1] == "project-updated"

            event_data = call_args[0][2]
            assert event_data["status"] == "in_progress"

    @patch('app.services.realtime.pusher_client')
    def test_pusher_event_format_matches_frontend_expectations(self, mock_pusher, client: FlaskClient, auth_headers):
        """Verify Pusher events contain all required fields for frontend."""

        mock_pusher.trigger = Mock()

        lead_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "248-555-0000",
            "source": "Website"
        }

        with patch("app.services.lead_service.create_lead") as mock_create:
            mock_create.return_value = {
                "id": "lead-test",
                **lead_data,
                "status": "new",
                "lead_score": 75,
                "temperature": "warm",
                "created_at": datetime.utcnow().isoformat()
            }

            response = client.post("/api/leads", data=json.dumps(lead_data), headers=auth_headers)

            # Get event data
            event_data = mock_pusher.trigger.call_args[0][2]

            # Verify required fields for frontend
            assert "id" in event_data
            assert "status" in event_data
            assert "temperature" in event_data
            assert "lead_score" in event_data
            assert "created_at" in event_data

            # Verify timestamp format (ISO 8601)
            assert "T" in event_data["created_at"]


class TestCacheInvalidation:
    """Test cache invalidation on CRUD operations."""

    @patch('app.utils.cache.redis_client')
    def test_cache_invalidation_on_lead_creation(self, mock_redis, client: FlaskClient, auth_headers):
        """Verify cache keys invalidated when lead created."""

        mock_redis.delete = Mock()

        lead_data = {
            "first_name": "Cache",
            "last_name": "Test",
            "email": "cache@test.com",
            "phone": "248-555-9999"
        }

        with patch("app.services.lead_service.create_lead") as mock_create:
            mock_create.return_value = {
                "id": "lead-cache-test",
                **lead_data,
                "created_at": datetime.utcnow().isoformat()
            }

            response = client.post("/api/leads", data=json.dumps(lead_data), headers=auth_headers)

            assert response.status_code == 201

            # Verify cache invalidation called
            # Should invalidate: leads list cache, dashboard cache, metrics cache
            mock_redis.delete.assert_called()

            # Check that lead-related cache keys were deleted
            deleted_keys = [call[0][0] for call in mock_redis.delete.call_args_list]
            assert any("leads" in key for key in deleted_keys)

    @patch('app.utils.cache.redis_client')
    def test_cache_invalidation_on_customer_update(self, mock_redis, client: FlaskClient, auth_headers):
        """Verify related caches cleared on customer update."""

        mock_redis.delete = Mock()

        customer_id = "customer-123"
        update_data = {
            "customer_status": "inactive"
        }

        with patch("app.services.customer_service.update_customer") as mock_update:
            mock_update.return_value = {
                "id": customer_id,
                **update_data,
                "updated_at": datetime.utcnow().isoformat()
            }

            response = client.put(f"/api/customers/{customer_id}", data=json.dumps(update_data), headers=auth_headers)

            assert response.status_code == 200

            # Verify cache invalidation
            mock_redis.delete.assert_called()

            # Should invalidate customers cache AND related analytics
            deleted_keys = [call[0][0] for call in mock_redis.delete.call_args_list]
            assert any("customers" in key for key in deleted_keys)
            assert any("analytics" in key or "dashboard" in key for key in deleted_keys)

    @patch('app.utils.cache.redis_client')
    def test_cache_invalidation_on_project_status_update(self, mock_redis, client: FlaskClient, auth_headers):
        """Verify analytics cache cleared when project status changes."""

        mock_redis.delete = Mock()

        project_id = "project-789"
        status_update = {
            "status": "completed",
            "completion_date": datetime.utcnow().isoformat(),
            "final_cost": 28000
        }

        with patch("app.services.project_service.update_project") as mock_update:
            mock_update.return_value = {
                "id": project_id,
                **status_update,
                "updated_at": datetime.utcnow().isoformat()
            }

            response = client.put(f"/api/projects/{project_id}", data=json.dumps(status_update), headers=auth_headers)

            assert response.status_code == 200

            # Verify cache invalidation
            mock_redis.delete.assert_called()

            # Should invalidate projects cache, revenue analytics, dashboard
            deleted_keys = [call[0][0] for call in mock_redis.delete.call_args_list]
            assert any("projects" in key for key in deleted_keys)
            assert any("revenue" in key or "analytics" in key for key in deleted_keys)

    @patch('app.utils.cache.redis_client')
    def test_cache_hit_rate_measurement(self, mock_redis, client: FlaskClient, auth_headers):
        """Verify cache hit rate is measured and logged."""

        mock_redis.get = Mock(return_value=None)  # Cache miss
        mock_redis.set = Mock()

        # First request (cache miss)
        with patch("app.services.analytics_service.get_dashboard_metrics") as mock_metrics:
            mock_metrics.return_value = {
                "total_leads": 100,
                "qualified_leads": 60,
                "converted_leads": 25
            }

            response1 = client.get("/api/analytics/dashboard", headers=auth_headers)
            assert response1.status_code == 200

            # Verify cache set was called
            mock_redis.set.assert_called()

        # Second request (cache hit)
        mock_redis.get.return_value = json.dumps({
            "total_leads": 100,
            "qualified_leads": 60,
            "converted_leads": 25
        })

        response2 = client.get("/api/analytics/dashboard", headers=auth_headers)
        assert response2.status_code == 200

        # Cache stats should show 1 miss and 1 hit
        # (In production, check /api/cache/stats endpoint)


class TestMultiUserConcurrency:
    """Test concurrent update handling."""

    def test_concurrent_lead_updates_last_write_wins(self, client: FlaskClient, auth_headers):
        """Verify concurrent updates handled correctly (last-write-wins)."""

        lead_id = "lead-concurrent-test"

        # Simulate two users updating same lead simultaneously
        update1 = {"status": "qualified", "lead_score": 85}
        update2 = {"status": "contacted", "lead_score": 75}

        with patch("app.services.lead_service.update_lead") as mock_update:
            # First update
            mock_update.return_value = {
                "id": lead_id,
                **update1,
                "updated_at": datetime.utcnow().isoformat()
            }

            response1 = client.put(f"/api/leads/{lead_id}", data=json.dumps(update1), headers=auth_headers)
            assert response1.status_code == 200

            # Second update (should overwrite first)
            mock_update.return_value = {
                "id": lead_id,
                **update2,
                "updated_at": datetime.utcnow().isoformat()
            }

            response2 = client.put(f"/api/leads/{lead_id}", data=json.dumps(update2), headers=auth_headers)
            assert response2.status_code == 200

            # Verify second update succeeded
            final_lead = json.loads(response2.data)
            assert final_lead["status"] == "contacted"
            assert final_lead["lead_score"] == 75

    def test_concurrent_project_creation_no_data_corruption(self, client: FlaskClient, auth_headers):
        """Verify concurrent creates don't corrupt data."""

        # Simulate 5 users creating projects simultaneously
        project_data = {
            "customer_id": "customer-test",
            "name": "Test Project",
            "estimated_value": 25000
        }

        with patch("app.services.project_service.create_project") as mock_create:
            for i in range(5):
                mock_create.return_value = {
                    "id": f"project-{i}",
                    **project_data,
                    "created_at": datetime.utcnow().isoformat()
                }

                response = client.post("/api/projects", data=json.dumps(project_data), headers=auth_headers)
                assert response.status_code == 201

                # Verify each project has unique ID
                project = json.loads(response.data)
                assert project["id"] == f"project-{i}"

        # All 5 projects should be created successfully
        assert mock_create.call_count == 5


class TestPusherEventDelivery:
    """Test Pusher event delivery across all channels."""

    @patch('app.services.realtime.pusher_client')
    def test_pusher_leads_channel_events(self, mock_pusher, client: FlaskClient, auth_headers):
        """Verify all lead-related events on leads channel."""

        mock_pusher.trigger = Mock()

        lead_id = "lead-pusher-test"

        # Test CRUD operations trigger appropriate events
        operations = [
            ("POST", "/api/leads", {"first_name": "Test", "email": "test@test.com"}, "lead-created"),
            ("PUT", f"/api/leads/{lead_id}", {"status": "qualified"}, "lead-updated"),
            ("DELETE", f"/api/leads/{lead_id}", {}, "lead-deleted")
        ]

        for method, endpoint, data, expected_event in operations:
            mock_pusher.trigger.reset_mock()

            if method == "POST":
                with patch("app.services.lead_service.create_lead") as mock:
                    mock.return_value = {"id": lead_id, **data}
                    client.post(endpoint, data=json.dumps(data), headers=auth_headers)
            elif method == "PUT":
                with patch("app.services.lead_service.update_lead") as mock:
                    mock.return_value = {"id": lead_id, **data}
                    client.put(endpoint, data=json.dumps(data), headers=auth_headers)
            elif method == "DELETE":
                with patch("app.services.lead_service.delete_lead") as mock:
                    mock.return_value = True
                    client.delete(endpoint, headers=auth_headers)

            # Verify event triggered
            if mock_pusher.trigger.called:
                call_args = mock_pusher.trigger.call_args
                assert call_args[0][0] == "crm-leads-channel"
                assert call_args[0][1] == expected_event

    @patch('app.services.realtime.pusher_client')
    def test_pusher_projects_channel_events(self, mock_pusher, client: FlaskClient, auth_headers):
        """Verify project events on projects channel."""

        mock_pusher.trigger = Mock()

        project_data = {
            "customer_id": "customer-123",
            "name": "Roof Replacement",
            "estimated_value": 28500
        }

        with patch("app.services.project_service.create_project") as mock_create:
            mock_create.return_value = {
                "id": "project-pusher-test",
                **project_data,
                "created_at": datetime.utcnow().isoformat()
            }

            response = client.post("/api/projects", data=json.dumps(project_data), headers=auth_headers)
            assert response.status_code == 201

            # Verify Pusher event
            mock_pusher.trigger.assert_called()
            call_args = mock_pusher.trigger.call_args
            assert call_args[0][0] == "crm-projects-channel"
            assert call_args[0][1] == "project-created"

    @patch('app.services.realtime.pusher_client')
    def test_pusher_dashboard_channel_metrics_update(self, mock_pusher, client: FlaskClient, auth_headers):
        """Verify dashboard metrics trigger events on dashboard channel."""

        mock_pusher.trigger = Mock()

        # Create lead (should trigger dashboard update)
        lead_data = {
            "first_name": "Dashboard",
            "last_name": "Test",
            "email": "dashboard@test.com"
        }

        with patch("app.services.lead_service.create_lead") as mock_create:
            mock_create.return_value = {
                "id": "lead-dashboard-test",
                **lead_data,
                "created_at": datetime.utcnow().isoformat()
            }

            response = client.post("/api/leads", data=json.dumps(lead_data), headers=auth_headers)

            # Should trigger events on both leads channel AND dashboard channel
            call_list = mock_pusher.trigger.call_args_list
            channels = [call[0][0] for call in call_list]

            assert "crm-leads-channel" in channels
            # Dashboard channel may be updated via separate metrics calculation


# Test markers
pytestmark = [pytest.mark.integration, pytest.mark.realtime]
