"""
Revenue Forecasting ML Model

Implements time series forecasting for 30-day revenue predictions using:
- Prophet (Facebook's time series library)
- ARIMA (statistical forecasting)
- Linear regression with seasonal components
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("Warning: Prophet not installed. Using fallback ARIMA model.")

from sklearn.linear_model import LinearRegression
from statsmodels.tsa.arima.model import ARIMA

from app.models.project_sqlalchemy import Project
from app.models.lead_sqlalchemy import Lead
from app.database import get_db


class RevenueForecastingModel:
    """Revenue forecasting model using multiple approaches."""

    def __init__(self, db: Session):
        self.db = db
        self.model = None
        self.model_type = None
        self.training_data = None

    async def train_model(
        self,
        historical_days: int = 180,
        model_type: str = 'auto'
    ) -> Dict:
        """
        Train revenue forecasting model on historical data.

        Args:
            historical_days: Number of days of historical data to use
            model_type: Model type ('prophet', 'arima', 'linear', or 'auto')

        Returns:
            Dict with training results and metrics
        """
        # Validate model_type
        valid_types = ['prophet', 'arima', 'linear', 'auto']
        if model_type not in valid_types:
            raise ValueError(f"Invalid model_type '{model_type}'. Must be one of {valid_types}")

        # Get historical data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=historical_days)

        # Query daily revenue from completed projects
        daily_revenue = (
            self.db.query(
                func.date(Project.created_at).label('date'),
                func.sum(Project.final_amount).label('revenue'),
                func.count(Project.id).label('project_count')
            )
            .filter(
                and_(
                    Project.created_at >= start_date,
                    Project.created_at <= end_date,
                    Project.status.in_(['completed', 'in_progress']),
                    Project.final_amount.isnot(None)
                )
            )
            .group_by(func.date(Project.created_at))
            .order_by(func.date(Project.created_at))
            .all()
        )

        if not daily_revenue or len(daily_revenue) < 30:
            raise ValueError("Insufficient historical data for training (minimum 30 days required)")

        # Convert to pandas DataFrame
        df = pd.DataFrame(daily_revenue, columns=['date', 'revenue', 'project_count'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        # Fill missing dates with 0 revenue
        # Use periods parameter to get exact number of days requested
        date_range = pd.date_range(start=start_date, periods=historical_days, freq='D')
        df = df.reindex(date_range, fill_value=0)
        df.index.name = 'date'

        self.training_data = df

        # Auto-select model if requested
        if model_type == 'auto':
            if PROPHET_AVAILABLE and len(df) >= 60:
                model_type = 'prophet'
            elif len(df) >= 50:
                model_type = 'arima'
            else:
                model_type = 'linear'

        # Train selected model
        if model_type == 'prophet' and PROPHET_AVAILABLE:
            metrics = self._train_prophet(df)
        elif model_type == 'arima':
            metrics = self._train_arima(df)
        else:
            metrics = self._train_linear(df)

        self.model_type = model_type

        return {
            'model_type': model_type,
            'status': 'trained',  # Add status key for tests
            'training_days': len(df),
            'training_period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'metrics': metrics,
            'trained_at': datetime.utcnow().isoformat()
        }

    async def predict_revenue(
        self,
        days_ahead: int = 30,
        include_scenarios: bool = False,
        scenarios: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Predict future revenue for specified number of days.

        Args:
            days_ahead: Number of days to forecast
            include_scenarios: Include optimistic/pessimistic scenarios
            scenarios: Optional custom scenario adjustments

        Returns:
            Dict with forecast predictions
        """
        # Validate days_ahead first before any library calls
        if days_ahead <= 0:
            raise ValueError("days_ahead must be positive")

        if self.model is None or self.training_data is None:
            raise ValueError("No trained model available")

        # Generate predictions based on model type
        if self.model_type == 'prophet':
            predictions = self._predict_prophet(days_ahead)
        elif self.model_type == 'arima':
            predictions = self._predict_arima(days_ahead)
        else:
            predictions = self._predict_linear(days_ahead)

        # Apply custom scenario adjustments if provided
        if scenarios:
            predictions = self._apply_scenario_adjustments(predictions, scenarios)
        # Add scenarios if requested
        elif include_scenarios:
            predictions = self._add_scenarios(predictions)

        # Calculate summary statistics
        total_forecast = sum(p['predicted_revenue'] for p in predictions)
        avg_daily = total_forecast / days_ahead

        # Historical average for comparison
        historical_avg = float(self.training_data['revenue'].mean())
        growth_rate = ((avg_daily - historical_avg) / historical_avg * 100) if historical_avg > 0 else 0

        result = {
            'forecast': predictions,
            'summary': {
                'total_forecast_revenue': round(total_forecast, 2),
                'average_daily_revenue': round(avg_daily, 2),
                'historical_average': round(historical_avg, 2),
                'projected_growth_rate': round(growth_rate, 2),
                'forecast_period_days': days_ahead
            },
            'model': {
                'type': self.model_type,
                'trained_on_days': len(self.training_data)
            },
            'generated_at': datetime.utcnow().isoformat()
        }

        # Add scenarios key if custom scenarios were provided
        if scenarios:
            result['scenarios'] = scenarios

        return result

    async def get_forecast_accuracy(self) -> Dict:
        """
        Calculate forecast accuracy using backtesting.

        Returns:
            Dict with accuracy metrics
        """
        if self.training_data is None:
            raise ValueError("No trained model available")

        # Use last 30 days as test set
        test_days = 30
        if len(self.training_data) < test_days + 30:
            raise ValueError("Insufficient data for backtesting")

        train_data = self.training_data[:-test_days]
        test_data = self.training_data[-test_days:]

        # Temporarily train on subset
        original_model = self.model
        original_data = self.training_data

        self.training_data = train_data

        if self.model_type == 'prophet':
            self._train_prophet(train_data)
            predictions = self._predict_prophet(test_days)
        elif self.model_type == 'arima':
            self._train_arima(train_data)
            predictions = self._predict_arima(test_days)
        else:
            self._train_linear(train_data)
            predictions = self._predict_linear(test_days)

        # Restore original model
        self.model = original_model
        self.training_data = original_data

        # Calculate accuracy metrics
        actual_values = test_data['revenue'].values
        predicted_values = np.array([p['predicted_revenue'] for p in predictions])

        # Mean Absolute Error
        mae = np.mean(np.abs(actual_values - predicted_values))

        # Mean Absolute Percentage Error
        mape = np.mean(np.abs((actual_values - predicted_values) / (actual_values + 1))) * 100

        # Root Mean Squared Error
        rmse = np.sqrt(np.mean((actual_values - predicted_values) ** 2))

        # R-squared
        ss_res = np.sum((actual_values - predicted_values) ** 2)
        ss_tot = np.sum((actual_values - np.mean(actual_values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        return {
            'accuracy_metrics': {
                'mae': round(float(mae), 2),
                'mape': round(float(mape), 2),
                'rmse': round(float(rmse), 2),
                'r_squared': round(float(r_squared), 4)
            },
            'test_period_days': test_days,
            'model_type': self.model_type,
            'calculated_at': datetime.utcnow().isoformat()
        }

    # Model-specific training methods
    def _train_prophet(self, df: pd.DataFrame) -> Dict:
        """Train Prophet model."""
        # Prepare data for Prophet (requires 'ds' and 'y' columns)
        prophet_df = pd.DataFrame({
            'ds': df.index,
            'y': df['revenue'].values
        })

        # Initialize and train model
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False if len(df) < 365 else True,
            changepoint_prior_scale=0.05
        )

        model.fit(prophet_df)
        self.model = model

        # Calculate training metrics
        predictions = model.predict(prophet_df)
        mae = np.mean(np.abs(prophet_df['y'] - predictions['yhat']))

        return {
            'mae': round(float(mae), 2),
            'training_samples': len(df)
        }

    def _train_arima(self, df: pd.DataFrame) -> Dict:
        """Train ARIMA model."""
        # Determine optimal ARIMA order (p, d, q)
        # Using (1, 1, 1) as default for simplicity
        model = ARIMA(df['revenue'].values, order=(1, 1, 1))
        fitted_model = model.fit()

        self.model = fitted_model

        # Calculate training metrics
        predictions = fitted_model.fittedvalues
        mae = np.mean(np.abs(df['revenue'].values[1:] - predictions[1:]))

        return {
            'mae': round(float(mae), 2),
            'aic': round(float(fitted_model.aic), 2),
            'training_samples': len(df)
        }

    def _train_linear(self, df: pd.DataFrame) -> Dict:
        """Train linear regression model with seasonal components."""
        # Create features
        X = np.arange(len(df)).reshape(-1, 1)

        # Add day of week as feature
        day_of_week = pd.to_datetime(df.index).dayofweek.values.reshape(-1, 1)
        X = np.hstack([X, day_of_week])

        y = df['revenue'].values

        # Train model
        model = LinearRegression()
        model.fit(X, y)

        self.model = model

        # Calculate training metrics
        predictions = model.predict(X)
        mae = np.mean(np.abs(y - predictions))

        return {
            'mae': round(float(mae), 2),
            'r_squared': round(float(model.score(X, y)), 4),
            'training_samples': len(df)
        }

    # Model-specific prediction methods
    def _predict_prophet(self, days_ahead: int) -> List[Dict]:
        """Generate predictions using Prophet."""
        # Create future dataframe
        future = self.model.make_future_dataframe(periods=days_ahead)
        forecast = self.model.predict(future)

        # Extract future predictions only
        future_forecast = forecast.tail(days_ahead)

        predictions = []
        for _, row in future_forecast.iterrows():
            predictions.append({
                'date': row['ds'].strftime('%Y-%m-%d'),
                'predicted_revenue': max(0, round(float(row['yhat']), 2)),
                'lower_bound': max(0, round(float(row['yhat_lower']), 2)),
                'upper_bound': round(float(row['yhat_upper']), 2),
                'confidence_interval': 0.95
            })

        return predictions

    def _predict_arima(self, days_ahead: int) -> List[Dict]:
        """Generate predictions using ARIMA."""
        forecast_result = self.model.forecast(steps=days_ahead)
        std_error = np.sqrt(self.model.params.get('sigma2', 1))

        # Generate dates
        last_date = self.training_data.index[-1]
        future_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=days_ahead,
            freq='D'
        )

        predictions = []
        for i, date in enumerate(future_dates):
            pred_value = float(forecast_result[i])
            ci = 1.96 * std_error  # 95% confidence interval

            predictions.append({
                'date': date.strftime('%Y-%m-%d'),
                'predicted_revenue': max(0, round(pred_value, 2)),
                'lower_bound': max(0, round(pred_value - ci, 2)),
                'upper_bound': round(pred_value + ci, 2),
                'confidence_interval': 0.95
            })

        return predictions

    def _predict_linear(self, days_ahead: int) -> List[Dict]:
        """Generate predictions using linear regression."""
        # Generate future X values
        last_index = len(self.training_data)
        future_indices = np.arange(last_index, last_index + days_ahead).reshape(-1, 1)

        # Generate future dates to get day of week
        last_date = self.training_data.index[-1]
        future_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=days_ahead,
            freq='D'
        )
        day_of_week = future_dates.dayofweek.values.reshape(-1, 1)

        # Combine features
        X_future = np.hstack([future_indices, day_of_week])

        # Predict
        predictions_array = self.model.predict(X_future)

        # Calculate confidence interval based on training error
        training_X = np.arange(len(self.training_data)).reshape(-1, 1)
        training_dow = pd.to_datetime(self.training_data.index).dayofweek.values.reshape(-1, 1)
        training_X = np.hstack([training_X, training_dow])

        training_pred = self.model.predict(training_X)
        residuals = self.training_data['revenue'].values - training_pred
        std_error = np.std(residuals)
        ci = 1.96 * std_error

        predictions = []
        for i, date in enumerate(future_dates):
            pred_value = float(predictions_array[i])

            predictions.append({
                'date': date.strftime('%Y-%m-%d'),
                'predicted_revenue': max(0, round(pred_value, 2)),
                'lower_bound': max(0, round(pred_value - ci, 2)),
                'upper_bound': round(pred_value + ci, 2),
                'confidence_interval': 0.95
            })

        return predictions

    def _add_scenarios(self, predictions: List[Dict]) -> List[Dict]:
        """Add optimistic and pessimistic scenarios to predictions."""
        for pred in predictions:
            base = pred['predicted_revenue']

            # Optimistic: +20% from upper bound
            pred['optimistic_scenario'] = round(pred['upper_bound'] * 1.2, 2)

            # Pessimistic: -20% from lower bound
            pred['pessimistic_scenario'] = max(0, round(pred['lower_bound'] * 0.8, 2))

        return predictions

    def _apply_scenario_adjustments(self, predictions: List[Dict], scenarios: Dict[str, float]) -> List[Dict]:
        """Apply custom scenario adjustments to predictions."""
        for pred in predictions:
            base = pred['predicted_revenue']
            # Apply each scenario adjustment as multiplier
            for scenario_name, multiplier in scenarios.items():
                pred[f'{scenario_name}_scenario'] = round(base * multiplier, 2)
        return predictions


# Global instance
_revenue_forecasting_model: Optional[RevenueForecastingModel] = None


def get_revenue_forecasting_model(db: Session = None) -> RevenueForecastingModel:
    """Get or create revenue forecasting model instance."""
    global _revenue_forecasting_model
    if _revenue_forecasting_model is None:
        _revenue_forecasting_model = RevenueForecastingModel(db or next(get_db()))
    return _revenue_forecasting_model
