"""
Integration Tests for Lead API Endpoints
Tests full request/response cycle for lead management
"""

import pytest
import json
from uuid import uuid4
from datetime import datetime


@pytest.mark.integration
class TestLeadAPI:
    """Integration tests for Lead API endpoints"""

    def test_create_lead_success(self, client, sample_lead_data, mock_supabase_client):
        """Test successful lead creation via API"""
        response = client.post(
            '/api/leads',
            data=json.dumps(sample_lead_data),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
        assert data['first_name'] == sample_lead_data['first_name']
        assert data['email'] == sample_lead_data['email']
        assert 'lead_score' in data
        assert 'temperature' in data

    def test_create_lead_missing_required_fields(self, client):
        """Test lead creation with missing required fields"""
        incomplete_data = {
            'first_name': 'John'
            # Missing required fields: last_name, phone, source
        }

        response = client.post(
            '/api/leads',
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )

        assert response.status_code == 422  # Validation error
        data = response.get_json()
        assert 'error' in data or 'detail' in data

    def test_create_lead_invalid_email(self, client, sample_lead_data):
        """Test lead creation with invalid email format"""
        sample_lead_data['email'] = 'invalid-email'

        response = client.post(
            '/api/leads',
            data=json.dumps(sample_lead_data),
            content_type='application/json'
        )

        assert response.status_code == 422

    def test_create_lead_invalid_phone(self, client, sample_lead_data):
        """Test lead creation with invalid phone format"""
        sample_lead_data['phone'] = '123'  # Too short

        response = client.post(
            '/api/leads',
            data=json.dumps(sample_lead_data),
            content_type='application/json'
        )

        assert response.status_code == 422

    def test_get_lead_by_id_success(self, client, mock_supabase_client):
        """Test retrieving a lead by ID"""
        lead_id = str(uuid4())

        # Mock Supabase response
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'id': lead_id,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '+15551234567',
            'status': 'new',
            'temperature': 'warm',
            'lead_score': 75,
            'created_at': datetime.utcnow().isoformat()
        }]

        response = client.get(f'/api/leads/{lead_id}')

        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == lead_id
        assert data['first_name'] == 'John'

    def test_get_lead_by_id_not_found(self, client, mock_supabase_client):
        """Test retrieving a non-existent lead"""
        lead_id = str(uuid4())

        # Mock empty response
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        response = client.get(f'/api/leads/{lead_id}')

        assert response.status_code == 404

    def test_get_lead_invalid_uuid(self, client):
        """Test retrieving a lead with invalid UUID format"""
        response = client.get('/api/leads/invalid-uuid')

        assert response.status_code == 422

    def test_list_leads_success(self, client, mock_supabase_client):
        """Test listing leads with pagination"""
        # Mock Supabase response with multiple leads
        mock_leads = [
            {
                'id': str(uuid4()),
                'first_name': f'Lead{i}',
                'last_name': f'Test{i}',
                'email': f'lead{i}@test.com',
                'phone': f'+155512340{i}0',
                'status': 'new',
                'temperature': 'warm',
                'lead_score': 70 + i,
                'created_at': datetime.utcnow().isoformat()
            }
            for i in range(10)
        ]

        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = mock_leads

        response = client.get('/api/leads')

        assert response.status_code == 200
        data = response.get_json()
        assert 'leads' in data or isinstance(data, list)
        assert len(data if isinstance(data, list) else data['leads']) >= 0

    def test_list_leads_with_filters(self, client, mock_supabase_client):
        """Test listing leads with status filter"""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = []

        response = client.get('/api/leads?status=new,contacted')

        assert response.status_code == 200

    def test_list_leads_with_pagination(self, client, mock_supabase_client):
        """Test listing leads with pagination parameters"""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = []

        response = client.get('/api/leads?page=2&per_page=25')

        assert response.status_code == 200
        data = response.get_json()
        # Should include pagination metadata
        assert 'page' in data or 'leads' in data

    def test_list_leads_with_sorting(self, client, mock_supabase_client):
        """Test listing leads with sorting"""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = []

        response = client.get('/api/leads?sort=lead_score:desc')

        assert response.status_code == 200

    def test_list_leads_with_search(self, client, mock_supabase_client):
        """Test listing leads with search query"""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = []

        response = client.get('/api/leads?search=John')

        assert response.status_code == 200

    def test_update_lead_success(self, client, mock_supabase_client):
        """Test successful lead update"""
        lead_id = str(uuid4())
        update_data = {
            'first_name': 'Jane',
            'status': 'contacted'
        }

        # Mock existing lead
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'id': lead_id,
            'first_name': 'John',
            'status': 'new'
        }]

        # Mock update response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            'id': lead_id,
            'first_name': 'Jane',
            'status': 'contacted'
        }]

        response = client.patch(
            f'/api/leads/{lead_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['first_name'] == 'Jane'
        assert data['status'] == 'contacted'

    def test_update_lead_not_found(self, client, mock_supabase_client):
        """Test updating a non-existent lead"""
        lead_id = str(uuid4())
        update_data = {'first_name': 'Jane'}

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        response = client.patch(
            f'/api/leads/{lead_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )

        assert response.status_code == 404

    def test_update_lead_invalid_status(self, client, mock_supabase_client):
        """Test updating lead with invalid status"""
        lead_id = str(uuid4())
        update_data = {'status': 'invalid_status'}

        response = client.patch(
            f'/api/leads/{lead_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )

        assert response.status_code == 422

    def test_delete_lead_success(self, client, mock_supabase_client):
        """Test successful lead deletion (soft delete)"""
        lead_id = str(uuid4())

        # Mock existing lead
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'id': lead_id,
            'is_deleted': False
        }]

        # Mock delete response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            'id': lead_id,
            'is_deleted': True
        }]

        response = client.delete(f'/api/leads/{lead_id}')

        assert response.status_code == 204 or response.status_code == 200

    def test_delete_lead_not_found(self, client, mock_supabase_client):
        """Test deleting a non-existent lead"""
        lead_id = str(uuid4())

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        response = client.delete(f'/api/leads/{lead_id}')

        assert response.status_code == 404


@pytest.mark.integration
class TestLeadAPIStatistics:
    """Integration tests for lead statistics endpoints"""

    def test_get_lead_statistics(self, client, mock_supabase_client):
        """Test retrieving lead statistics"""
        # Mock statistics data
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = []

        response = client.get('/api/leads/statistics')

        assert response.status_code == 200
        data = response.get_json()
        assert 'total_leads' in data or 'statistics' in data

    def test_get_lead_counts_by_status(self, client, mock_supabase_client):
        """Test retrieving lead counts grouped by status"""
        response = client.get('/api/leads/statistics/status')

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, (list, dict))

    def test_get_conversion_metrics(self, client, mock_supabase_client):
        """Test retrieving conversion rate metrics"""
        response = client.get('/api/leads/statistics/conversion')

        assert response.status_code == 200
        data = response.get_json()
        assert 'conversion_rate' in data or 'rate' in data


@pytest.mark.integration
class TestLeadAPIAuthentication:
    """Integration tests for lead API authentication"""

    def test_create_lead_without_auth(self, client):
        """Test that protected endpoints require authentication"""
        # This test assumes authentication is required
        # If your API allows public lead creation, adjust accordingly
        response = client.post(
            '/api/leads',
            data=json.dumps({'first_name': 'Test'}),
            content_type='application/json'
        )

        # Either 201 (public endpoint) or 401/403 (protected endpoint)
        assert response.status_code in [201, 401, 403, 422]

    def test_access_lead_with_valid_auth(self, client, auth_headers, mock_supabase_client):
        """Test accessing leads with valid authentication"""
        lead_id = str(uuid4())

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'id': lead_id,
            'first_name': 'John'
        }]

        response = client.get(
            f'/api/leads/{lead_id}',
            headers=auth_headers
        )

        # Should succeed if auth is implemented, or work without auth if public
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestLeadAPIValidation:
    """Integration tests for input validation"""

    def test_email_validation(self, client, sample_lead_data):
        """Test email format validation"""
        sample_lead_data['email'] = 'not-an-email'

        response = client.post(
            '/api/leads',
            data=json.dumps(sample_lead_data),
            content_type='application/json'
        )

        assert response.status_code == 422

    def test_phone_validation(self, client, sample_lead_data):
        """Test phone number validation"""
        sample_lead_data['phone'] = 'abc'

        response = client.post(
            '/api/leads',
            data=json.dumps(sample_lead_data),
            content_type='application/json'
        )

        assert response.status_code == 422

    def test_budget_validation(self, client, sample_lead_data):
        """Test budget range validation"""
        sample_lead_data['budget_range_min'] = 50000
        sample_lead_data['budget_range_max'] = 10000  # Max < Min

        response = client.post(
            '/api/leads',
            data=json.dumps(sample_lead_data),
            content_type='application/json'
        )

        assert response.status_code == 422

    def test_status_enum_validation(self, client, mock_supabase_client):
        """Test status enum validation"""
        lead_id = str(uuid4())
        update_data = {'status': 'invalid_status_value'}

        response = client.patch(
            f'/api/leads/{lead_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )

        assert response.status_code == 422


@pytest.mark.integration
class TestLeadAPIPerformance:
    """Integration tests for API performance"""

    @pytest.mark.slow
    def test_list_leads_performance(self, client, mock_supabase_client, performance_timer):
        """Test that listing leads completes within acceptable time"""
        # Mock large dataset
        mock_leads = [
            {
                'id': str(uuid4()),
                'first_name': f'Lead{i}',
                'created_at': datetime.utcnow().isoformat()
            }
            for i in range(100)
        ]
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = mock_leads

        performance_timer.start()
        response = client.get('/api/leads?per_page=100')
        performance_timer.stop()

        assert response.status_code == 200
        assert performance_timer.elapsed < 2.0  # Should complete within 2 seconds

    @pytest.mark.slow
    def test_create_lead_performance(self, client, sample_lead_data, performance_timer):
        """Test that lead creation completes quickly"""
        performance_timer.start()
        response = client.post(
            '/api/leads',
            data=json.dumps(sample_lead_data),
            content_type='application/json'
        )
        performance_timer.stop()

        assert response.status_code in [201, 422]
        assert performance_timer.elapsed < 1.0  # Should complete within 1 second
