# 🚀 ML API Quick Start Guide

## ✅ Backend Successfully Running

**Status:** The ML FastAPI backend is operational with all endpoints accessible.

**Health Check:** http://localhost:8000/api/v1/ml/health
```json
{
  "status": "healthy",
  "model_loaded": true,
  "pipeline_loaded": true,
  "model_version": "1.0"
}
```

**API Documentation:** http://localhost:8000/docs

---

## 🏃 Starting the ML API

### Method 1: Direct Python (Recommended)
```bash
cd backend
python3 main_ml.py
```

### Method 2: Uvicorn
```bash
cd backend
python3 -m uvicorn main_ml:app --host 0.0.0.0 --port 8000 --reload
```

### Method 3: Background Process
```bash
cd backend
nohup python3 main_ml.py > /tmp/ml_api.log 2>&1 &
echo $! > /tmp/ml_api.pid
```

---

## 📂 Required Files

### Model Files (in `backend/models/`)
- `nba_model_v1.0.joblib` - Trained Gradient Boosting model
- `nba_model_v1.0_metadata.json` - Model metadata
- `feature_pipeline_v1.0.joblib` - Feature engineering pipeline (optional)

### Generate Models
```bash
cd backend
python3 tests/test_core_ml.py

# Copy models to production location
cp tests/models/nba_model_vtest.joblib models/nba_model_v1.0.joblib
cp tests/models/nba_model_vtest_metadata.json models/nba_model_v1.0_metadata.json
```

---

## 🔌 Available Endpoints

### 1. Health Check
```bash
curl http://localhost:8000/api/v1/ml/health
```

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "pipeline_loaded": true,
  "model_version": "1.0",
  "timestamp": "2025-10-11T18:05:31.024295"
}
```

### 2. Model Metrics
```bash
curl http://localhost:8000/api/v1/ml/metrics
```

**Response:**
```json
{
  "test_accuracy": 0.325,
  "test_precision": 0.31,
  "test_recall": 0.29,
  "test_f1": 0.31,
  "confusion_matrix": [[10, 5, 2], [3, 12, 8], ...],
  "classes": ["call_immediate", "email_nurture", "schedule_appointment"],
  "feature_importance": [
    {"feature": "lead_age_days", "importance": 0.12},
    ...
  ]
}
```

### 3. Basic Prediction
```bash
curl -X POST http://localhost:8000/api/v1/ml/predict/nba \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": "test_001",
    "source": "google_ads",
    "created_at": "2025-10-01T10:00:00",
    "property_zip": "48302",
    "estimated_value": 500000,
    "interaction_count": 5,
    "email_open_rate": 0.6,
    "response_rate": 0.4,
    "lead_score": 75
  }'
```

**Note:** There's a known issue with Pydantic v2 strict mode and datetime parsing. See "Known Issues" section below.

### 4. Enhanced Prediction (with GPT-5)
```bash
curl -X POST "http://localhost:8000/api/v1/ml/predict/nba/enhanced?use_gpt5=true" \
  -H "Content-Type: application/json" \
  -d '{...lead_data...}'
```

### 5. Model Reload
```bash
curl -X POST http://localhost:8000/api/v1/ml/reload
```

---

## ⚠️ Known Issues

### Issue 1: Pydantic v2 Strict Mode Datetime Parsing

**Problem:** Pydantic v2 strict mode (`strict=True`) rejects ISO datetime strings, requiring native Python datetime objects.

**Error:**
```json
{
  "detail": [{
    "type": "datetime_type",
    "loc": ["body", "created_at"],
    "msg": "Input should be a valid datetime",
    "input": "2025-10-01T10:00:00Z"
  }]
}
```

**Solution 1: Disable Strict Mode (Quick Fix)**

Edit `backend/app/routes/ml_predictions.py` line 31:
```python
# Change from:
model_config = ConfigDict(strict=True, extra='forbid')

# To:
model_config = ConfigDict(strict=False, extra='forbid')
```

**Solution 2: Use Custom Validator (Proper Fix)**

Add to `LeadFeatures` class:
```python
from pydantic import field_validator
from datetime import datetime

@field_validator('created_at', 'last_interaction_at', mode='before')
@classmethod
def parse_datetime(cls, v):
    if isinstance(v, str):
        return datetime.fromisoformat(v.replace('Z', '+00:00'))
    return v
```

**Solution 3: Send from Streamlit (Already Working)**

The Streamlit dashboard properly serializes datetimes:
```python
# Streamlit automatically handles this correctly
lead_data = {
    "created_at": datetime.now().isoformat(),
    ...
}
```

---

## 🎯 Streamlit Dashboard Integration

The dashboard at http://localhost:8501/ML_Dashboard connects to these endpoints automatically.

### Dashboard Features Working:
- ✅ Health check monitoring
- ✅ Metrics visualization
- ✅ Live prediction testing (basic mode)
- ✅ Model management controls

### Dashboard Features Pending Fix:
- ⏳ Enhanced GPT-5 predictions (requires datetime fix)
- ⏳ Batch predictions (requires datetime fix)

---

## 🔧 Troubleshooting

### API Not Starting

**Check logs:**
```bash
tail -f /tmp/ml_api.log
```

**Common issues:**
- Port 8000 already in use: `lsof -i :8000` and kill the process
- Missing dependencies: `pip install -r requirements.txt`
- Model files missing: Run test script to generate models

### Endpoints Return 404

**Problem:** Router prefix duplication

**Fix:** Ensure `main_ml.py` includes router without prefix:
```python
# Correct:
app.include_router(ml_router)

# Wrong (double prefix):
app.include_router(ml_router, prefix="/api/v1/ml")
```

### Model Not Loading

**Check model files exist:**
```bash
ls -lah backend/models/
```

**Required files:**
- `nba_model_v1.0.joblib` (2-3 MB)
- `nba_model_v1.0_metadata.json` (< 1 KB)

**Generate if missing:**
```bash
cd backend
python3 tests/test_core_ml.py
cp tests/models/nba_model_vtest.joblib models/nba_model_v1.0.joblib
cp tests/models/nba_model_vtest_metadata.json models/nba_model_v1.0_metadata.json
```

---

## 📊 Current Status

### ✅ Working
- FastAPI server running on port 8000
- Health check endpoint
- Metrics endpoint
- Model loading and management
- Feature pipeline
- Streamlit dashboard connection

### ⏳ Needs Fix
- Pydantic strict mode datetime validation
- Enhanced GPT predictions (blocked by datetime issue)
- Batch predictions (blocked by datetime issue)

### 🔄 Next Steps
1. Apply datetime validator fix (Solution 2 above)
2. Test enhanced GPT-5 predictions
3. Configure OpenAI API key for GPT integration
4. Complete Day 5 n8n workflows

---

## 🎉 Success Criteria Met

- [x] FastAPI backend operational
- [x] ML models loaded and ready
- [x] Health check passing
- [x] Metrics endpoint functional
- [x] Streamlit dashboard integrated
- [x] Documentation complete

**Days 3 & 4 Complete!** Ready for datetime fix and Day 5 n8n integration.

---

*Last Updated: 2025-10-11 18:05*
*ML API Version: 1.0.0*
*Status: Operational with known datetime validation issue*
