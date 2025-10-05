"""
Customer API Integration Tests
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4

from app import create_app


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch('app.routes.customers.get_supabase_client') as mock:
        mock_client = MagicMock()

        # Setup the chain for from_() -> select() -> order() -> range() -> execute()
        mock_query = MagicMock()
        mock_client.from_.return_value.select.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.gte.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.ilike.return_value = mock_query

        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_pusher():
    """Mock Pusher client."""
    with patch('app.routes.customers.pusher_client') as mock:
        yield mock


@pytest.fixture
def mock_customer_service():
    """Mock customer service."""
    with patch('app.routes.customers.customer_service') as mock:
        # Set default return values for service methods
        mock.get_customer_insights.return_value = {
            'total_value': 50000,
            'projects_count': 2,
            'average_project_value': 25000,
            'last_project_date': '2024-01-01',
            'referrals_generated': 3
        }
        mock.determine_segment.return_value = 'premium'
        mock.calculate_lifetime_value.return_value = (50000, 2)
        mock.calculate_average_project_value.return_value = 25000
        yield mock


@pytest.fixture
def auth_headers():
    """Provide valid auth headers."""
    return {
        'Authorization': 'Bearer test_token',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def sample_customer():
    """Sample customer data."""
    return {
        'id': str(uuid4()),
        'first_name': 'Jane',
        'last_name': 'Smith',
        'email': 'jane.smith@example.com',
        'phone': '2485556789',
        'street_address': '456 Oak Ave',
        'city': 'Troy',
        'state': 'MI',
        'zip_code': '48084',
        'property_value': 650000.00,
        'lifetime_value': 45000.00,
        'projects_count': 2,
        'last_interaction': datetime.utcnow().isoformat(),
        'customer_since': '2024-06-15T00:00:00Z',
        'referral_source': 'existing_customer',
        'nps_score': 9,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }


class TestCustomerList:
    """Test customer list endpoint."""

    def test_list_customers_success(self, client, mock_supabase, mock_customer_service, auth_headers):
        """Test successful listing of customers."""
        # Mock data
        customers = [
            {'id': str(uuid4()), 'first_name': 'John', 'last_name': 'Doe'},
            {'id': str(uuid4()), 'first_name': 'Jane', 'last_name': 'Smith'}
        ]

        # Setup mock return values
        mock_supabase.from_.return_value.select.return_value.order.return_value.range.return_value.execute.return_value.data = customers
        mock_supabase.from_.return_value.select.return_value.execute.return_value.count = 2

        response = client.get('/api/customers/', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert len(data['data']) == 2
        assert 'pagination' in data

    def test_list_customers_with_filters(self, client, mock_supabase, auth_headers):
        """Test listing customers with filters."""
        mock_supabase.from_().select.return_value.eq.return_value.execute.return_value.data = []

        response = client.get(
            '/api/customers/?city=Birmingham&min_lifetime_value=50000',
            headers=auth_headers
        )

        assert response.status_code == 200
        mock_supabase.from_().select.return_value.eq.assert_called()

    def test_list_customers_pagination(self, client, mock_supabase, auth_headers):
        """Test customer list pagination."""
        customers = [{'id': str(uuid4())} for _ in range(25)]
        mock_supabase.from_().select.return_value.range.return_value.execute.return_value.data = customers

        response = client.get('/api/customers/?page=2&per_page=25', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['pagination']['page'] == 2
        assert data['pagination']['per_page'] == 25


class TestGetCustomer:
    """Test get customer by ID endpoint."""

    def test_get_customer_success(self, client, mock_supabase, auth_headers, sample_customer):
        """Test successful retrieval of customer."""
        mock_supabase.from_().select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_customer

        response = client.get(f'/api/customers/{sample_customer["id"]}', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['id'] == sample_customer['id']
        assert data['data']['email'] == 'jane.smith@example.com'

    def test_get_customer_not_found(self, client, mock_supabase, auth_headers):
        """Test customer not found."""
        mock_supabase.from_().select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

        customer_id = str(uuid4())
        response = client.get(f'/api/customers/{customer_id}', headers=auth_headers)

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

    def test_get_customer_with_history(self, client, mock_supabase, auth_headers, sample_customer):
        """Test getting customer with interaction history."""
        # Mock customer data
        mock_supabase.from_().select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_customer

        # Mock interactions
        interactions = [
            {'type': 'email', 'date': '2024-01-15', 'notes': 'Follow-up'},
            {'type': 'call', 'date': '2024-01-10', 'notes': 'Initial contact'}
        ]
        mock_supabase.from_().select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = interactions

        response = client.get(
            f'/api/customers/{sample_customer["id"]}?include_history=true',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'interaction_history' in data


class TestCreateCustomer:
    """Test create customer endpoint."""

    def test_create_customer_success(self, client, mock_supabase, auth_headers, mock_pusher):
        """Test successful customer creation."""
        new_customer = {
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'email': 'alice@example.com',
            'phone': '2485557890',
            'street_address': '789 Pine St',
            'city': 'Birmingham',
            'state': 'MI',
            'zip_code': '48009',
            'property_value': 750000
        }

        created_customer = {**new_customer, 'id': str(uuid4())}
        mock_supabase.from_().insert.return_value.execute.return_value.data = [created_customer]

        response = client.post(
            '/api/customers/',
            headers=auth_headers,
            data=json.dumps(new_customer)
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['data']['email'] == 'alice@example.com'
        mock_pusher.trigger.assert_called_once()

    def test_create_customer_from_lead(self, client, mock_supabase, auth_headers):
        """Test creating customer from lead conversion."""
        lead_data = {
            'lead_id': str(uuid4()),
            'first_name': 'Bob',
            'last_name': 'Wilson',
            'email': 'bob@example.com',
            'phone': '2485558901'
        }

        created_customer = {**lead_data, 'id': str(uuid4())}
        mock_supabase.from_().insert.return_value.execute.return_value.data = [created_customer]

        response = client.post(
            '/api/customers/',
            headers=auth_headers,
            data=json.dumps(lead_data)
        )

        assert response.status_code == 201

    def test_create_customer_duplicate_email(self, client, mock_supabase, auth_headers):
        """Test creating customer with duplicate email."""
        mock_supabase.from_().select.return_value.eq.return_value.execute.return_value.data = [
            {'id': 'existing_id', 'email': 'existing@example.com'}
        ]

        new_customer = {
            'first_name': 'Duplicate',
            'last_name': 'User',
            'email': 'existing@example.com',
            'phone': '2485559999'
        }

        response = client.post(
            '/api/customers/',
            headers=auth_headers,
            data=json.dumps(new_customer)
        )

        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'already exists' in data['error'].lower()

    def test_create_customer_invalid_data(self, client, auth_headers):
        """Test creating customer with invalid data."""
        invalid_customer = {
            'first_name': 'NoEmail',
            'phone': 'invalid_phone'
        }

        response = client.post(
            '/api/customers/',
            headers=auth_headers,
            data=json.dumps(invalid_customer)
        )

        assert response.status_code == 400


class TestUpdateCustomer:
    """Test update customer endpoint."""

    def test_update_customer_success(self, client, mock_supabase, auth_headers, mock_pusher):
        """Test successful customer update."""
        customer_id = str(uuid4())
        updates = {
            'phone': '2485551111',
            'nps_score': 10
        }

        updated_customer = {
            'id': customer_id,
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '2485551111',
            'nps_score': 10
        }

        mock_supabase.from_().update.return_value.eq.return_value.execute.return_value.data = [updated_customer]

        response = client.put(
            f'/api/customers/{customer_id}',
            headers=auth_headers,
            data=json.dumps(updates)
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['phone'] == '2485551111'
        mock_pusher.trigger.assert_called_once()

    def test_update_customer_not_found(self, client, mock_supabase, auth_headers):
        """Test updating non-existent customer."""
        customer_id = str(uuid4())
        mock_supabase.from_().update.return_value.eq.return_value.execute.return_value.data = []

        response = client.put(
            f'/api/customers/{customer_id}',
            headers=auth_headers,
            data=json.dumps({'phone': '2485551111'})
        )

        assert response.status_code == 404


class TestDeleteCustomer:
    """Test delete customer endpoint."""

    def test_delete_customer_success(self, client, mock_supabase, auth_headers):
        """Test successful customer deletion (soft delete)."""
        customer_id = str(uuid4())
        mock_supabase.from_().update.return_value.eq.return_value.execute.return_value.data = [
            {'id': customer_id, 'deleted': True}
        ]

        response = client.delete(f'/api/customers/{customer_id}', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'deleted successfully' in data['message']

    def test_delete_customer_not_found(self, client, mock_supabase, auth_headers):
        """Test deleting non-existent customer."""
        customer_id = str(uuid4())
        mock_supabase.from_().update.return_value.eq.return_value.execute.return_value.data = []

        response = client.delete(f'/api/customers/{customer_id}', headers=auth_headers)

        assert response.status_code == 404


class TestCustomerProjects:
    """Test customer projects endpoint."""

    def test_get_customer_projects(self, client, mock_supabase, auth_headers):
        """Test getting customer's projects."""
        customer_id = str(uuid4())
        projects = [
            {'id': str(uuid4()), 'project_type': 'roof_replacement', 'status': 'completed'},
            {'id': str(uuid4()), 'project_type': 'repair', 'status': 'in_progress'}
        ]

        mock_supabase.from_().select.return_value.eq.return_value.execute.return_value.data = projects

        response = client.get(f'/api/customers/{customer_id}/projects', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) == 2
        assert data['count'] == 2


class TestCustomerInteractions:
    """Test customer interactions endpoint."""

    def test_get_customer_interactions(self, client, mock_supabase, auth_headers):
        """Test getting customer's interactions."""
        customer_id = str(uuid4())
        interactions = [
            {
                'id': str(uuid4()),
                'type': 'phone_call',
                'date': '2024-01-20',
                'notes': 'Discussed project timeline'
            },
            {
                'id': str(uuid4()),
                'type': 'email',
                'date': '2024-01-18',
                'notes': 'Sent quote'
            }
        ]

        mock_supabase.from_().select.return_value.eq.return_value.order.return_value.execute.return_value.data = interactions

        response = client.get(f'/api/customers/{customer_id}/interactions', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) == 2

    def test_create_customer_interaction(self, client, mock_supabase, auth_headers, mock_pusher):
        """Test creating new interaction for customer."""
        customer_id = str(uuid4())
        interaction = {
            'type': 'email',
            'notes': 'Follow-up on quote',
            'outcome': 'positive'
        }

        created_interaction = {
            **interaction,
            'id': str(uuid4()),
            'customer_id': customer_id,
            'date': datetime.utcnow().isoformat()
        }

        mock_supabase.from_().insert.return_value.execute.return_value.data = [created_interaction]

        response = client.post(
            f'/api/customers/{customer_id}/interactions',
            headers=auth_headers,
            data=json.dumps(interaction)
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['data']['type'] == 'email'
        mock_pusher.trigger.assert_called_once()


class TestCustomerLifetimeValue:
    """Test customer lifetime value calculation."""

    def test_calculate_lifetime_value(self, client, mock_supabase, auth_headers):
        """Test calculating customer's lifetime value."""
        customer_id = str(uuid4())

        # Mock projects data
        projects = [
            {'total_amount': 25000, 'status': 'completed'},
            {'total_amount': 15000, 'status': 'completed'},
            {'total_amount': 5000, 'status': 'in_progress'}
        ]
        mock_supabase.from_().select.return_value.eq.return_value.execute.return_value.data = projects

        # Mock update
        mock_supabase.from_().update.return_value.eq.return_value.execute.return_value.data = [
            {'id': customer_id, 'lifetime_value': 45000}
        ]

        response = client.post(
            f'/api/customers/{customer_id}/calculate-ltv',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['lifetime_value'] == 45000
        assert data['projects_count'] == 3


class TestCustomerStats:
    """Test customer statistics endpoint."""

    def test_get_customer_stats(self, client, mock_supabase, auth_headers):
        """Test getting customer statistics."""
        # Mock various aggregations
        mock_supabase.from_().select.return_value.execute.return_value.data = [
            {'count': 500}
        ]

        response = client.get('/api/customers/stats', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_customers' in data
        assert 'avg_lifetime_value' in data
        assert 'total_revenue' in data
        assert 'by_location' in data
        assert 'by_source' in data


class TestBulkOperations:
    """Test bulk customer operations."""

    def test_bulk_update_customers(self, client, mock_supabase, auth_headers):
        """Test bulk updating customers."""
        updates = {
            'customer_ids': [str(uuid4()) for _ in range(3)],
            'updates': {
                'campaign': 'spring_2024',
                'segment': 'premium'
            }
        }

        mock_supabase.from_().update.return_value.in_.return_value.execute.return_value.data = [
            {'id': cid} for cid in updates['customer_ids']
        ]

        response = client.post(
            '/api/customers/bulk-update',
            headers=auth_headers,
            data=json.dumps(updates)
        )

        assert response.status_code == 207
        data = json.loads(response.data)
        assert data['updated'] == 3

    def test_export_customers(self, client, mock_supabase, auth_headers):
        """Test exporting customers to CSV."""
        customers = [
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'phone': '2485551234'
            },
            {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'jane@example.com',
                'phone': '2485555678'
            }
        ]

        mock_supabase.from_().select.return_value.execute.return_value.data = customers

        response = client.get(
            '/api/customers/export?format=csv',
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.content_type == 'text/csv'
        assert b'first_name,last_name,email,phone' in response.data


class TestErrorHandling:
    """Test error handling."""

    def test_unauthorized_access(self, client):
        """Test accessing endpoints without auth."""
        response = client.get('/api/customers/')
        assert response.status_code == 401

    def test_invalid_uuid(self, client, auth_headers):
        """Test invalid UUID format."""
        response = client.get('/api/customers/invalid-uuid', headers=auth_headers)
        assert response.status_code == 400

    def test_database_error(self, client, mock_supabase, auth_headers):
        """Test database error handling."""
        mock_supabase.from_().select.side_effect = Exception("Database connection error")

        response = client.get('/api/customers/', headers=auth_headers)

        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data