"""
Integration Tests for Advanced Analytics Flask Routes

Tests for Flask API endpoints with actual HTTP requests.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from app import create_app


class TestAdvancedAnalyticsRoutes:
    """Test suite for advanced analytics Flask routes."""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        app = create_app('testing')
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        with patch('app.routes.advanced_analytics_flask.get_db') as mock:
            db_mock = Mock()
            mock.return_value = iter([db_mock])
            yield db_mock

    def test_revenue_forecast_endpoint(self, client, mock_db_session):
        """Test GET /api/advanced-analytics/revenue/forecast."""
        # Mock the analytics method
        with patch('app.routes.advanced_analytics_flask.AdvancedAnalytics') as MockAnalytics:
            mock_analytics = MockAnalytics.return_value
            mock_analytics.get_revenue_forecast.return_value = {
                'forecast': [
                    {
                        'date': '2025-10-12',
                        'predicted_revenue': 15000,
                        'lower_bound': 12000,
                        'upper_bound': 18000
                    }
                ],
                'summary': {
                    'forecast_period_days': 30,
                    'total_forecast_revenue': 450000,
                    'average_daily_revenue': 15000
                }
            }

            response = client.get('/api/advanced-analytics/revenue/forecast?days_ahead=30&confidence_level=0.95')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'forecast' in data
            assert 'summary' in data
            assert len(data['forecast']) > 0

    def test_revenue_forecast_default_params(self, client, mock_db_session):
        """Test revenue forecast with default parameters."""
        with patch('app.routes.advanced_analytics_flask.AdvancedAnalytics') as MockAnalytics:
            mock_analytics = MockAnalytics.return_value
            mock_analytics.get_revenue_forecast.return_value = {
                'forecast': [],
                'summary': {}
            }

            response = client.get('/api/advanced-analytics/revenue/forecast')

            assert response.status_code == 200

    def test_lead_quality_heatmap_endpoint(self, client, mock_db_session):
        """Test GET /api/advanced-analytics/leads/quality-heatmap."""
        with patch('app.routes.advanced_analytics_flask.AdvancedAnalytics') as MockAnalytics:
            mock_analytics = MockAnalytics.return_value
            mock_analytics.get_lead_quality_heatmap.return_value = {
                'heatmap': [
                    {
                        'segment': 'google_ads',
                        'excellent': 10,
                        'good': 20,
                        'fair': 15,
                        'poor': 5
                    }
                ],
                'summary': {
                    'segment_by': 'source',
                    'total_leads': 50
                }
            }

            response = client.get('/api/advanced-analytics/leads/quality-heatmap?segment_by=source')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'heatmap' in data
            assert 'summary' in data

    def test_conversion_funnel_endpoint(self, client, mock_db_session):
        """Test GET /api/advanced-analytics/conversion/funnel."""
        with patch('app.routes.advanced_analytics_flask.AdvancedAnalytics') as MockAnalytics:
            mock_analytics = MockAnalytics.return_value
            mock_analytics.get_conversion_funnel.return_value = {
                'funnel': [
                    {'stage': 'new', 'count': 100, 'conversion_rate': 100},
                    {'stage': 'contacted', 'count': 80, 'conversion_rate': 80},
                    {'stage': 'qualified', 'count': 60, 'conversion_rate': 60},
                    {'stage': 'proposal_sent', 'count': 40, 'conversion_rate': 40},
                    {'stage': 'negotiation', 'count': 30, 'conversion_rate': 30},
                    {'stage': 'won', 'count': 20, 'conversion_rate': 20}
                ],
                'summary': {
                    'total_leads': 100,
                    'won_leads': 20,
                    'overall_conversion_rate': 20
                }
            }

            response = client.get('/api/advanced-analytics/conversion/funnel')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'funnel' in data
            assert len(data['funnel']) == 6

    def test_clv_distribution_endpoint(self, client, mock_db_session):
        """Test GET /api/advanced-analytics/customers/clv-distribution."""
        with patch('app.routes.advanced_analytics_flask.AdvancedAnalytics') as MockAnalytics:
            mock_analytics = MockAnalytics.return_value
            mock_analytics.get_clv_distribution.return_value = {
                'distribution': [
                    {'bucket': '<$10K', 'count': 50, 'total_value': 300000},
                    {'bucket': '$10K-$25K', 'count': 30, 'total_value': 450000},
                    {'bucket': '$25K-$50K', 'count': 15, 'total_value': 525000},
                    {'bucket': '>$50K', 'count': 5, 'total_value': 350000}
                ],
                'summary': {
                    'total_customers': 100,
                    'avg_clv': 16250
                }
            }

            response = client.get('/api/advanced-analytics/customers/clv-distribution')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'distribution' in data
            assert 'summary' in data

    def test_churn_risk_endpoint(self, client, mock_db_session):
        """Test GET /api/advanced-analytics/customers/churn-risk."""
        with patch('app.routes.advanced_analytics_flask.AdvancedAnalytics') as MockAnalytics:
            mock_analytics = MockAnalytics.return_value
            mock_analytics.get_churn_risk_analysis.return_value = {
                'churn_analysis': [
                    {
                        'customer_id': 1,
                        'customer_name': 'John Doe',
                        'last_project_date': '2024-01-01',
                        'days_since_last_project': 300,
                        'churn_risk': 'high',
                        'risk_score': 0.8
                    }
                ],
                'summary': {
                    'total_customers': 100,
                    'high_risk': 20,
                    'medium_risk': 30,
                    'low_risk': 50
                }
            }

            response = client.get('/api/advanced-analytics/customers/churn-risk')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'churn_analysis' in data
            assert 'summary' in data

    def test_marketing_attribution_endpoint(self, client, mock_db_session):
        """Test GET /api/advanced-analytics/marketing/attribution."""
        with patch('app.routes.advanced_analytics_flask.AdvancedAnalytics') as MockAnalytics:
            mock_analytics = MockAnalytics.return_value
            mock_analytics.get_marketing_attribution.return_value = {
                'attribution': [
                    {
                        'source': 'google_ads',
                        'total_leads': 100,
                        'won_leads': 20,
                        'conversion_rate': 20,
                        'total_revenue': 500000,
                        'avg_project_value': 25000
                    }
                ],
                'summary': {
                    'total_leads': 200,
                    'total_channels': 5,
                    'best_channel': 'google_ads'
                }
            }

            response = client.get('/api/advanced-analytics/marketing/attribution')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'attribution' in data
            assert 'summary' in data


class TestMLRevenueRoutes:
    """Test suite for ML revenue forecasting routes."""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        app = create_app('testing')
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        with patch('app.routes.advanced_analytics_flask.get_db') as mock:
            db_mock = Mock()
            mock.return_value = iter([db_mock])
            yield db_mock

    def test_train_revenue_model_endpoint(self, client, mock_db_session):
        """Test POST /api/advanced-analytics/ml/revenue/train."""
        with patch('app.routes.advanced_analytics_flask.RevenueForecastingModel') as MockModel:
            mock_model = MockModel.return_value
            mock_model.train_model.return_value = {
                'status': 'trained',
                'model_type': 'prophet',
                'training_days': 180,
                'metrics': {
                    'mae': 2000,
                    'r_squared': 0.85
                },
                'training_period': {
                    'start_date': '2024-04-01',
                    'end_date': '2024-10-01'
                }
            }

            payload = {
                'historical_days': 180,
                'model_type': 'prophet'
            }

            response = client.post(
                '/api/advanced-analytics/ml/revenue/train',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'trained'
            assert data['model_type'] == 'prophet'

    def test_train_revenue_model_default_params(self, client, mock_db_session):
        """Test training with default parameters."""
        with patch('app.routes.advanced_analytics_flask.RevenueForecastingModel') as MockModel:
            mock_model = MockModel.return_value
            mock_model.train_model.return_value = {
                'status': 'trained',
                'model_type': 'auto',
                'training_days': 180
            }

            response = client.post(
                '/api/advanced-analytics/ml/revenue/train',
                data=json.dumps({}),
                content_type='application/json'
            )

            assert response.status_code == 200

    def test_predict_revenue_endpoint(self, client, mock_db_session):
        """Test GET /api/advanced-analytics/ml/revenue/predict."""
        with patch('app.routes.advanced_analytics_flask.RevenueForecastingModel') as MockModel:
            mock_model = MockModel.return_value
            mock_model.predict_revenue.return_value = {
                'forecast': [
                    {
                        'date': '2025-10-12',
                        'predicted_revenue': 15000,
                        'lower_bound': 12000,
                        'upper_bound': 18000
                    }
                ],
                'summary': {
                    'total_forecast_revenue': 450000,
                    'average_daily_revenue': 15000,
                    'forecast_period_days': 30
                }
            }

            response = client.get('/api/advanced-analytics/ml/revenue/predict?days_ahead=30')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'forecast' in data
            assert 'summary' in data

    def test_forecast_accuracy_endpoint(self, client, mock_db_session):
        """Test GET /api/advanced-analytics/ml/revenue/accuracy."""
        with patch('app.routes.advanced_analytics_flask.RevenueForecastingModel') as MockModel:
            mock_model = MockModel.return_value
            mock_model.get_forecast_accuracy.return_value = {
                'accuracy_metrics': {
                    'mae': 2000,
                    'mape': 8.5,
                    'rmse': 2500,
                    'r_squared': 0.85
                },
                'test_period_days': 30,
                'model_type': 'prophet'
            }

            response = client.get('/api/advanced-analytics/ml/revenue/accuracy')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'accuracy_metrics' in data
            assert data['accuracy_metrics']['mae'] == 2000


class TestABTestingRoutes:
    """Test suite for A/B testing routes."""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        app = create_app('testing')
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    def test_create_experiment_endpoint(self, client):
        """Test POST /api/advanced-analytics/ab-testing/experiments."""
        with patch('app.routes.advanced_analytics_flask.ABTestingFramework') as MockFramework:
            mock_framework = MockFramework.return_value
            mock_framework.create_experiment.return_value = {
                'experiment_id': 'exp_123',
                'status': 'created',
                'name': 'Test Campaign',
                'variants': [
                    {'id': 'control', 'name': 'Control'},
                    {'id': 'variant_a', 'name': 'Variant A'}
                ]
            }

            payload = {
                'name': 'Test Campaign',
                'hypothesis': 'New design increases conversions',
                'variants': [
                    {'id': 'control', 'name': 'Control', 'traffic_percentage': 50},
                    {'id': 'variant_a', 'name': 'Variant A', 'traffic_percentage': 50}
                ],
                'start_date': '2025-10-12T00:00:00',
                'end_date': '2025-11-12T00:00:00',
                'primary_metric': 'conversion_rate',
                'sample_size_per_variant': 1000
            }

            response = client.post(
                '/api/advanced-analytics/ab-testing/experiments',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert 'experiment_id' in data
            assert data['status'] == 'created'

    def test_assign_variant_endpoint(self, client):
        """Test GET /api/advanced-analytics/ab-testing/experiments/{id}/assign/{user_id}."""
        with patch('app.routes.advanced_analytics_flask.ABTestingFramework') as MockFramework:
            mock_framework = MockFramework.return_value
            mock_framework.assign_variant.return_value = {
                'experiment_id': 'exp_123',
                'user_id': 'user_456',
                'variant_id': 'variant_a',
                'assigned_at': '2025-10-12T10:00:00'
            }

            response = client.get('/api/advanced-analytics/ab-testing/experiments/exp_123/assign/user_456')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['variant_id'] == 'variant_a'

    def test_record_result_endpoint(self, client):
        """Test POST /api/advanced-analytics/ab-testing/experiments/{id}/results."""
        with patch('app.routes.advanced_analytics_flask.ABTestingFramework') as MockFramework:
            mock_framework = MockFramework.return_value
            mock_framework.record_result.return_value = {
                'status': 'recorded',
                'experiment_id': 'exp_123'
            }

            payload = {
                'user_id': 'user_456',
                'variant_id': 'variant_a',
                'converted': True,
                'value': 100.0
            }

            response = client.post(
                '/api/advanced-analytics/ab-testing/experiments/exp_123/results',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'recorded'

    def test_analyze_experiment_endpoint(self, client):
        """Test GET /api/advanced-analytics/ab-testing/experiments/{id}/analyze."""
        with patch('app.routes.advanced_analytics_flask.ABTestingFramework') as MockFramework:
            mock_framework = MockFramework.return_value
            mock_framework.analyze_experiment.return_value = {
                'variants': [
                    {
                        'variant_id': 'control',
                        'total_users': 1000,
                        'conversions': 200,
                        'conversion_rate': 0.20,
                        'p_value': 0.05,
                        'statistically_significant': True
                    }
                ],
                'summary': {
                    'winner': 'variant_a',
                    'confidence_level': 0.95
                }
            }

            response = client.get('/api/advanced-analytics/ab-testing/experiments/exp_123/analyze')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'variants' in data
            assert 'summary' in data

    def test_get_experiment_summary_endpoint(self, client):
        """Test GET /api/advanced-analytics/ab-testing/experiments/{id}/summary."""
        with patch('app.routes.advanced_analytics_flask.ABTestingFramework') as MockFramework:
            mock_framework = MockFramework.return_value
            mock_framework.get_experiment_summary.return_value = {
                'experiment_id': 'exp_123',
                'name': 'Test Campaign',
                'status': 'running',
                'variants': ['control', 'variant_a']
            }

            response = client.get('/api/advanced-analytics/ab-testing/experiments/exp_123/summary')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['experiment_id'] == 'exp_123'

    def test_select_winner_endpoint(self, client):
        """Test POST /api/advanced-analytics/ab-testing/experiments/{id}/select-winner."""
        with patch('app.routes.advanced_analytics_flask.ABTestingFramework') as MockFramework:
            mock_framework = MockFramework.return_value
            mock_framework.select_winner.return_value = {
                'status': 'completed',
                'winner': {
                    'variant_id': 'variant_a',
                    'conversion_rate': 0.25,
                    'lift': 25.0
                }
            }

            response = client.post('/api/advanced-analytics/ab-testing/experiments/exp_123/select-winner')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'completed'
            assert 'winner' in data


class TestErrorHandling:
    """Test error handling in routes."""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        app = create_app('testing')
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    def test_revenue_forecast_error_handling(self, client):
        """Test error handling in revenue forecast endpoint."""
        with patch('app.routes.advanced_analytics_flask.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")

            response = client.get('/api/advanced-analytics/revenue/forecast')

            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

    def test_invalid_json_payload(self, client):
        """Test handling of invalid JSON payload."""
        response = client.post(
            '/api/advanced-analytics/ml/revenue/train',
            data='invalid json',
            content_type='application/json'
        )

        # Should return 400 or 500 depending on error handling
        assert response.status_code in [400, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
