# Week 8 Implementation Plan: ML Model Development & Deployment

**Phase 4, Week 8 (Weeks 8-12 Overall)**
**Focus**: Next Best Action (NBA) Engine Development
**Duration**: 5 working days
**Updated**: 2025-10-10 with 2025 best practices

---

## Executive Summary

Week 8 kicks off Phase 4 implementation by building the foundational ML infrastructure and deploying the first predictive model: the **Next Best Action (NBA) Engine**. This model will analyze lead behavior and recommend optimal actions for sales reps, targeting a **35% conversion rate improvement**.

### Success Metrics
- ✅ NBA model accuracy: **≥85%** on validation set
- ✅ API response time: **<200ms** for predictions
- ✅ Dashboard uptime: **99.9%**
- ✅ Test coverage: **≥80%**
- ✅ n8n workflow reliability: **100%** successful executions

---

## Technology Stack (2025 Best Practices)

### Core ML/AI
- **Python 3.13** - Latest stable version
- **scikit-learn 1.7.2** - ML model training with pre-built wheels
- **pandas 2.2.3** - Data manipulation
- **numpy 2.2.1** - Numerical computing
- **joblib** - Model persistence (protocol=5 for memory efficiency)

### API & Backend
- **FastAPI** - Modern async web framework
- **Pydantic v2.12.0** - Enhanced data validation
- **OpenAI 1.59.8** - GPT-4 Turbo with structured outputs
- **Anthropic 0.44.0** - Claude 3.5 Sonnet for complex reasoning

### Database & Storage
- **Supabase** - PostgreSQL backend
- **Redis 5.2.0** - Caching and session management

### Frontend & Visualization
- **Streamlit** - ML dashboard and metrics
- **Plotly/Altair** - Interactive visualizations

### Automation & Orchestration
- **n8n** - AI agent workflow automation
- **Celery 5.4.0** - Background task processing

### Testing & Quality
- **pytest 8.3.0** - Unit and integration testing
- **pytest-asyncio 0.25.0** - Async test support
- **pytest-cov 6.0.0** - Coverage reporting

---

## Week 8 Task Breakdown

### Day 1: Data Extraction & Preparation (8 hours)

#### Task 1.1: Extract Historical CRM Data (3 hours)
**Objective**: Pull 6-12 months of lead interaction data from Supabase

**Data Requirements**:
- Leads table: `id`, `source`, `status`, `created_at`, `assigned_to`
- Interactions table: `lead_id`, `type`, `timestamp`, `outcome`
- Appointments table: `lead_id`, `scheduled_at`, `completed`, `result`
- Projects table: `lead_id`, `value`, `status`, `closed_at`

**Implementation**:
```python
# backend/app/ml/data_extraction.py
from supabase import create_client
import pandas as pd
from datetime import datetime, timedelta
import os

class DataExtractor:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )

    def extract_leads_data(self, months_back: int = 12) -> pd.DataFrame:
        """Extract historical lead data for ML training"""
        cutoff_date = (datetime.now() - timedelta(days=30 * months_back)).isoformat()

        response = self.supabase.table("leads").select(
            "id, source, status, created_at, assigned_to, "
            "interactions(type, timestamp, outcome), "
            "appointments(scheduled_at, completed, result), "
            "projects(value, status, closed_at)"
        ).gte("created_at", cutoff_date).execute()

        return pd.DataFrame(response.data)

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess extracted data"""
        # Handle missing values
        df['source'] = df['source'].fillna('unknown')
        df['assigned_to'] = df['assigned_to'].fillna('unassigned')

        # Remove duplicates
        df = df.drop_duplicates(subset=['id'])

        # Handle outliers in numerical columns
        if 'value' in df.columns:
            q1 = df['value'].quantile(0.25)
            q3 = df['value'].quantile(0.75)
            iqr = q3 - q1
            df = df[~((df['value'] < (q1 - 1.5 * iqr)) | (df['value'] > (q3 + 1.5 * iqr)))]

        return df

    def create_train_test_split(self, df: pd.DataFrame, test_size: float = 0.2):
        """Create stratified train/validation/test splits"""
        from sklearn.model_selection import train_test_split

        # Stratify by conversion status
        train_val, test = train_test_split(
            df, test_size=test_size, stratify=df['status'], random_state=42
        )

        train, val = train_test_split(
            train_val, test_size=0.25, stratify=train_val['status'], random_state=42
        )

        return train, val, test
```

**Success Criteria**:
- ✅ Minimum **10,000 lead records** extracted
- ✅ Data completeness: **≥95%** for critical features
- ✅ No duplicate records
- ✅ Balanced class distribution (±10% variance)

---

#### Task 1.2: Design Feature Engineering Pipeline (5 hours)
**Objective**: Create robust feature transformation pipeline using 2025 best practices

**Feature Categories**:
1. **Temporal Features**: `lead_age_days`, `days_since_last_contact`, `hour_of_first_contact`
2. **Behavioral Features**: `interaction_count`, `email_open_rate`, `response_rate`
3. **Engagement Features**: `avg_response_time_hours`, `appointment_show_rate`, `reschedule_count`
4. **Demographic Features**: `property_value_tier`, `zip_code_encoded`, `source_channel`
5. **Derived Features**: `engagement_score`, `urgency_score`, `conversion_probability`

**Implementation**:
```python
# backend/app/ml/feature_engineering.py
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
import pandas as pd
import numpy as np

class TemporalFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract time-based features from lead data"""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        X['lead_age_days'] = (pd.Timestamp.now() - pd.to_datetime(X['created_at'])).dt.days
        X['days_since_last_contact'] = (
            pd.Timestamp.now() - pd.to_datetime(X['last_interaction_at'])
        ).dt.days
        X['hour_of_first_contact'] = pd.to_datetime(X['created_at']).dt.hour
        X['is_weekend'] = pd.to_datetime(X['created_at']).dt.dayofweek >= 5
        return X

class BehavioralFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract behavioral engagement features"""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        X['interaction_count'] = X['interactions'].apply(len)
        X['email_open_rate'] = X.apply(self._calculate_email_open_rate, axis=1)
        X['response_rate'] = X.apply(self._calculate_response_rate, axis=1)
        X['appointment_show_rate'] = X.apply(self._calculate_show_rate, axis=1)
        return X

    def _calculate_email_open_rate(self, row):
        emails = [i for i in row['interactions'] if i['type'] == 'email']
        if not emails:
            return 0.0
        opened = sum(1 for e in emails if e.get('opened', False))
        return opened / len(emails)

    def _calculate_response_rate(self, row):
        outbound = [i for i in row['interactions'] if i.get('direction') == 'outbound']
        if not outbound:
            return 0.0
        responses = sum(1 for i in outbound if i.get('response_received', False))
        return responses / len(outbound)

    def _calculate_show_rate(self, row):
        appointments = row.get('appointments', [])
        if not appointments:
            return 0.0
        showed = sum(1 for a in appointments if a.get('completed', False))
        return showed / len(appointments)

class EngagementScoreCalculator(BaseEstimator, TransformerMixin):
    """Calculate composite engagement score (0-100)"""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()

        # Weighted engagement score
        X['engagement_score'] = (
            X['interaction_count'] * 0.3 +
            X['email_open_rate'] * 100 * 0.2 +
            X['response_rate'] * 100 * 0.3 +
            X['appointment_show_rate'] * 100 * 0.2
        ).clip(0, 100)

        # Urgency score based on time decay
        X['urgency_score'] = 100 * np.exp(-X['days_since_last_contact'] / 7)

        return X

def build_feature_pipeline():
    """Build complete feature engineering pipeline"""

    # Categorical features for encoding
    categorical_features = ['source', 'zip_code', 'assigned_to']

    # Numerical features for scaling
    numerical_features = [
        'lead_age_days', 'days_since_last_contact', 'interaction_count',
        'email_open_rate', 'response_rate', 'engagement_score', 'urgency_score'
    ]

    # Preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ]
    )

    # Full pipeline
    pipeline = Pipeline([
        ('temporal', TemporalFeatureExtractor()),
        ('behavioral', BehavioralFeatureExtractor()),
        ('engagement', EngagementScoreCalculator()),
        ('preprocessor', preprocessor)
    ])

    return pipeline
```

**Success Criteria**:
- ✅ All features have **<5% missing values** after imputation
- ✅ No feature has **>0.95 correlation** with another (avoid multicollinearity)
- ✅ Pipeline is **pickleable** and **reproducible**
- ✅ Feature importance can be calculated

---

### Day 2: NBA Model Training (8 hours)

#### Task 2.1: Implement NBA Prediction Model (6 hours)
**Objective**: Train high-accuracy classification model for next best action recommendations

**Model Architecture Options**:
1. **Random Forest** - Baseline, good interpretability
2. **Gradient Boosting (XGBoost/LightGBM)** - Higher accuracy
3. **Neural Network** - Maximum flexibility

**Implementation** (Using Gradient Boosting):
```python
# backend/app/ml/next_best_action.py
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import joblib
import json
from pathlib import Path
import numpy as np

class NextBestActionModel:
    """
    NBA Model predicts optimal next action for each lead:
    - call_immediate
    - email_nurture
    - schedule_appointment
    - send_proposal
    - no_action
    """

    def __init__(self, model_path: str = "./models"):
        self.model_path = Path(model_path)
        self.model_path.mkdir(exist_ok=True)
        self.model = None
        self.feature_pipeline = None
        self.classes = [
            'call_immediate', 'email_nurture', 'schedule_appointment',
            'send_proposal', 'no_action'
        ]

    def train(self, X_train, y_train, X_val, y_val):
        """Train NBA model with hyperparameter optimization"""
        from sklearn.model_selection import RandomizedSearchCV

        # Hyperparameter search space
        param_dist = {
            'n_estimators': [100, 200, 300],
            'learning_rate': [0.01, 0.05, 0.1],
            'max_depth': [3, 5, 7],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'subsample': [0.8, 0.9, 1.0]
        }

        # Base model
        base_model = GradientBoostingClassifier(random_state=42)

        # Randomized search
        search = RandomizedSearchCV(
            base_model,
            param_distributions=param_dist,
            n_iter=20,
            cv=5,
            scoring='f1_weighted',
            n_jobs=-1,
            random_state=42
        )

        print("Starting hyperparameter optimization...")
        search.fit(X_train, y_train)

        self.model = search.best_estimator_
        print(f"Best parameters: {search.best_params_}")
        print(f"Best CV score: {search.best_score_:.4f}")

        # Validate
        val_score = self.model.score(X_val, y_val)
        print(f"Validation accuracy: {val_score:.4f}")

        return self

    def evaluate(self, X_test, y_test):
        """Comprehensive model evaluation"""
        y_pred = self.model.predict(X_test)

        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='weighted'
        )

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)

        # Feature importance
        feature_importance = self.model.feature_importances_

        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': cm.tolist(),
            'feature_importance': feature_importance.tolist()
        }

        print("\n=== Model Evaluation ===")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1 Score: {f1:.4f}")

        return metrics

    def predict(self, X):
        """Predict next best action with confidence scores"""
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)

        results = []
        for pred, probs in zip(predictions, probabilities):
            results.append({
                'action': pred,
                'confidence': float(probs.max()),
                'all_probabilities': {
                    action: float(prob)
                    for action, prob in zip(self.classes, probs)
                }
            })

        return results

    def save(self, version: str = "1.0"):
        """Save model using joblib with protocol=5 (2025 best practice)"""
        model_file = self.model_path / f"nba_model_v{version}.joblib"
        joblib.dump(self.model, model_file, protocol=5)

        # Save metadata
        metadata = {
            'version': version,
            'classes': self.classes,
            'n_features': self.model.n_features_in_,
            'trained_at': pd.Timestamp.now().isoformat()
        }

        metadata_file = self.model_path / f"nba_model_v{version}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"Model saved to {model_file}")
        return model_file

    def load(self, version: str = "1.0"):
        """Load model from disk"""
        model_file = self.model_path / f"nba_model_v{version}.joblib"
        self.model = joblib.load(model_file)
        print(f"Model loaded from {model_file}")
        return self
```

**Training Script**:
```python
# backend/app/scripts/train_nba_model.py
import sys
sys.path.append('..')

from ml.data_extraction import DataExtractor
from ml.feature_engineering import build_feature_pipeline
from ml.next_best_action import NextBestActionModel

def main():
    print("=== NBA Model Training Pipeline ===\n")

    # 1. Extract data
    print("Step 1: Extracting data...")
    extractor = DataExtractor()
    df = extractor.extract_leads_data(months_back=12)
    df = extractor.clean_data(df)
    train, val, test = extractor.create_train_test_split(df)
    print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

    # 2. Build features
    print("\nStep 2: Feature engineering...")
    pipeline = build_feature_pipeline()
    X_train = pipeline.fit_transform(train)
    X_val = pipeline.transform(val)
    X_test = pipeline.transform(test)

    y_train = train['next_best_action']
    y_val = val['next_best_action']
    y_test = test['next_best_action']

    # 3. Train model
    print("\nStep 3: Training NBA model...")
    nba_model = NextBestActionModel()
    nba_model.train(X_train, y_train, X_val, y_val)

    # 4. Evaluate
    print("\nStep 4: Evaluating model...")
    metrics = nba_model.evaluate(X_test, y_test)

    # 5. Save
    print("\nStep 5: Saving model...")
    nba_model.save(version="1.0")

    print("\n✅ Training complete!")

if __name__ == "__main__":
    main()
```

**Success Criteria**:
- ✅ Validation accuracy: **≥85%**
- ✅ F1 score: **≥0.80**
- ✅ No class has recall **<70%**
- ✅ Model file size: **<50MB**

---

#### Task 2.2: Model Performance Optimization (2 hours)
**Objective**: Fine-tune hyperparameters and validate production readiness

**Optimization Checklist**:
- [ ] Cross-validation with k=5 folds
- [ ] Hyperparameter tuning (learning_rate, max_depth, n_estimators)
- [ ] Class imbalance handling (if needed)
- [ ] Feature selection (remove low-importance features)
- [ ] Calibration curve analysis

**Success Criteria**:
- ✅ Cross-validation score variance: **<5%**
- ✅ Training time: **<10 minutes**
- ✅ Inference latency: **<50ms per prediction**

---

### Day 3: FastAPI Integration (8 hours)

#### Task 3.1: Create ML Prediction Endpoints with Pydantic v2 (5 hours)
**Objective**: Build production-ready API endpoints using 2025 best practices

**Implementation**:
```python
# backend/app/routes/ml_predictions.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
from datetime import datetime
import joblib
from pathlib import Path

router = APIRouter(prefix="/api/v1/ml", tags=["ML Predictions"])

# Pydantic v2 models with modern patterns
class LeadFeatures(BaseModel):
    """Input features for NBA prediction (2025 Pydantic v2 pattern)"""
    model_config = ConfigDict(strict=True)

    lead_id: str = Field(..., description="Unique lead identifier")
    source: str = Field(..., description="Lead source channel")
    created_at: datetime = Field(..., description="Lead creation timestamp")
    last_interaction_at: Optional[datetime] = Field(None, description="Last interaction timestamp")
    interaction_count: int = Field(0, ge=0, description="Total interactions")
    email_open_rate: float = Field(0.0, ge=0.0, le=1.0, description="Email open rate (0-1)")
    response_rate: float = Field(0.0, ge=0.0, le=1.0, description="Response rate (0-1)")
    appointment_show_rate: float = Field(0.0, ge=0.0, le=1.0, description="Appointment show rate (0-1)")
    property_value: Optional[float] = Field(None, ge=0, description="Property value estimate")
    zip_code: str = Field(..., description="Property zip code")

class NBAprediction(BaseModel):
    """NBA prediction output (2025 Pydantic v2 pattern)"""
    model_config = ConfigDict(strict=True)

    lead_id: str
    action: str = Field(..., description="Recommended next action")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence (0-1)")
    all_probabilities: Dict[str, float] = Field(..., description="Probabilities for all actions")
    predicted_at: datetime = Field(default_factory=datetime.now)
    model_version: str = Field(default="1.0")

class BatchPredictionRequest(BaseModel):
    """Batch prediction request"""
    model_config = ConfigDict(strict=True)

    leads: List[LeadFeatures] = Field(..., max_length=100, description="Batch of leads (max 100)")

class BatchPredictionResponse(BaseModel):
    """Batch prediction response"""
    model_config = ConfigDict(strict=True)

    predictions: List[NBAprediction]
    processed_count: int
    failed_count: int
    processing_time_ms: float

# Load model on startup
model_path = Path("./models/nba_model_v1.0.joblib")
nba_model = None

@router.on_event("startup")
async def load_model():
    """Load NBA model on API startup"""
    global nba_model
    try:
        nba_model = joblib.load(model_path)
        print(f"✅ NBA model loaded from {model_path}")
    except Exception as e:
        print(f"❌ Failed to load NBA model: {e}")
        raise

@router.post("/predict/nba", response_model=NBAPredict)
async def predict_next_best_action(features: LeadFeatures):
    """
    Predict next best action for a single lead

    Returns:
        NBAPredict: Recommended action with confidence scores

    Raises:
        HTTPException: If model not loaded or prediction fails
    """
    if nba_model is None:
        raise HTTPException(status_code=503, detail="NBA model not loaded")

    try:
        # Transform features
        from app.ml.feature_engineering import build_feature_pipeline
        pipeline = build_feature_pipeline()
        X = pipeline.transform(features.model_dump())

        # Predict
        prediction = nba_model.predict(X)[0]
        probabilities = nba_model.predict_proba(X)[0]

        # Format response
        result = NBAPredict(
            lead_id=features.lead_id,
            action=prediction,
            confidence=float(probabilities.max()),
            all_probabilities={
                action: float(prob)
                for action, prob in zip(nba_model.classes_, probabilities)
            }
        )

        # Log prediction to database
        await log_prediction(result)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/predict/nba/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest):
    """
    Batch prediction for multiple leads (max 100)

    Optimized for throughput with parallel processing
    """
    import time
    start_time = time.time()

    if nba_model is None:
        raise HTTPException(status_code=503, detail="NBA model not loaded")

    predictions = []
    failed = 0

    for lead in request.leads:
        try:
            # Transform and predict
            from app.ml.feature_engineering import build_feature_pipeline
            pipeline = build_feature_pipeline()
            X = pipeline.transform(lead.model_dump())

            prediction = nba_model.predict(X)[0]
            probabilities = nba_model.predict_proba(X)[0]

            predictions.append(NBAPredict(
                lead_id=lead.lead_id,
                action=prediction,
                confidence=float(probabilities.max()),
                all_probabilities={
                    action: float(prob)
                    for action, prob in zip(nba_model.classes_, probabilities)
                }
            ))
        except Exception as e:
            print(f"Failed to predict for lead {lead.lead_id}: {e}")
            failed += 1

    processing_time = (time.time() - start_time) * 1000  # ms

    return BatchPredictionResponse(
        predictions=predictions,
        processed_count=len(predictions),
        failed_count=failed,
        processing_time_ms=processing_time
    )

async def log_prediction(prediction: NBAPredict):
    """Log prediction to database for monitoring"""
    from app.database import get_db

    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO ml_predictions (lead_id, model_type, prediction_value, confidence_score, created_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            prediction.lead_id,
            'nba',
            prediction.action,
            prediction.confidence,
            prediction.predicted_at
        )
```

**OpenAI Integration for Enhanced Predictions** (2025 Structured Outputs Pattern):
```python
# backend/app/integrations/ai/openai_nba.py
from openai import OpenAI
from pydantic import BaseModel
from typing import List
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class EnhancedNBARecommendation(BaseModel):
    """Enhanced NBA recommendation with GPT-4 reasoning"""
    action: str
    reasoning: str
    talking_points: List[str]
    urgency_level: str  # 'low', 'medium', 'high', 'critical'
    estimated_conversion_probability: float

async def enhance_nba_with_gpt4(lead_data: dict, ml_prediction: str) -> EnhancedNBARecommendation:
    """
    Use GPT-4 Turbo with Structured Outputs to enhance ML prediction

    2025 Best Practice: Using response_format with Pydantic for guaranteed schema adherence
    """

    system_prompt = """You are an expert sales strategist for a premium roofing company.

    Given lead data and an ML-predicted next best action, provide:
    1. Refined action recommendation with strategic reasoning
    2. Specific talking points for the sales rep
    3. Urgency assessment
    4. Estimated conversion probability
    """

    user_prompt = f"""
    Lead Data:
    {lead_data}

    ML Predicted Action: {ml_prediction}

    Provide enhanced recommendation.
    """

    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",  # 2025 recommended model
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "enhanced_nba_recommendation",
                "strict": True,
                "schema": EnhancedNBARecommendation.model_json_schema()
            }
        }
    )

    # Parse response with guaranteed schema match (2025 feature)
    result = EnhancedNBARecommendation.model_validate_json(
        response.choices[0].message.content
    )

    return result

@router.post("/predict/nba/enhanced", response_model=EnhancedNBARecommendation)
async def predict_nba_enhanced(features: LeadFeatures):
    """
    Enhanced NBA prediction combining ML + GPT-4 reasoning

    Best for high-value leads requiring strategic guidance
    """
    # Get ML prediction first
    ml_prediction = await predict_next_best_action(features)

    # Enhance with GPT-4
    enhanced = await enhance_nba_with_gpt4(
        lead_data=features.model_dump(),
        ml_prediction=ml_prediction.action
    )

    return enhanced
```

**Success Criteria**:
- ✅ API response time: **<200ms** (single prediction)
- ✅ Batch throughput: **>100 predictions/second**
- ✅ Error rate: **<0.1%**
- ✅ OpenAPI documentation: **100% complete**

---

#### Task 3.2: Add Caching and Rate Limiting (3 hours)
**Objective**: Implement production-grade performance and security features

**Redis Caching Implementation**:
```python
# backend/app/utils/redis_cache.py
import redis
import json
from functools import wraps
import hashlib

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 1)),
    decode_responses=True
)

def cache_prediction(ttl: int = 3600):
    """Cache prediction results for TTL seconds"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function args
            cache_key = f"nba:{hashlib.md5(json.dumps(kwargs).encode()).hexdigest()}"

            # Check cache
            cached = redis_client.get(cache_key)
            if cached:
                print(f"Cache hit: {cache_key}")
                return json.loads(cached)

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            redis_client.setex(cache_key, ttl, json.dumps(result))

            return result
        return wrapper
    return decorator

# Apply to endpoint
@router.post("/predict/nba")
@cache_prediction(ttl=3600)
async def predict_next_best_action(features: LeadFeatures):
    # ... prediction logic
```

**Rate Limiting**:
```python
# backend/app/middleware/rate_limit.py
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# Apply to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Rate limit endpoint
@router.post("/predict/nba")
@limiter.limit("100/minute")
async def predict_next_best_action(request: Request, features: LeadFeatures):
    # ... prediction logic
```

**Success Criteria**:
- ✅ Cache hit rate: **>80%** for repeat requests
- ✅ Rate limiting: **100 requests/minute per IP**
- ✅ Redis connection pooling enabled
- ✅ Graceful degradation if Redis unavailable

---

### Day 4: Streamlit Dashboard (8 hours)

#### Task 4.1: Build ML Metrics Dashboard (6 hours)
**Objective**: Create interactive dashboard for monitoring NBA model performance

**Implementation**:
```python
# frontend-streamlit/pages/phase4/ml_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="ML Dashboard", layout="wide")

def load_model_metrics():
    """Load model performance metrics from API"""
    response = requests.get("http://localhost:8000/api/v1/ml/metrics")
    return response.json()

def load_recent_predictions(days: int = 7):
    """Load recent predictions from database"""
    response = requests.get(
        f"http://localhost:8000/api/v1/ml/predictions/recent?days={days}"
    )
    return pd.DataFrame(response.json())

# Page title
st.title("🧠 ML Model Performance Dashboard")
st.markdown("Real-time monitoring of NBA prediction model")

# Metrics row
col1, col2, col3, col4 = st.columns(4)

metrics = load_model_metrics()

with col1:
    st.metric(
        "Model Accuracy",
        f"{metrics['accuracy']:.2%}",
        delta=f"{metrics['accuracy_change']:.2%}"
    )

with col2:
    st.metric(
        "Predictions Today",
        f"{metrics['predictions_today']:,}",
        delta=f"{metrics['predictions_change']:+,}"
    )

with col3:
    st.metric(
        "Avg Confidence",
        f"{metrics['avg_confidence']:.2%}",
        delta=f"{metrics['confidence_change']:.2%}"
    )

with col4:
    st.metric(
        "API Latency (ms)",
        f"{metrics['avg_latency_ms']:.0f}",
        delta=f"{metrics['latency_change']:.0f}",
        delta_color="inverse"
    )

st.divider()

# Confusion Matrix
st.subheader("📊 Confusion Matrix")
cm = pd.DataFrame(
    metrics['confusion_matrix'],
    index=metrics['classes'],
    columns=metrics['classes']
)

fig_cm = px.imshow(
    cm,
    labels=dict(x="Predicted", y="Actual", color="Count"),
    x=cm.columns,
    y=cm.index,
    color_continuous_scale="Blues",
    text_auto=True
)
fig_cm.update_layout(height=500)
st.plotly_chart(fig_cm, use_container_width=True)

# Prediction Distribution
col1, col2 = st.columns(2)

with col1:
    st.subheader("🎯 Action Distribution")
    predictions_df = load_recent_predictions(days=7)

    action_counts = predictions_df['action'].value_counts()
    fig_actions = px.pie(
        values=action_counts.values,
        names=action_counts.index,
        title="Recommended Actions (Last 7 Days)"
    )
    st.plotly_chart(fig_actions, use_container_width=True)

with col2:
    st.subheader("📈 Confidence Distribution")
    fig_confidence = px.histogram(
        predictions_df,
        x="confidence",
        nbins=20,
        title="Prediction Confidence Scores"
    )
    fig_confidence.update_layout(
        xaxis_title="Confidence Score",
        yaxis_title="Count"
    )
    st.plotly_chart(fig_confidence, use_container_width=True)

# Time Series
st.subheader("⏱️ Predictions Over Time")
predictions_by_day = predictions_df.groupby(
    predictions_df['predicted_at'].dt.date
).size().reset_index(name='count')

fig_timeseries = px.line(
    predictions_by_day,
    x='predicted_at',
    y='count',
    title="Daily Prediction Volume"
)
fig_timeseries.update_layout(
    xaxis_title="Date",
    yaxis_title="Predictions"
)
st.plotly_chart(fig_timeseries, use_container_width=True)

# Feature Importance
st.subheader("🔍 Feature Importance")
feature_importance = pd.DataFrame({
    'feature': metrics['feature_names'],
    'importance': metrics['feature_importance']
}).sort_values('importance', ascending=False).head(10)

fig_features = px.bar(
    feature_importance,
    x='importance',
    y='feature',
    orientation='h',
    title="Top 10 Most Important Features"
)
st.plotly_chart(fig_features, use_container_width=True)

# Model Version Info
st.divider()
st.subheader("ℹ️ Model Information")
col1, col2, col3 = st.columns(3)

with col1:
    st.write(f"**Model Version:** {metrics['model_version']}")
    st.write(f"**Algorithm:** Gradient Boosting")

with col2:
    st.write(f"**Trained:** {metrics['trained_at']}")
    st.write(f"**Features:** {metrics['n_features']}")

with col3:
    st.write(f"**Training Samples:** {metrics['n_training_samples']:,}")
    st.write(f"**Classes:** {len(metrics['classes'])}")

# Recent Predictions Table
st.subheader("📋 Recent Predictions")
st.dataframe(
    predictions_df[['lead_id', 'action', 'confidence', 'predicted_at']].head(20),
    use_container_width=True
)

# Refresh button
if st.button("🔄 Refresh Data"):
    st.rerun()
```

**Success Criteria**:
- ✅ Dashboard loads in **<2 seconds**
- ✅ All charts render correctly
- ✅ Real-time data updates every **60 seconds**
- ✅ Mobile-responsive design

---

#### Task 4.2: Add Live Prediction Testing (2 hours)
**Objective**: Interactive widget for testing NBA predictions in real-time

**Implementation**:
```python
# Add to ml_dashboard.py

st.divider()
st.subheader("🧪 Test NBA Prediction")

with st.form("prediction_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        source = st.selectbox("Lead Source", ["Google Ads", "Facebook", "Referral", "Organic"])
        interaction_count = st.number_input("Interactions", min_value=0, value=5)

    with col2:
        email_open_rate = st.slider("Email Open Rate", 0.0, 1.0, 0.5)
        response_rate = st.slider("Response Rate", 0.0, 1.0, 0.3)

    with col3:
        property_value = st.number_input("Property Value ($)", min_value=0, value=500000)
        zip_code = st.text_input("Zip Code", value="48302")

    submit = st.form_submit_button("🚀 Get Prediction")

    if submit:
        # Call API
        payload = {
            "lead_id": "test-" + datetime.now().isoformat(),
            "source": source,
            "created_at": (datetime.now() - timedelta(days=7)).isoformat(),
            "last_interaction_at": (datetime.now() - timedelta(days=2)).isoformat(),
            "interaction_count": interaction_count,
            "email_open_rate": email_open_rate,
            "response_rate": response_rate,
            "appointment_show_rate": 0.5,
            "property_value": property_value,
            "zip_code": zip_code
        }

        response = requests.post(
            "http://localhost:8000/api/v1/ml/predict/nba",
            json=payload
        )

        if response.status_code == 200:
            result = response.json()

            st.success(f"✅ Recommended Action: **{result['action']}**")
            st.info(f"Confidence: **{result['confidence']:.2%}**")

            # Show all probabilities
            st.write("**All Action Probabilities:**")
            probs_df = pd.DataFrame([result['all_probabilities']]).T
            probs_df.columns = ['Probability']
            probs_df = probs_df.sort_values('Probability', ascending=False)

            fig = px.bar(probs_df, x=probs_df.index, y='Probability')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"❌ Prediction failed: {response.text}")
```

---

### Day 5: n8n Integration & Testing (8 hours)

#### Task 5.1: Configure n8n AI Agent Workflows (4 hours)
**Objective**: Set up automated ML pipeline orchestration using n8n 2025 best practices

**Workflow 1: Automated NBA Predictions for New Leads**
```json
{
  "name": "Auto-NBA-Prediction-New-Leads",
  "nodes": [
    {
      "parameters": {
        "mode": "webhook",
        "webhookUrl": "/webhook/new-lead"
      },
      "name": "New Lead Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300]
    },
    {
      "parameters": {
        "system": "You are an ML data validator. Ensure lead data has all required fields for NBA prediction.",
        "messages": [
          "Validate this lead data: {{ $json.lead }}"
        ]
      },
      "name": "AI Data Validator",
      "type": "@n8n/n8n-nodes-langchain.agent",
      "position": [450, 300],
      "typeVersion": 1.1
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://localhost:8000/api/v1/ml/predict/nba",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "options": {
          "timeout": 5000
        },
        "bodyParameters": {
          "parameters": [
            {
              "name": "lead_id",
              "value": "={{ $json.lead.id }}"
            },
            {
              "name": "source",
              "value": "={{ $json.lead.source }}"
            }
          ]
        }
      },
      "name": "Call NBA Prediction API",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300]
    },
    {
      "parameters": {
        "system": "You are a sales strategy advisor. Based on the NBA prediction, create actionable tasks for the sales rep.",
        "messages": [
          "NBA Prediction: {{ $json.action }}\nConfidence: {{ $json.confidence }}\nLead ID: {{ $json.lead_id }}\n\nCreate task list."
        ],
        "model": "gpt-4-turbo-preview",
        "memory": {
          "type": "windowBuffer",
          "sessionKey": "={{ $json.lead_id }}",
          "contextWindowLength": 10
        }
      },
      "name": "AI Task Generator",
      "type": "@n8n/n8n-nodes-langchain.agent",
      "position": [850, 300]
    },
    {
      "parameters": {
        "resource": "database",
        "operation": "executeQuery",
        "query": "INSERT INTO ml_predictions (lead_id, model_type, prediction_value, confidence_score) VALUES ($1, $2, $3, $4)",
        "queryParameters": {
          "parameters": [
            "={{ $json.lead_id }}",
            "nba",
            "={{ $json.action }}",
            "={{ $json.confidence }}"
          ]
        }
      },
      "name": "Log to Database",
      "type": "n8n-nodes-base.postgres",
      "position": [1050, 300]
    },
    {
      "parameters": {
        "resource": "task",
        "operation": "create",
        "subject": "NBA Action: {{ $json.action }}",
        "description": "{{ $json.task_description }}",
        "assigned_to": "={{ $json.assigned_rep_id }}"
      },
      "name": "Create CRM Task",
      "type": "n8n-nodes-base.accuLynx",
      "position": [1250, 300]
    }
  ],
  "connections": {
    "New Lead Webhook": {
      "main": [[{"node": "AI Data Validator", "type": "main", "index": 0}]]
    },
    "AI Data Validator": {
      "main": [[{"node": "Call NBA Prediction API", "type": "main", "index": 0}]]
    },
    "Call NBA Prediction API": {
      "main": [[{"node": "AI Task Generator", "type": "main", "index": 0}]]
    },
    "AI Task Generator": {
      "main": [
        [
          {"node": "Log to Database", "type": "main", "index": 0},
          {"node": "Create CRM Task", "type": "main", "index": 0}
        ]
      ]
    }
  }
}
```

**Workflow 2: Daily Model Performance Monitoring**
```json
{
  "name": "Daily-ML-Model-Monitoring",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [{"field": "cronExpression", "expression": "0 9 * * *"}]
        }
      },
      "name": "Daily Trigger (9 AM)",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [250, 300]
    },
    {
      "parameters": {
        "method": "GET",
        "url": "http://localhost:8000/api/v1/ml/metrics"
      },
      "name": "Fetch Model Metrics",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300]
    },
    {
      "parameters": {
        "system": "You are an ML performance analyst. Analyze model metrics and identify issues or improvements.",
        "messages": [
          "Analyze these metrics:\nAccuracy: {{ $json.accuracy }}\nPredictions: {{ $json.predictions_today }}\nLatency: {{ $json.avg_latency_ms }}ms\n\nProvide insights."
        ],
        "model": "claude-3-opus-20240229",
        "tools": [
          {
            "toolType": "code",
            "language": "python"
          }
        ]
      },
      "name": "AI Performance Analyzer",
      "type": "@n8n/n8n-nodes-langchain.agent",
      "position": [650, 300]
    },
    {
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{ $json.accuracy }}",
              "operation": "smaller",
              "value2": 0.85
            }
          ]
        }
      },
      "name": "Check if Accuracy Dropped",
      "type": "n8n-nodes-base.if",
      "position": [850, 300]
    },
    {
      "parameters": {
        "fromEmail": "ml-alerts@iswitch-roofs.com",
        "toEmail": "data-team@iswitch-roofs.com",
        "subject": "🚨 NBA Model Accuracy Alert",
        "text": "Model accuracy dropped below 85%:\n\nCurrent: {{ $json.accuracy }}\nAnalysis: {{ $json.analysis }}"
      },
      "name": "Send Alert Email",
      "type": "n8n-nodes-base.emailSend",
      "position": [1050, 200]
    },
    {
      "parameters": {
        "resource": "file",
        "operation": "write",
        "fileName": "daily_ml_report_{{ $now.toFormat('yyyy-MM-dd') }}.json",
        "fileContent": "={{ JSON.stringify($json, null, 2) }}"
      },
      "name": "Save Report",
      "type": "n8n-nodes-base.fs",
      "position": [1050, 400]
    }
  ],
  "connections": {
    "Daily Trigger (9 AM)": {
      "main": [[{"node": "Fetch Model Metrics", "type": "main", "index": 0}]]
    },
    "Fetch Model Metrics": {
      "main": [[{"node": "AI Performance Analyzer", "type": "main", "index": 0}]]
    },
    "AI Performance Analyzer": {
      "main": [[{"node": "Check if Accuracy Dropped", "type": "main", "index": 0}]]
    },
    "Check if Accuracy Dropped": {
      "main": [
        [{"node": "Send Alert Email", "type": "main", "index": 0}],
        [{"node": "Save Report", "type": "main", "index": 0}]
      ]
    }
  }
}
```

**Success Criteria**:
- ✅ Workflows execute without errors
- ✅ AI agents respond in **<5 seconds**
- ✅ Memory persistence works across sessions
- ✅ Error handling and retry logic functional

---

#### Task 5.2: Write Comprehensive Tests (4 hours)
**Objective**: Ensure 80%+ test coverage for all ML components

**Test Suite**:
```python
# backend/tests/test_nba_model.py
import pytest
import pandas as pd
import numpy as np
from app.ml.next_best_action import NextBestActionModel
from app.ml.feature_engineering import build_feature_pipeline

@pytest.fixture
def sample_data():
    """Generate sample lead data for testing"""
    return pd.DataFrame({
        'lead_id': [f'lead_{i}' for i in range(100)],
        'source': np.random.choice(['Google', 'Facebook', 'Referral'], 100),
        'created_at': pd.date_range('2025-01-01', periods=100, freq='D'),
        'interaction_count': np.random.randint(0, 20, 100),
        'email_open_rate': np.random.uniform(0, 1, 100),
        'response_rate': np.random.uniform(0, 1, 100),
        'next_best_action': np.random.choice(
            ['call_immediate', 'email_nurture', 'schedule_appointment'], 100
        )
    })

def test_feature_pipeline(sample_data):
    """Test feature engineering pipeline"""
    pipeline = build_feature_pipeline()
    X = pipeline.fit_transform(sample_data)

    assert X.shape[0] == 100
    assert not np.isnan(X).any()
    assert not np.isinf(X).any()

def test_model_training(sample_data):
    """Test NBA model training"""
    from sklearn.model_selection import train_test_split

    X = sample_data.drop('next_best_action', axis=1)
    y = sample_data['next_best_action']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = NextBestActionModel()
    model.train(X_train, y_train, X_test, y_test)

    assert model.model is not None
    score = model.model.score(X_test, y_test)
    assert score > 0.5  # At least better than random

def test_model_prediction(sample_data):
    """Test NBA model prediction"""
    model = NextBestActionModel()
    model.load(version="1.0")

    X = sample_data.drop('next_best_action', axis=1).head(10)
    predictions = model.predict(X)

    assert len(predictions) == 10
    assert all('action' in p for p in predictions)
    assert all('confidence' in p for p in predictions)
    assert all(0 <= p['confidence'] <= 1 for p in predictions)

def test_model_save_load():
    """Test model persistence"""
    from sklearn.ensemble import GradientBoostingClassifier

    model = NextBestActionModel()
    model.model = GradientBoostingClassifier()

    # Save
    model_file = model.save(version="test")
    assert model_file.exists()

    # Load
    loaded_model = NextBestActionModel()
    loaded_model.load(version="test")
    assert loaded_model.model is not None

@pytest.mark.asyncio
async def test_api_prediction_endpoint():
    """Test FastAPI prediction endpoint"""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    payload = {
        "lead_id": "test-123",
        "source": "Google",
        "created_at": "2025-01-01T00:00:00",
        "interaction_count": 5,
        "email_open_rate": 0.5,
        "response_rate": 0.3,
        "appointment_show_rate": 0.6,
        "property_value": 500000,
        "zip_code": "48302"
    }

    response = client.post("/api/v1/ml/predict/nba", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert 'action' in data
    assert 'confidence' in data
    assert 0 <= data['confidence'] <= 1

@pytest.mark.asyncio
async def test_api_batch_prediction():
    """Test batch prediction endpoint"""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    payload = {
        "leads": [
            {
                "lead_id": f"test-{i}",
                "source": "Google",
                "created_at": "2025-01-01T00:00:00",
                "interaction_count": i,
                "email_open_rate": 0.5,
                "response_rate": 0.3,
                "appointment_show_rate": 0.6,
                "property_value": 500000,
                "zip_code": "48302"
            }
            for i in range(10)
        ]
    }

    response = client.post("/api/v1/ml/predict/nba/batch", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data['processed_count'] == 10
    assert len(data['predictions']) == 10

def test_redis_cache():
    """Test Redis caching functionality"""
    from app.utils.redis_cache import redis_client, cache_prediction

    # Test connection
    assert redis_client.ping()

    # Test caching
    @cache_prediction(ttl=60)
    async def dummy_prediction(lead_id: str):
        return {"action": "call_immediate", "confidence": 0.95}

    import asyncio
    result1 = asyncio.run(dummy_prediction("test-123"))
    result2 = asyncio.run(dummy_prediction("test-123"))  # Should hit cache

    assert result1 == result2

@pytest.mark.integration
def test_n8n_workflow_execution():
    """Test n8n workflow execution"""
    import requests

    # Trigger n8n workflow via webhook
    response = requests.post(
        "http://localhost:5678/webhook/new-lead",
        json={
            "lead": {
                "id": "test-n8n-123",
                "source": "Google",
                "created_at": "2025-01-01T00:00:00"
            }
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert 'prediction' in data
```

**Run Tests**:
```bash
# Run all tests with coverage
pytest backend/tests/test_nba_model.py -v --cov=app/ml --cov-report=html

# Run only unit tests
pytest backend/tests/test_nba_model.py -v -m "not integration"

# Run only integration tests
pytest backend/tests/test_nba_model.py -v -m integration
```

**Success Criteria**:
- ✅ Test coverage: **≥80%**
- ✅ All tests pass
- ✅ No flaky tests
- ✅ Integration tests cover API + n8n workflows

---

## Week 8 Deliverables Checklist

### Code Artifacts
- [ ] `backend/app/ml/data_extraction.py` - Data extraction module
- [ ] `backend/app/ml/feature_engineering.py` - Feature pipeline
- [ ] `backend/app/ml/next_best_action.py` - NBA model class
- [ ] `backend/app/routes/ml_predictions.py` - FastAPI endpoints
- [ ] `backend/app/integrations/ai/openai_nba.py` - GPT-4 enhancement
- [ ] `backend/app/utils/redis_cache.py` - Caching utilities
- [ ] `backend/app/middleware/rate_limit.py` - Rate limiting
- [ ] `frontend-streamlit/pages/phase4/ml_dashboard.py` - Streamlit dashboard
- [ ] `backend/tests/test_nba_model.py` - Comprehensive test suite

### n8n Workflows
- [ ] `Auto-NBA-Prediction-New-Leads` workflow
- [ ] `Daily-ML-Model-Monitoring` workflow

### Documentation
- [ ] `docs/phase4/WEEK_8_RESULTS.md` - Implementation results
- [ ] `docs/phase4/api/ML_API_REFERENCE.md` - API documentation
- [ ] `backend/models/nba_model_v1.0_metadata.json` - Model metadata

### Database
- [ ] NBA model training data in Supabase
- [ ] `ml_predictions` table populated with test predictions
- [ ] Redis cache configured and operational

### Deployment
- [ ] NBA model deployed to staging environment
- [ ] FastAPI endpoints live at `http://staging.iswitch-roofs.com/api/v1/ml`
- [ ] Streamlit dashboard accessible at `http://staging.iswitch-roofs.com/ml-dashboard`
- [ ] n8n workflows deployed and scheduled

---

## Success Validation

### Performance Benchmarks
```bash
# API latency test
ab -n 1000 -c 10 http://localhost:8000/api/v1/ml/predict/nba

# Expected: Average response time <200ms
```

### Accuracy Validation
```bash
# Run validation script
python backend/app/scripts/validate_nba_model.py

# Expected output:
# ✅ Validation Accuracy: 87.3%
# ✅ F1 Score: 0.84
# ✅ All classes recall >70%
```

### Dashboard Load Test
```bash
# Streamlit load test
locust -f tests/load/test_dashboard.py --host=http://localhost:8501

# Expected: 100 concurrent users, <2s load time
```

---

## Risk Mitigation

### Potential Issues & Solutions

1. **Insufficient Training Data**
   - **Risk**: <10,000 lead records
   - **Mitigation**: Use data augmentation, transfer learning from similar datasets

2. **Model Overfitting**
   - **Risk**: High training accuracy, low validation accuracy
   - **Mitigation**: Cross-validation, regularization, early stopping

3. **API Performance Degradation**
   - **Risk**: Slow predictions under load
   - **Mitigation**: Redis caching, model quantization, horizontal scaling

4. **n8n Workflow Failures**
   - **Risk**: API timeouts, webhook issues
   - **Mitigation**: Retry logic, error queues, monitoring alerts

---

## Next Week Preview

**Week 9 Focus**: CLV & Churn Prediction Models
- Customer Lifetime Value forecasting
- 30/60-day churn prediction
- Multi-model ensemble
- Enhanced dashboard with CLV metrics

---

## Resources & References

### 2025 Best Practices Documentation
- [OpenAI Production Best Practices](https://platform.openai.com/docs/guides/production-best-practices)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [n8n LLM Agents Guide](https://blog.n8n.io/llm-agents/)
- [scikit-learn Model Persistence](https://scikit-learn.org/stable/model_persistence.html)

### Internal Documentation
- [Phase 4 Execution Plan](../PHASE_4_EXECUTION_PLAN.md)
- [n8n AI Agents Specifications](../PHASE_4_N8N_AI_AGENTS_PLAN.md)
- [Setup Completion Report](../../PHASE_4_SETUP_COMPLETE.md)

---

**Status**: 📋 Plan Complete - Ready for Execution
**Estimated Effort**: 40 hours (5 days × 8 hours)
**Priority**: HIGH
**Dependencies**: Phase 4 setup completed ✅

**Next Action**: Begin Day 1 data extraction implementation
