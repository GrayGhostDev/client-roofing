"""
Unit Tests for Advanced Analytics Module

Tests for revenue forecasting, lead quality analysis, and business intelligence.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np

from app.ml.advanced_analytics import AdvancedAnalytics


class TestAdvancedAnalytics:
    """Test suite for AdvancedAnalytics class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock()
        db.query = Mock()
        db.close = Mock()
        return db

    @pytest.fixture
    def analytics(self, mock_db):
        """Create AdvancedAnalytics instance with mock DB."""
        return AdvancedAnalytics(mock_db)

    @pytest.mark.asyncio
    async def test_get_revenue_forecast_basic(self, analytics, mock_db):
        """Test basic revenue forecast generation."""
        # Mock query results
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            (datetime.now() - timedelta(days=i), 10000 + i * 100, 2)
            for i in range(90)
        ]
        mock_db.query.return_value = mock_query

        # Test forecast
        result = await analytics.get_revenue_forecast(days_ahead=30, confidence_level=0.95)

        # Assertions
        assert 'forecast' in result
        assert 'summary' in result
        assert 'metadata' in result
        assert len(result['forecast']) == 30
        assert result['summary']['forecast_period_days'] == 30

        # Check forecast structure
        forecast_item = result['forecast'][0]
        assert 'date' in forecast_item
        assert 'predicted_revenue' in forecast_item
        assert 'lower_bound' in forecast_item
        assert 'upper_bound' in forecast_item
        assert forecast_item['predicted_revenue'] >= 0

    @pytest.mark.asyncio
    async def test_get_lead_quality_heatmap(self, analytics, mock_db):
        """Test lead quality heatmap generation."""
        # Mock leads data
        mock_lead = Mock()
        mock_lead.id = 1
        mock_lead.source = 'google_ads'
        mock_lead.zip_code = '48304'
        mock_lead.estimated_property_value = 450000
        mock_lead.contact_quality = 8
        mock_lead.status = 'won'

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_lead] * 50

        mock_db.query.return_value = mock_query

        # Test heatmap
        result = await analytics.get_lead_quality_heatmap(segment_by='source')

        # Assertions
        assert 'heatmap' in result
        assert 'summary' in result
        assert result['summary']['segment_by'] == 'source'
        assert result['summary']['total_leads'] > 0

    @pytest.mark.asyncio
    async def test_get_conversion_funnel(self, analytics, mock_db):
        """Test conversion funnel analysis."""
        # Mock query chain properly
        mock_query = Mock()
        mock_query.filter.return_value = mock_query

        # Set up scalar to return values in sequence
        # For each stage after 'new': 2 calls (current + progressed)
        # Stage 1 (new): 1 call = 100
        # Stage 2 (contacted): current=20, progressed=60 (total 80)
        # Stage 3 (qualified): current=10, progressed=50 (total 60)
        # Stage 4 (proposal_sent): current=5, progressed=35 (total 40)
        # Stage 5 (negotiation): current=10, progressed=20 (total 30)
        # Stage 6 (won): current=20, progressed=0 (total 20)
        mock_query.scalar.side_effect = [
            100,  # new count
            20, 60,  # contacted: current + progressed
            10, 50,  # qualified: current + progressed
            5, 35,   # proposal_sent: current + progressed
            10, 20,  # negotiation: current + progressed
            20, 0,   # won: current + progressed
            0, 0, 0  # Extra safety values
        ]

        mock_db.query.return_value = mock_query

        # Test funnel
        result = await analytics.get_conversion_funnel()

        # Assertions
        assert 'funnel' in result
        assert 'summary' in result
        assert len(result['funnel']) == 6
        assert result['summary']['total_leads'] >= result['summary']['won_leads']

        # Check funnel stages
        for stage in result['funnel']:
            assert 'stage' in stage
            assert 'count' in stage
            assert 'conversion_rate' in stage

    @pytest.mark.asyncio
    async def test_get_clv_distribution(self, analytics, mock_db):
        """Test CLV distribution analysis."""
        # Mock customer data
        mock_customer = Mock()
        mock_customer.id = 1

        mock_query_customers = Mock()
        mock_query_customers.join.return_value = mock_query_customers
        mock_query_customers.filter.return_value = mock_query_customers
        mock_query_customers.all.return_value = [mock_customer] * 10

        # Mock project value queries
        mock_query_value = Mock()
        mock_query_value.filter.return_value = mock_query_value
        mock_query_value.scalar.return_value = 50000

        # Mock project count queries
        mock_query_count = Mock()
        mock_query_count.filter.return_value = mock_query_count
        mock_query_count.scalar.return_value = 2

        # Setup query return values
        mock_db.query.side_effect = [
            mock_query_customers,  # First call for customers
            *([mock_query_value, mock_query_count] * 10)  # Alternating for each customer
        ]

        # Test CLV
        result = await analytics.get_clv_distribution()

        # Assertions
        assert 'distribution' in result
        assert 'summary' in result
        assert len(result['distribution']) > 0
        assert result['summary']['total_customers'] >= 0

    @pytest.mark.asyncio
    async def test_get_churn_risk_analysis(self, analytics, mock_db):
        """Test churn risk analysis."""
        # Mock customer with projects
        mock_customer = Mock()
        mock_customer.id = 1
        mock_customer.first_name = 'John'
        mock_customer.last_name = 'Doe'

        mock_project = Mock()
        mock_project.created_at = datetime.now() - timedelta(days=365)

        mock_query_customers = Mock()
        mock_query_customers.join.return_value = mock_query_customers
        mock_query_customers.filter.return_value = mock_query_customers
        mock_query_customers.distinct.return_value = mock_query_customers
        mock_query_customers.all.return_value = [mock_customer]

        mock_query_projects = Mock()
        mock_query_projects.filter.return_value = mock_query_projects
        mock_query_projects.order_by.return_value = mock_query_projects
        mock_query_projects.all.return_value = [mock_project]

        mock_db.query.side_effect = [mock_query_customers, mock_query_projects]

        # Test churn risk
        result = await analytics.get_churn_risk_analysis()

        # Assertions
        assert 'churn_analysis' in result
        assert 'summary' in result
        assert result['summary']['total_customers'] >= 0

    @pytest.mark.asyncio
    async def test_get_marketing_attribution(self, analytics, mock_db):
        """Test marketing channel attribution."""
        # Mock lead data
        mock_lead = Mock()
        mock_lead.source = 'google_ads'
        mock_lead.status = 'won'
        mock_lead.estimated_property_value = 50000

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_lead] * 30

        mock_db.query.return_value = mock_query

        # Test attribution
        result = await analytics.get_marketing_attribution()

        # Assertions
        assert 'attribution' in result
        assert 'summary' in result
        assert result['summary']['total_leads'] > 0
        assert result['summary']['total_channels'] >= 0

    def test_categorize_property_value(self, analytics):
        """Test property value categorization."""
        assert analytics._categorize_property_value(600000) == 'premium_500k+'
        assert analytics._categorize_property_value(400000) == 'upper_350k-500k'
        assert analytics._categorize_property_value(300000) == 'mid_250k-350k'
        assert analytics._categorize_property_value(200000) == 'entry_150k-250k'
        assert analytics._categorize_property_value(100000) == 'basic_<150k'

    def test_get_quality_tier(self, analytics):
        """Test quality tier classification."""
        assert analytics._get_quality_tier(85) == 'excellent'
        assert analytics._get_quality_tier(70) == 'good'
        assert analytics._get_quality_tier(50) == 'fair'
        assert analytics._get_quality_tier(30) == 'poor'

    def test_get_churn_action(self, analytics):
        """Test churn action recommendations."""
        action_high = analytics._get_churn_action('high')
        action_medium = analytics._get_churn_action('medium')
        action_low = analytics._get_churn_action('low')

        assert 'immediate' in action_high.lower() or 'outreach' in action_high.lower()
        assert 'call' in action_medium.lower() or 'check-in' in action_medium.lower()
        assert 'monitor' in action_low.lower() or 'newsletter' in action_low.lower()


class TestAdvancedAnalyticsEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock()

    @pytest.fixture
    def analytics(self, mock_db):
        """Create AdvancedAnalytics instance."""
        return AdvancedAnalytics(mock_db)

    @pytest.mark.asyncio
    async def test_empty_revenue_data(self, analytics, mock_db):
        """Test forecast with no historical data."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query

        # Should handle empty data gracefully
        result = await analytics.get_revenue_forecast(days_ahead=30)

        # Even with no data, should return structure
        assert 'forecast' in result
        assert 'summary' in result

    @pytest.mark.asyncio
    async def test_single_lead_heatmap(self, analytics, mock_db):
        """Test heatmap with only one lead."""
        mock_lead = Mock()
        mock_lead.id = 1
        mock_lead.source = 'direct'
        mock_lead.zip_code = '48304'
        mock_lead.estimated_property_value = 300000
        mock_lead.contact_quality = 7
        mock_lead.status = 'new'

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_lead]

        mock_db.query.return_value = mock_query

        result = await analytics.get_lead_quality_heatmap()

        assert 'heatmap' in result
        assert result['summary']['total_leads'] == 1

    @pytest.mark.asyncio
    async def test_no_customers_clv(self, analytics, mock_db):
        """Test CLV distribution with no customers."""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query

        result = await analytics.get_clv_distribution()

        assert 'distribution' in result
        assert result['summary']['total_customers'] == 0
        assert result['summary']['avg_clv'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
