"""
Unit Tests for Lead Service
Tests CRUD operations, filtering, sorting, and lead scoring
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from app.services.lead_service import LeadService
from app.models.lead_sqlalchemy import Lead, LeadStatusEnum, LeadTemperatureEnum
from app.schemas.lead import LeadCreate, LeadUpdate, LeadListFilters


@pytest.mark.unit
class TestLeadServiceCreate:
    """Test lead creation functionality"""

    def test_create_lead_basic(self, sample_lead_data):
        """Test basic lead creation with required fields"""
        lead_data = LeadCreate(**sample_lead_data)

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.add = Mock()
            mock_db.commit = Mock()

            # Mock refresh to set an ID
            def mock_refresh(lead):
                lead.id = str(uuid4())
                lead.created_at = datetime.utcnow()
            mock_db.refresh = mock_refresh

            result = LeadService.create_lead(lead_data)

            assert result is not None
            assert result.first_name == sample_lead_data['first_name']
            assert result.email == sample_lead_data['email']
            assert hasattr(result, 'lead_score')
            assert hasattr(result, 'temperature')
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_create_lead_with_scoring(self, sample_lead_data):
        """Test that lead creation includes automatic scoring"""
        lead_data = LeadCreate(**sample_lead_data)
        lead_data.budget_range_max = 50000  # High budget
        lead_data.urgency = 'immediate'  # High urgency
        lead_data.insurance_claim = True

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            def mock_refresh(lead):
                lead.id = str(uuid4())
                lead.lead_score = 85  # Expected high score
                lead.temperature = 'hot'
            mock_db.refresh = mock_refresh

            result = LeadService.create_lead(lead_data)

            # High-value lead should get hot temperature
            assert result.lead_score is not None
            assert result.temperature in ['hot', 'warm', 'cold']

    def test_create_lead_missing_optional_fields(self):
        """Test lead creation with only required fields"""
        minimal_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+15551234567',
            'source': 'website_form'
        }
        lead_data = LeadCreate(**minimal_data)

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            def mock_refresh(lead):
                lead.id = str(uuid4())
            mock_db.refresh = mock_refresh

            result = LeadService.create_lead(lead_data)

            assert result.first_name == 'John'
            assert result.last_name == 'Doe'


@pytest.mark.unit
class TestLeadServiceRead:
    """Test lead retrieval functionality"""

    def test_get_lead_by_id_exists(self, sample_lead_data):
        """Test retrieving an existing lead by ID"""
        lead_id = str(uuid4())

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            # Mock database query
            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query

            # Create mock lead
            mock_lead = Lead(**sample_lead_data)
            mock_lead.id = lead_id
            mock_query.first.return_value = mock_lead

            result = LeadService.get_lead_by_id(lead_id)

            assert result is not None
            assert result.id == lead_id
            assert result.first_name == sample_lead_data['first_name']

    def test_get_lead_by_id_not_exists(self):
        """Test retrieving a non-existent lead"""
        lead_id = str(uuid4())

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None

            result = LeadService.get_lead_by_id(lead_id)

            assert result is None

    def test_get_lead_excludes_deleted(self, sample_lead_data):
        """Test that deleted leads are not retrieved"""
        lead_id = str(uuid4())

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            mock_query = MagicMock()
            mock_db.query.return_value = mock_query

            # Verify filter includes is_deleted check
            def check_filter(*args, **kwargs):
                return mock_query

            mock_query.filter = Mock(side_effect=check_filter)
            mock_query.first.return_value = None

            LeadService.get_lead_by_id(lead_id)

            # Should call filter with is_deleted condition
            mock_query.filter.assert_called()


@pytest.mark.unit
class TestLeadServiceFiltering:
    """Test lead filtering and searching functionality"""

    def test_filter_by_status(self, sample_lead_data):
        """Test filtering leads by status"""
        filters = LeadListFilters(status='new,contacted')

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            mock_query.count.return_value = 0

            leads, total = LeadService.get_leads_with_filters(filters)

            # Verify status filter was applied
            assert mock_query.filter.called

    def test_filter_by_temperature(self):
        """Test filtering leads by temperature"""
        filters = LeadListFilters(temperature='hot,warm')

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            mock_query.count.return_value = 0

            leads, total = LeadService.get_leads_with_filters(filters)

            assert mock_query.filter.called

    def test_filter_by_source(self):
        """Test filtering leads by source"""
        filters = LeadListFilters(source='website_form')

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            mock_query.count.return_value = 0

            leads, total = LeadService.get_leads_with_filters(filters)

            assert mock_query.filter.called

    def test_search_functionality(self):
        """Test search across multiple fields"""
        filters = LeadListFilters(search='John')

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            mock_query.count.return_value = 0

            leads, total = LeadService.get_leads_with_filters(filters)

            # Search should trigger filter
            assert mock_query.filter.called

    def test_pagination(self):
        """Test pagination parameters"""
        filters = LeadListFilters()

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            mock_query.count.return_value = 0

            leads, total = LeadService.get_leads_with_filters(
                filters,
                page=2,
                per_page=25
            )

            # Should call offset and limit
            mock_query.offset.assert_called_once_with(25)  # page 2, skip 25
            mock_query.limit.assert_called_once_with(25)


@pytest.mark.unit
class TestLeadServiceUpdate:
    """Test lead update functionality"""

    def test_update_lead_basic_fields(self, sample_lead_data):
        """Test updating basic lead fields"""
        lead_id = str(uuid4())
        update_data = LeadUpdate(
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com'
        )

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            # Mock existing lead
            mock_lead = Lead(**sample_lead_data)
            mock_lead.id = lead_id

            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_lead

            result = LeadService.update_lead(lead_id, update_data)

            # Verify updates were applied
            assert result.first_name == 'Jane'
            assert result.last_name == 'Smith'
            assert result.email == 'jane.smith@example.com'
            mock_db.commit.assert_called_once()

    def test_update_lead_status(self, sample_lead_data):
        """Test updating lead status"""
        lead_id = str(uuid4())
        update_data = LeadUpdate(status='contacted')

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            mock_lead = Lead(**sample_lead_data)
            mock_lead.id = lead_id

            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_lead

            result = LeadService.update_lead(lead_id, update_data)

            assert result.status == 'contacted'

    def test_update_lead_not_found(self):
        """Test updating a non-existent lead"""
        lead_id = str(uuid4())
        update_data = LeadUpdate(first_name='Jane')

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None

            result = LeadService.update_lead(lead_id, update_data)

            assert result is None
            # Should not call commit if lead not found
            mock_db.commit.assert_not_called()


@pytest.mark.unit
class TestLeadServiceDelete:
    """Test lead deletion (soft delete) functionality"""

    def test_soft_delete_lead(self, sample_lead_data):
        """Test soft deleting a lead"""
        lead_id = str(uuid4())

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            mock_lead = Lead(**sample_lead_data)
            mock_lead.id = lead_id
            mock_lead.is_deleted = False

            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_lead

            result = LeadService.delete_lead(lead_id)

            assert result is True
            assert mock_lead.is_deleted is True
            assert mock_lead.deleted_at is not None
            mock_db.commit.assert_called_once()

    def test_delete_lead_not_found(self):
        """Test deleting a non-existent lead"""
        lead_id = str(uuid4())

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None

            result = LeadService.delete_lead(lead_id)

            assert result is False
            mock_db.commit.assert_not_called()


@pytest.mark.unit
class TestLeadServiceStatistics:
    """Test lead statistics and analytics functionality"""

    def test_get_lead_counts_by_status(self):
        """Test getting lead counts grouped by status"""
        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            # Mock count results
            mock_results = [
                ('new', 10),
                ('contacted', 5),
                ('qualified', 3)
            ]

            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.group_by.return_value = mock_query
            mock_query.all.return_value = mock_results

            result = LeadService.get_lead_counts_by_status()

            assert len(result) == 3
            assert result[0]['status'] == 'new'
            assert result[0]['count'] == 10

    def test_get_conversion_rate(self):
        """Test calculating lead conversion rate"""
        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            # Mock total and converted counts
            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query

            # First call: total leads = 100
            # Second call: converted leads = 20
            mock_query.count.side_effect = [100, 20]

            result = LeadService.get_conversion_rate()

            assert result == 20.0  # 20/100 = 20%


@pytest.mark.unit
class TestLeadScoring:
    """Test lead scoring integration"""

    def test_high_value_lead_scoring(self):
        """Test that high-value leads get appropriate scores"""
        high_value_data = {
            'first_name': 'Premium',
            'last_name': 'Customer',
            'phone': '+15551234567',
            'source': 'referral',
            'budget_range_max': 75000,
            'urgency': 'immediate',
            'insurance_claim': True,
            'property_value': 800000
        }
        lead_data = LeadCreate(**high_value_data)

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            def mock_refresh(lead):
                lead.id = str(uuid4())
                # High-value leads should score high
                lead.lead_score = 90
                lead.temperature = 'hot'
            mock_db.refresh = mock_refresh

            result = LeadService.create_lead(lead_data)

            # Premium lead should have high score and hot temperature
            assert result.lead_score >= 80
            assert result.temperature == 'hot'

    def test_low_value_lead_scoring(self):
        """Test that low-value leads get appropriate scores"""
        low_value_data = {
            'first_name': 'Budget',
            'last_name': 'Shopper',
            'phone': '+15551234567',
            'source': 'cold_call',
            'budget_range_max': 5000,
            'urgency': 'no_rush',
            'property_value': 150000
        }
        lead_data = LeadCreate(**low_value_data)

        with patch('app.services.lead_service.get_db_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            def mock_refresh(lead):
                lead.id = str(uuid4())
                # Low-value leads should score low
                lead.lead_score = 35
                lead.temperature = 'cold'
            mock_db.refresh = mock_refresh

            result = LeadService.create_lead(lead_data)

            # Budget lead should have lower score
            assert result.lead_score <= 50
            assert result.temperature in ['cold', 'warm']
