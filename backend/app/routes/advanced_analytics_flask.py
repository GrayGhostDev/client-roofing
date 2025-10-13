"""
Advanced Analytics API Routes (Flask Blueprint)

Flask blueprint for advanced analytics features including:
- Revenue forecasting
- Lead quality heatmaps
- Conversion funnel analysis
- CLV distributions
- Churn risk analysis
- Marketing attribution
- A/B testing
- Revenue forecasting ML
"""

import asyncio
from functools import wraps
from flask import Blueprint, jsonify, request

from app.database import get_db
from app.ml.advanced_analytics import AdvancedAnalytics
from app.ml.revenue_forecasting import get_revenue_forecasting_model
from app.ml.ab_testing import get_ab_testing_framework, ExperimentConfig

# Create Flask blueprint
bp = Blueprint('advanced_analytics', __name__)


def async_route(f):
    """Decorator to run async functions in Flask routes."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@bp.route('/revenue/forecast', methods=['GET'])
@async_route
async def get_revenue_forecast():
    """
    GET /api/advanced-analytics/revenue/forecast

    Query params:
        days_ahead: Days to forecast (1-90, default 30)
        confidence_level: Confidence level (0.8-0.99, default 0.95)
    """
    days_ahead = request.args.get('days_ahead', 30, type=int)
    confidence_level = request.args.get('confidence_level', 0.95, type=float)

    if not (1 <= days_ahead <= 90):
        return jsonify({'error': 'days_ahead must be between 1 and 90'}), 400
    if not (0.8 <= confidence_level <= 0.99):
        return jsonify({'error': 'confidence_level must be between 0.8 and 0.99'}), 400

    db = next(get_db())
    analytics = AdvancedAnalytics(db)

    try:
        result = await analytics.get_revenue_forecast(days_ahead, confidence_level)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/leads/quality-heatmap', methods=['GET'])
@async_route
async def get_lead_quality_heatmap():
    """
    GET /api/advanced-analytics/leads/quality-heatmap

    Query params:
        segment_by: source, zip_code, or property_value (default: source)
    """
    segment_by = request.args.get('segment_by', 'source', type=str)

    db = next(get_db())
    analytics = AdvancedAnalytics(db)

    try:
        result = await analytics.get_lead_quality_heatmap(segment_by)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/conversion/funnel', methods=['GET'])
@async_route
async def get_conversion_funnel():
    """GET /api/advanced-analytics/conversion/funnel"""
    db = next(get_db())
    analytics = AdvancedAnalytics(db)

    try:
        result = await analytics.get_conversion_funnel()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/customers/clv-distribution', methods=['GET'])
@async_route
async def get_clv_distribution():
    """GET /api/advanced-analytics/customers/clv-distribution"""
    db = next(get_db())
    analytics = AdvancedAnalytics(db)

    try:
        result = await analytics.get_clv_distribution()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/customers/churn-risk', methods=['GET'])
@async_route
async def get_churn_risk_analysis():
    """GET /api/advanced-analytics/customers/churn-risk"""
    db = next(get_db())
    analytics = AdvancedAnalytics(db)

    try:
        result = await analytics.get_churn_risk_analysis()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/marketing/attribution', methods=['GET'])
@async_route
async def get_marketing_attribution():
    """GET /api/advanced-analytics/marketing/attribution"""
    db = next(get_db())
    analytics = AdvancedAnalytics(db)

    try:
        result = await analytics.get_marketing_attribution()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# ============================================================================
# REVENUE FORECASTING ML ENDPOINTS
# ============================================================================

@bp.route('/ml/revenue/train', methods=['POST'])
@async_route
async def train_revenue_model():
    """
    POST /api/advanced-analytics/ml/revenue/train

    JSON body:
        historical_days: Days of data (30-365, default 180)
        model_type: auto, prophet, arima, or linear (default: auto)
    """
    data = request.get_json() or {}
    historical_days = data.get('historical_days', 180)
    model_type = data.get('model_type', 'auto')

    if not (30 <= historical_days <= 365):
        return jsonify({'error': 'historical_days must be between 30 and 365'}), 400

    db = next(get_db())
    model = get_revenue_forecasting_model(db)

    try:
        result = await model.train_model(historical_days, model_type)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/ml/revenue/predict', methods=['GET'])
@async_route
async def predict_revenue():
    """
    GET /api/advanced-analytics/ml/revenue/predict

    Query params:
        days_ahead: Days to predict (1-90, default 30)
        include_scenarios: Include optimistic/pessimistic (default: false)
    """
    days_ahead = request.args.get('days_ahead', 30, type=int)
    include_scenarios = request.args.get('include_scenarios', 'false').lower() == 'true'

    if not (1 <= days_ahead <= 90):
        return jsonify({'error': 'days_ahead must be between 1 and 90'}), 400

    db = next(get_db())
    model = get_revenue_forecasting_model(db)

    try:
        result = await model.predict_revenue(days_ahead, include_scenarios)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/ml/revenue/accuracy', methods=['GET'])
@async_route
async def get_forecast_accuracy():
    """GET /api/advanced-analytics/ml/revenue/accuracy"""
    db = next(get_db())
    model = get_revenue_forecasting_model(db)

    try:
        result = await model.get_forecast_accuracy()
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# ============================================================================
# A/B TESTING ENDPOINTS
# ============================================================================

@bp.route('/ab-testing/experiments', methods=['POST'])
def create_experiment():
    """
    POST /api/advanced-analytics/ab-testing/experiments

    JSON body: ExperimentConfig
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    db = next(get_db())
    framework = get_ab_testing_framework(db)

    try:
        config = ExperimentConfig(**data)
        result = framework.create_experiment(config)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/ab-testing/experiments/<experiment_id>/assign/<user_id>', methods=['GET'])
def assign_variant(experiment_id, user_id):
    """GET /api/advanced-analytics/ab-testing/experiments/{id}/assign/{user_id}"""
    db = next(get_db())
    framework = get_ab_testing_framework(db)

    try:
        result = framework.assign_variant(experiment_id, user_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/ab-testing/experiments/<experiment_id>/results', methods=['POST'])
def record_experiment_result(experiment_id):
    """
    POST /api/advanced-analytics/ab-testing/experiments/{id}/results

    JSON body:
        user_id: string
        variant_id: string
        metric_value: number
        converted: boolean
        metadata: object (optional)
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    required_fields = ['user_id', 'variant_id', 'metric_value']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    db = next(get_db())
    framework = get_ab_testing_framework(db)

    try:
        result = framework.record_result(
            experiment_id=experiment_id,
            user_id=data['user_id'],
            variant_id=data['variant_id'],
            metric_value=data['metric_value'],
            converted=data.get('converted', False),
            metadata=data.get('metadata')
        )
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/ab-testing/experiments/<experiment_id>/analyze', methods=['GET'])
def analyze_experiment(experiment_id):
    """
    GET /api/advanced-analytics/ab-testing/experiments/{id}/analyze

    Query params:
        confidence_level: 0.8-0.99 (default: 0.95)
    """
    confidence_level = request.args.get('confidence_level', 0.95, type=float)

    if not (0.8 <= confidence_level <= 0.99):
        return jsonify({'error': 'confidence_level must be between 0.8 and 0.99'}), 400

    db = next(get_db())
    framework = get_ab_testing_framework(db)

    try:
        result = framework.analyze_experiment(experiment_id, confidence_level)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/ab-testing/experiments/<experiment_id>/summary', methods=['GET'])
def get_experiment_summary(experiment_id):
    """GET /api/advanced-analytics/ab-testing/experiments/{id}/summary"""
    db = next(get_db())
    framework = get_ab_testing_framework(db)

    try:
        result = framework.get_experiment_summary(experiment_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/ab-testing/experiments/<experiment_id>/select-winner', methods=['POST'])
def select_winner(experiment_id):
    """
    POST /api/advanced-analytics/ab-testing/experiments/{id}/select-winner

    JSON body:
        winner_variant_id: string
    """
    data = request.get_json()

    if not data or 'winner_variant_id' not in data:
        return jsonify({'error': 'winner_variant_id required'}), 400

    db = next(get_db())
    framework = get_ab_testing_framework(db)

    try:
        result = framework.select_winner(experiment_id, data['winner_variant_id'])
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# ============================================================================
# HEALTH CHECK
# ============================================================================

@bp.route('/health', methods=['GET'])
def health_check():
    """GET /api/advanced-analytics/health"""
    return jsonify({
        'status': 'healthy',
        'service': 'advanced-analytics',
        'endpoints': {
            'revenue_forecast': '/revenue/forecast',
            'lead_heatmap': '/leads/quality-heatmap',
            'conversion_funnel': '/conversion/funnel',
            'clv_distribution': '/customers/clv-distribution',
            'churn_risk': '/customers/churn-risk',
            'marketing_attribution': '/marketing/attribution',
            'ml_train': '/ml/revenue/train',
            'ml_predict': '/ml/revenue/predict',
            'ab_testing': '/ab-testing/experiments'
        }
    }), 200
