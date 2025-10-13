"""
Advanced Analytics API Routes

Endpoints for advanced analytics features including:
- Revenue forecasting
- Lead quality heatmaps
- Conversion funnel analysis
- CLV distributions
- Churn risk analysis
- Marketing attribution
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.ml.advanced_analytics import AdvancedAnalytics
from app.ml.revenue_forecasting import get_revenue_forecasting_model
from app.ml.ab_testing import get_ab_testing_framework, ExperimentConfig

router = APIRouter(prefix="/api/v1/analytics", tags=["Advanced Analytics"])


@router.get("/revenue/forecast")
async def get_revenue_forecast(
    days_ahead: int = Query(30, ge=1, le=90, description="Days to forecast"),
    confidence_level: float = Query(0.95, ge=0.8, le=0.99, description="Confidence level"),
    db: Session = Depends(get_db)
):
    """
    Get revenue forecast for specified number of days.

    Returns daily predictions with confidence intervals.
    """
    analytics = AdvancedAnalytics(db)
    return await analytics.get_revenue_forecast(
        days_ahead=days_ahead,
        confidence_level=confidence_level
    )


@router.get("/leads/quality-heatmap")
async def get_lead_quality_heatmap(
    segment_by: str = Query("source", description="Segment by: source, zip_code, property_value"),
    db: Session = Depends(get_db)
):
    """
    Get lead quality heatmap segmented by specified dimension.

    Returns quality scores, conversion rates, and tier classification.
    """
    analytics = AdvancedAnalytics(db)
    return await analytics.get_lead_quality_heatmap(segment_by=segment_by)


@router.get("/conversion/funnel")
async def get_conversion_funnel(db: Session = Depends(get_db)):
    """
    Get conversion funnel analysis showing drop-off at each stage.

    Returns funnel stages with conversion rates and drop-off percentages.
    """
    analytics = AdvancedAnalytics(db)
    return await analytics.get_conversion_funnel()


@router.get("/customers/clv-distribution")
async def get_clv_distribution(db: Session = Depends(get_db)):
    """
    Get customer lifetime value distribution.

    Returns CLV buckets, customer counts, and percentages.
    """
    analytics = AdvancedAnalytics(db)
    return await analytics.get_clv_distribution()


@router.get("/customers/churn-risk")
async def get_churn_risk_analysis(db: Session = Depends(get_db)):
    """
    Get churn risk analysis for existing customers.

    Returns risk scores, categories, and recommended actions.
    """
    analytics = AdvancedAnalytics(db)
    return await analytics.get_churn_risk_analysis()


@router.get("/marketing/attribution")
async def get_marketing_attribution(db: Session = Depends(get_db)):
    """
    Get marketing channel attribution analysis.

    Returns channel performance, conversion rates, and ROI metrics.
    """
    analytics = AdvancedAnalytics(db)
    return await analytics.get_marketing_attribution()


# Revenue Forecasting ML Model endpoints
@router.post("/ml/revenue/train")
async def train_revenue_model(
    historical_days: int = Query(180, ge=30, le=365, description="Historical data days"),
    model_type: str = Query("auto", description="Model type: auto, prophet, arima, linear"),
    db: Session = Depends(get_db)
):
    """
    Train revenue forecasting model on historical data.

    Returns training metrics and model information.
    """
    model = get_revenue_forecasting_model(db)

    try:
        result = await model.train_model(
            historical_days=historical_days,
            model_type=model_type
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ml/revenue/predict")
async def predict_revenue(
    days_ahead: int = Query(30, ge=1, le=90, description="Days to predict"),
    include_scenarios: bool = Query(False, description="Include optimistic/pessimistic scenarios"),
    db: Session = Depends(get_db)
):
    """
    Predict future revenue using trained ML model.

    Returns daily predictions with confidence intervals and scenarios.
    """
    model = get_revenue_forecasting_model(db)

    try:
        result = await model.predict_revenue(
            days_ahead=days_ahead,
            include_scenarios=include_scenarios
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ml/revenue/accuracy")
async def get_forecast_accuracy(db: Session = Depends(get_db)):
    """
    Get revenue forecast accuracy metrics using backtesting.

    Returns MAE, MAPE, RMSE, and R-squared scores.
    """
    model = get_revenue_forecasting_model(db)

    try:
        result = await model.get_forecast_accuracy()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# A/B Testing endpoints
@router.post("/ab-testing/experiments")
async def create_experiment(
    config: ExperimentConfig,
    db: Session = Depends(get_db)
):
    """
    Create a new A/B testing experiment.

    Returns experiment ID and configuration.
    """
    framework = get_ab_testing_framework(db)

    try:
        result = framework.create_experiment(config)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ab-testing/experiments/{experiment_id}/assign/{user_id}")
async def assign_variant(
    experiment_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Assign a user to an experiment variant.

    Returns assigned variant and configuration.
    """
    framework = get_ab_testing_framework(db)

    try:
        result = framework.assign_variant(experiment_id, user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/ab-testing/experiments/{experiment_id}/results")
async def record_experiment_result(
    experiment_id: str,
    user_id: str,
    variant_id: str,
    metric_value: float,
    converted: bool = False,
    db: Session = Depends(get_db)
):
    """
    Record experiment result for a user.

    Returns confirmation of result recording.
    """
    framework = get_ab_testing_framework(db)

    try:
        result = framework.record_result(
            experiment_id=experiment_id,
            user_id=user_id,
            variant_id=variant_id,
            metric_value=metric_value,
            converted=converted
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/ab-testing/experiments/{experiment_id}/analyze")
async def analyze_experiment(
    experiment_id: str,
    confidence_level: float = Query(0.95, ge=0.8, le=0.99),
    db: Session = Depends(get_db)
):
    """
    Analyze experiment results with statistical significance testing.

    Returns variant performance, p-values, and winner identification.
    """
    framework = get_ab_testing_framework(db)

    try:
        result = framework.analyze_experiment(
            experiment_id=experiment_id,
            confidence_level=confidence_level
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/ab-testing/experiments/{experiment_id}/summary")
async def get_experiment_summary(
    experiment_id: str,
    db: Session = Depends(get_db)
):
    """
    Get experiment summary with current status.

    Returns experiment details and basic statistics.
    """
    framework = get_ab_testing_framework(db)

    try:
        result = framework.get_experiment_summary(experiment_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/ab-testing/experiments/{experiment_id}/select-winner")
async def select_winner(
    experiment_id: str,
    winner_variant_id: str,
    db: Session = Depends(get_db)
):
    """
    Select a winner and complete the experiment.

    Returns winner confirmation and experiment completion.
    """
    framework = get_ab_testing_framework(db)

    try:
        result = framework.select_winner(experiment_id, winner_variant_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
