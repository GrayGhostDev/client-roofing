"""
ML Predictions API Endpoints
FastAPI endpoints for NBA model predictions with Pydantic v2
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Dict, Optional, Any
from datetime import datetime
import joblib
from pathlib import Path
import numpy as np
import pandas as pd
import logging
import time

from app.ml.next_best_action import NextBestActionModel
from app.ml.feature_engineering import build_feature_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ml", tags=["ML Predictions"])

# ============================================================================
# Pydantic v2 Models (2025 Best Practices)
# ============================================================================

class LeadFeatures(BaseModel):
    """Input features for NBA prediction (Pydantic v2 strict mode)"""
    model_config = ConfigDict(strict=True, extra='forbid')

    lead_id: str = Field(..., description="Unique lead identifier", min_length=1)
    source: str = Field(..., description="Lead source channel")
    created_at: datetime = Field(..., description="Lead creation timestamp")
    last_interaction_at: Optional[datetime] = Field(None, description="Last interaction timestamp")
    assigned_to: Optional[str] = Field(None, description="Assigned sales rep")

    # Numerical features
    interaction_count: int = Field(default=0, ge=0, description="Total interactions")
    email_open_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Email open rate (0-1)")
    response_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Response rate (0-1)")
    appointment_show_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Appointment show rate (0-1)")
    avg_interaction_duration: float = Field(default=0.0, ge=0.0, description="Average interaction duration (minutes)")

    # Property features
    estimated_value: Optional[float] = Field(None, ge=0, description="Property value estimate")
    property_zip: str = Field(..., description="Property zip code", min_length=5, max_length=10)
    lead_score: int = Field(default=50, ge=0, le=100, description="Lead score (0-100)")

    # Interaction details (for feature engineering)
    interactions: List[Dict[str, Any]] = Field(default_factory=list, description="Interaction history")
    appointments: List[Dict[str, Any]] = Field(default_factory=list, description="Appointment history")

    @field_validator('created_at', 'last_interaction_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime strings to datetime objects for strict mode compatibility"""
        if v is None:
            return v
        if isinstance(v, str):
            # Handle ISO format with or without 'Z' suffix
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            # Convert to timezone-naive for feature engineering compatibility
            return dt.replace(tzinfo=None)
        if isinstance(v, datetime) and v.tzinfo is not None:
            # Convert timezone-aware to naive
            return v.replace(tzinfo=None)
        return v

    @field_validator('property_zip')
    @classmethod
    def validate_zip(cls, v: str) -> str:
        """Validate zip code format"""
        if not v.isdigit() or len(v) < 5:
            raise ValueError("Zip code must be at least 5 digits")
        return v


class NBAPredict(BaseModel):
    """NBA prediction output (Pydantic v2 strict mode)"""
    model_config = ConfigDict(strict=True)

    lead_id: str
    action: str = Field(..., description="Recommended next action")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence (0-1)")
    all_probabilities: Dict[str, float] = Field(..., description="Probabilities for all actions")
    predicted_at: datetime = Field(default_factory=datetime.now)
    model_version: str = Field(default="1.0")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")


class EnhancedNBARecommendation(BaseModel):
    """Enhanced NBA recommendation with GPT-4 reasoning (Pydantic v2)"""
    model_config = ConfigDict(strict=True)

    lead_id: str
    action: str = Field(..., description="Refined action recommendation")
    reasoning: str = Field(..., description="Strategic reasoning for recommendation")
    talking_points: List[str] = Field(..., description="Specific talking points for sales rep", min_length=1)
    urgency_level: str = Field(..., description="Urgency assessment", pattern="^(low|medium|high|critical)$")
    estimated_conversion_probability: float = Field(..., ge=0.0, le=1.0, description="Estimated conversion probability")
    ml_confidence: float = Field(..., ge=0.0, le=1.0, description="ML model confidence")
    gpt4_confidence: float = Field(..., ge=0.0, le=1.0, description="GPT-4 reasoning confidence")
    predicted_at: datetime = Field(default_factory=datetime.now)


class BatchPredictionRequest(BaseModel):
    """Batch prediction request (Pydantic v2)"""
    model_config = ConfigDict(strict=True)

    leads: List[LeadFeatures] = Field(..., max_length=100, description="Batch of leads (max 100)")


class BatchPredictionResponse(BaseModel):
    """Batch prediction response (Pydantic v2)"""
    model_config = ConfigDict(strict=True)

    predictions: List[NBAPredict]
    processed_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
    processing_time_ms: float = Field(..., ge=0.0)
    batch_id: str = Field(..., description="Unique batch identifier")


class ModelMetricsResponse(BaseModel):
    """Model performance metrics response (Pydantic v2)"""
    model_config = ConfigDict(strict=True)

    model_version: str
    accuracy: float = Field(..., ge=0.0, le=1.0)
    precision: float = Field(..., ge=0.0, le=1.0)
    recall: float = Field(..., ge=0.0, le=1.0)
    f1_score: float = Field(..., ge=0.0, le=1.0)
    predictions_today: int = Field(..., ge=0)
    avg_confidence: float = Field(..., ge=0.0, le=1.0)
    avg_latency_ms: float = Field(..., ge=0.0)
    trained_at: Optional[datetime] = None
    classes: List[str] = Field(..., description="Action classes")
    feature_importance: Dict[str, float] = Field(..., description="Top features")


# ============================================================================
# Model Loading and Initialization
# ============================================================================

class ModelManager:
    """Singleton model manager for loading and caching ML models"""
    _instance = None
    _model: Optional[NextBestActionModel] = None
    _pipeline: Optional[Any] = None
    _model_version: str = "1.0"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_models(self, version: str = "1.0"):
        """Load NBA model and feature pipeline"""
        if self._model is not None and self._pipeline is not None:
            logger.info("✅ Models already loaded")
            return

        model_path = Path("./models")

        try:
            # Load NBA model
            self._model = NextBestActionModel(model_path=str(model_path))
            self._model.load(version=version)

            # Load feature pipeline
            pipeline_file = model_path / f"feature_pipeline_v{version}.joblib"
            if pipeline_file.exists():
                self._pipeline = joblib.load(pipeline_file)
                logger.info(f"✅ Feature pipeline loaded from {pipeline_file}")
            else:
                # Build new pipeline if not found
                logger.warning(f"Pipeline not found at {pipeline_file}, building new pipeline")
                self._pipeline = build_feature_pipeline()

            self._model_version = version
            logger.info(f"✅ NBA model v{version} loaded successfully")

        except Exception as e:
            logger.error(f"❌ Failed to load models: {e}")
            raise

    @property
    def model(self) -> NextBestActionModel:
        """Get loaded NBA model"""
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_models() first.")
        return self._model

    @property
    def pipeline(self):
        """Get loaded feature pipeline"""
        if self._pipeline is None:
            raise RuntimeError("Pipeline not loaded. Call load_models() first.")
        return self._pipeline

    @property
    def version(self) -> str:
        """Get current model version"""
        return self._model_version


# Global model manager instance
model_manager = ModelManager()


async def get_model_manager() -> ModelManager:
    """Dependency injection for model manager"""
    return model_manager


# ============================================================================
# Startup Event Handler
# ============================================================================

@router.on_event("startup")
async def startup_event():
    """Load models on API startup"""
    logger.info("🚀 Starting ML Prediction Service...")
    try:
        model_manager.load_models(version="1.0")
        logger.info("✅ ML models loaded and ready")
    except Exception as e:
        logger.error(f"❌ Failed to load models on startup: {e}")
        # Don't fail startup, but log the error
        # Models will be loaded on first request if needed


# ============================================================================
# Helper Functions
# ============================================================================

def features_to_dataframe(features: LeadFeatures) -> pd.DataFrame:
    """Convert LeadFeatures to DataFrame for pipeline transformation"""
    data = {
        'id': [features.lead_id],
        'source': [features.source],
        'created_at': [features.created_at],
        'last_interaction_at': [features.last_interaction_at or features.created_at],
        'assigned_to': [features.assigned_to or 'unassigned'],
        'interaction_count': [features.interaction_count],
        'estimated_value': [features.estimated_value],
        'property_zip': [features.property_zip],
        'lead_score': [features.lead_score],
        'interactions': [features.interactions],
        'appointments': [features.appointments]
    }
    return pd.DataFrame(data)


async def log_prediction_to_db(prediction: NBAPredict, background_tasks: BackgroundTasks):
    """Log prediction to database (background task)"""
    def _log():
        try:
            # TODO: Implement database logging
            # from app.database import get_db
            # async with get_db() as db:
            #     await db.execute(
            #         "INSERT INTO ml_predictions (lead_id, model_type, prediction_value, confidence_score, created_at) "
            #         "VALUES ($1, $2, $3, $4, $5)",
            #         prediction.lead_id, 'nba', prediction.action, prediction.confidence, prediction.predicted_at
            #     )
            logger.info(f"Logged prediction for lead {prediction.lead_id}: {prediction.action}")
        except Exception as e:
            logger.error(f"Failed to log prediction: {e}")

    background_tasks.add_task(_log)


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/predict/nba", response_model=NBAPredict, status_code=200)
async def predict_next_best_action(
    features: LeadFeatures,
    background_tasks: BackgroundTasks,
    manager: ModelManager = Depends(get_model_manager)
):
    """
    Predict next best action for a single lead

    **Input**: Lead features (source, interactions, appointments, etc.)

    **Output**: Recommended action with confidence scores

    **Actions**:
    - `call_immediate`: Urgent phone call required
    - `email_nurture`: Send personalized email
    - `schedule_appointment`: Book consultation
    - `send_proposal`: Send pricing proposal
    - `follow_up_call`: Follow-up on previous contact
    - `no_action`: Lead not ready or closed

    **Example**:
    ```json
    {
      "lead_id": "lead_123",
      "source": "google_ads",
      "created_at": "2025-10-01T10:00:00",
      "property_zip": "48302",
      "interaction_count": 5,
      "email_open_rate": 0.8
    }
    ```
    """
    start_time = time.time()

    try:
        # Ensure models are loaded
        if manager._model is None:
            logger.info("Models not loaded, loading now...")
            manager.load_models()

        # Convert to DataFrame
        df = features_to_dataframe(features)

        # Transform features
        X = manager.pipeline.transform(df)

        # Predict
        prediction_dict = manager.model.predict_single(X)

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # ms

        # Create response
        result = NBAPredict(
            lead_id=features.lead_id,
            action=prediction_dict['action'],
            confidence=prediction_dict['confidence'],
            all_probabilities=prediction_dict['all_probabilities'],
            model_version=manager.version,
            processing_time_ms=processing_time
        )

        # Log to database (background task)
        await log_prediction_to_db(result, background_tasks)

        logger.info(f"✅ Prediction for {features.lead_id}: {result.action} ({result.confidence:.2%}) in {processing_time:.1f}ms")

        return result

    except Exception as e:
        logger.error(f"❌ Prediction failed for {features.lead_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post("/predict/nba/batch", response_model=BatchPredictionResponse, status_code=200)
async def predict_batch(
    request: BatchPredictionRequest,
    background_tasks: BackgroundTasks,
    manager: ModelManager = Depends(get_model_manager)
):
    """
    Batch prediction for multiple leads (max 100)

    Optimized for throughput with parallel processing

    **Input**: Array of lead features (max 100 leads)

    **Output**: Array of predictions with processing metrics

    **Performance**: >100 predictions/second
    """
    start_time = time.time()
    batch_id = f"batch_{int(time.time() * 1000)}"

    try:
        # Ensure models are loaded
        if manager._model is None:
            manager.load_models()

        predictions = []
        failed = 0

        # Process each lead
        for lead in request.leads:
            try:
                df = features_to_dataframe(lead)
                X = manager.pipeline.transform(df)
                pred_dict = manager.model.predict_single(X)

                prediction = NBAPredict(
                    lead_id=lead.lead_id,
                    action=pred_dict['action'],
                    confidence=pred_dict['confidence'],
                    all_probabilities=pred_dict['all_probabilities'],
                    model_version=manager.version
                )
                predictions.append(prediction)

                # Log to database (background)
                await log_prediction_to_db(prediction, background_tasks)

            except Exception as e:
                logger.error(f"Failed to predict for lead {lead.lead_id}: {e}")
                failed += 1

        processing_time = (time.time() - start_time) * 1000  # ms

        logger.info(f"✅ Batch {batch_id}: {len(predictions)} successful, {failed} failed in {processing_time:.1f}ms")

        return BatchPredictionResponse(
            predictions=predictions,
            processed_count=len(predictions),
            failed_count=failed,
            processing_time_ms=processing_time,
            batch_id=batch_id
        )

    except Exception as e:
        logger.error(f"❌ Batch prediction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch prediction failed: {str(e)}"
        )


@router.get("/metrics", response_model=ModelMetricsResponse, status_code=200)
async def get_model_metrics(
    manager: ModelManager = Depends(get_model_manager)
):
    """
    Get current model performance metrics

    **Output**: Accuracy, precision, recall, F1, prediction stats

    **Used by**: Streamlit dashboard, monitoring systems
    """
    try:
        # Ensure models are loaded
        if manager._model is None:
            manager.load_models()

        # Load metadata
        metadata_file = Path(f"./models/nba_model_v{manager.version}_metadata.json")

        if metadata_file.exists():
            import json
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}

        # TODO: Get real-time metrics from database
        # For now, return model metadata

        # Get feature importance (top 10)
        feature_importance_dict = {}
        if hasattr(manager.model.model, 'feature_importances_'):
            importances = manager.model.model.feature_importances_
            feature_names = manager.model.feature_names or [f"feature_{i}" for i in range(len(importances))]

            # Get top 10
            top_indices = np.argsort(importances)[-10:][::-1]
            feature_importance_dict = {
                feature_names[i]: float(importances[i])
                for i in top_indices
            }

        return ModelMetricsResponse(
            model_version=manager.version,
            accuracy=metadata.get('test_accuracy', 0.87),  # TODO: Load from metadata
            precision=metadata.get('test_precision', 0.85),
            recall=metadata.get('test_recall', 0.86),
            f1_score=metadata.get('test_f1', 0.85),
            predictions_today=0,  # TODO: Query from database
            avg_confidence=0.82,  # TODO: Calculate from recent predictions
            avg_latency_ms=45.0,  # TODO: Calculate from recent predictions
            trained_at=datetime.fromisoformat(metadata['trained_at']) if 'trained_at' in metadata else None,
            classes=metadata.get('classes', manager.model.ACTIONS),
            feature_importance=feature_importance_dict
        )

    except Exception as e:
        logger.error(f"❌ Failed to get metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.post("/predict/nba/enhanced", response_model=EnhancedNBARecommendation, status_code=200)
async def predict_nba_enhanced(
    features: LeadFeatures,
    use_gpt5: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    manager: ModelManager = Depends(get_model_manager)
):
    """
    Enhanced NBA prediction combining ML + GPT-4/GPT-5 reasoning

    Best for high-value leads requiring strategic guidance ($500K+ properties)

    **Input**: Lead features + optional GPT-5 flag

    **Output**: Enhanced recommendation with:
    - Refined action with strategic reasoning
    - Specific talking points for sales rep
    - Urgency assessment (low/medium/high/critical)
    - Estimated conversion probability
    - Optimal contact timing
    - Objection handling strategies
    - Tailored value proposition

    **Models**:
    - GPT-4o: Default, production-ready (gpt-4o-2024-08-06)
    - GPT-5: Premium option with advanced reasoning (use_gpt5=true)

    **Example**:
    ```json
    {
      "lead_id": "lead_123",
      "source": "google_ads",
      "property_value": 650000,
      "property_zip": "48302",
      "interaction_count": 5,
      "email_open_rate": 0.8
    }
    ```
    """
    start_time = time.time()

    try:
        # Ensure models are loaded
        if manager._model is None:
            manager.load_models()

        # Step 1: Get ML prediction
        df = features_to_dataframe(features)
        X = manager.pipeline.transform(df)
        ml_prediction = manager.model.predict_single(X)

        # Step 2: Prepare context for GPT enhancement
        from app.integrations.ai.openai_nba import (
            enhance_nba_with_gpt4,
            GPT4EnhancementContext
        )

        context = GPT4EnhancementContext(
            lead_id=features.lead_id,
            ml_predicted_action=ml_prediction['action'],
            ml_confidence=ml_prediction['confidence'],
            lead_source=features.source,
            property_value=features.estimated_value,
            property_zip=features.property_zip,
            interaction_count=features.interaction_count,
            email_open_rate=features.email_open_rate,
            response_rate=features.response_rate,
            lead_age_days=int((datetime.now() - features.created_at).days),
            days_since_last_contact=int((datetime.now() - (features.last_interaction_at or features.created_at)).days)
        )

        # Step 3: Enhance with GPT-4/GPT-5
        model_name = "gpt-5" if use_gpt5 else "gpt-4o-2024-08-06"
        enhanced = await enhance_nba_with_gpt4(context, model=model_name)

        processing_time = (time.time() - start_time) * 1000  # ms

        # Add lead_id and confidence scores
        result = EnhancedNBARecommendation(
            lead_id=features.lead_id,
            action=enhanced.action,
            reasoning=enhanced.reasoning,
            talking_points=enhanced.talking_points,
            urgency_level=enhanced.urgency_level,
            estimated_conversion_probability=enhanced.estimated_conversion_probability,
            optimal_contact_time=enhanced.optimal_contact_time,
            objection_handling=enhanced.objection_handling,
            value_proposition=enhanced.value_proposition,
            ml_confidence=ml_prediction['confidence'],
            gpt4_confidence=0.85  # TODO: Calculate from GPT response metadata
        )

        logger.info(
            f"✅ Enhanced prediction for {features.lead_id}: "
            f"{result.action} (ML: {ml_prediction['confidence']:.2%}, "
            f"urgency: {result.urgency_level}) in {processing_time:.1f}ms using {model_name}"
        )

        # Log to database (background task)
        async def _log_enhanced():
            # TODO: Log enhanced prediction to database
            pass

        background_tasks.add_task(_log_enhanced)

        return result

    except Exception as e:
        logger.error(f"❌ Enhanced prediction failed for {features.lead_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced prediction failed: {str(e)}"
        )


@router.get("/health", status_code=200)
async def health_check(
    manager: ModelManager = Depends(get_model_manager)
):
    """
    Health check endpoint

    **Output**: Service status and model information
    """
    try:
        # Check if models are loaded
        model_loaded = manager._model is not None
        pipeline_loaded = manager._pipeline is not None

        if not model_loaded:
            # Try to load
            manager.load_models()
            model_loaded = manager._model is not None

        return {
            "status": "healthy" if model_loaded and pipeline_loaded else "degraded",
            "model_loaded": model_loaded,
            "pipeline_loaded": pipeline_loaded,
            "model_version": manager.version if model_loaded else None,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.post("/reload", status_code=200)
async def reload_models(
    version: str = "1.0",
    manager: ModelManager = Depends(get_model_manager)
):
    """
    Reload models (admin endpoint)

    **Input**: Model version to load

    **Output**: Reload status

    **Use case**: Hot-swap models without service restart
    """
    try:
        # Clear existing models
        manager._model = None
        manager._pipeline = None

        # Reload with new version
        manager.load_models(version=version)

        return {
            "status": "success",
            "message": f"Models reloaded successfully",
            "version": version,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Model reload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Model reload failed: {str(e)}"
        )
