"""
iSwitch Roofs CRM - Lead Assignment Integration Tests
Version: 1.0.0

Tests for lead assignment endpoint.
"""

import pytest
import json
from uuid import uuid4
from unittest.mock import MagicMock

from app.models.lead import LeadStatus


class TestLeadAssignment:
    """Test suite for lead assignment functionality."""

    @pytest.mark.integration
    def test_assign_lead_success(self, client, auth_headers, mock_supabase_client):
        """Test successful lead assignment to team member."""
        lead_id = str(uuid4())
        team_member_id = str(uuid4())

        # Mock the lead fetch
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'id': lead_id,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '2485551234',
            'source': 'website_form',
            'status': 'new',
            'assigned_to': None
        }]

        # Mock the update
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            'id': lead_id,
            'assigned_to': team_member_id,
            'assigned_at': '2025-01-01T12:00:00',
            'status': 'contacted'
        }]

        response = client.post(
            f'/api/leads/{lead_id}/assign',
            json={
                'team_member_id': team_member_id,
                'notes': 'High priority lead, needs immediate follow-up'
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Lead assigned successfully'
        assert data['lead_id'] == lead_id
        assert data['assigned_to'] == team_member_id

    @pytest.mark.integration
    def test_assign_lead_not_found(self, client, auth_headers, mock_supabase_client):
        """Test assigning non-existent lead returns 404."""
        lead_id = str(uuid4())
        team_member_id = str(uuid4())

        # Mock empty result (lead not found)
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        response = client.post(
            f'/api/leads/{lead_id}/assign',
            json={'team_member_id': team_member_id},
            headers=auth_headers
        )

        assert response.status_code == 404
        assert 'not found' in response.json()['error'].lower()

    @pytest.mark.integration
    def test_assign_lead_already_assigned(self, client, auth_headers, mock_supabase_client):
        """Test reassigning a lead that's already assigned."""
        lead_id = str(uuid4())
        old_member_id = str(uuid4())
        new_member_id = str(uuid4())

        # Mock lead already assigned
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'id': lead_id,
            'assigned_to': old_member_id,
            'status': 'contacted'
        }]

        # Mock successful reassignment
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            'id': lead_id,
            'assigned_to': new_member_id
        }]

        response = client.post(
            f'/api/leads/{lead_id}/assign',
            json={
                'team_member_id': new_member_id,
                'force_reassign': True
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['assigned_to'] == new_member_id
        assert 'reassigned' in data.get('message', '').lower()

    @pytest.mark.integration
    def test_assign_lead_invalid_team_member(self, client, auth_headers, mock_supabase_client):
        """Test assigning lead to invalid team member."""
        lead_id = str(uuid4())

        # Mock lead exists
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'id': lead_id,
            'status': 'new'
        }]

        # Mock team member validation failure
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[{'id': lead_id}]),  # Lead exists
            MagicMock(data=[])  # Team member doesn't exist
        ]

        response = client.post(
            f'/api/leads/{lead_id}/assign',
            json={'team_member_id': 'invalid_id'},
            headers=auth_headers
        )

        assert response.status_code == 400
        assert 'team member' in response.json()['error'].lower()

    @pytest.mark.integration
    def test_assign_lead_without_auth(self, client):
        """Test that assignment requires authentication."""
        lead_id = str(uuid4())

        response = client.post(
            f'/api/leads/{lead_id}/assign',
            json={'team_member_id': str(uuid4())}
        )

        # Should require authentication
        assert response.status_code in [401, 403]

    @pytest.mark.integration
    def test_assign_lead_round_robin(self, client, auth_headers, mock_supabase_client):
        """Test automatic round-robin assignment."""
        lead_id = str(uuid4())

        # Mock lead exists
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'id': lead_id,
            'status': 'new'
        }]

        # Mock available team members
        team_members = [
            {'id': str(uuid4()), 'name': 'Sales Rep 1', 'active_leads': 5},
            {'id': str(uuid4()), 'name': 'Sales Rep 2', 'active_leads': 3},
            {'id': str(uuid4()), 'name': 'Sales Rep 3', 'active_leads': 4}
        ]

        response = client.post(
            f'/api/leads/{lead_id}/assign',
            json={'auto_assign': True, 'strategy': 'round_robin'},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert 'assigned_to' in data

    @pytest.mark.integration
    def test_assign_lead_with_notification(self, client, auth_headers, mock_supabase_client, mock_pusher_client):
        """Test that assignment triggers real-time notification."""
        lead_id = str(uuid4())
        team_member_id = str(uuid4())

        # Mock successful assignment
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'id': lead_id,
            'first_name': 'John',
            'last_name': 'Doe',
            'status': 'new'
        }]

        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            'id': lead_id,
            'assigned_to': team_member_id
        }]

        response = client.post(
            f'/api/leads/{lead_id}/assign',
            json={
                'team_member_id': team_member_id,
                'send_notification': True
            },
            headers=auth_headers
        )

        assert response.status_code == 200

        # Check that Pusher was called
        mock_pusher_client.trigger.assert_called()
        call_args = mock_pusher_client.trigger.call_args
        assert 'lead-assigned' in str(call_args)

    @pytest.mark.integration
    def test_assign_lead_validation(self, client, auth_headers):
        """Test input validation for assignment endpoint."""
        lead_id = str(uuid4())

        # Test missing team_member_id
        response = client.post(
            f'/api/leads/{lead_id}/assign',
            json={},
            headers=auth_headers
        )

        assert response.status_code == 400
        assert 'required' in response.json()['error'].lower()

        # Test invalid UUID format
        response = client.post(
            f'/api/leads/not-a-uuid/assign',
            json={'team_member_id': str(uuid4())},
            headers=auth_headers
        )

        assert response.status_code == 400
        assert 'invalid' in response.json()['error'].lower()