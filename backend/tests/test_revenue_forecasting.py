"""
Unit Tests for Revenue Forecasting Module

Tests for model training, prediction, and accuracy validation.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np

from app.ml.revenue_forecasting import RevenueForecastingModel


class TestRevenueForecastingModel:
    """Test suite for RevenueForecastingModel class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock()
        db.query = Mock()
        db.close = Mock()
        return db

    @pytest.fixture
    def forecasting_model(self, mock_db):
        """Create RevenueForecastingModel instance with mock DB."""
        return RevenueForecastingModel(mock_db)

    @pytest.fixture
    def sample_revenue_data(self):
        """Generate sample revenue data for testing."""
        dates = [datetime.now() - timedelta(days=i) for i in range(180)]
        revenues = [5000 + i * 50 + np.random.normal(0, 500) for i in range(180)]
        projects = [2 + np.random.randint(0, 3) for _ in range(180)]
        return list(zip(dates, revenues, projects))

    @pytest.mark.asyncio
    async def test_train_model_linear(self, forecasting_model, mock_db, sample_revenue_data):
        """Test training with linear regression model."""
        # Mock query results
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_revenue_data

        mock_db.query.return_value = mock_query

        # Train model
        result = await forecasting_model.train_model(historical_days=180, model_type='linear')

        # Assertions
        assert 'model_type' in result
        assert result['model_type'] == 'linear'
        assert 'training_days' in result
        assert result['training_days'] == 180
        assert 'metrics' in result
        assert 'training_period' in result
        assert result['status'] == 'trained'

        # Check metrics exist
        metrics = result['metrics']
        assert 'mae' in metrics
        assert 'r_squared' in metrics
        assert metrics['mae'] >= 0

    @pytest.mark.asyncio
    @patch('app.ml.revenue_forecasting.Prophet')
    async def test_train_model_prophet(self, mock_prophet, forecasting_model, mock_db, sample_revenue_data):
        """Test training with Prophet model."""
        # Mock Prophet
        mock_prophet_instance = Mock()
        mock_prophet_instance.fit.return_value = mock_prophet_instance
        mock_prophet.return_value = mock_prophet_instance

        # Mock query results
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_revenue_data

        mock_db.query.return_value = mock_query

        # Train model
        result = await forecasting_model.train_model(historical_days=180, model_type='prophet')

        # Assertions
        assert result['model_type'] == 'prophet'
        assert result['status'] == 'trained'

    @pytest.mark.asyncio
    async def test_train_model_auto_selection(self, forecasting_model, mock_db, sample_revenue_data):
        """Test automatic model selection."""
        # Mock query results
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_revenue_data

        mock_db.query.return_value = mock_query

        # Train with auto selection
        result = await forecasting_model.train_model(historical_days=180, model_type='auto')

        # Should select a model
        assert result['model_type'] in ['prophet', 'arima', 'linear']
        assert result['status'] == 'trained'

    @pytest.mark.asyncio
    async def test_train_model_insufficient_data(self, forecasting_model, mock_db):
        """Test training with insufficient data."""
        # Mock query with very little data
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            (datetime.now() - timedelta(days=i), 5000, 2)
            for i in range(10)  # Only 10 days
        ]

        mock_db.query.return_value = mock_query

        # Should fall back to linear model
        result = await forecasting_model.train_model(historical_days=30, model_type='auto')

        assert result['model_type'] == 'linear'
        assert 'warning' in result or result['status'] == 'trained'

    @pytest.mark.asyncio
    async def test_predict_revenue_basic(self, forecasting_model, mock_db, sample_revenue_data):
        """Test basic revenue prediction."""
        # First train the model
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_revenue_data

        mock_db.query.return_value = mock_query

        await forecasting_model.train_model(historical_days=180, model_type='linear')

        # Now predict
        result = await forecasting_model.predict_revenue(days_ahead=30, include_scenarios=False)

        # Assertions
        assert 'forecast' in result
        assert 'summary' in result
        assert len(result['forecast']) == 30

        # Check forecast structure
        forecast_item = result['forecast'][0]
        assert 'date' in forecast_item
        assert 'predicted_revenue' in forecast_item
        assert 'lower_bound' in forecast_item
        assert 'upper_bound' in forecast_item
        assert forecast_item['predicted_revenue'] >= 0

    @pytest.mark.asyncio
    async def test_predict_revenue_with_scenarios(self, forecasting_model, mock_db, sample_revenue_data):
        """Test prediction with optimistic/pessimistic scenarios."""
        # Train model
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_revenue_data

        mock_db.query.return_value = mock_query

        await forecasting_model.train_model(historical_days=180, model_type='linear')

        # Predict with scenarios
        result = await forecasting_model.predict_revenue(days_ahead=30, include_scenarios=True)

        # Check scenarios are included
        forecast_item = result['forecast'][0]
        assert 'optimistic_scenario' in forecast_item
        assert 'pessimistic_scenario' in forecast_item
        assert forecast_item['optimistic_scenario'] > forecast_item['predicted_revenue']
        assert forecast_item['pessimistic_scenario'] < forecast_item['predicted_revenue']

    @pytest.mark.asyncio
    async def test_predict_revenue_no_model(self, forecasting_model):
        """Test prediction without trained model."""
        # Try to predict without training
        with pytest.raises(ValueError, match="No trained model available"):
            await forecasting_model.predict_revenue(days_ahead=30)

    @pytest.mark.asyncio
    async def test_predict_revenue_90_days(self, forecasting_model, mock_db, sample_revenue_data):
        """Test 90-day prediction."""
        # Train model
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_revenue_data

        mock_db.query.return_value = mock_query

        await forecasting_model.train_model(historical_days=180, model_type='linear')

        # Predict 90 days
        result = await forecasting_model.predict_revenue(days_ahead=90)

        assert len(result['forecast']) == 90
        assert result['summary']['forecast_period_days'] == 90

    @pytest.mark.asyncio
    async def test_get_forecast_accuracy(self, forecasting_model, mock_db, sample_revenue_data):
        """Test forecast accuracy calculation using backtesting."""
        # Mock query results
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_revenue_data

        mock_db.query.return_value = mock_query

        # Train model (will use all data except last 30 days for backtesting)
        await forecasting_model.train_model(historical_days=180, model_type='linear')

        # Get accuracy
        result = await forecasting_model.get_forecast_accuracy()

        # Assertions
        assert 'accuracy_metrics' in result
        assert 'test_period_days' in result
        assert 'model_type' in result

        metrics = result['accuracy_metrics']
        assert 'mae' in metrics
        assert 'mape' in metrics
        assert 'rmse' in metrics
        assert 'r_squared' in metrics

        # All metrics should be non-negative
        assert metrics['mae'] >= 0
        assert metrics['mape'] >= 0
        assert metrics['rmse'] >= 0

    @pytest.mark.asyncio
    async def test_get_forecast_accuracy_no_model(self, forecasting_model):
        """Test accuracy calculation without trained model."""
        with pytest.raises(ValueError, match="No trained model available"):
            await forecasting_model.get_forecast_accuracy()

    @pytest.mark.asyncio
    async def test_confidence_intervals(self, forecasting_model, mock_db, sample_revenue_data):
        """Test that confidence intervals are reasonable."""
        # Train model
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_revenue_data

        mock_db.query.return_value = mock_query

        await forecasting_model.train_model(historical_days=180, model_type='linear')

        # Predict
        result = await forecasting_model.predict_revenue(days_ahead=30)

        # Check all confidence intervals
        for forecast in result['forecast']:
            predicted = forecast['predicted_revenue']
            lower = forecast['lower_bound']
            upper = forecast['upper_bound']

            # Lower < Predicted < Upper
            assert lower <= predicted <= upper, \
                f"Confidence interval invalid: {lower} <= {predicted} <= {upper}"

    @pytest.mark.asyncio
    async def test_summary_statistics(self, forecasting_model, mock_db, sample_revenue_data):
        """Test summary statistics in prediction."""
        # Train model
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_revenue_data

        mock_db.query.return_value = mock_query

        await forecasting_model.train_model(historical_days=180, model_type='linear')

        # Predict
        result = await forecasting_model.predict_revenue(days_ahead=30)

        # Check summary
        summary = result['summary']
        assert 'total_forecast_revenue' in summary
        assert 'average_daily_revenue' in summary
        assert 'historical_average' in summary
        assert 'projected_growth_rate' in summary
        assert 'forecast_period_days' in summary

        assert summary['forecast_period_days'] == 30
        assert summary['total_forecast_revenue'] > 0
        assert summary['average_daily_revenue'] > 0


class TestRevenueForecastingEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock()

    @pytest.fixture
    def forecasting_model(self, mock_db):
        """Create RevenueForecastingModel instance."""
        return RevenueForecastingModel(mock_db)

    @pytest.mark.asyncio
    async def test_empty_historical_data(self, forecasting_model, mock_db):
        """Test training with no historical data."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="Insufficient historical data"):
            await forecasting_model.train_model(historical_days=180)

    @pytest.mark.asyncio
    async def test_constant_revenue(self, forecasting_model, mock_db):
        """Test with constant revenue (no variance)."""
        # Mock constant revenue
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            (datetime.now() - timedelta(days=i), 5000, 2)  # Same revenue every day
            for i in range(90)
        ]

        mock_db.query.return_value = mock_query

        # Should still train successfully
        result = await forecasting_model.train_model(historical_days=90, model_type='linear')

        assert result['status'] == 'trained'

    @pytest.mark.asyncio
    async def test_negative_days_ahead(self, forecasting_model, mock_db):
        """Test prediction with negative days ahead."""
        # Train first
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            (datetime.now() - timedelta(days=i), 5000 + i * 100, 2)
            for i in range(90)
        ]

        mock_db.query.return_value = mock_query

        await forecasting_model.train_model(historical_days=90, model_type='linear')

        # Try negative days
        with pytest.raises(ValueError, match="days_ahead must be positive"):
            await forecasting_model.predict_revenue(days_ahead=-10)

    @pytest.mark.asyncio
    async def test_zero_days_ahead(self, forecasting_model, mock_db):
        """Test prediction with zero days ahead."""
        # Train first
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            (datetime.now() - timedelta(days=i), 5000 + i * 100, 2)
            for i in range(90)
        ]

        mock_db.query.return_value = mock_query

        await forecasting_model.train_model(historical_days=90, model_type='linear')

        # Try zero days
        with pytest.raises(ValueError, match="days_ahead must be positive"):
            await forecasting_model.predict_revenue(days_ahead=0)

    @pytest.mark.asyncio
    async def test_excessive_days_ahead(self, forecasting_model, mock_db):
        """Test prediction with very large days ahead."""
        # Train first
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            (datetime.now() - timedelta(days=i), 5000 + i * 100, 2)
            for i in range(90)
        ]

        mock_db.query.return_value = mock_query

        await forecasting_model.train_model(historical_days=90, model_type='linear')

        # Try 1 year prediction (should work but might have warning)
        result = await forecasting_model.predict_revenue(days_ahead=365)

        assert len(result['forecast']) == 365


class TestRevenueForecastingModelTypes:
    """Test different model types."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock()

    @pytest.fixture
    def forecasting_model(self, mock_db):
        """Create RevenueForecastingModel instance."""
        return RevenueForecastingModel(mock_db)

    @pytest.fixture
    def sample_data(self):
        """Generate sample data."""
        return [
            (datetime.now() - timedelta(days=i), 5000 + i * 50, 2)
            for i in range(180)
        ]

    @pytest.mark.asyncio
    async def test_linear_model(self, forecasting_model, mock_db, sample_data):
        """Test linear regression model specifically."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_data

        mock_db.query.return_value = mock_query

        result = await forecasting_model.train_model(historical_days=180, model_type='linear')

        assert result['model_type'] == 'linear'
        assert 'metrics' in result

    @pytest.mark.asyncio
    async def test_invalid_model_type(self, forecasting_model, mock_db, sample_data):
        """Test invalid model type."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_data

        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="Invalid model_type"):
            await forecasting_model.train_model(historical_days=180, model_type='invalid_model')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
